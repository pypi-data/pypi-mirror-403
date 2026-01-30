"""
OMNIMIND Triton Kernels - High-Performance GPU Operations

This module provides optimized Triton kernels for:
- SSM (State-Space Model) selective scan
- LayerNorm / RMSNorm with fused operations
- Activation functions (SwiGLU, GeGLU)  
- Rotary Position Embedding (RoPE)
- Cross-Entropy loss with online softmax
- Mixture of Experts (MoE) routing
- Quantized matrix multiplication (INT4/INT8/NF4)

All kernels include:
- @triton.autotune for optimal block sizes
- Forward and backward passes for training
- PyTorch fallbacks for CPU/non-CUDA

GRACEFUL FALLBACK POLICY:
- If Triton is not available, all functions automatically use PyTorch implementations
- Performance will be slower but functionality is preserved
- A warning is printed once at import time if Triton is unavailable
"""

import warnings
import platform
import logging

logger = logging.getLogger("omnimind.kernels")

# ============================================================================
# TRITON AVAILABILITY DETECTION WITH DETAILED DIAGNOSTICS
# ============================================================================

def _check_triton_availability():
    """
    Check Triton availability with detailed diagnostics.
    Returns (is_available, reason_if_not)
    """
    system = platform.system()
    
    # macOS: Triton doesn't work (no CUDA)
    if system == "Darwin":
        return False, "macOS detected - Triton requires NVIDIA CUDA (using PyTorch fallback)"
    
    # Windows: Triton support is limited
    if system == "Windows":
        try:
            import triton
            return True, None
        except ImportError:
            return False, "Triton not installed on Windows (using PyTorch fallback)"
        except Exception as e:
            return False, f"Triton failed on Windows: {e} (using PyTorch fallback)"
    
    # Linux: Should work if installed
    try:
        import triton
        import torch
        if not torch.cuda.is_available():
            return False, "CUDA not available - Triton requires CUDA (using PyTorch fallback)"
        return True, None
    except ImportError:
        return False, "Triton not installed (using PyTorch fallback)"
    except Exception as e:
        return False, f"Triton initialization failed: {e} (using PyTorch fallback)"


HAS_TRITON, TRITON_UNAVAILABLE_REASON = _check_triton_availability()

# Print warning once if Triton is unavailable
if not HAS_TRITON:
    _warned = False
    if not _warned:
        logger.warning(f"⚠️ {TRITON_UNAVAILABLE_REASON}")
        logger.warning("   Performance may be reduced. For best speed, use Linux with NVIDIA GPU.")
        _warned = True


# ============================================================================
# SAFE IMPORTS WITH FALLBACKS
# ============================================================================

def _safe_import(module_name, items):
    """Safely import items from a kernel module with error handling."""
    result = {}
    try:
        module = __import__(f"omnimind.kernels.{module_name}", fromlist=items)
        for item in items:
            result[item] = getattr(module, item, None)
    except ImportError as e:
        logger.warning(f"Failed to import {module_name}: {e}")
        for item in items:
            result[item] = None
    except Exception as e:
        logger.warning(f"Error loading {module_name}: {e}")
        for item in items:
            result[item] = None
    return result


# LayerNorm / RMSNorm
from .layernorm import (
    fast_rms_norm,
    fast_layer_norm,
    fast_fused_add_rms_norm,
)

# Activation functions
from .swiglu import (
    fast_swiglu,
    fast_fused_swiglu_linear,
)
from .geglu import (
    fast_geglu,
    fast_geglu_split,
)

# SSM kernels
from .ssm import fast_ssm_scan

# Position embeddings
from .rope import (
    fast_rope_embedding,
    fast_rope_single,
    precompute_rope_cache,
)

# Loss functions
from .cross_entropy import (
    fast_cross_entropy_loss,
    fast_cross_entropy_with_logits,
)

# MoE kernels
from .moe import (
    fast_moe_routing,
    fast_moe_gate,
    moe_dispatch_combine,
    compute_load_balancing_loss,
)

# Quantization kernels
from .quant_matmul import (
    fast_quant_matmul,
    quantize_weight_int4,
)


# ============================================================================
# RUNTIME KERNEL SELECTION
# ============================================================================

def get_kernel_info():
    """Get information about available kernels and their backends."""
    return {
        "triton_available": HAS_TRITON,
        "triton_reason": TRITON_UNAVAILABLE_REASON if not HAS_TRITON else "OK",
        "platform": platform.system(),
        "kernels": {
            "rms_norm": "triton" if HAS_TRITON else "pytorch",
            "layer_norm": "triton" if HAS_TRITON else "pytorch",
            "swiglu": "triton" if HAS_TRITON else "pytorch",
            "ssm_scan": "triton" if HAS_TRITON else "pytorch",
            "rope": "triton" if HAS_TRITON else "pytorch",
            "cross_entropy": "triton" if HAS_TRITON else "pytorch",
            "moe_routing": "triton" if HAS_TRITON else "pytorch",
            "quant_matmul": "triton" if HAS_TRITON else "pytorch",
        }
    }

__all__ = [
    # Core flag
    "HAS_TRITON",
    "TRITON_UNAVAILABLE_REASON",
    "get_kernel_info",
    
    # Normalization
    "fast_rms_norm",
    "fast_layer_norm", 
    "fast_fused_add_rms_norm",
    
    # Activations
    "fast_swiglu",
    "fast_fused_swiglu_linear",
    "fast_geglu",
    "fast_geglu_split",
    
    # SSM
    "fast_ssm_scan",
    
    # RoPE
    "fast_rope_embedding",
    "fast_rope_single",
    "precompute_rope_cache",
    
    # Loss
    "fast_cross_entropy_loss",
    "fast_cross_entropy_with_logits",
    
    # MoE
    "fast_moe_routing",
    "fast_moe_gate",
    "moe_dispatch_combine",
    "compute_load_balancing_loss",
    
    # Quantization
    "fast_quant_matmul",
    "quantize_weight_int4",
]
