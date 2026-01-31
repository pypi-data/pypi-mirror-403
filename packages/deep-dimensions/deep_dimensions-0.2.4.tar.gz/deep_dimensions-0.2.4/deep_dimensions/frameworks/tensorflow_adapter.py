"""TensorFlow framework adapter.

This module provides TensorFlow-specific implementations for the
framework adapter interface.
"""

from typing import Any, Tuple, Union

from deep_dimensions.interfaces.framework_adapter import IFrameworkAdapter

# Lazy import to avoid requiring tensorflow
_tf = None


def _get_tf():
    """Lazily import tensorflow."""
    global _tf
    if _tf is None:
        try:
            import tensorflow as tf
            _tf = tf
        except ImportError:
            _tf = False
    return _tf


class TensorFlowAdapter(IFrameworkAdapter):
    """Framework adapter for TensorFlow.
    
    Provides TensorFlow-specific tensor operations and memory detection.
    """

    # Mapping of dtype to bytes per element
    DTYPE_SIZES = {}

    def __init__(self) -> None:
        """Initialize the TensorFlow adapter."""
        tf = _get_tf()
        if tf:
            self.DTYPE_SIZES = {
                tf.float16: 2,
                tf.float32: 4,
                tf.float64: 8,
                tf.bfloat16: 2,
                tf.int8: 1,
                tf.int16: 2,
                tf.int32: 4,
                tf.int64: 8,
                tf.uint8: 1,
                tf.uint16: 2,
                tf.uint32: 4,
                tf.uint64: 8,
                tf.bool: 1,
                tf.complex64: 8,
                tf.complex128: 16,
            }

    @property
    def name(self) -> str:
        """Return the framework name."""
        return "tensorflow"

    def is_available(self) -> bool:
        """Check if TensorFlow is available."""
        tf = _get_tf()
        return tf is not False

    def get_dtype_size(self, dtype: Any) -> int:
        """Get the size in bytes of a TensorFlow dtype.
        
        Args:
            dtype: TensorFlow data type.
            
        Returns:
            Size in bytes per element.
        """
        if dtype in self.DTYPE_SIZES:
            return self.DTYPE_SIZES[dtype]
        raise ValueError(f"Unsupported dtype: {dtype}")

    def get_default_dtype(self) -> Any:
        """Get the default TensorFlow dtype (float32)."""
        tf = _get_tf()
        if not tf:
            raise RuntimeError("TensorFlow is not available")
        return tf.float32

    def create_tensor(
        self,
        dimensions: Tuple[int, ...],
        dtype: Any,
        device: str,
        fill_value: Union[float, None] = None,
        requires_grad: bool = False,
    ) -> Any:
        """Create a TensorFlow tensor.
        
        Args:
            dimensions: Tensor shape.
            dtype: TensorFlow data type.
            device: Device ("cpu" or "cuda"/"gpu").
            fill_value: Optional fill value.
            requires_grad: If True, creates a Variable for gradient tracking.
            
        Returns:
            TensorFlow tensor or Variable.
        """
        tf = _get_tf()
        if not tf:
            raise RuntimeError("TensorFlow is not available")

        # Map device names
        if device == "cuda":
            device = "/GPU:0"
        elif device == "cpu":
            device = "/CPU:0"

        with tf.device(device):
            if fill_value is None:
                # TensorFlow doesn't have uninitialized tensors like PyTorch
                # Use zeros as default
                tensor = tf.zeros(dimensions, dtype=dtype)
            elif fill_value == 0.0:
                tensor = tf.zeros(dimensions, dtype=dtype)
            elif fill_value == 1.0:
                tensor = tf.ones(dimensions, dtype=dtype)
            else:
                tensor = tf.fill(dimensions, tf.cast(fill_value, dtype))

            if requires_grad:
                return tf.Variable(tensor, trainable=True)
            return tensor

    def is_cuda_available(self) -> bool:
        """Check if GPU is available in TensorFlow."""
        tf = _get_tf()
        if not tf:
            return False
        gpus = tf.config.list_physical_devices('GPU')
        return len(gpus) > 0

    def get_cuda_memory_info(self, device_index: int = 0) -> Tuple[int, int, int]:
        """Get GPU memory information for TensorFlow.
        
        Note: TensorFlow's memory reporting is less precise than PyTorch's.
        
        Args:
            device_index: GPU device index.
            
        Returns:
            Tuple of (total, available, used) memory in bytes.
        """
        tf = _get_tf()
        if not tf:
            raise RuntimeError("TensorFlow is not available")

        gpus = tf.config.list_physical_devices('GPU')
        if not gpus:
            raise RuntimeError("No GPU available")

        if device_index >= len(gpus):
            raise RuntimeError(f"GPU device {device_index} not found")

        try:
            # Try to get memory info using nvidia-smi via pynvml
            import subprocess
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=memory.total,memory.free,memory.used',
                 '--format=csv,nounits,noheader', f'-id={device_index}'],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                values = result.stdout.strip().split(',')
                total = int(values[0]) * 1024 * 1024  # Convert MB to bytes
                available = int(values[1]) * 1024 * 1024
                used = int(values[2]) * 1024 * 1024
                return total, available, used
        except (FileNotFoundError, subprocess.SubprocessError):
            pass

        # Fallback: Use psutil to estimate (not GPU-specific)
        import psutil
        mem = psutil.virtual_memory()
        return mem.total, mem.available, mem.used

    def validate_dtype(self, dtype: Any) -> bool:
        """Validate that a dtype is a valid TensorFlow dtype."""
        return dtype in self.DTYPE_SIZES
