"""Interfaces for the deep_dimensions library."""

from deep_dimensions.interfaces.framework_adapter import IFrameworkAdapter
from deep_dimensions.interfaces.memory_provider import IMemoryProvider
from deep_dimensions.interfaces.scaling_strategy import IScalingStrategy

__all__ = ["IMemoryProvider", "IScalingStrategy", "IFrameworkAdapter"]
