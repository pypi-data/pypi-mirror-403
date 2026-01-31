"""CUDA (GPU) memory provider implementation.

This module provides memory introspection for NVIDIA GPUs.
Works with both PyTorch and TensorFlow.
"""

from typing import Literal, Optional

from deep_dimensions.interfaces.framework_adapter import IFrameworkAdapter
from deep_dimensions.interfaces.memory_provider import IMemoryProvider, MemoryInfo


class CUDAMemoryProvider(IMemoryProvider):
    """Memory provider for CUDA (GPU) memory.
    
    Uses the provided framework adapter to query GPU memory.
    """

    def __init__(
        self,
        device_index: int = 0,
        framework_adapter: Optional[IFrameworkAdapter] = None,
    ) -> None:
        """Initialize the CUDA memory provider.
        
        Args:
            device_index: Index of the CUDA device to monitor.
            framework_adapter: Optional framework adapter. If None,
                              will try to auto-detect.
        """
        if device_index < 0:
            raise ValueError("Device index must be non-negative")
        self._device_index = device_index
        self._device_type: Literal["cuda"] = "cuda"
        self._adapter = framework_adapter

    def _get_adapter(self) -> Optional[IFrameworkAdapter]:
        """Get or discover framework adapter."""
        if self._adapter is not None:
            return self._adapter
        
        # Try to discover an adapter
        try:
            from deep_dimensions.frameworks.registry import FrameworkRegistry
            registry = FrameworkRegistry()
            self._adapter = registry.get_default_adapter()
            return self._adapter
        except RuntimeError:
            return None

    def get_memory_info(self) -> MemoryInfo:
        """Get current CUDA memory information."""
        if not self.is_available():
            raise RuntimeError("CUDA is not available")

        adapter = self._get_adapter()
        if adapter is None:
            raise RuntimeError("No framework adapter available for CUDA")

        total, available, used = adapter.get_cuda_memory_info(self._device_index)
        
        return MemoryInfo(
            total=total,
            available=available,
            used=used,
            device_type=self._device_type,
            device_index=self._device_index,
        )

    def is_available(self) -> bool:
        """Check if CUDA is available."""
        adapter = self._get_adapter()
        if adapter is None:
            return False
        return adapter.is_cuda_available()

    @property
    def device_type(self) -> Literal["cpu", "cuda", "tpu"]:
        """Return the device type."""
        return self._device_type

    @property
    def device_index(self) -> int:
        """Return the CUDA device index."""
        return self._device_index
