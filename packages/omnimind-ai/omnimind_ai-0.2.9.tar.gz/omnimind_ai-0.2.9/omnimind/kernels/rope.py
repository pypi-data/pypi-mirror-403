"""
OMNIMIND RoPE Triton Kernels - Full Implementation
High-performance Rotary Position Embedding with autotuning and fused QK processing
"""
import torch
try:
    import triton
    import triton.language as tl
    HAS_TRITON = True
except ImportError:
    HAS_TRITON = False
    class MockTriton:
        @staticmethod
        def jit(fn): return fn
        @staticmethod
        def autotune(configs, key): return lambda fn: fn
    triton = MockTriton()
    import types
    tl = types.SimpleNamespace()
    tl.constexpr = int

def get_rope_autotune_configs():
    """Autotune configurations for RoPE kernels"""
    if not HAS_TRITON:
        return []
    return [
        triton.Config({'BLOCK_SIZE': 32}, num_warps=2),
        triton.Config({'BLOCK_SIZE': 64}, num_warps=4),
        triton.Config({'BLOCK_SIZE': 128}, num_warps=4),
    ]

if HAS_TRITON:
    @triton.autotune(configs=get_rope_autotune_configs(), key=['half_dim'])
    @triton.jit
    def _rope_fwd_kernel(
        Q, Cos, Sin, Y,
        stride_q_b, stride_q_s, stride_q_h, stride_q_d,
        stride_cos_s, stride_cos_d,
        stride_sin_s, stride_sin_d,
        stride_y_b, stride_y_s, stride_y_h, stride_y_d,
        seq_len, head_dim, half_dim,
        BLOCK_SIZE: tl.constexpr,
    ):
        """
        RoPE Forward: Apply rotary position embedding
        q1_out = q1 * cos - q2 * sin
        q2_out = q2 * cos + q1 * sin
        """
        pid_b = tl.program_id(0)
        pid_s = tl.program_id(1)
        pid_h = tl.program_id(2)
        
        # Base pointers
        q_ptr = Q + pid_b * stride_q_b + pid_s * stride_q_s + pid_h * stride_q_h
        y_ptr = Y + pid_b * stride_y_b + pid_s * stride_y_s + pid_h * stride_y_h
        cos_ptr = Cos + pid_s * stride_cos_s
        sin_ptr = Sin + pid_s * stride_sin_s
        
        # Process in blocks for larger head dimensions
        for off in range(0, half_dim, BLOCK_SIZE):
            offs_d = off + tl.arange(0, BLOCK_SIZE)
            mask = offs_d < half_dim
            
            # Load Q halves
            q1 = tl.load(q_ptr + offs_d * stride_q_d, mask=mask, other=0.0)
            q2 = tl.load(q_ptr + (offs_d + half_dim) * stride_q_d, mask=mask, other=0.0)
            
            # Load cos/sin
            cos = tl.load(cos_ptr + offs_d * stride_cos_d, mask=mask, other=1.0)
            sin = tl.load(sin_ptr + offs_d * stride_sin_d, mask=mask, other=0.0)
            
            # Apply RoPE rotation
            out1 = q1 * cos - q2 * sin
            out2 = q2 * cos + q1 * sin
            
            # Store
            tl.store(y_ptr + offs_d * stride_y_d, out1, mask=mask)
            tl.store(y_ptr + (offs_d + half_dim) * stride_y_d, out2, mask=mask)

    @triton.autotune(configs=get_rope_autotune_configs(), key=['half_dim'])
    @triton.jit
    def _rope_bwd_kernel(
        dY, Cos, Sin, dQ,
        stride_dy_b, stride_dy_s, stride_dy_h, stride_dy_d,
        stride_cos_s, stride_cos_d,
        stride_sin_s, stride_sin_d,
        stride_dq_b, stride_dq_s, stride_dq_h, stride_dq_d,
        seq_len, head_dim, half_dim,
        BLOCK_SIZE: tl.constexpr,
    ):
        """
        RoPE Backward: 
        dq1 = dy1 * cos + dy2 * sin
        dq2 = -dy1 * sin + dy2 * cos
        """
        pid_b = tl.program_id(0)
        pid_s = tl.program_id(1)
        pid_h = tl.program_id(2)
        
        dy_ptr = dY + pid_b * stride_dy_b + pid_s * stride_dy_s + pid_h * stride_dy_h
        dq_ptr = dQ + pid_b * stride_dq_b + pid_s * stride_dq_s + pid_h * stride_dq_h
        cos_ptr = Cos + pid_s * stride_cos_s
        sin_ptr = Sin + pid_s * stride_sin_s
        
        for off in range(0, half_dim, BLOCK_SIZE):
            offs_d = off + tl.arange(0, BLOCK_SIZE)
            mask = offs_d < half_dim
            
            # Load dY halves
            dy1 = tl.load(dy_ptr + offs_d * stride_dy_d, mask=mask, other=0.0)
            dy2 = tl.load(dy_ptr + (offs_d + half_dim) * stride_dy_d, mask=mask, other=0.0)
            
            # Load cos/sin
            cos = tl.load(cos_ptr + offs_d * stride_cos_d, mask=mask, other=1.0)
            sin = tl.load(sin_ptr + offs_d * stride_sin_d, mask=mask, other=0.0)
            
            # Inverse rotation for gradient
            dq1 = dy1 * cos + dy2 * sin
            dq2 = -dy1 * sin + dy2 * cos
            
            tl.store(dq_ptr + offs_d * stride_dq_d, dq1, mask=mask)
            tl.store(dq_ptr + (offs_d + half_dim) * stride_dq_d, dq2, mask=mask)

    @triton.jit
    def _rope_fused_qk_kernel(
        Q, K, Cos, Sin, Q_out, K_out,
        stride_q_b, stride_q_s, stride_q_h, stride_q_d,
        stride_k_b, stride_k_s, stride_k_h, stride_k_d,
        stride_cos_s, stride_cos_d,
        stride_sin_s, stride_sin_d,
        stride_qo_b, stride_qo_s, stride_qo_h, stride_qo_d,
        stride_ko_b, stride_ko_s, stride_ko_h, stride_ko_d,
        seq_len, n_heads, n_kv_heads, head_dim, half_dim,
        BLOCK_SIZE: tl.constexpr,
    ):
        """
        Fused RoPE for Q and K in single kernel launch
        Handles GQA (grouped query attention) with different head counts
        """
        pid_b = tl.program_id(0)
        pid_s = tl.program_id(1)
        pid_h = tl.program_id(2)
        
        # Compute KV head index for GQA
        kv_head_idx = pid_h * n_kv_heads // n_heads
        
        # Load cos/sin (shared between Q and K)
        cos_ptr = Cos + pid_s * stride_cos_s
        sin_ptr = Sin + pid_s * stride_sin_s
        
        for off in range(0, half_dim, BLOCK_SIZE):
            offs_d = off + tl.arange(0, BLOCK_SIZE)
            mask = offs_d < half_dim
            
            cos = tl.load(cos_ptr + offs_d * stride_cos_d, mask=mask, other=1.0)
            sin = tl.load(sin_ptr + offs_d * stride_sin_d, mask=mask, other=0.0)
            
            # Process Q
            q_ptr = Q + pid_b * stride_q_b + pid_s * stride_q_s + pid_h * stride_q_h
            qo_ptr = Q_out + pid_b * stride_qo_b + pid_s * stride_qo_s + pid_h * stride_qo_h
            
            q1 = tl.load(q_ptr + offs_d * stride_q_d, mask=mask, other=0.0)
            q2 = tl.load(q_ptr + (offs_d + half_dim) * stride_q_d, mask=mask, other=0.0)
            
            q_out1 = q1 * cos - q2 * sin
            q_out2 = q2 * cos + q1 * sin
            
            tl.store(qo_ptr + offs_d * stride_qo_d, q_out1, mask=mask)
            tl.store(qo_ptr + (offs_d + half_dim) * stride_qo_d, q_out2, mask=mask)
            
            # Process K (only for valid KV heads)
            if pid_h < n_kv_heads:
                k_ptr = K + pid_b * stride_k_b + pid_s * stride_k_s + pid_h * stride_k_h
                ko_ptr = K_out + pid_b * stride_ko_b + pid_s * stride_ko_s + pid_h * stride_ko_h
                
                k1 = tl.load(k_ptr + offs_d * stride_k_d, mask=mask, other=0.0)
                k2 = tl.load(k_ptr + (offs_d + half_dim) * stride_k_d, mask=mask, other=0.0)
                
                k_out1 = k1 * cos - k2 * sin
                k_out2 = k2 * cos + k1 * sin
                
                tl.store(ko_ptr + offs_d * stride_ko_d, k_out1, mask=mask)
                tl.store(ko_ptr + (offs_d + half_dim) * stride_ko_d, k_out2, mask=mask)


