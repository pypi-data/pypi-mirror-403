"""System (CPU) memory provider implementation.

This module provides memory introspection for system RAM using psutil.
"""

from typing import Literal

import psutil

from deep_dimensions.interfaces.memory_provider import IMemoryProvider, MemoryInfo


class SystemMemoryProvider(IMemoryProvider):
    """Memory provider for system RAM.
    
    Uses psutil to query available system memory. This provider
    is always available on supported platforms.
    """

    def __init__(self) -> None:
        """Initialize the system memory provider."""
        self._device_type: Literal["cpu"] = "cpu"

    def get_memory_info(self) -> MemoryInfo:
        """Get current system memory information."""
        mem = psutil.virtual_memory()
        return MemoryInfo(
            total=mem.total,
            available=mem.available,
            used=mem.used,
            device_type=self._device_type,
            device_index=0,
        )

    def is_available(self) -> bool:
        """Check if system memory is available."""
        return True

    @property
    def device_type(self) -> Literal["cpu", "cuda", "tpu"]:
        """Return the device type."""
        return self._device_type
