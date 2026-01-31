"""Exponential scaling strategy implementation."""

from typing import Tuple
import math

from deep_dimensions.interfaces.scaling_strategy import (
    IScalingStrategy,
    ScalingContext,
    ScalingResult,
)
from deep_dimensions.utils.logging import get_logger
from deep_dimensions.utils.validation import estimate_tensor_memory

logger = get_logger(__name__)


class ExponentialScalingStrategy(IScalingStrategy):
    """Exponential scaling - reduces larger dimensions more aggressively."""

    def __init__(self, exponent: float = 2.0) -> None:
        if exponent <= 0:
            raise ValueError("Exponent must be positive")
        self._exponent = exponent

    @property
    def name(self) -> str:
        return "exponential"

    @property
    def exponent(self) -> float:
        return self._exponent

    def calculate_scale_factor(self, context: ScalingContext) -> float:
        target_memory = int(context.available_memory * context.memory_threshold)
        
        if context.required_memory <= target_memory:
            return 1.0
        
        memory_ratio = target_memory / context.required_memory
        n_dims = len(context.original_dimensions)
        scale_factor = math.pow(memory_ratio, 1.0 / n_dims)
        
        return max(0.01, min(1.0, scale_factor))

    def apply_to_dimensions(
        self,
        dimensions: Tuple[int, ...],
        scale_factor: float,
        min_dimensions: Tuple[int, ...] | None = None,
        max_dimensions: Tuple[int, ...] | None = None,
    ) -> Tuple[int, ...]:
        if scale_factor >= 1.0:
            return dimensions
        
        max_dim = max(dimensions)
        if max_dim == 0:
            return dimensions
        
        normalized = [d / max_dim for d in dimensions]
        
        scaled = []
        for i, (dim, norm) in enumerate(zip(dimensions, normalized)):
            weight = math.pow(norm, self._exponent)
            dim_scale = scale_factor + (1 - scale_factor) * (1 - weight)
            new_dim = max(1, int(round(dim * dim_scale)))
            
            if min_dimensions is not None and i < len(min_dimensions):
                new_dim = max(new_dim, min_dimensions[i])
            
            if max_dimensions is not None and i < len(max_dimensions):
                new_dim = min(new_dim, max_dimensions[i])
            
            scaled.append(new_dim)
        
        return tuple(scaled)

    def scale(
        self,
        context: ScalingContext,
        min_dimensions: Tuple[int, ...] | None = None,
        max_dimensions: Tuple[int, ...] | None = None,
    ) -> ScalingResult:
        scale_factor = self.calculate_scale_factor(context)
        
        if scale_factor >= 1.0:
            return ScalingResult(
                scaled_dimensions=context.original_dimensions,
                scale_factor=1.0,
                estimated_memory=context.required_memory,
                was_scaled=False,
            )
        
        scaled_dims = self.apply_to_dimensions(
            context.original_dimensions,
            scale_factor,
            min_dimensions,
            max_dimensions,
        )
        
        estimated_memory = estimate_tensor_memory(scaled_dims, context.dtype_size)
        
        logger.info(
            f"Exponential scaling: {context.original_dimensions} -> {scaled_dims}"
        )
        
        return ScalingResult(
            scaled_dimensions=scaled_dims,
            scale_factor=scale_factor,
            estimated_memory=estimated_memory,
            was_scaled=True,
        )
