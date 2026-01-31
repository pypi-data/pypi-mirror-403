"""Main AutoScaler class for deep_dimensions.

This module provides the primary public API for the library,
supporting both PyTorch and TensorFlow.
"""

from typing import Any, Literal, Tuple, Union

from deep_dimensions.config.settings import ScalingConfig
from deep_dimensions.core.exceptions import FrameworkNotAvailableError
from deep_dimensions.frameworks.registry import FrameworkRegistry
from deep_dimensions.interfaces.framework_adapter import IFrameworkAdapter
from deep_dimensions.interfaces.memory_provider import MemoryInfo
from deep_dimensions.interfaces.scaling_strategy import ScalingResult
from deep_dimensions.memory.monitor import MemoryMonitor
from deep_dimensions.scaling.calculator import DimensionCalculator
from deep_dimensions.utils.logging import configure_logging, get_logger
from deep_dimensions.utils.validation import validate_dimensions

logger = get_logger(__name__)


class AutoScaler:
    """Main interface for automatic dimension scaling.
    
    Supports both PyTorch and TensorFlow frameworks.
    
    Example:
        >>> # PyTorch
        >>> scaler = AutoScaler(framework="pytorch")
        >>> dims = scaler.scale_dimensions((4096, 4096, 3))
        
        >>> # TensorFlow
        >>> scaler = AutoScaler(framework="tensorflow")
        >>> dims = scaler.scale_dimensions((4096, 4096, 3))
        
        >>> # Auto-detect
        >>> scaler = AutoScaler()
        >>> tensor = scaler.create_scaled_tensor((2048, 2048, 3))
    """

    def __init__(
        self,
        config: ScalingConfig | None = None,
        framework: Literal["pytorch", "tensorflow", "auto"] | None = None,
    ) -> None:
        """Initialize the AutoScaler.
        
        Args:
            config: Optional scaling configuration.
            framework: Framework to use. Overrides config.framework if provided.
        """
        self._config = config or ScalingConfig()
        
        # Configure logging
        configure_logging(level=self._config.log_level)
        
        # Determine framework
        framework_choice = framework or self._config.framework
        
        # Initialize framework registry and get adapter
        self._registry = FrameworkRegistry()
        
        if framework_choice == "auto":
            try:
                self._adapter = self._registry.get_default_adapter()
            except RuntimeError as e:
                raise FrameworkNotAvailableError(str(e), framework="auto")
        else:
            try:
                self._adapter = self._registry.get_adapter(framework_choice)
            except RuntimeError as e:
                raise FrameworkNotAvailableError(str(e), framework=framework_choice)
        
        # Initialize components
        self._memory_monitor = MemoryMonitor(
            device=self._config.device,
            cuda_device_index=self._config.cuda_device_index,
        )
        self._calculator = DimensionCalculator()
        
        logger.info(
            f"AutoScaler initialized: framework={self._adapter.name}, "
            f"device={self._config.device}, threshold={self._config.memory_threshold}"
        )

    @property
    def config(self) -> ScalingConfig:
        """Return the current configuration."""
        return self._config

    @property
    def framework(self) -> str:
        """Return the active framework name."""
        return self._adapter.name

    @property
    def device_type(self) -> Literal["cpu", "cuda", "tpu"]:
        """Return the active device type."""
        return self._memory_monitor.device_type

    @property
    def adapter(self) -> IFrameworkAdapter:
        """Return the framework adapter."""
        return self._adapter

    def get_memory_info(self) -> MemoryInfo:
        """Get current memory information."""
        return self._memory_monitor.get_memory_info()

    def get_available_memory(self) -> int:
        """Get available memory in bytes."""
        return self._memory_monitor.get_available_memory()

    def estimate_memory(
        self,
        dimensions: Tuple[int, ...],
        dtype: Any = None,
    ) -> int:
        """Estimate memory required for given dimensions.
        
        Args:
            dimensions: Tensor dimensions.
            dtype: Framework-specific data type. Uses default if None.
            
        Returns:
            Estimated memory in bytes.
        """
        validated_dims = validate_dimensions(dimensions)
        if dtype is None:
            dtype = self._adapter.get_default_dtype()
        dtype_size = self._adapter.get_dtype_size(dtype)
        return self._calculator.estimate_memory(validated_dims, dtype_size)

    def scale_dimensions(
        self,
        dimensions: Tuple[int, ...],
        dtype: Any = None,
    ) -> Tuple[int, ...]:
        """Scale dimensions to fit within available memory.
        
        Args:
            dimensions: Desired tensor dimensions.
            dtype: Framework-specific data type. Uses default if None.
            
        Returns:
            Scaled dimensions that fit within memory constraints.
        """
        validated_dims = validate_dimensions(dimensions)
        if dtype is None:
            dtype = self._adapter.get_default_dtype()
        dtype_size = self._adapter.get_dtype_size(dtype)
        
        memory_info = self._memory_monitor.get_memory_info()
        
        result = self._calculator.calculate(
            validated_dims,
            dtype,
            dtype_size,
            memory_info,
            self._config,
        )
        
        return result.scaled_dimensions

    def scale_dimensions_with_info(
        self,
        dimensions: Tuple[int, ...],
        dtype: Any = None,
    ) -> ScalingResult:
        """Scale dimensions and return detailed result."""
        validated_dims = validate_dimensions(dimensions)
        if dtype is None:
            dtype = self._adapter.get_default_dtype()
        dtype_size = self._adapter.get_dtype_size(dtype)
        
        memory_info = self._memory_monitor.get_memory_info()
        
        return self._calculator.calculate(
            validated_dims,
            dtype,
            dtype_size,
            memory_info,
            self._config,
        )

    def create_scaled_tensor(
        self,
        dimensions: Tuple[int, ...],
        dtype: Any = None,
        fill_value: float | None = None,
        requires_grad: bool = False,
    ) -> Any:
        """Create a tensor with automatically scaled dimensions.
        
        Args:
            dimensions: Desired tensor dimensions.
            dtype: Framework-specific data type. Uses default if None.
            fill_value: Optional value to fill tensor with.
            requires_grad: Whether tensor requires gradients.
            
        Returns:
            Framework-specific tensor object.
        """
        if dtype is None:
            dtype = self._adapter.get_default_dtype()
            
        scaled_dims = self.scale_dimensions(dimensions, dtype)
        
        device = "cuda" if self.device_type == "cuda" else "cpu"
        
        tensor = self._adapter.create_tensor(
            scaled_dims,
            dtype,
            device,
            fill_value,
            requires_grad,
        )
        
        logger.debug(
            f"Created tensor: original={dimensions}, scaled={scaled_dims}, "
            f"framework={self.framework}"
        )
        
        return tensor

    def can_fit(
        self,
        dimensions: Tuple[int, ...],
        dtype: Any = None,
    ) -> bool:
        """Check if dimensions can fit in available memory."""
        validated_dims = validate_dimensions(dimensions)
        if dtype is None:
            dtype = self._adapter.get_default_dtype()
        dtype_size = self._adapter.get_dtype_size(dtype)
        
        memory_info = self._memory_monitor.get_memory_info()
        
        return self._calculator.can_fit(
            validated_dims,
            dtype_size,
            memory_info,
            self._config.effective_threshold,
        )

    def refresh_memory_info(self) -> MemoryInfo:
        """Refresh and return current memory information."""
        return self._memory_monitor.get_memory_info()

    def __repr__(self) -> str:
        return (
            f"AutoScaler("
            f"framework={self.framework!r}, "
            f"device={self.device_type!r}, "
            f"threshold={self._config.memory_threshold})"
        )
