"""Structured logging utilities for deep_dimensions."""

import logging
import sys
from typing import Optional

_loggers: dict[str, logging.Logger] = {}
DEFAULT_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_handler_configured = False


def configure_logging(level: str = "INFO", format_string: Optional[str] = None) -> None:
    """Configure the root logger for deep_dimensions."""
    global _handler_configured
    
    root_logger = logging.getLogger("deep_dimensions")
    root_logger.setLevel(getattr(logging, level.upper()))
    
    if not _handler_configured:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(format_string or DEFAULT_FORMAT))
        root_logger.addHandler(handler)
        _handler_configured = True


def get_logger(name: str) -> logging.Logger:
    """Get or create a logger for the given module name."""
    if not name.startswith("deep_dimensions"):
        name = f"deep_dimensions.{name}"
    
    if name not in _loggers:
        logger = logging.getLogger(name)
        _loggers[name] = logger
    
    return _loggers[name]


class LogContext:
    """Context manager for temporary log level changes."""
    
    def __init__(self, logger_name: str, level: str) -> None:
        self._logger = logging.getLogger(logger_name)
        self._new_level = getattr(logging, level.upper())
        self._old_level: Optional[int] = None
    
    def __enter__(self) -> "LogContext":
        self._old_level = self._logger.level
        self._logger.setLevel(self._new_level)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._old_level is not None:
            self._logger.setLevel(self._old_level)
