"""Input validation utilities for deep_dimensions.

This module provides validation functions that follow the
fail-fast principle and input sanitization best practices.
"""

from typing import Any, Tuple, Union

from deep_dimensions.core.exceptions import ConfigurationError


def validate_dimensions(
    dimensions: Union[Tuple[int, ...], list[int]],
    name: str = "dimensions",
) -> Tuple[int, ...]:
    """Validate and normalize tensor dimensions."""
    if dimensions is None:
        raise ConfigurationError(f"{name} cannot be None")
    
    if isinstance(dimensions, list):
        dimensions = tuple(dimensions)
    
    if not isinstance(dimensions, tuple):
        raise ConfigurationError(
            f"{name} must be a tuple or list, got {type(dimensions).__name__}"
        )
    
    if not dimensions:
        raise ConfigurationError(f"{name} cannot be empty")
    
    for i, dim in enumerate(dimensions):
        if not isinstance(dim, int):
            raise ConfigurationError(
                f"{name}[{i}] must be an integer, got {type(dim).__name__}"
            )
        if dim <= 0:
            raise ConfigurationError(
                f"{name}[{i}] must be positive, got {dim}"
            )
    
    return dimensions


def validate_positive_int(
    value: int,
    name: str = "value",
    min_value: int = 1,
) -> int:
    """Validate that a value is a positive integer."""
    if not isinstance(value, int):
        raise ConfigurationError(
            f"{name} must be an integer, got {type(value).__name__}"
        )
    if value < min_value:
        raise ConfigurationError(
            f"{name} must be at least {min_value}, got {value}"
        )
    return value


def estimate_tensor_memory(
    dimensions: Tuple[int, ...],
    dtype_size: int,
) -> int:
    """Estimate memory required for a tensor.
    
    Args:
        dimensions: Tensor dimensions.
        dtype_size: Size of dtype in bytes.
        
    Returns:
        Estimated memory in bytes.
    """
    num_elements = 1
    for dim in dimensions:
        num_elements *= dim
    return num_elements * dtype_size
