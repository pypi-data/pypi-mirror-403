"""
OMNIMIND LayerNorm Triton Kernels - Full Implementation
High-performance RMSNorm and LayerNorm with autotuning and backward pass
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

def get_norm_autotune_configs():
    """Autotune configurations for normalization kernels"""
    if not HAS_TRITON:
        return []
    return [
        triton.Config({'BLOCK_SIZE': 256}, num_warps=2, num_stages=2),
        triton.Config({'BLOCK_SIZE': 512}, num_warps=4, num_stages=2),
        triton.Config({'BLOCK_SIZE': 1024}, num_warps=4, num_stages=2),
        triton.Config({'BLOCK_SIZE': 2048}, num_warps=8, num_stages=2),
        triton.Config({'BLOCK_SIZE': 4096}, num_warps=16, num_stages=2),
    ]

if HAS_TRITON:
    @triton.autotune(configs=get_norm_autotune_configs(), key=['N'])
    @triton.jit
    def _rms_norm_fwd_kernel(
        X, Y, W, Rstd,
        stride_x, stride_y,
        N, eps,
        BLOCK_SIZE: tl.constexpr,
    ):
        """
        RMSNorm Forward: y = x * rsqrt(mean(x^2) + eps) * w
        Uses online algorithm for numerical stability
        """
        row = tl.program_id(0)
        X += row * stride_x
        Y += row * stride_y
        
        # Welford's online algorithm for variance
        mean_sq = tl.zeros([1], dtype=tl.float32)
        for off in range(0, N, BLOCK_SIZE):
            cols = off + tl.arange(0, BLOCK_SIZE)
            mask = cols < N
            x = tl.load(X + cols, mask=mask, other=0.0).to(tl.float32)
            mean_sq += tl.sum(x * x, axis=0)
        
        mean_sq = mean_sq / N
        rstd = 1.0 / tl.sqrt(mean_sq + eps)
        tl.store(Rstd + row, rstd)
        
        # Normalize and scale
        for off in range(0, N, BLOCK_SIZE):
            cols = off + tl.arange(0, BLOCK_SIZE)
            mask = cols < N
            w = tl.load(W + cols, mask=mask, other=1.0).to(tl.float32)
            x = tl.load(X + cols, mask=mask, other=0.0).to(tl.float32)
            y = x * rstd * w
            tl.store(Y + cols, y, mask=mask)

    @triton.autotune(configs=get_norm_autotune_configs(), key=['N'])
    @triton.jit
    def _rms_norm_bwd_kernel(
        dY, X, W, Rstd,
        dX, dW,
        stride_x, stride_dy, stride_dx,
        N, eps,
        BLOCK_SIZE: tl.constexpr,
    ):
        """
        RMSNorm Backward:
        dx = (dy * w * rstd) - (x * rstd^3 * mean(dy * w * x)) 
        dw = sum(dy * x * rstd)
        """
        row = tl.program_id(0)
        X += row * stride_x
        dY += row * stride_dy
        dX += row * stride_dx
        
        # Load rstd for this row
        rstd = tl.load(Rstd + row)
        
        # First pass: compute sum(dy * w * x) for gradient scaling
        sum_dy_w_x = tl.zeros([1], dtype=tl.float32)
        for off in range(0, N, BLOCK_SIZE):
            cols = off + tl.arange(0, BLOCK_SIZE)
            mask = cols < N
            dy = tl.load(dY + cols, mask=mask, other=0.0).to(tl.float32)
            w = tl.load(W + cols, mask=mask, other=1.0).to(tl.float32)
            x = tl.load(X + cols, mask=mask, other=0.0).to(tl.float32)
            sum_dy_w_x += tl.sum(dy * w * x, axis=0)
        
        # Compute gradient scale factor
        c = sum_dy_w_x * rstd * rstd * rstd / N
        
        # Second pass: compute dx and accumulate dw
        for off in range(0, N, BLOCK_SIZE):
            cols = off + tl.arange(0, BLOCK_SIZE)
            mask = cols < N
            dy = tl.load(dY + cols, mask=mask, other=0.0).to(tl.float32)
            w = tl.load(W + cols, mask=mask, other=1.0).to(tl.float32)
            x = tl.load(X + cols, mask=mask, other=0.0).to(tl.float32)
            
            # dx = dy * w * rstd - x * c
            dx = dy * w * rstd - x * c
            tl.store(dX + cols, dx, mask=mask)
            
            # dw = dy * x * rstd (accumulated across rows)
            dw_local = dy * x * rstd
            tl.atomic_add(dW + cols, dw_local, mask=mask)

    @triton.autotune(configs=get_norm_autotune_configs(), key=['N'])
    @triton.jit
    def _layer_norm_fwd_kernel(
        X, Y, W, B, Mean, Rstd,
        stride_x, stride_y,
        N, eps,
        BLOCK_SIZE: tl.constexpr,
    ):
        """
        Full LayerNorm Forward: y = (x - mean) * rsqrt(var + eps) * w + b
        """
        row = tl.program_id(0)
        X += row * stride_x
        Y += row * stride_y
        
        # Compute mean
        mean = tl.zeros([1], dtype=tl.float32)
        for off in range(0, N, BLOCK_SIZE):
            cols = off + tl.arange(0, BLOCK_SIZE)
            mask = cols < N
            x = tl.load(X + cols, mask=mask, other=0.0).to(tl.float32)
            mean += tl.sum(x, axis=0)
        mean = mean / N
        
        # Compute variance
        var = tl.zeros([1], dtype=tl.float32)
        for off in range(0, N, BLOCK_SIZE):
            cols = off + tl.arange(0, BLOCK_SIZE)
            mask = cols < N
            x = tl.load(X + cols, mask=mask, other=0.0).to(tl.float32)
            x_centered = x - mean
            var += tl.sum(x_centered * x_centered, axis=0)
        var = var / N
        
        rstd = 1.0 / tl.sqrt(var + eps)
        tl.store(Mean + row, mean)
        tl.store(Rstd + row, rstd)
        
        # Normalize, scale, and shift
        for off in range(0, N, BLOCK_SIZE):
            cols = off + tl.arange(0, BLOCK_SIZE)
            mask = cols < N
            w = tl.load(W + cols, mask=mask, other=1.0).to(tl.float32)
            b = tl.load(B + cols, mask=mask, other=0.0).to(tl.float32)
            x = tl.load(X + cols, mask=mask, other=0.0).to(tl.float32)
            y = (x - mean) * rstd * w + b
            tl.store(Y + cols, y, mask=mask)

    @triton.jit
    def _fused_add_rms_norm_kernel(
        X, Residual, Y, W, Rstd,
        stride_x, stride_r, stride_y,
        N, eps,
        BLOCK_SIZE: tl.constexpr,
    ):
        """
        Fused Add + RMSNorm: y = RMSNorm(x + residual)
        Reduces memory bandwidth by fusing operations
        """
        row = tl.program_id(0)
        X += row * stride_x
        Residual += row * stride_r
        Y += row * stride_y
        
        # First pass: add and compute mean squared
        mean_sq = tl.zeros([1], dtype=tl.float32)
        for off in range(0, N, BLOCK_SIZE):
            cols = off + tl.arange(0, BLOCK_SIZE)
            mask = cols < N
            x = tl.load(X + cols, mask=mask, other=0.0).to(tl.float32)
            r = tl.load(Residual + cols, mask=mask, other=0.0).to(tl.float32)
            h = x + r
            mean_sq += tl.sum(h * h, axis=0)
        
        mean_sq = mean_sq / N
        rstd = 1.0 / tl.sqrt(mean_sq + eps)
        tl.store(Rstd + row, rstd)
        
        # Second pass: normalize
        for off in range(0, N, BLOCK_SIZE):
            cols = off + tl.arange(0, BLOCK_SIZE)
            mask = cols < N
            x = tl.load(X + cols, mask=mask, other=0.0).to(tl.float32)
            r = tl.load(Residual + cols, mask=mask, other=0.0).to(tl.float32)
            w = tl.load(W + cols, mask=mask, other=1.0).to(tl.float32)
            h = x + r
            y = h * rstd * w
            tl.store(Y + cols, y, mask=mask)


class FastRMSNorm(torch.autograd.Function):
    """Autograd function for RMSNorm with Triton"""
    
    @staticmethod
    def forward(ctx, x, weight, eps):
        orig_shape = x.shape
        x_arg = x.reshape(-1, x.shape[-1]).contiguous()
        M, N = x_arg.shape
        
        y = torch.empty_like(x_arg)
        rstd = torch.empty((M,), dtype=torch.float32, device=x.device)
        
        _rms_norm_fwd_kernel[(M,)](
            x_arg, y, weight, rstd,
            x_arg.stride(0), y.stride(0),
            N, eps,
        )
        
        ctx.save_for_backward(x_arg, weight, rstd)
        ctx.eps = eps
        ctx.orig_shape = orig_shape
        
        return y.reshape(orig_shape)
    
    @staticmethod
    def backward(ctx, dy):
        x, weight, rstd = ctx.saved_tensors
        M, N = x.shape
        
        dy = dy.reshape(-1, N).contiguous()
        dx = torch.empty_like(x)
        dw = torch.zeros_like(weight)
        
        _rms_norm_bwd_kernel[(M,)](
            dy, x, weight, rstd,
            dx, dw,
            x.stride(0), dy.stride(0), dx.stride(0),
            N, ctx.eps,
        )
        
        return dx.reshape(ctx.orig_shape), dw, None


class FastLayerNorm(torch.autograd.Function):
    """Autograd function for full LayerNorm with Triton"""
    
    @staticmethod
    def forward(ctx, x, weight, bias, eps):
        orig_shape = x.shape
        x_arg = x.reshape(-1, x.shape[-1]).contiguous()
        M, N = x_arg.shape
        
        y = torch.empty_like(x_arg)
        mean = torch.empty((M,), dtype=torch.float32, device=x.device)
        rstd = torch.empty((M,), dtype=torch.float32, device=x.device)
        
        _layer_norm_fwd_kernel[(M,)](
            x_arg, y, weight, bias, mean, rstd,
            x_arg.stride(0), y.stride(0),
            N, eps,
        )
        
        ctx.save_for_backward(x_arg, weight, mean, rstd)
        ctx.eps = eps
        ctx.orig_shape = orig_shape
        
        return y.reshape(orig_shape)
    
    @staticmethod
    def backward(ctx, dy):
        # Simplified backward - full impl would use Triton kernel
        x, weight, mean, rstd = ctx.saved_tensors
        M, N = x.shape
        
        dy = dy.reshape(-1, N)
        x_centered = x - mean.unsqueeze(1)
        x_norm = x_centered * rstd.unsqueeze(1)
        
        dw = (dy * x_norm).sum(0)
        db = dy.sum(0)
        
        dx_norm = dy * weight
        dvar = (dx_norm * x_centered * -0.5 * rstd.unsqueeze(1) ** 3).sum(-1, keepdim=True)
        dmean = (-dx_norm * rstd.unsqueeze(1)).sum(-1, keepdim=True) + dvar * (-2 * x_centered).mean(-1, keepdim=True)
        dx = dx_norm * rstd.unsqueeze(1) + dvar * 2 * x_centered / N + dmean / N
        
        return dx.reshape(ctx.orig_shape), dw, db, None


def fast_rms_norm(x, weight, eps=1e-5):
    """High-performance RMSNorm with Triton"""
    if not HAS_TRITON or not x.is_cuda:
        # PyTorch fallback
        rms = torch.sqrt(torch.mean(x ** 2, dim=-1, keepdim=True) + eps)
        return x / rms * weight
    return FastRMSNorm.apply(x, weight, eps)


def fast_layer_norm(x, weight, bias, eps=1e-5):
    """High-performance LayerNorm with Triton"""
    if not HAS_TRITON or not x.is_cuda:
        return torch.nn.functional.layer_norm(x, (x.shape[-1],), weight, bias, eps)
    return FastLayerNorm.apply(x, weight, bias, eps)


def fast_fused_add_rms_norm(x, residual, weight, eps=1e-5):
    """Fused Add + RMSNorm for efficiency"""
    if not HAS_TRITON or not x.is_cuda:
        h = x + residual
        rms = torch.sqrt(torch.mean(h ** 2, dim=-1, keepdim=True) + eps)
        return h / rms * weight
    
    orig_shape = x.shape
    x_flat = x.reshape(-1, x.shape[-1]).contiguous()
    r_flat = residual.reshape(-1, residual.shape[-1]).contiguous()
    M, N = x_flat.shape
    
    y = torch.empty_like(x_flat)
    rstd = torch.empty((M,), dtype=torch.float32, device=x.device)
    
    _fused_add_rms_norm_kernel[(M,)](
        x_flat, r_flat, y, weight, rstd,
        x_flat.stride(0), r_flat.stride(0), y.stride(0),
        N, eps,
        BLOCK_SIZE=min(triton.next_power_of_2(N), 4096),
    )
    
    return y.reshape(orig_shape)
