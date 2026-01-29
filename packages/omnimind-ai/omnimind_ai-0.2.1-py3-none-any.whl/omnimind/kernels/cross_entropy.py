"""
OMNIMIND Cross-Entropy Triton Kernels - Full Implementation
High-performance fused cross-entropy with online softmax and backward pass
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

def get_ce_autotune_configs():
    """Autotune configurations for cross-entropy kernels"""
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
    @triton.autotune(configs=get_ce_autotune_configs(), key=['n_vocab'])
    @triton.jit
    def _cross_entropy_fwd_kernel(
        Logits, Labels, Loss, MaxLogit, SumExp,
        stride_logits_b, stride_logits_v,
        n_vocab,
        BLOCK_SIZE: tl.constexpr,
    ):
        """
        Fused Cross-Entropy Forward with Online Softmax
        Uses numerically stable computation: loss = log(sum_exp) - logit[label] + max
        """
        pid = tl.program_id(0)
        
        # Load label
        label = tl.load(Labels + pid)
        
        # Handle ignore index (-100)
        if label == -100:
            tl.store(Loss + pid, 0.0)
            tl.store(MaxLogit + pid, 0.0)
            tl.store(SumExp + pid, 1.0)
            return
        
        logits_ptr = Logits + pid * stride_logits_b
        
        # Online softmax: single pass for max and sum_exp
        # Using Welford-style online algorithm
        max_val = float('-inf')
        sum_exp = 0.0
        
        for off in range(0, n_vocab, BLOCK_SIZE):
            cols = off + tl.arange(0, BLOCK_SIZE)
            mask = cols < n_vocab
            val = tl.load(logits_ptr + cols * stride_logits_v, mask=mask, other=float('-inf'))
            
            # Update max and rescale sum_exp
            new_max = tl.maximum(max_val, tl.max(val, axis=0))
            sum_exp = sum_exp * tl.exp(max_val - new_max) + tl.sum(tl.exp(val - new_max), axis=0)
            max_val = new_max
        
        # Store for backward
        tl.store(MaxLogit + pid, max_val)
        tl.store(SumExp + pid, sum_exp)
        
        # Compute loss: -log(softmax[label]) = log(sum_exp) - (logit[label] - max)
        label_logit = tl.load(logits_ptr + label * stride_logits_v)
        loss = tl.log(sum_exp) - (label_logit - max_val)
        
        tl.store(Loss + pid, loss)

    @triton.autotune(configs=get_ce_autotune_configs(), key=['n_vocab'])
    @triton.jit
    def _cross_entropy_bwd_kernel(
        Logits, Labels, dLogits,
        MaxLogit, SumExp,
        grad_scale,
        stride_logits_b, stride_logits_v,
        stride_dlogits_b, stride_dlogits_v,
        n_vocab,
        BLOCK_SIZE: tl.constexpr,
    ):
        """
        Cross-Entropy Backward: dlogits = softmax(logits) - one_hot(label)
        Fused computation to avoid materializing softmax
        """
        pid = tl.program_id(0)
        
        label = tl.load(Labels + pid)
        
        # Handle ignore index
        if label == -100:
            for off in range(0, n_vocab, BLOCK_SIZE):
                cols = off + tl.arange(0, BLOCK_SIZE)
                mask = cols < n_vocab
                tl.store(dLogits + pid * stride_dlogits_b + cols * stride_dlogits_v, 
                        tl.zeros([BLOCK_SIZE], dtype=tl.float32), mask=mask)
            return
        
        logits_ptr = Logits + pid * stride_logits_b
        dlogits_ptr = dLogits + pid * stride_dlogits_b
        
        max_val = tl.load(MaxLogit + pid)
        sum_exp = tl.load(SumExp + pid)
        
        for off in range(0, n_vocab, BLOCK_SIZE):
            cols = off + tl.arange(0, BLOCK_SIZE)
            mask = cols < n_vocab
            
            # Load logits
            val = tl.load(logits_ptr + cols * stride_logits_v, mask=mask, other=0.0)
            
            # Compute softmax
            softmax = tl.exp(val - max_val) / sum_exp
            
            # Subtract 1 for the correct label
            is_label = (cols == label)
            grad = (softmax - is_label.to(tl.float32)) * grad_scale
            
            tl.store(dlogits_ptr + cols * stride_dlogits_v, grad, mask=mask)

    @triton.autotune(configs=get_ce_autotune_configs(), key=['n_vocab'])
    @triton.jit
    def _cross_entropy_fused_kernel(
        Logits, Labels, Loss,
        stride_logits_b, stride_logits_v,
        n_vocab, ignore_index,
        BLOCK_SIZE: tl.constexpr,
    ):
        """
        Fully fused cross-entropy without saving intermediates
        Most memory efficient for inference
        """
        pid = tl.program_id(0)
        label = tl.load(Labels + pid)
        
        if label == ignore_index:
            tl.store(Loss + pid, 0.0)
            return
        
        logits_ptr = Logits + pid * stride_logits_b
        
        # Two-pass for numerical stability
        # Pass 1: Find max
        max_val = float('-inf')
        for off in range(0, n_vocab, BLOCK_SIZE):
            cols = off + tl.arange(0, BLOCK_SIZE)
            mask = cols < n_vocab
            val = tl.load(logits_ptr + cols * stride_logits_v, mask=mask, other=float('-inf'))
            max_val = tl.maximum(max_val, tl.max(val, axis=0))
        
        # Pass 2: Compute sum_exp and get label logit
        sum_exp = 0.0
        for off in range(0, n_vocab, BLOCK_SIZE):
            cols = off + tl.arange(0, BLOCK_SIZE)
            mask = cols < n_vocab
            val = tl.load(logits_ptr + cols * stride_logits_v, mask=mask, other=float('-inf'))
            sum_exp += tl.sum(tl.exp(val - max_val), axis=0)
        
        label_logit = tl.load(logits_ptr + label * stride_logits_v)
        loss = tl.log(sum_exp) - (label_logit - max_val)
        
        tl.store(Loss + pid, loss)

    @triton.jit  
    def _label_smoothing_ce_kernel(
        Logits, Labels, Loss,
        stride_logits_b, stride_logits_v,
        n_vocab, smoothing, ignore_index,
        BLOCK_SIZE: tl.constexpr,
    ):
        """
        Cross-entropy with label smoothing
        loss = (1 - smoothing) * CE(label) + smoothing * mean(CE(all))
        """
        pid = tl.program_id(0)
        label = tl.load(Labels + pid)
        
        if label == ignore_index:
            tl.store(Loss + pid, 0.0)
            return
        
        logits_ptr = Logits + pid * stride_logits_b
        
        # Find max for stability
        max_val = float('-inf')
        for off in range(0, n_vocab, BLOCK_SIZE):
            cols = off + tl.arange(0, BLOCK_SIZE)
            mask = cols < n_vocab
            val = tl.load(logits_ptr + cols * stride_logits_v, mask=mask, other=float('-inf'))
            max_val = tl.maximum(max_val, tl.max(val, axis=0))
        
        # Compute log_sum_exp and sum of logits
        sum_exp = 0.0
        sum_logits = 0.0
        for off in range(0, n_vocab, BLOCK_SIZE):
            cols = off + tl.arange(0, BLOCK_SIZE)
            mask = cols < n_vocab
            val = tl.load(logits_ptr + cols * stride_logits_v, mask=mask, other=0.0)
            sum_exp += tl.sum(tl.exp(val - max_val), axis=0)
            sum_logits += tl.sum(val, axis=0)
        
        log_sum_exp = tl.log(sum_exp) + max_val
        label_logit = tl.load(logits_ptr + label * stride_logits_v)
        
        # Hard label loss
        hard_loss = log_sum_exp - label_logit
        
        # Soft label loss (uniform distribution)
        soft_loss = log_sum_exp - sum_logits / n_vocab
        
        # Combined loss
        loss = (1.0 - smoothing) * hard_loss + smoothing * soft_loss
        
        tl.store(Loss + pid, loss)


class CrossEntropyFunction(torch.autograd.Function):
    """Autograd function for cross-entropy with Triton"""
    
    @staticmethod
    def forward(ctx, logits, labels, ignore_index=-100):
        n_rows, n_vocab = logits.shape
        
        losses = torch.empty(n_rows, dtype=torch.float32, device=logits.device)
        max_logits = torch.empty(n_rows, dtype=torch.float32, device=logits.device)
        sum_exps = torch.empty(n_rows, dtype=torch.float32, device=logits.device)
        
        grid = (n_rows,)
        _cross_entropy_fwd_kernel[grid](
            logits, labels, losses, max_logits, sum_exps,
            logits.stride(0), logits.stride(1),
            n_vocab,
        )
        
        # Count valid labels for mean
        valid_count = (labels != ignore_index).sum()
        
        ctx.save_for_backward(logits, labels, max_logits, sum_exps)
        ctx.n_vocab = n_vocab
        ctx.valid_count = valid_count
        
        return losses.sum() / valid_count if valid_count > 0 else losses.sum()
    
    @staticmethod
    def backward(ctx, grad_output):
        logits, labels, max_logits, sum_exps = ctx.saved_tensors
        n_rows, n_vocab = logits.shape
        
        dlogits = torch.empty_like(logits)
        grad_scale = grad_output / ctx.valid_count if ctx.valid_count > 0 else grad_output
        
        grid = (n_rows,)
        _cross_entropy_bwd_kernel[grid](
            logits, labels, dlogits,
            max_logits, sum_exps,
            grad_scale.item(),
            logits.stride(0), logits.stride(1),
            dlogits.stride(0), dlogits.stride(1),
            n_vocab,
        )
        
        return dlogits, None, None


def fast_cross_entropy_loss(logits, labels, ignore_index=-100, label_smoothing=0.0):
    """
    High-performance fused cross-entropy loss
    
    Args:
        logits: [batch*seq, vocab] or [batch, seq, vocab]
        labels: [batch*seq] or [batch, seq]
        ignore_index: Label value to ignore (default -100)
        label_smoothing: Label smoothing factor (default 0.0)
    
    Returns:
        Scalar loss value
    """
    # Handle 3D input
    if logits.dim() == 3:
        batch, seq, vocab = logits.shape
        logits = logits.reshape(-1, vocab)
        labels = labels.reshape(-1)
    
    if not HAS_TRITON or not logits.is_cuda:
        return _pytorch_cross_entropy(logits, labels, ignore_index, label_smoothing)
    
    logits = logits.contiguous()
    labels = labels.contiguous()
    
    if label_smoothing > 0:
        return _label_smoothed_ce(logits, labels, label_smoothing, ignore_index)
    
    return CrossEntropyFunction.apply(logits, labels, ignore_index)


def _label_smoothed_ce(logits, labels, smoothing, ignore_index):
    """Label smoothed cross-entropy with Triton"""
    n_rows, n_vocab = logits.shape
    losses = torch.empty(n_rows, dtype=torch.float32, device=logits.device)
    
    grid = (n_rows,)
    _label_smoothing_ce_kernel[grid](
        logits, labels, losses,
        logits.stride(0), logits.stride(1),
        n_vocab, smoothing, ignore_index,
        BLOCK_SIZE=min(triton.next_power_of_2(n_vocab), 4096),
    )
    
    valid_count = (labels != ignore_index).sum()
    return losses.sum() / valid_count if valid_count > 0 else losses.sum()


def _pytorch_cross_entropy(logits, labels, ignore_index, label_smoothing):
    """PyTorch fallback for cross-entropy"""
    return torch.nn.functional.cross_entropy(
        logits, labels, 
        ignore_index=ignore_index,
        label_smoothing=label_smoothing
    )


def fast_cross_entropy_with_logits(logits, labels, ignore_index=-100):
    """
    Memory-efficient cross-entropy for inference (no backward)
    """
    if logits.dim() == 3:
        batch, seq, vocab = logits.shape
        logits = logits.reshape(-1, vocab)
        labels = labels.reshape(-1)
    
    if not HAS_TRITON or not logits.is_cuda:
        return _pytorch_cross_entropy(logits, labels, ignore_index, 0.0)
    
    n_rows, n_vocab = logits.shape
    losses = torch.empty(n_rows, dtype=torch.float32, device=logits.device)
    
    grid = (n_rows,)
    _cross_entropy_fused_kernel[grid](
        logits.contiguous(), labels.contiguous(), losses,
        logits.stride(0), logits.stride(1),
        n_vocab, ignore_index,
    )
    
    valid_count = (labels != ignore_index).sum()
    return losses.sum() / valid_count if valid_count > 0 else losses.sum()
