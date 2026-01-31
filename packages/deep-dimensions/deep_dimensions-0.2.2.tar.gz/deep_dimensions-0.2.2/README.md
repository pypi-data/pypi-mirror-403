# Deep Dimensions

> Multi-framework tensor dimension auto-scaling for PyTorch and TensorFlow

Automatically scales tensor dimensions based on available system memory. Prevents OOM errors by intelligently reducing dimensions while preserving aspect ratios.

## Installation

```bash
pip install deep-dimensions

# Or with specific framework
pip install deep-dimensions[pytorch]
pip install deep-dimensions[tensorflow]
pip install deep-dimensions[all]
```

## Quick Start

```python
from deep_dimensions import AutoScaler

# Auto-detects framework (PyTorch or TensorFlow)
scaler = AutoScaler()

# Scale dimensions to fit memory
dims = scaler.scale_dimensions((4096, 4096, 3))
print(f"Scaled: {dims}")

# Create a memory-safe tensor
tensor = scaler.create_scaled_tensor((8192, 8192, 3), fill_value=0.0)
```

## Framework-Specific Usage

### PyTorch

```python
import torch
from deep_dimensions import AutoScaler, ScalingConfig

config = ScalingConfig(
    memory_threshold=0.7,      # Use max 70% of available memory
    strategy="exponential",    # Reduce larger dims more aggressively
    device="auto",             # CPU or CUDA auto-detection
)

scaler = AutoScaler(config, framework="pytorch")
tensor = scaler.create_scaled_tensor((2048, 2048, 3), dtype=torch.float16)
```

### TensorFlow

```python
import tensorflow as tf
from deep_dimensions import AutoScaler, ScalingConfig

config = ScalingConfig(
    memory_threshold=0.6,
    strategy="linear",
)

scaler = AutoScaler(config, framework="tensorflow")
tensor = scaler.create_scaled_tensor((2048, 2048, 3), dtype=tf.float32)
```

## Core API

| Method | Description |
|--------|-------------|
| `scale_dimensions(dims, dtype)` | Returns scaled dimensions that fit in memory |
| `create_scaled_tensor(dims, dtype, fill_value)` | Creates a tensor with auto-scaled dimensions |
| `scale_dimensions_with_info(dims, dtype)` | Returns `ScalingResult` with metadata |
| `can_fit(dims, dtype)` | Checks if dimensions fit in available memory |
| `get_memory_info()` | Returns current memory status |
| `estimate_memory(dims, dtype)` | Estimates memory needed for dimensions |

## Configuration

```python
from deep_dimensions import ScalingConfig

config = ScalingConfig(
    memory_threshold=0.8,      # Max memory usage ratio (0-1)
    safety_margin=0.1,         # Additional safety buffer
    device="auto",             # "cpu", "cuda", or "auto"
    strategy="linear",         # "linear" or "exponential"
    framework="auto",          # "pytorch", "tensorflow", or "auto"
    min_dimensions=(32, 32),   # Minimum allowed dimensions
    max_dimensions=(4096, 4096),  # Maximum allowed dimensions
)
```

## Scaling Strategies

**Linear**: Reduces all dimensions proportionally
```
(1024, 1024, 3) → (512, 512, 2)  # All dims scaled ~50%
```

**Exponential**: Reduces larger dimensions more aggressively
```
(1024, 256, 3) → (256, 128, 3)   # Larger dims reduced more
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     AutoScaler                          │
│  (Public API - Facade Pattern)                          │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │MemoryMonitor │  │DimensionCalc │  │FrameworkReg  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
├─────────────────────────────────────────────────────────┤
│         IMemoryProvider     IScalingStrategy            │
│         IFrameworkAdapter                               │
│  (Abstractions - Dependency Inversion)                  │
├─────────────────────────────────────────────────────────┤
│  ┌────────────┐ ┌────────────┐ ┌────────────┐          │
│  │SystemMem   │ │LinearScale │ │PyTorchAdpt │          │
│  │CUDAMem     │ │ExpoScale   │ │TFAdapter   │          │
│  └────────────┘ └────────────┘ └────────────┘          │
│  (Implementations - Strategy Pattern)                   │
└─────────────────────────────────────────────────────────┘
```

## Design Principles

- **SOLID**: Single responsibility, Open/closed, Interface segregation
- **Dependency Inversion**: Core depends on abstractions, not implementations
- **Strategy Pattern**: Pluggable scaling algorithms
- **Facade Pattern**: Simple API hiding complex internals
- **Immutability**: Config and result objects are frozen dataclasses
- **Fail-Fast**: Validates inputs at boundaries with clear errors
