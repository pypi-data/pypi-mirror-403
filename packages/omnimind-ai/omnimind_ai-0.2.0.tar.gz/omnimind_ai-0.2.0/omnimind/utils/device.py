"""
OMNIMIND Device Detection Utilities
Auto-detect and manage GPU/accelerator devices.
"""

import functools
import torch
from typing import Optional

__all__ = [
    "is_hip",
    "is_mps",
    "get_device_type",
    "get_device_count",
    "get_optimal_device",
    "DEVICE_TYPE",
    "DEVICE_COUNT",
    "HAS_CUDA",
    "HAS_MPS",
    "HAS_TRITON",
]

@functools.cache
def is_hip() -> bool:
    """Check if running on AMD ROCm/HIP"""
    return bool(getattr(getattr(torch, "version", None), "hip", None))

@functools.cache
def is_mps() -> bool:
    """Check if running on Apple Silicon MPS"""
    return hasattr(torch.backends, "mps") and torch.backends.mps.is_available()

@functools.cache
def get_device_type() -> str:
    """
    Detect the available accelerator type.
    
    Returns:
        "cuda", "mps", "hip", "xpu", or "cpu"
    """
    # Check CUDA first (most common)
    if hasattr(torch, "cuda") and torch.cuda.is_available():
        if is_hip():
            return "hip"
        return "cuda"
    
    # Check Apple MPS
    if is_mps():
        return "mps"
    
    # Check Intel XPU
    if hasattr(torch, "xpu") and torch.xpu.is_available():
        return "xpu"
    
    # Fallback to CPU
    return "cpu"

@functools.cache
def get_device_count() -> int:
    """Get number of available accelerators"""
    device_type = get_device_type()
    
    if device_type in ("cuda", "hip"):
        return torch.cuda.device_count()
    elif device_type == "xpu":
        return torch.xpu.device_count()
    elif device_type == "mps":
        return 1  # MPS is single device
    else:
        return 0  # CPU

def get_optimal_device(device_id: Optional[int] = None) -> torch.device:
    """
    Get the optimal device for computation.
    
    Args:
        device_id: Specific device ID (for multi-GPU)
        
    Returns:
        torch.device object
    """
    device_type = get_device_type()
    
    if device_type == "cpu":
        return torch.device("cpu")
    elif device_type == "mps":
        return torch.device("mps")
    elif device_type in ("cuda", "hip"):
        if device_id is not None:
            return torch.device(f"cuda:{device_id}")
        return torch.device("cuda")
    elif device_type == "xpu":
        if device_id is not None:
            return torch.device(f"xpu:{device_id}")
        return torch.device("xpu")
    
    return torch.device("cpu")

def get_optimal_dtype(device: Optional[torch.device] = None) -> torch.dtype:
    """
    Get optimal dtype for the device.
    
    - CUDA/HIP: bfloat16 (if supported) or float16
    - MPS: float16
    - CPU: float32
    """
    if device is None:
        device = get_optimal_device()
    
    if device.type in ("cuda", "hip"):
        # Check bfloat16 support
        if torch.cuda.is_bf16_supported():
            return torch.bfloat16
        return torch.float16
    elif device.type == "mps":
        return torch.float16
    else:
        return torch.float32

# Module-level constants (computed once on import)
DEVICE_TYPE: str = get_device_type()
DEVICE_COUNT: int = get_device_count()
HAS_CUDA: bool = DEVICE_TYPE in ("cuda", "hip")
HAS_MPS: bool = DEVICE_TYPE == "mps"

# Check Triton availability
try:
    import triton
    HAS_TRITON = HAS_CUDA  # Triton requires CUDA
except ImportError:
    HAS_TRITON = False

# Status message on import
if __name__ != "__main__":
    if DEVICE_TYPE == "cpu":
        print("⚠️ Omnimind: No GPU detected, running on CPU (slower)")
    else:
        print(f"✅ Omnimind: Using {DEVICE_TYPE.upper()} ({DEVICE_COUNT} device{'s' if DEVICE_COUNT > 1 else ''})")
