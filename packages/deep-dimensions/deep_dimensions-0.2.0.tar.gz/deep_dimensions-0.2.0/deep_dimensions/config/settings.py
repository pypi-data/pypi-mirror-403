"""Configuration settings for deep_dimensions.

This module defines immutable configuration dataclasses for the library.
"""

from dataclasses import dataclass
from typing import Literal, Tuple


@dataclass(frozen=True)
class ScalingConfig:
    """Immutable configuration for auto-scaling behavior.
    
    Attributes:
        memory_threshold: Target memory usage ratio (0.0-1.0).
        device: Device to use ("cpu", "cuda", or "auto").
        cuda_device_index: Index of CUDA device when using CUDA.
        strategy: Scaling strategy name ("linear" or "exponential").
        framework: Framework to use ("pytorch", "tensorflow", or "auto").
        min_dimensions: Optional minimum dimension constraints.
        max_dimensions: Optional maximum dimension constraints.
        preserve_aspect_ratio: Whether to preserve aspect ratio when scaling.
        safety_margin: Additional safety margin for memory calculations.
        log_level: Logging level for the library.
    """
    
    memory_threshold: float = 0.8
    device: Literal["cpu", "cuda", "auto"] = "auto"
    cuda_device_index: int = 0
    strategy: Literal["linear", "exponential"] = "linear"
    framework: Literal["pytorch", "tensorflow", "auto"] = "auto"
    min_dimensions: Tuple[int, ...] | None = None
    max_dimensions: Tuple[int, ...] | None = None
    preserve_aspect_ratio: bool = True
    safety_margin: float = 0.1
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    def __post_init__(self) -> None:
        """Validate configuration values."""
        if not 0.0 < self.memory_threshold <= 1.0:
            raise ValueError(
                f"memory_threshold must be between 0 and 1, got {self.memory_threshold}"
            )
        
        if not 0.0 <= self.safety_margin < 1.0:
            raise ValueError(
                f"safety_margin must be between 0 and 1, got {self.safety_margin}"
            )
        
        if self.memory_threshold + self.safety_margin > 1.0:
            raise ValueError(
                f"memory_threshold ({self.memory_threshold}) + safety_margin "
                f"({self.safety_margin}) must not exceed 1.0"
            )
        
        if self.cuda_device_index < 0:
            raise ValueError(
                f"cuda_device_index must be non-negative, got {self.cuda_device_index}"
            )
        
        if self.min_dimensions is not None:
            if not self.min_dimensions:
                raise ValueError("min_dimensions cannot be empty tuple")
            if any(d <= 0 for d in self.min_dimensions):
                raise ValueError("All min_dimensions must be positive")
        
        if self.max_dimensions is not None:
            if not self.max_dimensions:
                raise ValueError("max_dimensions cannot be empty tuple")
            if any(d <= 0 for d in self.max_dimensions):
                raise ValueError("All max_dimensions must be positive")
        
        if self.min_dimensions is not None and self.max_dimensions is not None:
            if len(self.min_dimensions) != len(self.max_dimensions):
                raise ValueError(
                    f"min_dimensions ({len(self.min_dimensions)}) and "
                    f"max_dimensions ({len(self.max_dimensions)}) must have same length"
                )
            for i, (min_d, max_d) in enumerate(
                zip(self.min_dimensions, self.max_dimensions)
            ):
                if min_d > max_d:
                    raise ValueError(
                        f"min_dimensions[{i}] ({min_d}) cannot exceed "
                        f"max_dimensions[{i}] ({max_d})"
                    )

    @property
    def effective_threshold(self) -> float:
        """Return the effective memory threshold after safety margin."""
        return self.memory_threshold - self.safety_margin

    def with_overrides(self, **kwargs) -> "ScalingConfig":
        """Create a new config with specified overrides."""
        current = {
            "memory_threshold": self.memory_threshold,
            "device": self.device,
            "cuda_device_index": self.cuda_device_index,
            "strategy": self.strategy,
            "framework": self.framework,
            "min_dimensions": self.min_dimensions,
            "max_dimensions": self.max_dimensions,
            "preserve_aspect_ratio": self.preserve_aspect_ratio,
            "safety_margin": self.safety_margin,
            "log_level": self.log_level,
        }
        current.update(kwargs)
        return ScalingConfig(**current)
