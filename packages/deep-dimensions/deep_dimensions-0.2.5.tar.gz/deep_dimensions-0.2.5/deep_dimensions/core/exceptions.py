"""Custom exceptions for deep_dimensions."""


class AutoScaleError(Exception):
    """Base exception for all deep_dimensions errors."""
    pass


class ConfigurationError(AutoScaleError):
    """Raised when configuration is invalid."""
    pass


class InsufficientMemoryError(AutoScaleError):
    """Raised when there is not enough memory to create a tensor."""
    
    def __init__(
        self,
        message: str,
        required_memory: int | None = None,
        available_memory: int | None = None,
        min_dimensions: tuple[int, ...] | None = None,
    ) -> None:
        super().__init__(message)
        self.required_memory = required_memory
        self.available_memory = available_memory
        self.min_dimensions = min_dimensions


class UnsupportedDeviceError(AutoScaleError):
    """Raised when an unsupported device is requested."""
    
    def __init__(self, message: str, device: str | None = None) -> None:
        super().__init__(message)
        self.device = device


class FrameworkNotAvailableError(AutoScaleError):
    """Raised when a requested framework is not available."""
    
    def __init__(self, message: str, framework: str | None = None) -> None:
        super().__init__(message)
        self.framework = framework
