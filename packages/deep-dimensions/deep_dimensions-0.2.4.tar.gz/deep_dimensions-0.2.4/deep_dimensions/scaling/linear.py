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
    """Linear scaling strategy - reduces dimensions proportionally."""

    @property
    def name(self) -> str:
        return "linear"

    def calculate_scale_factor(
        self,
        context: ScalingContext,
        scalable_indices: Tuple[int, ...] | None = None,
        maximize: bool = False,
    ) -> float:
        """Calculate the linear scaling factor."""
        target_memory = int(context.available_memory * context.memory_threshold)
        
        # If memory is sufficient and we are not maximizing, return 1.0
        if context.required_memory <= target_memory and not maximize:
            return 1.0
            
        # Avoid division by zero
        if context.required_memory == 0:
            return 1.0

        memory_ratio = target_memory / context.required_memory
        
        # Determine number of dimensions participating in scaling
        if scalable_indices is not None:
            n_dims = len(scalable_indices)
            if n_dims == 0:
                logger.warning("No scalable indices provided, returning 1.0")
                return 1.0
        else:
            n_dims = len(context.original_dimensions)

        # Scale factor is N-th root of memory ratio (since mem ~ dim^N)
        scale_factor = math.pow(memory_ratio, 1.0 / n_dims)
        
        if maximize:
            # When maximizing, we allow factor > 1.0, but reasonable caps (e.g. 100x)
            return max(0.01, min(100.0, scale_factor))
        else:
            return max(0.01, min(1.0, scale_factor))

    def apply_to_dimensions(
        self,
        dimensions: Tuple[int, ...],
        scale_factor: float,
        min_dimensions: Tuple[int, ...] | None = None,
        max_dimensions: Tuple[int, ...] | None = None,
        scalable_indices: Tuple[int, ...] | None = None,
    ) -> Tuple[int, ...]:
        """Apply the scale factor to dimensions linearly."""
        if scale_factor == 1.0:
            return dimensions
        
        scaled = list(dimensions)
        indices_to_scale = scalable_indices if scalable_indices is not None else range(len(dimensions))
        
        for i in indices_to_scale:
            if i >= len(dimensions):
                continue
                
            original_dim = dimensions[i]
            # Use floor for downscaling to be safe, round/ceil for upscaling?
            # Standard round is usually safest generic approach, but for memory limits floor is better.
            # But let's stick to round for aspect ratio preservation, as long as we check memory later.
            new_dim = max(1, int(round(original_dim * scale_factor)))
            
            if min_dimensions is not None and i < len(min_dimensions):
                new_dim = max(new_dim, min_dimensions[i])
            
            if max_dimensions is not None and i < len(max_dimensions):
                new_dim = min(new_dim, max_dimensions[i])
                
            scaled[i] = new_dim
        
        return tuple(scaled)

    def scale(
        self,
        context: ScalingContext,
        min_dimensions: Tuple[int, ...] | None = None,
        max_dimensions: Tuple[int, ...] | None = None,
        scalable_indices: Tuple[int, ...] | None = None,
        maximize: bool = False,
    ) -> ScalingResult:
        """Perform complete linear scaling."""
        scale_factor = self.calculate_scale_factor(
            context,
            scalable_indices=scalable_indices,
            maximize=maximize
        )
        
        if scale_factor == 1.0:
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
            scalable_indices,
        )
        
        estimated_memory = estimate_tensor_memory(scaled_dims, context.dtype_size)
        
        # Logging
        if maximize and scale_factor > 1.0:
            logger.info(f"Scaled UP: {context.original_dimensions} -> {scaled_dims} (Factor: {scale_factor:.2f})")
        elif scale_factor < 1.0:
            logger.info(f"Scaled DOWN: {context.original_dimensions} -> {scaled_dims} (Factor: {scale_factor:.2f})")
            
        return ScalingResult(
            scaled_dimensions=scaled_dims,
            scale_factor=scale_factor,
            estimated_memory=estimated_memory,
            was_scaled=True,
        )