class RoPEFunction(torch.autograd.Function):
    """Autograd function for RoPE with Triton"""
    
    @staticmethod
    def forward(ctx, q, cos, sin):
        batch, seq_len, n_heads, head_dim = q.shape
        half_dim = head_dim // 2
        
        q_out = torch.empty_like(q)
        grid = (batch, seq_len, n_heads)
        
        _rope_fwd_kernel[grid](
            q, cos, sin, q_out,
            q.stride(0), q.stride(1), q.stride(2), q.stride(3),
            cos.stride(0), cos.stride(1),
            sin.stride(0), sin.stride(1),
            q_out.stride(0), q_out.stride(1), q_out.stride(2), q_out.stride(3),
            seq_len, head_dim, half_dim,
        )
        
        ctx.save_for_backward(cos, sin)
        ctx.shape = q.shape
        return q_out
    
    @staticmethod
    def backward(ctx, dy):
        cos, sin = ctx.saved_tensors
        batch, seq_len, n_heads, head_dim = ctx.shape
        half_dim = head_dim // 2
        
        dq = torch.empty_like(dy)
        grid = (batch, seq_len, n_heads)
        
        _rope_bwd_kernel[grid](
            dy.contiguous(), cos, sin, dq,
            dy.stride(0), dy.stride(1), dy.stride(2), dy.stride(3),
            cos.stride(0), cos.stride(1),
            sin.stride(0), sin.stride(1),
            dq.stride(0), dq.stride(1), dq.stride(2), dq.stride(3),
            seq_len, head_dim, half_dim,
        )
        
        return dq, None, None


