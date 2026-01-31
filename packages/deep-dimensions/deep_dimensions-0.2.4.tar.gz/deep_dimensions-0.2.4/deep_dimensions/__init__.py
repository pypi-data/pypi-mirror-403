"""
Deep Dimensions - Auto-scaling tensor dimensions for deep learning frameworks.

This library provides utilities to automatically scale tensor dimensions
based on available system memory (RAM or VRAM). Supports PyTorch and TensorFlow.
"""

from deep_dimensions.config.settings import ScalingConfig
from deep_dimensions.core.autoscaler import AutoScaler
from deep_dimensions.core.autotuner import AutoTuner
from deep_dimensions.core.exceptions import (
    AutoScaleError,
    ConfigurationError,
    FrameworkNotAvailableError,
    InsufficientMemoryError,
    UnsupportedDeviceError,
)
from deep_dimensions.interfaces.framework_adapter import IFrameworkAdapter
from deep_dimensions.interfaces.memory_provider import IMemoryProvider
from deep_dimensions.interfaces.scaling_strategy import IScalingStrategy

__version__ = "0.2.0"
__all__ = [
    "AutoScaler",
    "ScalingConfig",
    "IMemoryProvider",
    "IScalingStrategy",
    "IFrameworkAdapter",
    "AutoScaleError",
    "ConfigurationError",
    "InsufficientMemoryError",
    "UnsupportedDeviceError",
    "FrameworkNotAvailableError",
]
