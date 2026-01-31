"""Abstract base class for memory providers.

This module defines the interface that all memory providers must implement.
Memory providers are responsible for detecting available memory on different
devices (CPU, CUDA, etc.).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class MemoryInfo:
    """Immutable container for memory information.
    
    Attributes:
        total: Total memory in bytes.
        available: Currently available memory in bytes.
        used: Currently used memory in bytes.
        device_type: Type of device ("cpu", "cuda", or "tpu").
        device_index: Device index for multi-device systems.
    """
    total: int
    available: int
    used: int
    device_type: Literal["cpu", "cuda", "tpu"]
    device_index: int = 0

    def __post_init__(self) -> None:
        """Validate memory info values."""
        if self.total < 0:
            raise ValueError("Total memory cannot be negative")
        if self.available < 0:
            raise ValueError("Available memory cannot be negative")
        if self.used < 0:
            raise ValueError("Used memory cannot be negative")
        if self.available > self.total:
            raise ValueError("Available memory cannot exceed total memory")

    @property
    def usage_ratio(self) -> float:
        """Return the ratio of used memory to total memory."""
        if self.total == 0:
            return 0.0
        return self.used / self.total


class IMemoryProvider(ABC):
    """Abstract interface for memory introspection.
    
    Implementations of this interface provide memory information for
    specific device types (CPU, CUDA, TPU, etc.).
    
    This follows the Interface Segregation Principle by keeping the
    interface minimal and focused on memory introspection only.
    """

    @abstractmethod
    def get_memory_info(self) -> MemoryInfo:
        """Get current memory information.
        
        Returns:
            MemoryInfo containing total, available, and used memory.
            
        Raises:
            UnsupportedDeviceError: If the device is not available.
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this memory provider's device is available.
        
        Returns:
            True if the device is available, False otherwise.
        """
        pass

    @property
    @abstractmethod
    def device_type(self) -> Literal["cpu", "cuda", "tpu"]:
        """Return the device type this provider handles."""
        pass
