"""Dimension calculator for deep_dimensions."""

from typing import Any, Literal, Tuple

from deep_dimensions.config.settings import ScalingConfig
from deep_dimensions.core.exceptions import InsufficientMemoryError
from deep_dimensions.interfaces.framework_adapter import IFrameworkAdapter
from deep_dimensions.interfaces.memory_provider import MemoryInfo
from deep_dimensions.interfaces.scaling_strategy import (
    IScalingStrategy,
    ScalingContext,
    ScalingResult,
)
from deep_dimensions.scaling.exponential import ExponentialScalingStrategy
from deep_dimensions.scaling.linear import LinearScalingStrategy
from deep_dimensions.utils.logging import get_logger
from deep_dimensions.utils.validation import estimate_tensor_memory, validate_dimensions

logger = get_logger(__name__)


class DimensionCalculator:
    """Core dimension calculation engine."""

    def __init__(self) -> None:
        self._strategies: dict[str, IScalingStrategy] = {}

    def _get_strategy(self, name: Literal["linear", "exponential"]) -> IScalingStrategy:
        if name not in self._strategies:
            if name == "linear":
                self._strategies[name] = LinearScalingStrategy()
            elif name == "exponential":
                self._strategies[name] = ExponentialScalingStrategy()
        return self._strategies[name]

    def estimate_memory(
        self,
        dimensions: Tuple[int, ...],
        dtype_size: int,
    ) -> int:
        """Estimate memory required for given dimensions."""
        return estimate_tensor_memory(dimensions, dtype_size)

    def calculate(
        self,
        dimensions: Tuple[int, ...],
        dtype: Any,
        dtype_size: int,
        memory_info: MemoryInfo,
        config: ScalingConfig,
        scalable_indices: Tuple[int, ...] | None = None,
        maximize: bool = False,
    ) -> ScalingResult:
        """Calculate optimal dimensions based on memory constraints.
        
        Args:
            dimensions: Desired dimensions.
            dtype: Framework dtype.
            dtype_size: Size of dtype in bytes.
            memory_info: Current memory info.
            config: Scaling configuration.
            scalable_indices: Indices of dimensions to scale.
            maximize: Whether to allow scaling up.
            
        Returns:
            ScalingResult with new dimensions and metadata.
        """
        validated_dims = validate_dimensions(dimensions)
        required_memory = self.estimate_memory(validated_dims, dtype_size)
        
        logger.debug(
            f"Calculating dimensions: dims={validated_dims}, "
            f"required_memory={required_memory:,}, "
            f"available_memory={memory_info.available:,}"
        )
        
        target_memory = int(memory_info.available * config.effective_threshold)
        
        # Optimization: Early return if it fits and we are NOT maximizing
        if required_memory <= target_memory and not maximize:
            return ScalingResult(
                scaled_dimensions=validated_dims,
                scale_factor=1.0,
                estimated_memory=required_memory,
                was_scaled=False,
            )
        
        context = ScalingContext(
            available_memory=memory_info.available,
            required_memory=required_memory,
            original_dimensions=validated_dims,
            dtype=dtype,
            dtype_size=dtype_size,
            memory_threshold=config.effective_threshold,
        )
        
        strategy = self._get_strategy(config.strategy)
        result = strategy.scale(
            context,
            min_dimensions=config.min_dimensions,
            max_dimensions=config.max_dimensions,
            scalable_indices=scalable_indices,
            maximize=maximize,
        )
        
        # If we scaled DOWN but still exceed memory (and didn't error out earlier in strategy)
        if result.estimated_memory > target_memory and not maximize:
            # Check if even min dimensions exceed output
            if config.min_dimensions is not None:
                min_memory = self.estimate_memory(config.min_dimensions, dtype_size)
                if min_memory > target_memory:
                     # This check should probably happen regardless, but strictly it's an error state
                    raise InsufficientMemoryError(
                        f"Cannot fit minimum dimensions in available memory",
                        required_memory=min_memory,
                        available_memory=target_memory,
                        min_dimensions=config.min_dimensions,
                    )
        
        return result

    def can_fit(
        self,
        dimensions: Tuple[int, ...],
        dtype_size: int,
        memory_info: MemoryInfo,
        threshold: float = 0.8,
    ) -> bool:
        """Check if dimensions can fit in available memory."""
        required = self.estimate_memory(dimensions, dtype_size)
        available = int(memory_info.available * threshold)
        return required <= available
