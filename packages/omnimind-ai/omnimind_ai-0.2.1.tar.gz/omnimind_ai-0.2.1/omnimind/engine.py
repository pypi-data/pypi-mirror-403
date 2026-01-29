"""
Native MoE-SSM Integration Layer

This module provides a unified Python interface to the native Rust modules
with automatic fallbacks to pure Python implementations when native modules
are not available.

Usage:
    from omnimind.native.integration import NativeMoESSM
    
    engine = NativeMoESSM(config)
    output = engine.forward(input_ids, position)
"""

import numpy as np
from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass, field
import time

# Try to import torch (needed for Triton kernels)
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    torch = None

# Try to import native modules (Triton / Rust)
try:
    # 1. Try Triton Kernels (Pro Implementation)
    from omnimind.kernels import HAS_TRITON
    if HAS_TRITON and HAS_TORCH:
        import omnimind.kernels as _native
        HAS_NATIVE = True
        NATIVE_MODULES = ['ssm', 'layernorm', 'swiglu']
    else:
        # 2. Try Legacy Rust Native
        import omnimind_native as _native
        HAS_NATIVE = True
        NATIVE_MODULES = getattr(_native, 'MODULES', [])
except ImportError:
    HAS_NATIVE = False
    NATIVE_MODULES = []
    _native = None


@dataclass
class MoESSMConfig:
    """Configuration for MoE-SSM model."""
    dim: int = 4096
    num_layers: int = 32
    num_experts: int = 64
    top_k: int = 2
    state_dim: int = 16
    conv_kernel: int = 4
    expand_factor: int = 2
    dt_rank: int = 0  # 0 = auto (dim // 16)
    group_size: int = 128  # Quantization group size
    vocab_size: int = 32000
    
    def __post_init__(self):
        if self.dt_rank == 0:
            self.dt_rank = self.dim // 16
        self.inner_dim = self.dim * self.expand_factor
        self.expert_dim = self.dim * 4 // self.num_experts


@dataclass
class InferenceStats:
    """Performance statistics for inference."""
    total_tokens: int = 0
    total_time_ms: float = 0.0
    prefill_time_ms: float = 0.0
    decode_time_ms: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    
    @property
    def tokens_per_second(self) -> float:
        if self.total_time_ms == 0:
            return 0.0
        return self.total_tokens / (self.total_time_ms / 1000.0)
    
    def report(self) -> str:
        return (
            f"Tokens: {self.total_tokens} | "
            f"Speed: {self.tokens_per_second:.1f} tok/s | "
            f"Prefill: {self.prefill_time_ms:.1f}ms | "
            f"Decode: {self.decode_time_ms:.1f}ms"
        )


class SSMState:
    """SSM hidden state with constant memory footprint."""
    
    def __init__(self, batch_size: int, num_layers: int, dim: int, state_dim: int, conv_kernel: int = 4):
        self.batch_size = batch_size
        self.num_layers = num_layers
        self.dim = dim
        self.state_dim = state_dim
        self.conv_kernel = conv_kernel
        
        # Hidden state: [batch, layers, dim, state_dim]
        # This is O(1) in sequence length!
        self.h = np.zeros((batch_size, num_layers, dim, state_dim), dtype=np.float32)
        
        # Conv state: [batch, layers, dim, conv_kernel]
        self.conv_state = np.zeros((batch_size, num_layers, dim, conv_kernel), dtype=np.float32)
    
    def reset(self):
        """Reset state to zeros."""
        self.h.fill(0)
        self.conv_state.fill(0)
    
    def get_layer(self, layer_idx: int) -> Tuple[np.ndarray, np.ndarray]:
        """Get state for a specific layer."""
        return self.h[:, layer_idx], self.conv_state[:, layer_idx]
    
    def set_layer(self, layer_idx: int, h: np.ndarray, conv: np.ndarray):
        """Set state for a specific layer."""
        self.h[:, layer_idx] = h
        self.conv_state[:, layer_idx] = conv
    
    def memory_bytes(self) -> int:
        """Return memory usage in bytes."""
        return self.h.nbytes + self.conv_state.nbytes


