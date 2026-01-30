"""
OMNIMIND State-Space Model Layer
O(n) complexity State-Space Layer

Based on Mamba's Selective SSM approach but simplified for clarity.

SSM Equations:
    h(t) = A·h(t-1) + B·x(t)   # State update (recurrence)
    y(t) = C·h(t) + D·x(t)     # Output

Key Properties:
    - O(n) time complexity (vs O(n²) for attention)
    - Fixed state size (constant memory)
    - Selective state update (input-dependent)
"""
import math
from typing import Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F
from einops import rearrange, repeat

from .config import OmnimindConfig

try:
    import omnimind_native
    HAS_NATIVE = True
except ImportError:
    HAS_NATIVE = False

# Triton kernel integration for maximum performance
try:
    from omnimind.kernels import (
        HAS_TRITON, 
        fast_ssm_scan, 
        fast_rms_norm,
        fast_fused_add_rms_norm,
        fast_swiglu,
    )
except ImportError:
    HAS_TRITON = False
    fast_ssm_scan = None
    fast_rms_norm = None
    fast_fused_add_rms_norm = None
    fast_swiglu = None


class SelectiveSSM(nn.Module):
    """
    Selective State-Space Model
    
    แทน Attention ด้วย:
    1. ประมวลผลแบบ sequential O(n)
    2. State มีขนาดคงที่
    3. เลือก compress/keep ตาม input
    """
    
    def __init__(self, config: OmnimindConfig):
        super().__init__()
        self.config = config
        self.d_model = config.d_model
        self.d_state = config.d_state
        self.d_inner = config.d_inner
        self.dt_rank = config.dt_rank_value
        self.d_conv = config.d_conv
        
        # Input projection (x -> expanded)
        self.in_proj = nn.Linear(self.d_model, self.d_inner * 2, bias=False)
        
        # Convolution for local context
        self.conv1d = nn.Conv1d(
            in_channels=self.d_inner,
            out_channels=self.d_inner,
            kernel_size=config.d_conv,
            padding=config.d_conv - 1,
            groups=self.d_inner,  # Depthwise
            bias=True
        )
        
        # SSM parameters projections
        # x -> (Δ, B, C) projections
        self.x_proj = nn.Linear(
            self.d_inner, 
            self.dt_rank + self.d_state * 2,  # dt_rank + B + C
            bias=False
        )
        
        # Δ projection
        self.dt_proj = nn.Linear(self.dt_rank, self.d_inner, bias=True)
        
        # Initialize Δ projection bias for proper time step range
        dt_init_std = self.dt_rank ** -0.5 * config.dt_scale
        if config.dt_init == "constant":
            nn.init.constant_(self.dt_proj.weight, dt_init_std)
        else:
            nn.init.uniform_(self.dt_proj.weight, -dt_init_std, dt_init_std)
        
        # Initialize Δ bias to be in range [dt_min, dt_max]
        dt = torch.exp(
            torch.rand(self.d_inner) * (math.log(config.dt_max) - math.log(config.dt_min))
            + math.log(config.dt_min)
        ).clamp(min=config.dt_init_floor)
        inv_dt = dt + torch.log(-torch.expm1(-dt))
        with torch.no_grad():
            self.dt_proj.bias.copy_(inv_dt)
        
        # A parameter (state transition matrix - diagonal)
        # Initialize as negative (for stability with exp)
        A = repeat(
            torch.arange(1, self.d_state + 1, dtype=torch.float32),
            "n -> d n",
            d=self.d_inner
        )
        self.A_log = nn.Parameter(torch.log(A))
        
        # D parameter (skip connection)
        self.D = nn.Parameter(torch.ones(self.d_inner))
        
        # Output projection
        self.out_proj = nn.Linear(self.d_inner, self.d_model, bias=False)
    
    def load_converted_weights(self, converted_weights: dict, strict: bool = False) -> dict:
        """
        Load weights from Transformer-to-SSM conversion.
        
        Coordinates with omnimind.conversion.advanced_conversion output.
        
        Args:
            converted_weights: Dict from attention_to_ssm_weights()
            strict: If True, require all weights to match exactly
            
        Returns:
            Dict with load statistics
        """
        stats = {"loaded": 0, "skipped": 0, "mismatched": []}
        
        weight_mapping = {
            "in_proj.weight": self.in_proj.weight,
            "out_proj.weight": self.out_proj.weight,
            "x_proj.weight": self.x_proj.weight,
            "dt_proj.weight": self.dt_proj.weight,
            "dt_proj.bias": self.dt_proj.bias,
            "A_log": self.A_log,
            "D": self.D,
        }
        
        with torch.no_grad():
            for key, target_param in weight_mapping.items():
                if key in converted_weights:
                    source_tensor = converted_weights[key]
                    
                    if source_tensor.shape == target_param.shape:
                        target_param.copy_(source_tensor)
                        stats["loaded"] += 1
                    else:
                        stats["mismatched"].append(
                            f"{key}: {source_tensor.shape} vs {target_param.shape}"
                        )
                        if not strict:
                            # Try partial copy for compatible dimensions
                            min_shape = [min(s, t) for s, t in zip(source_tensor.shape, target_param.shape)]
                            if len(min_shape) == 2:
                                target_param[:min_shape[0], :min_shape[1]] = source_tensor[:min_shape[0], :min_shape[1]]
                            elif len(min_shape) == 1:
                                target_param[:min_shape[0]] = source_tensor[:min_shape[0]]
                            stats["loaded"] += 1
                else:
                    stats["skipped"] += 1
        
        return stats
    
    def get_stability_metrics(self) -> dict:
        """
        Compute stability metrics for the current SSM parameters.
        
        Useful for monitoring after conversion or during training.
        """
        with torch.no_grad():
            A = -torch.exp(self.A_log.float())
            dt_actual = torch.nn.functional.softplus(self.dt_proj.bias)
            
            return {
                "A_all_negative": (A < 0).all().item(),
                "A_mean": A.mean().item(),
                "A_min": A.min().item(),
                "A_max": A.max().item(),
                "dt_mean": dt_actual.mean().item(),
                "dt_min": dt_actual.min().item(),
                "dt_max": dt_actual.max().item(),
                "D_mean": self.D.mean().item(),
            }
    
    def forward(
        self, 
        hidden_states: torch.Tensor,
        cache: Optional[Tuple[torch.Tensor, torch.Tensor]] = None
    ) -> Tuple[torch.Tensor, Optional[Tuple[torch.Tensor, torch.Tensor]]]:
        """
        Forward pass
        
        Args:
            hidden_states: (batch, seq_len, d_model)
            cache: Optional (conv_state, ssm_state) for inference
            
        Returns:
            output: (batch, seq_len, d_model)
            new_cache: Updated cache for next step
        """
        batch, seq_len, _ = hidden_states.shape
        
        # Optimized Native Inference (CPU only, seq_len=1, batch=1)
        # Native kernel currently supports 1D dt input, so batch must be 1 (or constant dt)
        if HAS_NATIVE and seq_len == 1 and batch == 1 and cache is not None and hidden_states.device.type == "cpu":
            try:
                return self._native_inference_forward(hidden_states, cache)
            except Exception:
                # Fallback on error
                pass

        # Input projection -> (z, x)
        xz = self.in_proj(hidden_states)  # (B, L, 2*d_inner)
        x, z = xz.chunk(2, dim=-1)  # Each: (B, L, d_inner)
        
        # Convolution (with caching for inference)
        if cache is not None:
            conv_state, ssm_state = cache
            # Prepend cached conv state
            x = torch.cat([conv_state, x], dim=1)
            new_conv_state = x[:, -self.d_conv + 1:, :].clone()
        else:
            new_conv_state = None
            ssm_state = None
        
        # Apply causal convolution
        x = rearrange(x, "b l d -> b d l")
        x = self.conv1d(x)[:, :, :seq_len]  # Causal: take only first seq_len
        x = rearrange(x, "b d l -> b l d")
        x = F.silu(x)
        
        # Selective SSM
        y, new_ssm_state = self.selective_scan(x, ssm_state)
        
        # Gate with z
        y = y * F.silu(z)
        
        # Output projection
        output = self.out_proj(y)
        
        # Build new cache
        if cache is not None:
            new_cache = (new_conv_state, new_ssm_state)
        else:
            new_cache = None
        
        return output, new_cache

    def _native_inference_forward(
        self, 
        hidden_states: torch.Tensor, 
        cache: Tuple[torch.Tensor, torch.Tensor]
    ) -> Tuple[torch.Tensor, Tuple[torch.Tensor, torch.Tensor]]:
        """Optimized inference using omnimind_native kernels"""
        conv_state, ssm_state = cache
        
        # 1. Projections
        xz = self.in_proj(hidden_states).squeeze(1) # (B, 2*D)
        x, z = xz.chunk(2, dim=-1)
        
        # 2. Native Conv1d Update
        # Prepare inputs (numpy views)
        x_np = x.detach().numpy()
        # Weight shape (D, 1, K) -> (D, K)
        w_conv = self.conv1d.weight.squeeze(1).detach().numpy()
        b_conv = self.conv1d.bias.detach().numpy()
        conv_state_np = conv_state.detach().numpy()
        
        x_conv_np, new_conv_state_np = omnimind_native.conv_state_update(
            x_np, conv_state_np, w_conv, b_conv
        )
        
        # To Torch for activation/proj
        x_conv = torch.from_numpy(x_conv_np)
        new_conv_state = torch.from_numpy(new_conv_state_np)
        
        # Activation
        x_ssm = F.silu(x_conv)
        
        # 3. SSM Projections (dt, B, C)
        x_proj = self.x_proj(x_ssm)
        dt_proj, B, C = torch.split(x_proj, [self.dt_rank, self.d_state, self.d_state], dim=-1)
        dt = F.softplus(self.dt_proj(dt_proj)) # (B, D_inner)
        
        # 4. Native SSM Fused Gate
        x_ssm_np = x_ssm.detach().numpy()
        z_np = z.detach().numpy()
        ssm_state_np = ssm_state.detach().numpy()
        
        A = -torch.exp(self.A_log.float())
        A_np = A.detach().numpy()
        D_np = self.D.detach().numpy()
        B_np = B.detach().numpy()
        C_np = C.detach().numpy()
        # Flatten dt to (D,) as native kernel expects shared dt
        dt_np = dt.detach().numpy().flatten()
        
        y_out_np, new_ssm_state_np = omnimind_native.ssm_fused_gate(
            x_ssm_np, z_np, ssm_state_np, A_np, B_np, C_np, D_np, dt_np
        )
        
        y = torch.from_numpy(y_out_np)
        new_ssm_state = torch.from_numpy(new_ssm_state_np)
        
        # 5. Output Projection
        output = self.out_proj(y)
        
        return output.unsqueeze(1), (new_conv_state, new_ssm_state)
    
    def selective_scan(
        self, 
        x: torch.Tensor,
        ssm_state: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Selective State-Space Scan
        
        This is the core SSM computation with input-dependent parameters.
        
        For training: parallel scan for efficiency
        For inference: sequential scan with state caching
        
        Args:
            x: (batch, seq_len, d_inner)
            ssm_state: Optional previous state (batch, d_inner, d_state)
            
        Returns:
            y: (batch, seq_len, d_inner)
            final_state: (batch, d_inner, d_state)
        """
        batch, seq_len, d_inner = x.shape
        
        # Get A (state transition matrix)
        A = -torch.exp(self.A_log.float())  # (d_inner, d_state)
        D = self.D.float()  # (d_inner,)
        
        # Project x to get Δ, B, C
        x_proj = self.x_proj(x)  # (B, L, dt_rank + d_state * 2)
        
        # Split projections
        dt, B, C = torch.split(
            x_proj, 
            [self.dt_rank, self.d_state, self.d_state], 
            dim=-1
        )
        
        # Compute Δ (time step)
        dt = self.dt_proj(dt)  # (B, L, d_inner)
        dt = F.softplus(dt)  # Ensure positive
        
        # Discretize A and B
        # Δ controls how much to update state
        # dA = exp(Δ * A)
        # dB = Δ * B
        
        # Initialize state if not provided
        if ssm_state is None:
            ssm_state = torch.zeros(
                batch, d_inner, self.d_state, 
                device=x.device, dtype=x.dtype
            )
        
        # Run selective scan - Use Triton kernel if available
        if HAS_TRITON and x.is_cuda and fast_ssm_scan is not None:
            # Fast Triton path
            y = self._triton_scan(x, dt, A, B, C, D, ssm_state)
        else:
            # Fallback to optimized PyTorch
            y = self._sequential_scan_optimized(x, dt, A, B, C, D, ssm_state)
        
        # Get final state (last state after processing all tokens)
        final_state = ssm_state  # Updated in-place
        
        return y, final_state
    
    def _triton_scan(
        self,
        x: torch.Tensor,
        dt: torch.Tensor,
        A: torch.Tensor,
        B: torch.Tensor,
        C: torch.Tensor,
        D: torch.Tensor,
        state: torch.Tensor,
    ) -> torch.Tensor:
        """Fast SSM scan using Triton kernel"""
        # Use the Triton kernel - argument order: x, dt, A, B, C, D, state
        return fast_ssm_scan(x, dt, A, B, C, D, state)
    
    def _sequential_scan_optimized(
        self,
        x: torch.Tensor,      # (B, L, D)
        dt: torch.Tensor,     # (B, L, D)
        A: torch.Tensor,      # (D, N) - state transition
        B: torch.Tensor,      # (B, L, N) - input matrix
        C: torch.Tensor,      # (B, L, N) - output matrix
        D: torch.Tensor,      # (D,) - skip connection
        state: torch.Tensor,  # (B, D, N) - initial state
    ) -> torch.Tensor:
        """
        Optimized Sequential SSM scan with reduced memory allocations
        
        For each time step:
            h(t) = exp(Δ*A) * h(t-1) + Δ*B * x(t)
            y(t) = C * h(t) + D * x(t)
        """
        batch, seq_len, d_inner = x.shape
        
        # Pre-allocate output tensor (avoid appending to list)
        y = torch.empty_like(x)
        
        # Pre-compute A expansion
        A_expanded = A.unsqueeze(0)  # (1, D, N)
        
        for t in range(seq_len):
            # Get current inputs (views, no copy)
            x_t = x[:, t, :]           # (B, D)
            dt_t = dt[:, t, :]         # (B, D)
            B_t = B[:, t, :]           # (B, N)
            C_t = C[:, t, :]           # (B, N)
            
            # Discretize with fused operations
            dt_t_expand = dt_t.unsqueeze(-1)  # (B, D, 1)
            dA = torch.exp(dt_t_expand * A_expanded)  # (B, D, N)
            dB = dt_t_expand * B_t.unsqueeze(1)  # (B, D, N)
            
            # State update (in-place for memory efficiency)
            state.mul_(dA).add_(dB * x_t.unsqueeze(-1))
            
            # Output computation
            y[:, t, :] = torch.einsum("bn,bdn->bd", C_t, state) + D * x_t
        
        return y


class OmnimindBlock(nn.Module):
    """
    Single OMNIMIND block = SSM + Residual + Norm
    
    Structure:
        x -> Norm -> SSM -> + -> output
             |______________|
                (residual)
    """
    
    def __init__(self, config: OmnimindConfig, layer_idx: int = 0):
        super().__init__()
        self.config = config
        self.layer_idx = layer_idx
        
        # Pre-norm (RMSNorm for efficiency)
        self.norm = RMSNorm(config.d_model)
        
        # SSM layer
        self.ssm = SelectiveSSM(config)
        
        # Dropout
        self.dropout = nn.Dropout(config.dropout)
    
    def forward(
        self, 
        hidden_states: torch.Tensor,
        cache: Optional[Tuple[torch.Tensor, torch.Tensor]] = None
    ) -> Tuple[torch.Tensor, Optional[Tuple[torch.Tensor, torch.Tensor]]]:
        """
        Forward pass with residual
        
        Args:
            hidden_states: (batch, seq_len, d_model)
            cache: Optional SSM cache
            
        Returns:
            output: (batch, seq_len, d_model)
            new_cache: Updated cache
        """
        residual = hidden_states
        
        # Norm -> SSM
        hidden_states = self.norm(hidden_states)
        hidden_states, new_cache = self.ssm(hidden_states, cache)
        
        # Dropout + Residual
        hidden_states = self.dropout(hidden_states)
        output = residual + hidden_states
        
        return output, new_cache


class RMSNorm(nn.Module):
    """Root Mean Square Layer Normalization with Triton optimization"""
    
    def __init__(self, d_model: int, eps: float = 1e-6):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(d_model))
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Use Triton kernel for GPU (fastest)
        if HAS_TRITON and x.is_cuda and fast_rms_norm is not None:
            return fast_rms_norm(x, self.weight, self.eps)
        
        # Use native kernel for CPU inference
        if HAS_NATIVE and x.device.type == "cpu" and not x.requires_grad:
            try:
                orig_shape = x.shape
                d_model = orig_shape[-1]
                x_flat = x.detach().numpy().reshape(-1, d_model)
                w_np = self.weight.detach().numpy()
                
                out_flat = omnimind_native.rmsnorm_fused(
                    x_flat, w_np, None, None, self.eps
                )
                
                return torch.from_numpy(out_flat).reshape(orig_shape)
            except Exception:
                pass
        
        # PyTorch fallback
        rms = torch.sqrt(torch.mean(x ** 2, dim=-1, keepdim=True) + self.eps)
        return x / rms * self.weight
    
    def fused_add_norm(self, x: torch.Tensor, residual: torch.Tensor) -> torch.Tensor:
        """
        Fused Add + RMSNorm: y = RMSNorm(x + residual)
        Reduces memory bandwidth by combining operations
        """
        if HAS_TRITON and x.is_cuda and fast_fused_add_rms_norm is not None:
            return fast_fused_add_rms_norm(x, residual, self.weight, self.eps)
        
        # Fallback: separate add and norm
        h = x + residual
        rms = torch.sqrt(torch.mean(h ** 2, dim=-1, keepdim=True) + self.eps)
        return h / rms * self.weight
