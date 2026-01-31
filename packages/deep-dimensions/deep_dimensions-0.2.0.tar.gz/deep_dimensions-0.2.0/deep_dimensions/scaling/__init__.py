"""Scaling module for deep_dimensions."""

from deep_dimensions.scaling.calculator import DimensionCalculator
from deep_dimensions.scaling.exponential import ExponentialScalingStrategy
from deep_dimensions.scaling.linear import LinearScalingStrategy

__all__ = [
    "DimensionCalculator",
    "LinearScalingStrategy",
    "ExponentialScalingStrategy",
]
