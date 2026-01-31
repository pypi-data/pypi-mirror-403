"""PyTorch framework adapter.

This module provides PyTorch-specific implementations for the
framework adapter interface.
"""

from typing import Any, Tuple, Union

from deep_dimensions.interfaces.framework_adapter import IFrameworkAdapter

# Lazy import to avoid requiring torch
_torch = None


def _get_torch():
    """Lazily import torch."""
    global _torch
    if _torch is None:
        try:
            import torch
            _torch = torch
        except ImportError:
            _torch = False
    return _torch


class PyTorchAdapter(IFrameworkAdapter):
    """Framework adapter for PyTorch.
    
    Provides PyTorch-specific tensor operations and memory detection.
    """

    # Mapping of dtype to bytes per element
    DTYPE_SIZES = {}

    def __init__(self) -> None:
        """Initialize the PyTorch adapter."""
        torch = _get_torch()
        if torch:
            self.DTYPE_SIZES = {
                torch.float16: 2,
                torch.float32: 4,
                torch.float64: 8,
                torch.bfloat16: 2,
                torch.int8: 1,
                torch.int16: 2,
                torch.int32: 4,
                torch.int64: 8,
                torch.uint8: 1,
                torch.bool: 1,
                torch.complex64: 8,
                torch.complex128: 16,
            }

    @property
    def name(self) -> str:
        """Return the framework name."""
        return "pytorch"

    def is_available(self) -> bool:
        """Check if PyTorch is available."""
        torch = _get_torch()
        return torch is not False

    def get_dtype_size(self, dtype: Any) -> int:
        """Get the size in bytes of a PyTorch dtype.
        
        Args:
            dtype: PyTorch data type.
            
        Returns:
            Size in bytes per element.
        """
        if dtype in self.DTYPE_SIZES:
            return self.DTYPE_SIZES[dtype]
        raise ValueError(f"Unsupported dtype: {dtype}")

    def get_default_dtype(self) -> Any:
        """Get the default PyTorch dtype (float32)."""
        torch = _get_torch()
        if not torch:
            raise RuntimeError("PyTorch is not available")
        return torch.float32

    def create_tensor(
        self,
        dimensions: Tuple[int, ...],
        dtype: Any,
        device: str,
        fill_value: Union[float, None] = None,
        requires_grad: bool = False,
    ) -> Any:
        """Create a PyTorch tensor.
        
        Args:
            dimensions: Tensor shape.
            dtype: PyTorch data type.
            device: Device ("cpu" or "cuda").
            fill_value: Optional fill value.
            requires_grad: Whether to track gradients.
            
        Returns:
            PyTorch tensor.
        """
        torch = _get_torch()
        if not torch:
            raise RuntimeError("PyTorch is not available")

        if fill_value is None:
            return torch.empty(
                *dimensions,
                dtype=dtype,
                device=device,
                requires_grad=requires_grad,
            )
        elif fill_value == 0.0:
            return torch.zeros(
                *dimensions,
                dtype=dtype,
                device=device,
                requires_grad=requires_grad,
            )
        elif fill_value == 1.0:
            return torch.ones(
                *dimensions,
                dtype=dtype,
                device=device,
                requires_grad=requires_grad,
            )
        else:
            return torch.full(
                dimensions,
                fill_value,
                dtype=dtype,
                device=device,
                requires_grad=requires_grad,
            )

    def is_cuda_available(self) -> bool:
        """Check if CUDA is available in PyTorch."""
        torch = _get_torch()
        if not torch:
            return False
        return torch.cuda.is_available()

    def get_cuda_memory_info(self, device_index: int = 0) -> Tuple[int, int, int]:
        """Get CUDA memory information.
        
        Args:
            device_index: CUDA device index.
            
        Returns:
            Tuple of (total, available, used) memory in bytes.
        """
        torch = _get_torch()
        if not torch:
            raise RuntimeError("PyTorch is not available")
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA is not available")

        total = torch.cuda.get_device_properties(device_index).total_memory
        reserved = torch.cuda.memory_reserved(device_index)
        available = total - reserved

        return total, available, reserved

    def validate_dtype(self, dtype: Any) -> bool:
        """Validate that a dtype is a valid PyTorch dtype."""
        return dtype in self.DTYPE_SIZES
