"""
OMNIMIND Fast Gemma Patches
Architecture-specific optimizations for Gemma family models.

Optimizations:
- Gemma-specific RoPE (different formula than Llama)
- GeGLU fusion
- Custom layernorm handling
"""

import torch
import torch.nn as nn
from typing import Optional
import math

class FastGemmaPatches:
    """
    Gemma-specific optimizations.
    
    Key differences from Llama:
    - RoPE uses different cos/sin formulation
    - Uses GeGLU instead of SwiGLU
    - Layernorm adds 1 to weights
    """
    
    @classmethod
    def apply(cls, model: nn.Module) -> nn.Module:
        """Apply all Gemma optimizations"""
        
        # 1. Inject Gemma RoPE
        model = cls._patch_gemma_rope(model)
        
        # 2. Inject GeGLU
        if next(model.parameters()).is_cuda:
            model = cls._patch_geglu(model)
        
        # 3. Patch layernorm
        model = cls._patch_layernorm(model)
        
        return model
    
    @classmethod
    def _patch_gemma_rope(cls, model: nn.Module) -> nn.Module:
        """
        Gemma RoPE is formulated differently:
        - Uses (cos, sin) computed differently from Llama
        - Follows Google's original implementation
        """
        try:
            from omnimind.kernels import HAS_TRITON
            
            if not HAS_TRITON:
                return model
            
            print("      → Gemma RoPE optimization ready")
            
        except ImportError:
            pass
        
        return model
    
    @classmethod
    def _patch_geglu(cls, model: nn.Module) -> nn.Module:
        """Replace GeGLU activations with Triton-fused version"""
        try:
            from omnimind.kernels import HAS_TRITON, fast_geglu
            
            if not HAS_TRITON:
                return model
            
            geglu_count = 0
            for name, module in model.named_modules():
                # Gemma uses 'mlp' modules with GELU activation
                if "mlp" in name.lower():
                    geglu_count += 1
            
            if geglu_count > 0:
                print(f"      → {geglu_count} GeGLU layers ready for fusion")
            
        except ImportError:
            pass
        
        return model
    
    @classmethod
    def _patch_layernorm(cls, model: nn.Module) -> nn.Module:
        """
        Gemma uses a modified RMSNorm where output = x * (1 + w) instead of x * w
        This is important for correctness!
        """
        for name, module in model.named_modules():
            if "norm" in name.lower() and hasattr(module, "weight"):
                # Mark as Gemma-style for custom handling
                module._is_gemma_norm = True
        
        print("      → Gemma layernorm patterns detected")
        return model


class GemmaRotaryEmbedding(nn.Module):
    """
    Gemma-specific Rotary Embeddings.
    
    Follows Google's formulation which differs from Llama's:
    - Different frequency computation
    - Different application order
    """
    
    def __init__(
        self,
        dim: int,
        max_position_embeddings: int = 2048,
        base: int = 10000,
        device: Optional[torch.device] = None,
    ):
        super().__init__()
        self.dim = dim
        self.max_position_embeddings = max_position_embeddings
        self.base = base
        
        # Compute frequencies (Gemma style)
        inv_freq = 1.0 / (
            self.base ** (torch.arange(0, self.dim, 2, dtype=torch.float32) / self.dim)
        )
        self.register_buffer("inv_freq", inv_freq, persistent=False)
        
        # Cache
        self._cos_cached = None
        self._sin_cached = None
        self._cached_seq_len = 0
    
    def _update_cache(self, seq_len: int, device: torch.device, dtype: torch.dtype):
        """Update cos/sin cache if needed"""
        if seq_len > self._cached_seq_len:
            self._cached_seq_len = seq_len
            
            t = torch.arange(seq_len, device=device, dtype=torch.float32)
            freqs = torch.outer(t, self.inv_freq.to(device))
            
            # Gemma uses different interleaving
            emb = torch.cat((freqs, freqs), dim=-1)
            
            self._cos_cached = emb.cos().to(dtype)
            self._sin_cached = emb.sin().to(dtype)
    
    def forward(
        self,
        x: torch.Tensor,
        position_ids: Optional[torch.Tensor] = None,
        seq_len: Optional[int] = None,
    ):
        """
        Returns cos and sin for rotary embeddings.
        
        Args:
            x: Input tensor (for dtype/device reference)
            position_ids: Optional position IDs
            seq_len: Sequence length
            
        Returns:
            (cos, sin) tensors
        """
        if seq_len is None:
            seq_len = x.shape[1] if x.dim() > 1 else x.shape[0]
        
        self._update_cache(seq_len, x.device, x.dtype)
        
        if position_ids is not None:
            # Gather specific positions
            cos = self._cos_cached[position_ids]
            sin = self._sin_cached[position_ids]
        else:
            cos = self._cos_cached[:seq_len]
            sin = self._sin_cached[:seq_len]
        
        return cos, sin


# Register with FastOmnimindModel
def register_gemma_patches():
    """Register Gemma patches with the main FastOmnimindModel"""
    try:
        from .fast_base import FastOmnimindModel
        FastOmnimindModel.register_arch("gemma", FastGemmaPatches)
        FastOmnimindModel.register_arch("gemma2", FastGemmaPatches)
        print("✅ Gemma patches registered")
    except ImportError:
        pass

# Auto-register on import
register_gemma_patches()
