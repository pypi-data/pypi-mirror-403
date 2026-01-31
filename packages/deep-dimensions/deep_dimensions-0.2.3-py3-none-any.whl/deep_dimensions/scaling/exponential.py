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
    """Exponential scaling strategy - reduces larger dimensions more aggressively."""

    def __init__(self, exponent: float = 2.0) -> None:
        if exponent <= 0:
            raise ValueError("Exponent must be positive")
        self._exponent = exponent

    @property
    def exponent(self) -> float:
        return self._exponent

    @property
    def name(self) -> str:
        return "exponential"

    def calculate_scale_factor(
        self,
        context: ScalingContext,
        scalable_indices: Tuple[int, ...] | None = None,
        maximize: bool = False,
    ) -> float:
        """Calculate scale factor based on memory ratio."""
        target_memory = int(context.available_memory * context.memory_threshold)
        
        if context.required_memory <= target_memory and not maximize:
            return 1.0

        if context.required_memory == 0:
            return 1.0

        # Heuristic: use same ratio calculation as linear for the 'base' factor
        # The 'exponential' part is in how it's applied to dimensions
        memory_ratio = target_memory / context.required_memory
        
        if scalable_indices is not None:
             n_dims = len(scalable_indices)
        else:
             n_dims = len(context.original_dimensions)
             
        scale_factor = math.pow(memory_ratio, 1.0 / n_dims)
        
        if maximize:
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
        """Apply scaling, penalizing larger dimensions more."""
        if scale_factor == 1.0:
            return dimensions
            
        scaled = list(dimensions)
        indices = scalable_indices if scalable_indices is not None else range(len(dimensions))
        
        # Calculate weights based on dimension size (larger dim = larger weight)
        dims_to_scale = [dimensions[i] for i in indices]
        if not dims_to_scale:
            return dimensions
            
        max_dim = max(dims_to_scale)
        
        for i in indices:
            dim = dimensions[i]
            # Weight is based on ratio to largest dimension
            weight = (dim / max_dim) ** self._exponent
            
            # Adjusted factor for this dimension
            # If scale_factor < 1 (reduction): larger weight -> more reduction (smaller factor)
            # If scale_factor > 1 (increase): larger weight -> more increase? 
            # Usually exponential strategy is for reduction. For maximization, linear is preferred.
            # But let's try to be consistent: 
            # If reducing: factor = base_factor * (something < 1 for large dims)
            
            if scale_factor < 1:
                # Reduction
                dim_factor = scale_factor * (1.0 - (weight * 0.1)) # Slight extra penalty
                dim_factor = max(scale_factor * 0.5, dim_factor) # Cap penalty
            else:
                # Increase - maybe just linear for now as 'exponential increase' is dangerous
                dim_factor = scale_factor
                
            new_dim = max(1, int(round(dim * dim_factor)))
            
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
        """Perform complete exponential scaling."""
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
        
        return ScalingResult(
            scaled_dimensions=scaled_dims,
            scale_factor=scale_factor,
            estimated_memory=estimated_memory,
            was_scaled=True,
        )
