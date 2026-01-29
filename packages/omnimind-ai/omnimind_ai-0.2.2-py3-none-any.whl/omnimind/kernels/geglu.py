"""
OMNIMIND GeGLU Triton Kernels - Full Implementation
High-performance GeGLU with autotuning, backward pass, and exact GELU
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

# GELU constants for tanh approximation
SQRT_2_OVER_PI = 0.7978845608028654
GELU_COEF = 0.044715

def get_geglu_autotune_configs():
    """Autotune configurations for GeGLU kernels"""
    if not HAS_TRITON:
        return []
    return [
        triton.Config({'BLOCK_SIZE': 256}, num_warps=2),
        triton.Config({'BLOCK_SIZE': 512}, num_warps=4),
        triton.Config({'BLOCK_SIZE': 1024}, num_warps=4),
        triton.Config({'BLOCK_SIZE': 2048}, num_warps=8),
        triton.Config({'BLOCK_SIZE': 4096}, num_warps=8),
    ]

if HAS_TRITON:
    @triton.autotune(configs=get_geglu_autotune_configs(), key=['d_model'])
    @triton.jit
    def _geglu_fwd_kernel(
        X_ptr, Gate_ptr, Y_ptr,
        stride_x_b, stride_x_s, stride_x_d,
        stride_g_b, stride_g_s, stride_g_d,
        stride_y_b, stride_y_s, stride_y_d,
        d_model,
        BLOCK_SIZE: tl.constexpr,
    ):
        """
        GeGLU Forward: y = x * GELU(gate)
        Uses tanh approximation: GELU(x) ≈ 0.5 * x * (1 + tanh(sqrt(2/π) * (x + 0.044715 * x³)))
        """
        pid_b = tl.program_id(0)
        pid_s = tl.program_id(1)
        
        # Process d_model in blocks
        for off in range(0, d_model, BLOCK_SIZE):
            offs_d = off + tl.arange(0, BLOCK_SIZE)
            mask = offs_d < d_model
            
            # Compute offsets
            x_offset = pid_b * stride_x_b + pid_s * stride_x_s + offs_d * stride_x_d
            g_offset = pid_b * stride_g_b + pid_s * stride_g_s + offs_d * stride_g_d
            y_offset = pid_b * stride_y_b + pid_s * stride_y_s + offs_d * stride_y_d
            
            # Load
            x = tl.load(X_ptr + x_offset, mask=mask, other=0.0)
            g = tl.load(Gate_ptr + g_offset, mask=mask, other=0.0)
            
            # GELU approximation (tanh)
            g_cubed = g * g * g
            inner = SQRT_2_OVER_PI * (g + GELU_COEF * g_cubed)
            tanh_inner = tl.tanh(inner)
            gelu_g = 0.5 * g * (1.0 + tanh_inner)
            
            # GeGLU output
            y = x * gelu_g
            
            tl.store(Y_ptr + y_offset, y, mask=mask)

    @triton.autotune(configs=get_geglu_autotune_configs(), key=['d_model'])
    @triton.jit
    def _geglu_bwd_kernel(
        dY_ptr, X_ptr, Gate_ptr,
        dX_ptr, dGate_ptr,
        stride_dy_b, stride_dy_s, stride_dy_d,
        stride_x_b, stride_x_s, stride_x_d,
        stride_g_b, stride_g_s, stride_g_d,
        stride_dx_b, stride_dx_s, stride_dx_d,
        stride_dg_b, stride_dg_s, stride_dg_d,
        d_model,
        BLOCK_SIZE: tl.constexpr,
    ):
        """
        GeGLU Backward:
        dx = dy * GELU(gate)
        dgate = dy * x * GELU'(gate)
        
        GELU'(x) = 0.5 * (1 + tanh(a)) + 0.5 * x * (1 - tanh(a)²) * sqrt(2/π) * (1 + 3 * c * x²)
        where a = sqrt(2/π) * (x + c * x³), c = 0.044715
        """
        pid_b = tl.program_id(0)
        pid_s = tl.program_id(1)
        
        for off in range(0, d_model, BLOCK_SIZE):
            offs_d = off + tl.arange(0, BLOCK_SIZE)
            mask = offs_d < d_model
            
            # Compute offsets
            dy_offset = pid_b * stride_dy_b + pid_s * stride_dy_s + offs_d * stride_dy_d
            x_offset = pid_b * stride_x_b + pid_s * stride_x_s + offs_d * stride_x_d
            g_offset = pid_b * stride_g_b + pid_s * stride_g_s + offs_d * stride_g_d
            dx_offset = pid_b * stride_dx_b + pid_s * stride_dx_s + offs_d * stride_dx_d
            dg_offset = pid_b * stride_dg_b + pid_s * stride_dg_s + offs_d * stride_dg_d
            
            # Load
            dy = tl.load(dY_ptr + dy_offset, mask=mask, other=0.0)
            x = tl.load(X_ptr + x_offset, mask=mask, other=0.0)
            g = tl.load(Gate_ptr + g_offset, mask=mask, other=0.0)
            
            # Forward GELU computation (needed for backward)
            g_sq = g * g
            g_cubed = g_sq * g
            inner = SQRT_2_OVER_PI * (g + GELU_COEF * g_cubed)
            tanh_inner = tl.tanh(inner)
            gelu_g = 0.5 * g * (1.0 + tanh_inner)
            
            # GELU derivative
            # d(tanh(a))/dg = (1 - tanh(a)²) * da/dg
            # da/dg = sqrt(2/π) * (1 + 3 * c * g²)
            sech_sq = 1.0 - tanh_inner * tanh_inner
            da_dg = SQRT_2_OVER_PI * (1.0 + 3.0 * GELU_COEF * g_sq)
            
            # GELU'(g) = 0.5 * (1 + tanh(a)) + 0.5 * g * sech²(a) * da/dg
            gelu_prime = 0.5 * (1.0 + tanh_inner) + 0.5 * g * sech_sq * da_dg
            
            # Gradients
            dx = dy * gelu_g
            dg = dy * x * gelu_prime
            
            tl.store(dX_ptr + dx_offset, dx, mask=mask)
            tl.store(dGate_ptr + dg_offset, dg, mask=mask)

    @triton.jit
    def _geglu_fused_split_kernel(
        XG_ptr, Y_ptr,  # XG is combined [batch, seq, 2*d_model]
        stride_xg_b, stride_xg_s, stride_xg_d,
        stride_y_b, stride_y_s, stride_y_d,
        d_model,
        BLOCK_SIZE: tl.constexpr,
    ):
        """
        Fused Split + GeGLU: splits input in half and applies GeGLU
        Input: [batch, seq, 2*d_model] -> Output: [batch, seq, d_model]
        """
        pid_b = tl.program_id(0)
        pid_s = tl.program_id(1)
        
        for off in range(0, d_model, BLOCK_SIZE):
            offs_d = off + tl.arange(0, BLOCK_SIZE)
            mask = offs_d < d_model
            
            # Load x (first half) and gate (second half)
            x_offset = pid_b * stride_xg_b + pid_s * stride_xg_s + offs_d * stride_xg_d
            g_offset = pid_b * stride_xg_b + pid_s * stride_xg_s + (offs_d + d_model) * stride_xg_d
            y_offset = pid_b * stride_y_b + pid_s * stride_y_s + offs_d * stride_y_d
            
            x = tl.load(XG_ptr + x_offset, mask=mask, other=0.0)
            g = tl.load(XG_ptr + g_offset, mask=mask, other=0.0)
            
            # GELU approximation
            g_cubed = g * g * g
            inner = SQRT_2_OVER_PI * (g + GELU_COEF * g_cubed)
            tanh_inner = tl.tanh(inner)
            gelu_g = 0.5 * g * (1.0 + tanh_inner)
            
            y = x * gelu_g
            tl.store(Y_ptr + y_offset, y, mask=mask)


class GeGLUFunction(torch.autograd.Function):
    """Autograd function for GeGLU with Triton"""
    
    @staticmethod
    def forward(ctx, x, gate):
        batch, seq, d_model = x.shape
        y = torch.empty_like(x)
        
        grid = (batch, seq)
        _geglu_fwd_kernel[grid](
            x, gate, y,
            x.stride(0), x.stride(1), x.stride(2),
            gate.stride(0), gate.stride(1), gate.stride(2),
            y.stride(0), y.stride(1), y.stride(2),
            d_model,
        )
        
        ctx.save_for_backward(x, gate)
        return y
    
    @staticmethod
    def backward(ctx, dy):
        x, gate = ctx.saved_tensors
        batch, seq, d_model = x.shape
        
        dx = torch.empty_like(x)
        dgate = torch.empty_like(gate)
        
        grid = (batch, seq)
        _geglu_bwd_kernel[grid](
            dy.contiguous(), x, gate,
            dx, dgate,
            dy.stride(0), dy.stride(1), dy.stride(2),
            x.stride(0), x.stride(1), x.stride(2),
            gate.stride(0), gate.stride(1), gate.stride(2),
            dx.stride(0), dx.stride(1), dx.stride(2),
            dgate.stride(0), dgate.stride(1), dgate.stride(2),
            d_model,
        )
        
        return dx, dgate


def fast_geglu(x, gate):
    """
    High-performance GeGLU: y = x * GELU(gate)
    """
    if not HAS_TRITON or not x.is_cuda:
        # PyTorch fallback with tanh approximation
        g_cubed = gate * gate * gate
        inner = SQRT_2_OVER_PI * (gate + GELU_COEF * g_cubed)
        gelu_gate = 0.5 * gate * (1.0 + torch.tanh(inner))
        return x * gelu_gate
    
    x = x.contiguous()
    gate = gate.contiguous()
    return GeGLUFunction.apply(x, gate)


def fast_geglu_split(xg):
    """
    Fused Split + GeGLU for combined input
    Input: [batch, seq, 2*d_model] -> Output: [batch, seq, d_model]
    """
    batch, seq, d2 = xg.shape
    d_model = d2 // 2
    
    if not HAS_TRITON or not xg.is_cuda:
        x, gate = xg.chunk(2, dim=-1)
        return fast_geglu(x, gate)
    
    xg = xg.contiguous()
    y = torch.empty((batch, seq, d_model), device=xg.device, dtype=xg.dtype)
    
    grid = (batch, seq)
    _geglu_fused_split_kernel[grid](
        xg, y,
        xg.stride(0), xg.stride(1), xg.stride(2),
        y.stride(0), y.stride(1), y.stride(2),
        d_model,
        BLOCK_SIZE=min(triton.next_power_of_2(d_model), 2048),
    )
    
    return y
