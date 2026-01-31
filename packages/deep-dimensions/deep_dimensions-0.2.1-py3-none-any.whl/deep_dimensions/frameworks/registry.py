"""Framework registry for managing available adapters.

This module provides a registry pattern for discovering and
selecting framework adapters.
"""

from typing import Dict, Literal, Optional

from deep_dimensions.interfaces.framework_adapter import IFrameworkAdapter
from deep_dimensions.utils.logging import get_logger

logger = get_logger(__name__)


class FrameworkRegistry:
    """Registry for framework adapters.
    
    Provides discovery and selection of available deep learning
    framework adapters.
    
    Example:
        >>> registry = FrameworkRegistry()
        >>> adapter = registry.get_adapter("pytorch")
        >>> # Or auto-detect
        >>> adapter = registry.get_default_adapter()
    """

    def __init__(self) -> None:
        """Initialize the registry and discover adapters."""
        self._adapters: Dict[str, IFrameworkAdapter] = {}
        self._discover_adapters()

    def _discover_adapters(self) -> None:
        """Discover and register available framework adapters."""
        # Import adapters - they handle their own availability checking
        from deep_dimensions.frameworks.pytorch_adapter import PyTorchAdapter
        from deep_dimensions.frameworks.tensorflow_adapter import TensorFlowAdapter

        # Register PyTorch
        pytorch_adapter = PyTorchAdapter()
        if pytorch_adapter.is_available():
            self._adapters["pytorch"] = pytorch_adapter
            logger.debug("PyTorch adapter registered")

        # Register TensorFlow
        tf_adapter = TensorFlowAdapter()
        if tf_adapter.is_available():
            self._adapters["tensorflow"] = tf_adapter
            logger.debug("TensorFlow adapter registered")

        logger.info(f"Discovered frameworks: {list(self._adapters.keys())}")

    def get_adapter(
        self,
        framework: Literal["pytorch", "tensorflow"],
    ) -> IFrameworkAdapter:
        """Get a specific framework adapter.
        
        Args:
            framework: Framework name ("pytorch" or "tensorflow").
            
        Returns:
            Framework adapter.
            
        Raises:
            RuntimeError: If the requested framework is not available.
        """
        if framework not in self._adapters:
            available = list(self._adapters.keys())
            raise RuntimeError(
                f"Framework '{framework}' is not available. "
                f"Available frameworks: {available}"
            )
        return self._adapters[framework]

    def get_default_adapter(self) -> IFrameworkAdapter:
        """Get the default (first available) framework adapter.
        
        Preference order: PyTorch, TensorFlow
        
        Returns:
            The default framework adapter.
            
        Raises:
            RuntimeError: If no frameworks are available.
        """
        # Preference order
        preference = ["pytorch", "tensorflow"]
        
        for name in preference:
            if name in self._adapters:
                logger.info(f"Using default framework: {name}")
                return self._adapters[name]

        raise RuntimeError(
            "No deep learning frameworks available. "
            "Please install PyTorch or TensorFlow."
        )

    def is_available(self, framework: str) -> bool:
        """Check if a framework is available.
        
        Args:
            framework: Framework name.
            
        Returns:
            True if available.
        """
        return framework in self._adapters

    @property
    def available_frameworks(self) -> list[str]:
        """Return list of available framework names."""
        return list(self._adapters.keys())
