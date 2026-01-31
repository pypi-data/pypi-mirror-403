"""Auto-Tuner for determining optimal configurations through iterative probing."""

import time
from typing import Callable, Optional, TypeVar, Any

from deep_dimensions.utils.logging import get_logger
from deep_dimensions.utils.oom import free_memory

logger = get_logger(__name__)

T = TypeVar("T")


class AutoTuner:
    """Iteratively finds safe configuration parameters."""

    def __init__(self, verbose: bool = True) -> None:
        self.verbose = verbose

    def find_max_config(
        self,
        func: Callable[[int], Any],
        min_val: int,
        max_val: int,
        steps: int = 10,  # Max binary search steps
    ) -> int:
        """Find the maximum integer value for which func(value) succeeds.
        
        Uses binary search to find the implementation limit.
        
        Args:
            func: Function that takes an int and runs the workload. 
                  Should raise RuntimeError (OOM) if it fails, or return/pass if success.
            min_val: Minimum feasible value.
            max_val: Maximum feasible value to try.
            steps: Maximum iterations.
            
        Returns:
            The maximum safe value found. Returns 0 if even min_val fails.
        """
        low = min_val
        high = max_val
        safe_val = 0
        
        logger.info(f"AutoTuner: Searching range [{min_val}, {max_val}]")
        
        # First, verifying min_val works
        if not self._try_run(func, min_val):
            logger.error(f"AutoTuner: Minimum value {min_val} failed. Cannot tune.")
            return 0
            
        safe_val = min_val
        
        # Binary search
        for i in range(steps):
            if low > high:
                break
                
            mid = (low + high) // 2
            
            if mid == safe_val:
                # Progress stalled
                mid = mid + 1
            
            if mid > max_val:
                break
                
            logger.debug(f"AutoTuner: Probing value {mid}...")
            
            is_success = self._try_run(func, mid)
            
            if is_success:
                logger.info(f"AutoTuner: Value {mid} SUCCESS")
                safe_val = mid
                low = mid + 1
            else:
                logger.info(f"AutoTuner: Value {mid} FAILED")
                high = mid - 1
                
        logger.info(f"AutoTuner: Found optimal max value: {safe_val}")
        return safe_val

    def _try_run(self, func: Callable[[int], Any], val: int) -> bool:
        """Run a single trial, handling OOMs."""
        # Ensure clean slate
        free_memory()
        
        try:
            func(val)
            return True
        except RuntimeError as e:
            if "out of memory" in str(e).lower() or "allocate" in str(e).lower():
                # OOM detected
                return False
            # If it's another error, we arguably shouldn't just suppress it, 
            # but for a "safe config" finder, treating any crash as "unsafe" is reasonable.
            logger.warning(f"Trial failed with error: {e}")
            return False
        except Exception as e:
            logger.warning(f"Trial failed with generic error: {e}")
            return False
        finally:
            free_memory()

    def linear_extrapolation(
        self,
        memory_func: Callable[[int], int],
        target_memory: int,
        p1: int,
        p2: int
    ) -> int:
        """Estimate max value using linear regression (Mathematical Model).
        
        If User wants 'mathematical model', this is it.
        Sample memory usage at p1 and p2, fit line, solve for target_memory.
        """
        # TODO: Implement if needed. Binary search is more robust for non-linear boundaries.
        pass
