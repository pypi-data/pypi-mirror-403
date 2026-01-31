"""Core module for deep_dimensions."""

from deep_dimensions.core.autoscaler import AutoScaler
from deep_dimensions.core.exceptions import (
    AutoScaleError,
    ConfigurationError,
    FrameworkNotAvailableError,
    InsufficientMemoryError,
    UnsupportedDeviceError,
)

__all__ = [
    "AutoScaler",
    "AutoScaleError",
    "ConfigurationError",
    "FrameworkNotAvailableError",
    "InsufficientMemoryError",
    "UnsupportedDeviceError",
]
