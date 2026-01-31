"""Abstract base class for scaling strategies.

This module defines the interface for dimension scaling algorithms.
Different strategies can implement different approaches to scaling
tensor dimensions based on available memory.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Tuple


@dataclass(frozen=True)
class ScalingContext:
    """Immutable context for scaling calculations.
    
    Attributes:
        available_memory: Available memory in bytes.
        required_memory: Estimated required memory in bytes.
        original_dimensions: Original tensor dimensions.
        dtype: Framework data type for the tensor.
        dtype_size: Size of dtype in bytes.
        memory_threshold: Target memory usage ratio (0.0-1.0).
    """
    available_memory: int
    required_memory: int
    original_dimensions: Tuple[int, ...]
    dtype: Any
    dtype_size: int
    memory_threshold: float

    def __post_init__(self) -> None:
        """Validate context values."""
        if self.available_memory < 0:
            raise ValueError("Available memory cannot be negative")
        if self.required_memory < 0:
            raise ValueError("Required memory cannot be negative")
        if not self.original_dimensions:
            raise ValueError("Original dimensions cannot be empty")
        if any(d <= 0 for d in self.original_dimensions):
            raise ValueError("All dimensions must be positive")
        if not 0.0 < self.memory_threshold <= 1.0:
            raise ValueError("Memory threshold must be between 0 and 1")


@dataclass(frozen=True)
class ScalingResult:
    """Immutable result of a scaling operation.
    
    Attributes:
        scaled_dimensions: The scaled tensor dimensions.
        scale_factor: The factor by which dimensions were scaled.
        estimated_memory: Estimated memory usage after scaling.
        was_scaled: Whether any scaling was applied.
    """
    scaled_dimensions: Tuple[int, ...]
    scale_factor: float
    estimated_memory: int
    was_scaled: bool


class IScalingStrategy(ABC):
    """Abstract interface for dimension scaling algorithms.
    
    Implementations of this interface provide different approaches
    to scaling tensor dimensions to fit within available memory.
    
    This follows the Strategy Pattern, allowing different scaling
    algorithms to be used interchangeably.
    """

    @abstractmethod
    def calculate_scale_factor(self, context: ScalingContext) -> float:
        """Calculate the scaling factor for the given context.
        
        Args:
            context: The scaling context with memory and dimension info.
            
        Returns:
            A scale factor between 0 and 1 (or 1 if no scaling needed).
        """
        pass

    @abstractmethod
    def apply_to_dimensions(
        self,
        dimensions: Tuple[int, ...],
        scale_factor: float,
        min_dimensions: Tuple[int, ...] | None = None,
        max_dimensions: Tuple[int, ...] | None = None,
    ) -> Tuple[int, ...]:
        """Apply the scale factor to dimensions.
        
        Args:
            dimensions: Original dimensions to scale.
            scale_factor: Factor to scale by (0 < factor <= 1).
            min_dimensions: Optional minimum dimension constraints.
            max_dimensions: Optional maximum dimension constraints.
            
        Returns:
            Scaled dimensions respecting constraints.
        """
        pass

    @abstractmethod
    def scale(
        self,
        context: ScalingContext,
        min_dimensions: Tuple[int, ...] | None = None,
        max_dimensions: Tuple[int, ...] | None = None,
    ) -> ScalingResult:
        """Perform complete scaling operation.
        
        This is the main entry point that combines factor calculation
        and dimension application.
        
        Args:
            context: The scaling context.
            min_dimensions: Optional minimum dimension constraints.
            max_dimensions: Optional maximum dimension constraints.
            
        Returns:
            ScalingResult with scaled dimensions and metadata.
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the name of this scaling strategy."""
        pass
