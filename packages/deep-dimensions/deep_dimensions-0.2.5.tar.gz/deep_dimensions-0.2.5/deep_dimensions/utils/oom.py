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
            raise
        else:
            raise
    finally:
        free_memory()


@contextmanager
def measure_peak_memory() -> Generator[Callable[[], int], None, None]:
    """Context manager to measure peak CUDA memory allocation in bytes.
    
    Yields a function that returns the peak memory used during the context.
    """
    free_memory()
    if torch.cuda.is_available():
        torch.cuda.reset_peek_memory_stats()
        torch.cuda.reset_peak_memory_stats()
        start_mem = torch.cuda.memory_allocated()
        
        # We wrap the result in a closure so the user can call it AFTER the block
        peak_val = 0
        def get_peak():
             # If called inside block, update peak
            nonlocal peak_val
            current_peak = torch.cuda.max_memory_allocated()
            peak_val = max(peak_val, current_peak)
            return peak_val - start_mem

        try:
            yield get_peak
        finally:
            # Update one last time
            get_peak()
    else:
        # Fallback for CPU/MPS (Mock implementation as torch doesn't track CPU peak efficiently per-thread)
        yield lambda: 0
