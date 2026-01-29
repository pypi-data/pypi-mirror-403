"""
OMNIMIND SwiGLU Triton Kernels - Full Implementation
High-performance SwiGLU with autotuning, backward pass, and fused variants
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

def get_activation_autotune_configs():
    """Autotune configurations for activation kernels"""
    if not HAS_TRITON:
        return []
    return [
        triton.Config({'BLOCK_SIZE': 512}, num_warps=4),
        triton.Config({'BLOCK_SIZE': 1024}, num_warps=4),
        triton.Config({'BLOCK_SIZE': 2048}, num_warps=8),
        triton.Config({'BLOCK_SIZE': 4096}, num_warps=8),
        triton.Config({'BLOCK_SIZE': 8192}, num_warps=16),
    ]

if HAS_TRITON:
    @triton.autotune(configs=get_activation_autotune_configs(), key=['n_elements'])
    @triton.jit
    def _swiglu_fwd_kernel(
        X, Gate, Y,
        n_elements,
        BLOCK_SIZE: tl.constexpr,
    ):
        """
        SwiGLU Forward: y = x * SiLU(gate) = x * gate * sigmoid(gate)
        """
        pid = tl.program_id(0)
        offsets = pid * BLOCK_SIZE + tl.arange(0, BLOCK_SIZE)
        mask = offsets < n_elements
        
        x = tl.load(X + offsets, mask=mask, other=0.0)
        g = tl.load(Gate + offsets, mask=mask, other=0.0)
        
        # SiLU(g) = g * sigmoid(g) = g / (1 + exp(-g))
        sigmoid_g = tl.sigmoid(g)
        silu_g = g * sigmoid_g
        y = x * silu_g
        
        tl.store(Y + offsets, y, mask=mask)

    @triton.autotune(configs=get_activation_autotune_configs(), key=['n_elements'])
    @triton.jit
    def _swiglu_bwd_kernel(
        dY, X, Gate,
        dX, dGate,
        n_elements,
        BLOCK_SIZE: tl.constexpr,
    ):
        """
        SwiGLU Backward:
        dx = dy * silu(gate)
        dgate = dy * x * (sigmoid(gate) + gate * sigmoid(gate) * (1 - sigmoid(gate)))
             = dy * x * sigmoid(gate) * (1 + gate * (1 - sigmoid(gate)))
        """
        pid = tl.program_id(0)
        offsets = pid * BLOCK_SIZE + tl.arange(0, BLOCK_SIZE)
        mask = offsets < n_elements
        
        dy = tl.load(dY + offsets, mask=mask, other=0.0)
        x = tl.load(X + offsets, mask=mask, other=0.0)
        g = tl.load(Gate + offsets, mask=mask, other=0.0)
        
        sigmoid_g = tl.sigmoid(g)
        silu_g = g * sigmoid_g
        
        # dx = dy * silu(gate)
        dx = dy * silu_g
        
        # dgate = dy * x * dsilu/dgate
        # dsilu/dgate = sigmoid(g) + g * sigmoid(g) * (1 - sigmoid(g))
        #             = sigmoid(g) * (1 + g * (1 - sigmoid(g)))
        dsilu_dg = sigmoid_g * (1.0 + g * (1.0 - sigmoid_g))
        dg = dy * x * dsilu_dg
        
        tl.store(dX + offsets, dx, mask=mask)
        tl.store(dGate + offsets, dg, mask=mask)

    @triton.autotune(configs=get_activation_autotune_configs(), key=['n_elements'])
    @triton.jit
    def _fused_swiglu_matmul_kernel(
        X, W_up, W_gate, Y,
        M, N, K,
        stride_xm, stride_xk,
        stride_wu_k, stride_wu_n,
        stride_wg_k, stride_wg_n,
        stride_ym, stride_yn,
        n_elements,
        BLOCK_SIZE_M: tl.constexpr,
        BLOCK_SIZE_N: tl.constexpr,
        BLOCK_SIZE_K: tl.constexpr,
        BLOCK_SIZE: tl.constexpr,
    ):
        """
        Fused MatMul + SwiGLU: Y = (X @ W_up) * SiLU(X @ W_gate)
        Reduces memory bandwidth by computing both projections and activation together
        """
        pid_m = tl.program_id(0)
        pid_n = tl.program_id(1)
        
        offs_m = pid_m * BLOCK_SIZE_M + tl.arange(0, BLOCK_SIZE_M)
        offs_n = pid_n * BLOCK_SIZE_N + tl.arange(0, BLOCK_SIZE_N)
        offs_k = tl.arange(0, BLOCK_SIZE_K)
        
        # Initialize accumulators
        acc_up = tl.zeros((BLOCK_SIZE_M, BLOCK_SIZE_N), dtype=tl.float32)
        acc_gate = tl.zeros((BLOCK_SIZE_M, BLOCK_SIZE_N), dtype=tl.float32)
        
        # Main GEMM loop
        for k in range(0, K, BLOCK_SIZE_K):
            k_offs = k + offs_k
            
            # Load X tile
            x_ptrs = X + offs_m[:, None] * stride_xm + k_offs[None, :] * stride_xk
            x_mask = (offs_m[:, None] < M) & (k_offs[None, :] < K)
            x = tl.load(x_ptrs, mask=x_mask, other=0.0)
            
            # Load W_up tile
            wu_ptrs = W_up + k_offs[:, None] * stride_wu_k + offs_n[None, :] * stride_wu_n
            wu_mask = (k_offs[:, None] < K) & (offs_n[None, :] < N)
            w_up = tl.load(wu_ptrs, mask=wu_mask, other=0.0)
            
            # Load W_gate tile
            wg_ptrs = W_gate + k_offs[:, None] * stride_wg_k + offs_n[None, :] * stride_wg_n
            wg_mask = (k_offs[:, None] < K) & (offs_n[None, :] < N)
            w_gate = tl.load(wg_ptrs, mask=wg_mask, other=0.0)
            
            # Accumulate
            acc_up += tl.dot(x, w_up)
            acc_gate += tl.dot(x, w_gate)
        
        # Apply SwiGLU activation
        sigmoid_gate = tl.sigmoid(acc_gate)
        silu_gate = acc_gate * sigmoid_gate
        y = acc_up * silu_gate
        
        # Store result
        y_ptrs = Y + offs_m[:, None] * stride_ym + offs_n[None, :] * stride_yn
        y_mask = (offs_m[:, None] < M) & (offs_n[None, :] < N)
        tl.store(y_ptrs, y, mask=y_mask)


class SwiGLUFunction(torch.autograd.Function):
    """Autograd function for SwiGLU with Triton"""
    
    @staticmethod
    def forward(ctx, x, gate):
        n_elements = x.numel()
        y = torch.empty_like(x)
        
        grid = lambda meta: (triton.cdiv(n_elements, meta['BLOCK_SIZE']),)
        _swiglu_fwd_kernel[grid](x, gate, y, n_elements)
        
        ctx.save_for_backward(x, gate)
        return y
    
    @staticmethod
    def backward(ctx, dy):
        x, gate = ctx.saved_tensors
        n_elements = x.numel()
        
        dx = torch.empty_like(x)
        dgate = torch.empty_like(gate)
        
        grid = lambda meta: (triton.cdiv(n_elements, meta['BLOCK_SIZE']),)
        _swiglu_bwd_kernel[grid](dy.contiguous(), x, gate, dx, dgate, n_elements)
        
        return dx, dgate


def fast_swiglu(x, gate):
    """
    High-performance SwiGLU: y = x * SiLU(gate)
    """
    if not HAS_TRITON or not x.is_cuda:
        # PyTorch fallback
        return x * torch.nn.functional.silu(gate)
    
    x = x.contiguous()
    gate = gate.contiguous()
    return SwiGLUFunction.apply(x, gate)


def fast_fused_swiglu_linear(x, w_up, w_gate):
    """
    Fused Linear + SwiGLU: y = (x @ w_up) * SiLU(x @ w_gate)
    """
    if not HAS_TRITON or not x.is_cuda:
        up = x @ w_up.t()
        gate = x @ w_gate.t()
        return up * torch.nn.functional.silu(gate)
    
    # Reshape for matmul
    orig_shape = x.shape[:-1]
    x_2d = x.reshape(-1, x.shape[-1]).contiguous()
    M, K = x_2d.shape
    N = w_up.shape[0]
    
    y = torch.empty((M, N), device=x.device, dtype=x.dtype)
    
    BLOCK_M, BLOCK_N, BLOCK_K = 64, 64, 32
    grid = (triton.cdiv(M, BLOCK_M), triton.cdiv(N, BLOCK_N))
    
    _fused_swiglu_matmul_kernel[grid](
        x_2d, w_up.t().contiguous(), w_gate.t().contiguous(), y,
        M, N, K,
        x_2d.stride(0), x_2d.stride(1),
        K, 1,  # w_up strides after transpose
        K, 1,  # w_gate strides after transpose
        y.stride(0), y.stride(1),
        M * N,
        BLOCK_SIZE_M=BLOCK_M, BLOCK_SIZE_N=BLOCK_N, BLOCK_SIZE_K=BLOCK_K,
        BLOCK_SIZE=1024,
    )
    
    return y.reshape(*orig_shape, N)
