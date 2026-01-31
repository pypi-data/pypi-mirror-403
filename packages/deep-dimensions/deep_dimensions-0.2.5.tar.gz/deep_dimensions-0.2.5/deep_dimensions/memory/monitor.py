"""Memory monitor facade.

This module provides a unified interface for memory introspection
across different device types.
"""

from typing import Literal

from deep_dimensions.interfaces.memory_provider import IMemoryProvider, MemoryInfo
from deep_dimensions.memory.cuda import CUDAMemoryProvider
from deep_dimensions.memory.system import SystemMemoryProvider
from deep_dimensions.utils.logging import get_logger

logger = get_logger(__name__)


class MemoryMonitor:
    """Facade for memory monitoring across devices."""

    def __init__(
        self,
        device: Literal["cpu", "cuda", "auto"] = "auto",
        cuda_device_index: int = 0,
    ) -> None:
        """Initialize the memory monitor."""
        self._device = device
        self._cuda_device_index = cuda_device_index
        self._provider = self._create_provider()
        
        logger.debug(
            f"MemoryMonitor initialized with device={device}, "
            f"selected provider={self._provider.device_type}"
        )

    def _create_provider(self) -> IMemoryProvider:
        """Create the appropriate memory provider."""
        if self._device == "cuda":
            provider = CUDAMemoryProvider(self._cuda_device_index)
            if not provider.is_available():
                logger.warning("CUDA not available, falling back to CPU")
                return SystemMemoryProvider()
            return provider
        
        if self._device == "auto":
            cuda_provider = CUDAMemoryProvider(self._cuda_device_index)
            if cuda_provider.is_available():
                logger.info("Auto-detected CUDA device, using GPU memory")
                return cuda_provider
            logger.info("CUDA not available, using system memory")
            return SystemMemoryProvider()
        
        return SystemMemoryProvider()

    def get_memory_info(self) -> MemoryInfo:
        """Get current memory information."""
        return self._provider.get_memory_info()

    def get_available_memory(self) -> int:
        """Get available memory in bytes."""
        return self._provider.get_memory_info().available

    def get_total_memory(self) -> int:
        """Get total memory in bytes."""
        return self._provider.get_memory_info().total

    @property
    def provider(self) -> IMemoryProvider:
        """Return the underlying memory provider."""
        return self._provider

    @property
    def device_type(self) -> Literal["cpu", "cuda", "tpu"]:
        """Return the active device type."""
        return self._provider.device_type
