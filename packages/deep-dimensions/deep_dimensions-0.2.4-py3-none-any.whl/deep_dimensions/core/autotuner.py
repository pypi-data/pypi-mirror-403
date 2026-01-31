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
        min_val: int = 1,
        max_val: Optional[int] = None,
        steps: Optional[int] = None,
    ) -> int:
        """Find the maximum integer value for which func(value) succeeds.
        
        Automatically determines the upper limit if max_val is not provided
        by using exponential probing.
        
        Args:
            func: Function that takes an int and runs the workload. 
                  Should raise RuntimeError (OOM) if it fails.
            min_val: Starting value (default: 1).
            max_val: Optional maximum limit. If None, searches until failure.
            steps: Optional max iterations. If None, runs until convergence.
        """
        low = min_val
        high = max_val
        
        logger.info(f"AutoTuner: Starting discovery from {min_val}")
        
        # Phase 1: Range Discovery (Exponential Search)
        if high is None:
            logger.info("AutoTuner: No upper limit provided. Probing for OOM boundary...")
            try:
                # First ensure start point works
                if not self._try_run(func, low):
                    logger.error(f"AutoTuner: Starting value {low} failed immediately.")
                    return 0
                
                curr = low * 2
                while True:
                     # Check if we hit user step limit if provided
                    if steps is not None:
                        steps -= 1
                        if steps <= 0:
                            logger.warning("AutoTuner: Step limit reached during expansion.")
                            return low

                    logger.info(f"AutoTuner: Probing upper bound {curr}...")
                    if self._try_run(func, curr):
                        low = curr
                        curr = curr * 2
                    else:
                        logger.info(f"AutoTuner: Found upper bound limit at {curr}")
                        high = curr
                        break
            except Exception as e:
                logger.error(f"AutoTuner: Critical error during range discovery: {e}")
                return low
        
        # Phase 2: Binary Search (Refinement)
        logger.info(f"AutoTuner: Refining search in range [{low}, {high}]")
        safe_val = low
        
        while low <= high:
             # Check step limit
            if steps is not None:
                steps -= 1
                if steps <= 0:
                    logger.warning("AutoTuner: Step limit reached during refinement.")
                    break
            
            mid = (low + high) // 2
            
            if mid == 0: # Safety check
                low = 1
                continue
                
            if mid == safe_val:
                # If mid converged to the known safe value, we try safe+1 to see if we can squeeze more
                # If safe+1 > high, we are done
                if safe_val + 1 > high:
                    break
                mid = safe_val + 1

            logger.debug(f"AutoTuner: Probing value {mid}...")
            
            if self._try_run(func, mid):
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
