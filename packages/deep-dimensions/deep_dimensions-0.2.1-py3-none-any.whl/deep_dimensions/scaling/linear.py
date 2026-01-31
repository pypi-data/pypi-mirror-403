"""Linear scaling strategy implementation."""

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


class LinearScalingStrategy(IScalingStrategy):
    """Linear scaling strategy - reduces all dimensions proportionally."""

    @property
    def name(self) -> str:
        return "linear"

    def calculate_scale_factor(self, context: ScalingContext) -> float:
        """Calculate the linear scaling factor."""
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
        """Apply the scale factor to dimensions linearly."""
        if scale_factor >= 1.0:
            return dimensions
        
        scaled = []
        for i, dim in enumerate(dimensions):
            new_dim = max(1, int(round(dim * scale_factor)))
            
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
        """Perform complete linear scaling."""
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
            f"Scaled dimensions: {context.original_dimensions} -> {scaled_dims}"
        )
        
        return ScalingResult(
            scaled_dimensions=scaled_dims,
            scale_factor=scale_factor,
            estimated_memory=estimated_memory,
            was_scaled=True,
        )
