"""Abstract base class for framework adapters.

This module defines the interface for deep learning framework adapters.
Each framework (PyTorch, TensorFlow) implements this interface to provide
unified tensor operations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Tuple, Union


@dataclass(frozen=True)
class DTypeInfo:
    """Information about a data type.
    
    Attributes:
        name: Human-readable name of the dtype.
        size_bytes: Size in bytes per element.
        framework: Framework this dtype belongs to.
        native_dtype: The native dtype object.
    """
    name: str
    size_bytes: int
    framework: str
    native_dtype: Any


class IFrameworkAdapter(ABC):
    """Abstract interface for deep learning framework adapters.
    
    This interface abstracts framework-specific operations, allowing
    the library to work with multiple frameworks (PyTorch, TensorFlow)
    without framework-specific code in the core logic.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the framework name."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this framework is available.
        
        Returns:
            True if the framework is installed and usable.
        """
        pass

    @abstractmethod
    def get_dtype_size(self, dtype: Any) -> int:
        """Get the size in bytes of a data type.
        
        Args:
            dtype: Framework-specific data type.
            
        Returns:
            Size in bytes per element.
        """
        pass

    @abstractmethod
    def get_default_dtype(self) -> Any:
        """Get the default floating-point dtype.
        
        Returns:
            The default dtype (typically float32).
        """
        pass

    @abstractmethod
    def create_tensor(
        self,
        dimensions: Tuple[int, ...],
        dtype: Any,
        device: str,
        fill_value: Union[float, None] = None,
        requires_grad: bool = False,
    ) -> Any:
        """Create a tensor with the given specifications.
        
        Args:
            dimensions: Tensor shape.
            dtype: Data type.
            device: Device to create tensor on ("cpu" or "cuda").
            fill_value: Optional value to fill tensor with.
            requires_grad: Whether tensor requires gradients.
            
        Returns:
            Framework-specific tensor object.
        """
        pass

    @abstractmethod
    def is_cuda_available(self) -> bool:
        """Check if CUDA is available in this framework.
        
        Returns:
            True if CUDA is available.
        """
        pass

    @abstractmethod
    def get_cuda_memory_info(self, device_index: int = 0) -> Tuple[int, int, int]:
        """Get CUDA memory information.
        
        Args:
            device_index: CUDA device index.
            
        Returns:
            Tuple of (total, available, used) memory in bytes.
            
        Raises:
            RuntimeError: If CUDA is not available.
        """
        pass

    @abstractmethod
    def validate_dtype(self, dtype: Any) -> bool:
        """Validate that a dtype is supported.
        
        Args:
            dtype: Data type to validate.
            
        Returns:
            True if dtype is valid for this framework.
        """
        pass