class NativeMoESSM:
    """
    Native MoE-SSM inference engine with automatic fallbacks.
    
    This class provides the main interface for running MoE-SSM inference.
    It automatically uses native Rust implementations when available,
    falling back to pure Python when native modules are not compiled.
    """
    
    def __init__(self, config: MoESSMConfig):
        self.config = config
        self.state: Optional[SSMState] = None
        self.stats = InferenceStats()
        self.weights: Dict[str, np.ndarray] = {}
        self.weight_cache: Dict[str, np.ndarray] = {}
        self._use_native = HAS_NATIVE and 'moe_ssm' in NATIVE_MODULES
        
        # Check which native modules are available
        self.has_native_ssm = HAS_NATIVE and 'ssm' in NATIVE_MODULES
        self.has_native_quant = HAS_NATIVE and 'quantization' in NATIVE_MODULES
        self.has_native_router = HAS_NATIVE and 'router' in NATIVE_MODULES
        self.has_native_fused = HAS_NATIVE and 'fused_ops' in NATIVE_MODULES
    
    def init_state(self, batch_size: int = 1):
        """Initialize SSM state."""
        self.state = SSMState(
            batch_size=batch_size,
            num_layers=self.config.num_layers,
            dim=self.config.dim,
            state_dim=self.config.state_dim,
            conv_kernel=self.config.conv_kernel,
        )
    
    def load_weights(self, weights: Dict[str, np.ndarray]):
        """Load model weights."""
        self.weights = weights
        self.weight_cache.clear()
    
    def _rmsnorm(self, x: np.ndarray, weight: np.ndarray, eps: float = 1e-5) -> np.ndarray:
        """RMSNorm with optional native acceleration."""
        if HAS_NATIVE and HAS_TRITON:
             # Convert to tensor for Triton
             x_t = torch.from_numpy(x).cuda()
             w_t = torch.from_numpy(weight).cuda()
             return _native.fast_rms_norm(x_t, w_t, eps).cpu().numpy()
        
        if self.has_native_fused:
            return _native.rmsnorm_fused(x, weight, eps)
        
        # Python fallback
        rms = np.sqrt(np.mean(x ** 2, axis=-1, keepdims=True) + eps)
        return (x / rms) * weight
    
    def _swiglu(self, x: np.ndarray, gate: np.ndarray) -> np.ndarray:
        """SwiGLU activation with optional native acceleration."""
        if HAS_NATIVE and HAS_TRITON:
             x_t = torch.from_numpy(x).cuda()
             g_t = torch.from_numpy(gate).cuda()
             return _native.fast_swiglu(x_t, g_t).cpu().numpy()

        if self.has_native_fused:
            return _native.swiglu_fused(x, gate)
        
        # Python fallback
        return x * (gate / (1.0 + np.exp(-gate)))  # x * silu(gate)
    
    def _softmax(self, x: np.ndarray, axis: int = -1) -> np.ndarray:
        """Softmax with optional native acceleration."""
        # Triton softmax included in standard torch usually sufficient, or implement custom
        if self.has_native_fused:
            return _native.softmax(x)
        
        # Python fallback
        exp_x = np.exp(x - np.max(x, axis=axis, keepdims=True))
        return exp_x / np.sum(exp_x, axis=axis, keepdims=True)
    
    def _topk_experts(self, router_logits: np.ndarray, k: int) -> Tuple[np.ndarray, np.ndarray]:
        """Select top-k experts with optional native acceleration."""
        if self.has_native_router:
            return _native.softmax_topk(router_logits, k)
        
        # Python fallback
        probs = self._softmax(router_logits)
        indices = np.argpartition(-probs, k, axis=-1)[..., :k]
        weights = np.take_along_axis(probs, indices, axis=-1)
        # Sort by weight descending
        sort_idx = np.argsort(-weights, axis=-1)
        indices = np.take_along_axis(indices, sort_idx, axis=-1)
        weights = np.take_along_axis(weights, sort_idx, axis=-1)
        # Renormalize
        weights = weights / np.sum(weights, axis=-1, keepdims=True)
        return indices, weights
    
    def _ssm_step(
        self,
        x: np.ndarray,
        h: np.ndarray,
        A: np.ndarray,
        B: np.ndarray,
        C: np.ndarray,
        D: np.ndarray,
        dt: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Single SSM step with optional native acceleration."""
        if self.has_native_ssm:
            return _native.ssm_step(x, h, A, B, C, D, dt)
        
        # Python fallback - discretize and apply
        # Discretize: A_bar = exp(dt * A)
        dt_A = dt[..., None] * A
        A_bar = np.exp(dt_A)
        
        # B_bar = (exp(dt * A) - 1) / A * B ≈ dt * B for small dt
        B_bar = dt[..., None] * B
        
        # State update: h' = A_bar * h + B_bar * x
        h_new = A_bar * h + B_bar * x[..., None]
        
        # Output: y = C @ h + D * x
        y = np.sum(C * h_new, axis=-1) + D * x
        
        return y, h_new
    
    def _dequant_matmul(
        self,
        x: np.ndarray,
        packed_weight: np.ndarray,
        scales: np.ndarray,
        zeros: Optional[np.ndarray] = None,
        group_size: int = 128,
    ) -> np.ndarray:
        """Dequantize and matmul with optional native acceleration."""
        if self.has_native_quant:
            if zeros is not None:
                return _native.dequant_matmul_int4(x, packed_weight, scales, zeros, group_size)
            else:
                return _native.dequant_matmul_nf4(x, packed_weight, scales, group_size)
        
        # Python fallback - simple dequantization
        # Unpack INT4 weights
        out_features = packed_weight.shape[0]
        in_features = packed_weight.shape[1] * 2
        
        low = packed_weight & 0x0F
        high = (packed_weight >> 4) & 0x0F
        weight = np.empty((out_features, in_features), dtype=np.float32)
        weight[:, 0::2] = low.astype(np.float32)
        weight[:, 1::2] = high.astype(np.float32)
        
        # Dequantize with scales
        num_groups = in_features // group_size
        weight = weight.reshape(out_features, num_groups, group_size)
        weight = (weight - 8) * scales[:, :, None]  # Assuming symmetric around 8
        weight = weight.reshape(out_features, in_features)
        
        return x @ weight.T
    
    def forward_layer(
        self,
        layer_idx: int,
        hidden: np.ndarray,
        position: int,
    ) -> np.ndarray:
        """Forward pass for a single layer."""
        batch_size, dim = hidden.shape
        
        # Get layer weights
        prefix = f"layers.{layer_idx}"
        
        # 1. Input norm
        norm_weight = self.weights.get(f"{prefix}.norm.weight", np.ones(dim))
        normed = self._rmsnorm(hidden, norm_weight)
        
        # 2. SSM block
        h_state, conv_state = self.state.get_layer(layer_idx)
        
        # Project to inner dim
        in_proj = self.weights.get(f"{prefix}.ssm.in_proj.weight")
        in_proj_scales = self.weights.get(f"{prefix}.ssm.in_proj.scales")
        
        if in_proj is not None and in_proj_scales is not None:
            x = self._dequant_matmul(normed, in_proj, in_proj_scales)
        else:
            # Use full precision weight
            in_proj_full = self.weights.get(f"{prefix}.ssm.in_proj.weight_full", np.eye(dim))
            x = normed @ in_proj_full.T
        
        # SSM parameters
        A = self.weights.get(f"{prefix}.ssm.A", -np.ones((dim, self.config.state_dim)))
        D = self.weights.get(f"{prefix}.ssm.D", np.ones(dim))
        
        # Compute B, C from x (selective mechanism)
        x_bc = x[:, :2*self.config.state_dim]
        B = x_bc[:, :self.config.state_dim]
        C = x_bc[:, self.config.state_dim:]
        
        # dt projection
        dt_proj = self.weights.get(f"{prefix}.ssm.dt_proj.weight")
        if dt_proj is not None:
            dt = x @ dt_proj.T
            dt = np.log(1 + np.exp(dt))  # softplus
        else:
            dt = np.ones_like(x[:, :dim]) * 0.01
        
        # SSM step
        y, h_new = self._ssm_step(x[:, :dim], h_state[:batch_size], A, B, C, D, dt)
        
        # Update state
        self.state.h[:batch_size, layer_idx] = h_new
        
        # Output projection + residual
        out_proj = self.weights.get(f"{prefix}.ssm.out_proj.weight")
        out_proj_scales = self.weights.get(f"{prefix}.ssm.out_proj.scales")
        
        if out_proj is not None and out_proj_scales is not None:
            ssm_out = self._dequant_matmul(y, out_proj, out_proj_scales)
        else:
            out_proj_full = self.weights.get(f"{prefix}.ssm.out_proj.weight_full", np.eye(dim))
            ssm_out = y @ out_proj_full.T
        
        hidden = hidden + ssm_out
        
        # 3. MoE block
        moe_norm_weight = self.weights.get(f"{prefix}.moe_norm.weight", np.ones(dim))
        moe_input = self._rmsnorm(hidden, moe_norm_weight)
        
        # Router
        router_weight = self.weights.get(f"{prefix}.router.weight")
        if router_weight is not None:
            router_logits = moe_input @ router_weight.T
        else:
            router_logits = np.zeros((batch_size, self.config.num_experts))
        
        # Top-k expert selection
        expert_indices, expert_weights = self._topk_experts(router_logits, self.config.top_k)
        
        # Sparse expert computation
        moe_output = np.zeros_like(moe_input)
        for k in range(self.config.top_k):
            for b in range(batch_size):
                expert_idx = expert_indices[b, k]
                weight = expert_weights[b, k]
                
                # Get expert weights
                gate_proj = self.weights.get(f"{prefix}.experts.{expert_idx}.gate_proj.weight")
                up_proj = self.weights.get(f"{prefix}.experts.{expert_idx}.up_proj.weight")
                down_proj = self.weights.get(f"{prefix}.experts.{expert_idx}.down_proj.weight")
                
                if gate_proj is not None and up_proj is not None and down_proj is not None:
                    gate = moe_input[b:b+1] @ gate_proj.T
                    up = moe_input[b:b+1] @ up_proj.T
                    expert_out = self._swiglu(up, gate)
                    expert_out = expert_out @ down_proj.T
                    moe_output[b] += weight * expert_out[0]
        
        hidden = hidden + moe_output
        
        return hidden
    
    def forward(
        self,
        input_ids: np.ndarray,
        position: int = 0,
    ) -> np.ndarray:
        """
        Full forward pass through all layers.
        
        Args:
            input_ids: Token IDs [batch, seq_len] or [batch]
            position: Starting position for positional encoding
            
        Returns:
            logits: Output logits [batch, vocab_size]
        """
        start_time = time.perf_counter()
        
        if self.state is None:
            batch_size = input_ids.shape[0] if input_ids.ndim > 1 else 1
            self.init_state(batch_size)
        
        # Handle sequence or single token
        if input_ids.ndim == 1:
            input_ids = input_ids.reshape(-1, 1)
        
        batch_size, seq_len = input_ids.shape
        
        # Embedding lookup
        embed_weight = self.weights.get("embed_tokens.weight")
        if embed_weight is not None:
            hidden = embed_weight[input_ids[:, -1]]  # Use last token
        else:
            hidden = np.zeros((batch_size, self.config.dim), dtype=np.float32)
        
        # Forward through layers
        for layer_idx in range(self.config.num_layers):
            hidden = self.forward_layer(layer_idx, hidden, position + seq_len - 1)
        
        # Final norm
        final_norm_weight = self.weights.get("norm.weight", np.ones(self.config.dim))
        hidden = self._rmsnorm(hidden, final_norm_weight)
        
        # LM head
        lm_head = self.weights.get("lm_head.weight")
        if lm_head is not None:
            logits = hidden @ lm_head.T
        else:
            logits = np.zeros((batch_size, self.config.vocab_size), dtype=np.float32)
        
        # Update stats
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        self.stats.total_tokens += 1
        self.stats.total_time_ms += elapsed_ms
        self.stats.decode_time_ms += elapsed_ms
        
        return logits
    
    def generate(
        self,
        input_ids: np.ndarray,
        max_tokens: int = 100,
        temperature: float = 1.0,
        top_p: float = 0.9,
    ) -> List[int]:
        """
        Generate tokens autoregressively.
        
        Args:
            input_ids: Initial token IDs [batch] or [batch, seq]
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling threshold
            
        Returns:
            generated_ids: List of generated token IDs
        """
        if input_ids.ndim == 1:
            input_ids = input_ids.reshape(1, -1)
        
        batch_size, seq_len = input_ids.shape
        
        # Reset state and stats
        self.init_state(batch_size)
        self.stats = InferenceStats()
        
        generated = []
        current_ids = input_ids
        position = 0
        
        # Prefill
        prefill_start = time.perf_counter()
        for pos in range(seq_len - 1):
            self.forward(current_ids[:, pos:pos+1], position=pos)
        self.stats.prefill_time_ms = (time.perf_counter() - prefill_start) * 1000
        
        # Start from last input token
        current_ids = input_ids[:, -1:]
        position = seq_len - 1
        
        # Decode
        for _ in range(max_tokens):
            logits = self.forward(current_ids, position=position)
            
            # Sample
            if temperature > 0:
                probs = self._softmax(logits / temperature)
                
                # Top-p filtering
                sorted_indices = np.argsort(-probs, axis=-1)
                sorted_probs = np.take_along_axis(probs, sorted_indices, axis=-1)
                cumsum = np.cumsum(sorted_probs, axis=-1)
                mask = cumsum <= top_p
                mask[..., 0] = True  # Keep at least one
                sorted_probs = sorted_probs * mask
                sorted_probs = sorted_probs / np.sum(sorted_probs, axis=-1, keepdims=True)
                
                # Sample from filtered distribution
                next_token = np.array([
                    sorted_indices[b, np.random.choice(len(sorted_probs[b]), p=sorted_probs[b])]
                    for b in range(batch_size)
                ])
            else:
                next_token = np.argmax(logits, axis=-1)
            
            generated.append(int(next_token[0]))
            current_ids = next_token.reshape(-1, 1)
            position += 1
        
        return generated
    
    def get_stats(self) -> InferenceStats:
        """Get inference statistics."""
        return self.stats
    
    def memory_usage_bytes(self) -> int:
        """Get current memory usage in bytes."""
        total = 0
        if self.state is not None:
            total += self.state.memory_bytes()
        for name, weight in self.weights.items():
            total += weight.nbytes
        for name, cached in self.weight_cache.items():
            total += cached.nbytes
        return total
    
    def memory_usage_mb(self) -> float:
        """Get current memory usage in MB."""
        return self.memory_usage_bytes() / (1024 * 1024)


def create_engine(
    dim: int = 4096,
    num_layers: int = 32,
    num_experts: int = 64,
    **kwargs
) -> NativeMoESSM:
    """
    Factory function to create a NativeMoESSM engine.
    
    Args:
        dim: Model dimension
        num_layers: Number of layers
        num_experts: Number of MoE experts
        **kwargs: Additional config options
        
    Returns:
        Configured NativeMoESSM engine
    """
    config = MoESSMConfig(
        dim=dim,
        num_layers=num_layers,
        num_experts=num_experts,
        **kwargs
    )
    return NativeMoESSM(config)


def benchmark(
    dim: int = 4096,
    num_layers: int = 32,
    num_tokens: int = 100,
) -> Dict[str, Any]:
    """
    Benchmark the engine with random weights.
    
    Args:
        dim: Model dimension
        num_layers: Number of layers
        num_tokens: Tokens to generate
        
    Returns:
        Benchmark results
    """
    print(f"Benchmarking MoE-SSM: dim={dim}, layers={num_layers}, tokens={num_tokens}")
    print(f"Native modules available: {HAS_NATIVE}")
    if HAS_NATIVE:
        print(f"Active modules: {NATIVE_MODULES}")
    
    config = MoESSMConfig(dim=dim, num_layers=num_layers)
    engine = NativeMoESSM(config)
    
    # Create random weights (simplified)
    weights = {
        "embed_tokens.weight": np.random.randn(config.vocab_size, dim).astype(np.float32) * 0.02,
        "norm.weight": np.ones(dim, dtype=np.float32),
        "lm_head.weight": np.random.randn(config.vocab_size, dim).astype(np.float32) * 0.02,
    }
    
    for layer in range(num_layers):
        prefix = f"layers.{layer}"
        weights[f"{prefix}.norm.weight"] = np.ones(dim, dtype=np.float32)
        weights[f"{prefix}.moe_norm.weight"] = np.ones(dim, dtype=np.float32)
        weights[f"{prefix}.ssm.A"] = -np.random.rand(dim, config.state_dim).astype(np.float32)
        weights[f"{prefix}.ssm.D"] = np.ones(dim, dtype=np.float32)
        weights[f"{prefix}.router.weight"] = np.random.randn(config.num_experts, dim).astype(np.float32) * 0.02
    
    engine.load_weights(weights)
    
    # Run benchmark
    input_ids = np.array([[1, 2, 3]])
    
    print("Warming up...")
    engine.generate(input_ids, max_tokens=10)
    
    print(f"Generating {num_tokens} tokens...")
    start = time.perf_counter()
    generated = engine.generate(input_ids, max_tokens=num_tokens)
    elapsed = time.perf_counter() - start
    
    stats = engine.get_stats()
    memory_mb = engine.memory_usage_mb()
    
    results = {
        "tokens": len(generated),
        "time_seconds": elapsed,
        "tokens_per_second": len(generated) / elapsed,
        "prefill_ms": stats.prefill_time_ms,
        "decode_ms": stats.decode_time_ms,
        "memory_mb": memory_mb,
        "native_enabled": HAS_NATIVE,
    }
    
    print(f"\nResults:")
    print(f"  Tokens: {results['tokens']}")
    print(f"  Speed: {results['tokens_per_second']:.1f} tok/s")
    print(f"  Prefill: {results['prefill_ms']:.1f}ms")
    print(f"  Memory: {results['memory_mb']:.1f}MB")
    
    return results


if __name__ == "__main__":
    benchmark()
