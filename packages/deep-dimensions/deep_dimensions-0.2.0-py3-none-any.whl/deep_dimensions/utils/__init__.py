"""Utility module for deep_dimensions."""

from deep_dimensions.utils.logging import get_logger
from deep_dimensions.utils.validation import validate_dimensions, validate_positive_int

__all__ = [
    "get_logger",
    "validate_dimensions",
    "validate_positive_int",
]
