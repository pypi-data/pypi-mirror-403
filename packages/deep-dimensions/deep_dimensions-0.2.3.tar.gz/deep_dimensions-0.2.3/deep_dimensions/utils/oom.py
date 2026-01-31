"""Utilities for handling Out-Of-Memory errors and cleanup."""

import gc
import torch
from contextlib import contextmanager
from typing import Generator

from deep_dimensions.utils.logging import get_logger

logger = get_logger(__name__)


def free_memory() -> None:
    """Force garbage collection and clear framework caches."""
    # Python GC
    gc.collect()
    
    # Framework cleanup (currently focusing on PyTorch as it's the primary OOM culprit)
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()
    
    # Check for MPS (Mac)
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        if hasattr(torch, "mps") and hasattr(torch.mps, "empty_cache"):
             torch.mps.empty_cache()


@contextmanager
def safe_execution() -> Generator[None, None, None]:
    """Context manager to catch OOM errors and clean up."""
    try:
        yield
    except RuntimeError as e:
        if "out of memory" in str(e).lower():
            logger.warning("Caught OOM error during safe execution. Cleaning up...")
            free_memory()
            # Re-raise so the tuner knows it failed, but memory is potentially cleaner?
            # Actually, the tuner just needs to know it failed.
            # But specific OOM exception handling usually requires raising to caller 
            # or returning a status.
            raise
        else:
            raise
    finally:
        # Always try to free memory after a trial
        free_memory()