def fast_rope_embedding(q, k, cos, sin, position_ids=None):
    """
    High-performance RoPE for Q and K
    q: [batch, seq_len, n_heads, head_dim]
    k: [batch, seq_len, n_kv_heads, head_dim]
    cos, sin: [seq_len, head_dim // 2]
    """
    if not HAS_TRITON or not q.is_cuda:
        return _pytorch_rope(q, k, cos, sin)
    
    batch, seq_len, n_heads, head_dim = q.shape
    n_kv_heads = k.shape[2]
    half_dim = head_dim // 2
    
    q = q.contiguous()
    k = k.contiguous()
    cos = cos.contiguous()
    sin = sin.contiguous()
    
    q_out = torch.empty_like(q)
    k_out = torch.empty_like(k)
    
    # Use fused kernel for efficiency
    grid = (batch, seq_len, n_heads)
    
    _rope_fused_qk_kernel[grid](
        q, k, cos, sin, q_out, k_out,
        q.stride(0), q.stride(1), q.stride(2), q.stride(3),
        k.stride(0), k.stride(1), k.stride(2), k.stride(3),
        cos.stride(0), cos.stride(1),
        sin.stride(0), sin.stride(1),
        q_out.stride(0), q_out.stride(1), q_out.stride(2), q_out.stride(3),
        k_out.stride(0), k_out.stride(1), k_out.stride(2), k_out.stride(3),
        seq_len, n_heads, n_kv_heads, head_dim, half_dim,
        BLOCK_SIZE=min(64, half_dim),
    )
    
    return q_out, k_out


def fast_rope_single(x, cos, sin):
    """Apply RoPE to single tensor (Q or K)"""
    if not HAS_TRITON or not x.is_cuda:
        half_dim = x.shape[-1] // 2
        x1, x2 = x[..., :half_dim], x[..., half_dim:]
        cos = cos.unsqueeze(1)
        sin = sin.unsqueeze(1)
        return torch.cat([x1 * cos - x2 * sin, x2 * cos + x1 * sin], dim=-1)
    
    return RoPEFunction.apply(x.contiguous(), cos.contiguous(), sin.contiguous())


def _pytorch_rope(q, k, cos, sin):
    """PyTorch fallback for RoPE"""
    half_dim = q.shape[-1] // 2
    
    # Reshape cos/sin for broadcasting
    cos = cos.unsqueeze(1)  # [seq, 1, half_dim]
    sin = sin.unsqueeze(1)
    
    # Q rotation
    q1, q2 = q[..., :half_dim], q[..., half_dim:]
    q_out = torch.cat([q1 * cos - q2 * sin, q2 * cos + q1 * sin], dim=-1)
    
    # K rotation
    k1, k2 = k[..., :half_dim], k[..., half_dim:]
    k_out = torch.cat([k1 * cos - k2 * sin, k2 * cos + k1 * sin], dim=-1)
    
    return q_out, k_out


def precompute_rope_cache(seq_len, head_dim, base=10000.0, device='cuda', dtype=torch.float32):
    """Precompute cos/sin cache for RoPE"""
    half_dim = head_dim // 2
    
    # Compute inverse frequencies
    inv_freq = 1.0 / (base ** (torch.arange(0, half_dim, dtype=dtype, device=device) / half_dim))
    
    # Compute position angles
    positions = torch.arange(seq_len, dtype=dtype, device=device)
    angles = positions.unsqueeze(1) * inv_freq.unsqueeze(0)  # [seq_len, half_dim]
    
    cos = torch.cos(angles)
    sin = torch.sin(angles)
    
    return cos, sin
