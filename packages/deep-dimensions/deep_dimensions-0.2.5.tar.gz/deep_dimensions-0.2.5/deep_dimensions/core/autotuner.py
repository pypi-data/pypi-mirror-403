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

    def predict_max_config(
        self,
        func: Callable[[int], Any],
        min_val: int = 1,
        step_factor: float = 2.0,
        safety_buffer: float = 0.95
    ) -> int:
        """Mathematically predict the maximum config using Linear Regression.
        
        Runs two small probes to calculate the Memory Slope (MB/dim),
        then solves for the maximum dimension that fits in Available VRAM.
        
        Args:
            func: Workload function.
            min_val: First probe point.
            step_factor: Multiplier for second probe point.
            safety_buffer: Percent of available memory to target (default 95%).
        """
        import torch
        from deep_dimensions.utils.oom import measure_peak_memory
        
        if not torch.cuda.is_available():
            logger.warning("AutoTuner: Predictive tuning requires CUDA to measure memory. Falling back to search.")
            return self.find_max_config(func, min_val)
            
        logger.info("AutoTuner: Starting Mathematical Extrapolation...")
        
        # 1. Get Baseline (Available Memory)
        free_memory()
        total_mem = torch.cuda.get_device_properties(0).total_memory
        reserved = torch.cuda.memory_reserved(0)
        allocated = torch.cuda.memory_allocated(0)
        # We want to fill the *remaining* space + whatever we cleared from reserved
        # Effectively, we are targeting total device capacity minus system overhead
        # A safer bet is:
        available_target = (total_mem - allocated) * safety_buffer
        
        logger.info(f"AutoTuner: Target Available Memory: {available_target / 1e6:.2f} MB")

        # 2. Probe 1
        x1 = min_val
        logger.info(f"AutoTuner: Probe 1 (x={x1})...")
        y1 = 0
        with measure_peak_memory() as get_mem:
            if not self._try_run(func, x1):
                logger.error("AutoTuner: Probe 1 failed. Cannot predict.")
                return 0
            y1 = get_mem()
            
        logger.info(f"AutoTuner: Probe 1 Memory: {y1 / 1e6:.2f} MB")

        # 3. Probe 2
        x2 = int(min_val * step_factor)
        logger.info(f"AutoTuner: Probe 2 (x={x2})...")
        y2 = 0
        with measure_peak_memory() as get_mem:
            if not self._try_run(func, x2):
                logger.warning(f"AutoTuner: Probe 2 failed at {x2}. Fallback to finding max in range [{x1}, {x2}].")
                return self.find_max_config(func, min_val=x1, max_val=x2)
            y2 = get_mem()
            
        logger.info(f"AutoTuner: Probe 2 Memory: {y2 / 1e6:.2f} MB")
        
        # 4. Calculate Slope (Linear Regression for 2 points)
        # y = mx + c
        # m = (y2 - y1) / (x2 - x1)
        if x2 == x1: return x1 # Avoid div by zero
        
        slope = (y2 - y1) / (x2 - x1)
        intercept = y1 - (slope * x1)
        
        logger.info(f"AutoTuner: Calculated Slope: {slope:.4f} bytes/dim")
        
        if slope <= 0:
            logger.warning("AutoTuner: Non-positive memory slope detected (memory didn't increase). Extrapolation unreliable.")
            return self.find_max_config(func, min_val=x2)

        # 5. Solve for Target
        # Target = m * x + c  =>  x = (Target - c) / m
        predicted_max = (available_target - intercept) / slope
        predicted_max = int(predicted_max)
        
        logger.info(f"AutoTuner: Mathematically Predicted Max: {predicted_max}")
        
        if predicted_max <= x2:
             logger.warning("AutoTuner: Predicted max is lower than probe. Something is weird. Returning probe.")
             return x2

        # 6. Verify Prediction
        logger.info(f"AutoTuner: Verifying prediction {predicted_max}...")
        if self._try_run(func, predicted_max):
            logger.info("AutoTuner: Prediction Valid! ✅")
            return predicted_max
        else:
            logger.warning("AutoTuner: Prediction OOM'd. It was too aggressive.")
            # Fallback: We know x2 works, predicted_max fails. 
            # The 'true' limit is likely close. Let's Backoff 5% (Newton's method-ish or just conservative step)
            # Or binary search the gap.
            logger.info("AutoTuner: Refining prediction with search...")
            return self.find_max_config(func, min_val=x2, max_val=predicted_max)
