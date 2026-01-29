"""
OMNIMIND Advanced Quantization System
Production-grade quantization for 70B-200B+ models on mobile devices

Supported Quantization Types:
- FP32: Full precision (baseline)
- FP16: Half precision  
- BF16: Brain Float 16 (better range than FP16)
- FP8:  8-bit floating point (E4M3/E5M2)
- FP4:  4-bit floating point
- INT8: 8-bit integer
- INT4: 4-bit integer (packed, 2 values per byte)
- NF4:  Normal Float 4 (optimized for neural network weights)

Memory Savings:
- FP32 → INT4: 8x reduction
- 70B model: 280GB → 35GB
- Fits on 512GB mobile storage!
"""

import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple, Dict, Any, Union, List
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np


class QuantType(Enum):
    """Supported quantization types"""
    FP32 = "fp32"
    FP16 = "fp16"
    BF16 = "bf16"
    FP8_E4M3 = "fp8_e4m3"  # 4 exponent, 3 mantissa bits
    FP8_E5M2 = "fp8_e5m2"  # 5 exponent, 2 mantissa bits
    FP4 = "fp4"
    INT8 = "int8"
    INT4 = "int4"
    NF4 = "nf4"  # Normal Float 4


# Quantization type specifications
QUANT_SPECS = {
    QuantType.FP32: {"bits": 32, "bytes_per_param": 4.0, "is_float": True},
    QuantType.FP16: {"bits": 16, "bytes_per_param": 2.0, "is_float": True},
    QuantType.BF16: {"bits": 16, "bytes_per_param": 2.0, "is_float": True},
    QuantType.FP8_E4M3: {"bits": 8, "bytes_per_param": 1.0, "is_float": True},
    QuantType.FP8_E5M2: {"bits": 8, "bytes_per_param": 1.0, "is_float": True},
    QuantType.FP4: {"bits": 4, "bytes_per_param": 0.5, "is_float": True},
    QuantType.INT8: {"bits": 8, "bytes_per_param": 1.0, "is_float": False},
    QuantType.INT4: {"bits": 4, "bytes_per_param": 0.5, "is_float": False},
    QuantType.NF4: {"bits": 4, "bytes_per_param": 0.5, "is_float": True},
}

# NF4 quantization levels (optimized for normally distributed weights)
# These values are derived from the quantiles of a standard normal distribution
NF4_LEVELS = torch.tensor([
    -1.0, -0.6961928009986877, -0.5250730514526367, -0.39491748809814453,
    -0.28444138169288635, -0.18477343022823334, -0.09105003625154495, 0.0,
    0.07958029955625534, 0.16093020141124725, 0.24611230194568634, 0.33791524171829224,
    0.44070982933044434, 0.5626170039176941, 0.7229568362236023, 1.0
])


@dataclass
class QuantConfig:
    """Configuration for quantization"""
    quant_type: QuantType = QuantType.INT4
    group_size: int = 128  # Quantization group size
    symmetric: bool = False  # Symmetric vs asymmetric quantization
    compute_dtype: torch.dtype = torch.float16  # Dtype for computation
    double_quant: bool = False  # Quantize the scales too
    threshold: float = 6.0  # Outlier threshold for mixed precision
    
    @property
    def bits(self) -> int:
        return QUANT_SPECS[self.quant_type]["bits"]
    
    @property
    def bytes_per_param(self) -> float:
        return QUANT_SPECS[self.quant_type]["bytes_per_param"]


class FP8Quantizer:
    """
    FP8 (8-bit Floating Point) Quantizer
    
    Supports two formats:
    - E4M3: 4 exponent bits, 3 mantissa bits (better precision)
    - E5M2: 5 exponent bits, 2 mantissa bits (better range)
    
    FP8 is better than INT8 for neural networks because it preserves
    the floating-point distribution of weights.
    """
    
    # E4M3 configuration
    E4M3_MAX = 448.0
    E4M3_MIN = -448.0
    
    # E5M2 configuration  
    E5M2_MAX = 57344.0
    E5M2_MIN = -57344.0
    
    @staticmethod
    def quantize_e4m3(
        tensor: torch.Tensor,
        scale: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Quantize to FP8 E4M3 format
        
        Args:
            tensor: Input tensor
            scale: Optional pre-computed scale
            
        Returns:
            Tuple of (quantized_tensor, scale)
        """
        if scale is None:
            # Compute per-tensor scale
            abs_max = tensor.abs().max().clamp(min=1e-12)
            scale = abs_max / FP8Quantizer.E4M3_MAX
        
        # Scale and clamp
        scaled = tensor / scale
        clamped = scaled.clamp(FP8Quantizer.E4M3_MIN, FP8Quantizer.E4M3_MAX)
        
        # Simulate FP8 by rounding (since PyTorch doesn't have native FP8)
        # This rounds to nearest representable FP8 value
        quantized = FP8Quantizer._round_to_fp8_e4m3(clamped)
        
        return quantized.to(torch.int8), scale
    
    @staticmethod
    def quantize_e5m2(
        tensor: torch.Tensor,
        scale: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Quantize to FP8 E5M2 format"""
        if scale is None:
            abs_max = tensor.abs().max().clamp(min=1e-12)
            scale = abs_max / FP8Quantizer.E5M2_MAX
        
        scaled = tensor / scale
        clamped = scaled.clamp(FP8Quantizer.E5M2_MIN, FP8Quantizer.E5M2_MAX)
        quantized = FP8Quantizer._round_to_fp8_e5m2(clamped)
        
        return quantized.to(torch.int8), scale
    
    @staticmethod
    def _round_to_fp8_e4m3(x: torch.Tensor) -> torch.Tensor:
        """Round to nearest FP8 E4M3 representable value"""
        # Simplified simulation - in production would use actual FP8 ops
        mantissa_bits = 3
        scale_factor = 2 ** mantissa_bits
        return torch.round(x * scale_factor) / scale_factor
    
    @staticmethod
    def _round_to_fp8_e5m2(x: torch.Tensor) -> torch.Tensor:
        """Round to nearest FP8 E5M2 representable value"""
        mantissa_bits = 2
        scale_factor = 2 ** mantissa_bits
        return torch.round(x * scale_factor) / scale_factor
    
    @staticmethod
    def dequantize(
        quantized: torch.Tensor,
        scale: torch.Tensor,
        dtype: torch.dtype = torch.float16
    ) -> torch.Tensor:
        """Dequantize FP8 back to higher precision"""
        return quantized.to(dtype) * scale


class FP4Quantizer:
    """
    FP4 (4-bit Floating Point) Quantizer
    
    Uses 16 representable values based on the FP4 E2M1 format:
    - 1 sign bit
    - 2 exponent bits  
    - 1 mantissa bit
    
    This preserves floating-point properties better than INT4
    for neural network weights.
    """
    
    # FP4 E2M1 representable values (positive)
    FP4_VALUES = torch.tensor([0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0])
    
    @staticmethod
    def quantize(
        tensor: torch.Tensor,
        group_size: int = 128
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Quantize to FP4 format
        
        Args:
            tensor: Input tensor (will be flattened)
            group_size: Number of elements per quantization group
            
        Returns:
            Tuple of (packed_quantized, scales)
        """
        original_shape = tensor.shape
        flat = tensor.flatten()
        
        # Pad to multiple of group_size
        numel = flat.numel()
        padded_len = ((numel + group_size - 1) // group_size) * group_size
        if padded_len > numel:
            flat = F.pad(flat, (0, padded_len - numel))
        
        # Reshape to groups
        grouped = flat.view(-1, group_size)
        num_groups = grouped.shape[0]
        
        # Compute per-group scales
        abs_max = grouped.abs().max(dim=1, keepdim=True)[0].clamp(min=1e-12)
        scales = abs_max / 6.0  # 6.0 is max FP4 value
        
        # Normalize to [-6, 6] range
        normalized = grouped / scales
        
        # Quantize each element to nearest FP4 value
        fp4_values = FP4Quantizer.FP4_VALUES.to(tensor.device)
        quantized = torch.zeros_like(normalized, dtype=torch.int8)
        
        for i, v in enumerate(fp4_values):
            # Handle positive values
            mask = (normalized >= 0) & (normalized >= v - 0.25) & (normalized < v + 0.25)
            quantized[mask] = i
            
            # Handle negative values (indices 8-15)
            mask_neg = (normalized < 0) & (normalized >= -v - 0.25) & (normalized < -v + 0.25)
            quantized[mask_neg] = i + 8
        
        # Pack 2 FP4 values per byte
        quantized_flat = quantized.flatten()
        packed = torch.zeros(quantized_flat.numel() // 2, dtype=torch.uint8, device=tensor.device)
        packed = (quantized_flat[0::2].to(torch.uint8) & 0x0F) | ((quantized_flat[1::2].to(torch.uint8) & 0x0F) << 4)
        
        return packed, scales.flatten(), original_shape, numel
    
    @staticmethod
    def dequantize(
        packed: torch.Tensor,
        scales: torch.Tensor,
        original_shape: torch.Size,
        original_numel: int,
        group_size: int = 128,
        dtype: torch.dtype = torch.float16
    ) -> torch.Tensor:
        """Dequantize FP4 back to higher precision"""
        # Unpack
        low = (packed & 0x0F).to(torch.int8)
        high = ((packed >> 4) & 0x0F).to(torch.int8)
        quantized = torch.zeros(packed.numel() * 2, dtype=torch.int8, device=packed.device)
        quantized[0::2] = low
        quantized[1::2] = high
        
        # Map indices back to FP4 values
        fp4_values = FP4Quantizer.FP4_VALUES.to(packed.device)
        dequantized = torch.zeros(quantized.numel(), dtype=dtype, device=packed.device)
        
        for i in range(8):
            # Positive values (indices 0-7)
            mask = quantized == i
            dequantized[mask] = fp4_values[i].to(dtype)
            
            # Negative values (indices 8-15)
            mask_neg = quantized == (i + 8)
            dequantized[mask_neg] = -fp4_values[i].to(dtype)
        
        # Apply scales and reshape
        grouped = dequantized.view(-1, group_size)
        scaled = grouped * scales.view(-1, 1)
        result = scaled.flatten()[:original_numel].view(original_shape)
        
        return result


class NF4Quantizer:
    """
    NF4 (Normal Float 4) Quantizer
    
    NF4 uses quantization levels optimized for the normal distribution
    of neural network weights. This provides better accuracy than
    uniform INT4 or standard FP4 for weight quantization.
    
    Based on the paper: "QLoRA: Efficient Finetuning of Quantized LLMs"
    """
    
    @staticmethod
    def quantize(
        tensor: torch.Tensor,
        group_size: int = 128
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Size, int]:
        """
        Quantize to NF4 format
        
        Args:
            tensor: Input tensor
            group_size: Number of elements per quantization group
            
        Returns:
            Tuple of (packed_quantized, scales, original_shape, original_numel)
        """
        original_shape = tensor.shape
        flat = tensor.flatten().float()
        
        # Pad to multiple of group_size
        numel = flat.numel()
        padded_len = ((numel + group_size - 1) // group_size) * group_size
        if padded_len > numel:
            flat = F.pad(flat, (0, padded_len - numel))
        
        # Reshape to groups
        grouped = flat.view(-1, group_size)
        
        # Compute per-group scales (absmax normalization)
        abs_max = grouped.abs().max(dim=1, keepdim=True)[0].clamp(min=1e-12)
        scales = abs_max
        
        # Normalize to [-1, 1]
        normalized = grouped / scales
        
        # Find nearest NF4 level for each element
        nf4_levels = NF4_LEVELS.to(tensor.device)
        
        # Vectorized nearest neighbor search
        # Shape: (num_groups, group_size, 16)
        distances = (normalized.unsqueeze(-1) - nf4_levels).abs()
        indices = distances.argmin(dim=-1).to(torch.uint8)
        
        # Pack 2 NF4 values per byte
        indices_flat = indices.flatten()
        packed = (indices_flat[0::2] & 0x0F) | ((indices_flat[1::2] & 0x0F) << 4)
        
        return packed, scales.flatten(), original_shape, numel
    
    @staticmethod
    def dequantize(
        packed: torch.Tensor,
        scales: torch.Tensor,
        original_shape: torch.Size,
        original_numel: int,
        group_size: int = 128,
        dtype: torch.dtype = torch.float16
    ) -> torch.Tensor:
        """Dequantize NF4 back to higher precision"""
        # Unpack
        low = (packed & 0x0F)
        high = ((packed >> 4) & 0x0F)
        indices = torch.zeros(packed.numel() * 2, dtype=torch.long, device=packed.device)
        indices[0::2] = low.long()
        indices[1::2] = high.long()
        
        # Map indices to NF4 values
        nf4_levels = NF4_LEVELS.to(packed.device).to(dtype)
        dequantized = nf4_levels[indices]
        
        # Apply scales
        grouped = dequantized.view(-1, group_size)
        scaled = grouped * scales.view(-1, 1).to(dtype)
        result = scaled.flatten()[:original_numel].view(original_shape)
        
        return result


class INT4Quantizer:
    """
    INT4 (4-bit Integer) Quantizer
    
    Production-ready INT4 with fixes for:
    - Odd dimension handling
    - Proper zero-point computation
    - Vectorized operations
    """
    
    @staticmethod
    def quantize(
        tensor: torch.Tensor,
        group_size: int = 128,
        symmetric: bool = False
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Size, int]:
        """
        Quantize to INT4 format with proper handling
        
        Returns:
            Tuple of (packed, scales, zeros, original_shape, original_numel)
        """
        original_shape = tensor.shape
        flat = tensor.flatten().float()
        numel = flat.numel()
        
        # Pad to multiple of group_size * 2 (for packing)
        padded_len = ((numel + group_size - 1) // group_size) * group_size
        if padded_len % 2 != 0:
            padded_len += group_size  # Ensure even number for packing
        
        if padded_len > numel:
            flat = F.pad(flat, (0, padded_len - numel))
        
        # Reshape to groups
        grouped = flat.view(-1, group_size)
        num_groups = grouped.shape[0]
        
        if symmetric:
            # Symmetric quantization: [-7, 7]
            abs_max = grouped.abs().max(dim=1, keepdim=True)[0].clamp(min=1e-12)
            scales = abs_max / 7.0
            zeros = torch.zeros(num_groups, 1, device=tensor.device)
            
            # Quantize
            quantized = torch.round(grouped / scales).clamp(-8, 7).to(torch.int8)
        else:
            # Asymmetric quantization: [0, 15]
            w_min = grouped.min(dim=1, keepdim=True)[0]
            w_max = grouped.max(dim=1, keepdim=True)[0]
            
            scales = ((w_max - w_min) / 15.0).clamp(min=1e-12)
            zeros = w_min
            
            # Quantize
            quantized = torch.round((grouped - zeros) / scales).clamp(0, 15).to(torch.uint8)
        
        # Pack 2 INT4 values per byte
        quantized_flat = quantized.flatten()
        if symmetric:
            # For symmetric, shift to unsigned [0, 15]
            quantized_flat = (quantized_flat + 8).to(torch.uint8)
        
        packed = (quantized_flat[0::2] & 0x0F) | ((quantized_flat[1::2] & 0x0F) << 4)
        
        return packed, scales.flatten(), zeros.flatten(), original_shape, numel
    
    @staticmethod
    def dequantize(
        packed: torch.Tensor,
        scales: torch.Tensor,
        zeros: torch.Tensor,
        original_shape: torch.Size,
        original_numel: int,
        group_size: int = 128,
        symmetric: bool = False,
        dtype: torch.dtype = torch.float16
    ) -> torch.Tensor:
        """Dequantize INT4 back to higher precision"""
        # Unpack
        low = (packed & 0x0F)
        high = ((packed >> 4) & 0x0F)
        quantized = torch.zeros(packed.numel() * 2, dtype=torch.float32, device=packed.device)
        quantized[0::2] = low.float()
        quantized[1::2] = high.float()
        
        # Reshape to groups
        grouped = quantized.view(-1, group_size)
        
        if symmetric:
            # Shift back to signed [-8, 7]
            grouped = grouped - 8
            # Dequantize
            dequantized = grouped * scales.view(-1, 1)
        else:
            # Dequantize
            dequantized = grouped * scales.view(-1, 1) + zeros.view(-1, 1)
        
        result = dequantized.flatten()[:original_numel].view(original_shape).to(dtype)
        return result


class INT8Quantizer:
    """INT8 Quantizer with per-tensor and per-channel options"""
    
    @staticmethod
    def quantize(
        tensor: torch.Tensor,
        per_channel: bool = True,
        symmetric: bool = True
    ) -> Tuple[torch.Tensor, torch.Tensor, Optional[torch.Tensor]]:
        """Quantize to INT8"""
        if per_channel and tensor.dim() >= 2:
            # Per-channel quantization (along output dimension)
            if symmetric:
                abs_max = tensor.abs().max(dim=1, keepdim=True)[0].clamp(min=1e-12)
                scales = abs_max / 127.0
                quantized = torch.round(tensor / scales).clamp(-128, 127).to(torch.int8)
                return quantized, scales.flatten(), None
            else:
                w_min = tensor.min(dim=1, keepdim=True)[0]
                w_max = tensor.max(dim=1, keepdim=True)[0]
                scales = ((w_max - w_min) / 255.0).clamp(min=1e-12)
                zeros = w_min
                quantized = torch.round((tensor - zeros) / scales).clamp(0, 255).to(torch.uint8)
                return quantized, scales.flatten(), zeros.flatten()
        else:
            # Per-tensor quantization
            if symmetric:
                abs_max = tensor.abs().max().clamp(min=1e-12)
                scale = abs_max / 127.0
                quantized = torch.round(tensor / scale).clamp(-128, 127).to(torch.int8)
                return quantized, scale.unsqueeze(0), None
            else:
                w_min = tensor.min()
                w_max = tensor.max()
                scale = ((w_max - w_min) / 255.0).clamp(min=1e-12)
                zero = w_min
                quantized = torch.round((tensor - zero) / scale).clamp(0, 255).to(torch.uint8)
                return quantized, scale.unsqueeze(0), zero.unsqueeze(0)
    
    @staticmethod
    def dequantize(
        quantized: torch.Tensor,
        scales: torch.Tensor,
        zeros: Optional[torch.Tensor] = None,
        dtype: torch.dtype = torch.float16
    ) -> torch.Tensor:
        """Dequantize INT8"""
        if zeros is None:
            # Symmetric
            return quantized.to(dtype) * scales.view(-1, 1) if scales.numel() > 1 else quantized.to(dtype) * scales
        else:
            # Asymmetric
            return quantized.to(dtype) * scales.view(-1, 1) + zeros.view(-1, 1)


class UnifiedQuantizedLinear(nn.Module):
    """
    Unified Quantized Linear Layer supporting all quantization types
    
    This is the production-grade implementation that handles:
    - All quantization types (FP32/FP16/BF16/FP8/FP4/INT8/INT4/NF4)
    - Proper memory management
    - Efficient dequantization
    - GPU/CPU/MPS support
    """
    
    def __init__(
        self,
        in_features: int,
        out_features: int,
        config: QuantConfig,
        bias: bool = True
    ):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.config = config
        self.quant_type = config.quant_type
        
        # Storage for quantized weights (will be populated during quantize())
        self.weight_quantized = None
        self.weight_scales = None
        self.weight_zeros = None
        self.weight_shape = None
        self.weight_numel = None
        
        # Bias (not quantized)
        if bias:
            self.bias = nn.Parameter(torch.zeros(out_features))
        else:
            self.register_parameter('bias', None)
        
        # For on-the-fly dequantization tracking
        self._dequantized_weight = None
    
    def quantize_weight(self, weight: torch.Tensor):
        """Quantize weight tensor and store internally"""
        self.weight_shape = weight.shape
        self.weight_numel = weight.numel()
        
        if self.quant_type == QuantType.FP32:
            self.weight_quantized = weight.float()
            
        elif self.quant_type == QuantType.FP16:
            self.weight_quantized = weight.half()
            
        elif self.quant_type == QuantType.BF16:
            self.weight_quantized = weight.bfloat16()
            
        elif self.quant_type in [QuantType.FP8_E4M3, QuantType.FP8_E5M2]:
            if self.quant_type == QuantType.FP8_E4M3:
                self.weight_quantized, self.weight_scales = FP8Quantizer.quantize_e4m3(weight)
            else:
                self.weight_quantized, self.weight_scales = FP8Quantizer.quantize_e5m2(weight)
                
        elif self.quant_type == QuantType.FP4:
            result = FP4Quantizer.quantize(weight, self.config.group_size)
            self.weight_quantized, self.weight_scales, self.weight_shape, self.weight_numel = result
            
        elif self.quant_type == QuantType.NF4:
            result = NF4Quantizer.quantize(weight, self.config.group_size)
            self.weight_quantized, self.weight_scales, self.weight_shape, self.weight_numel = result
            
        elif self.quant_type == QuantType.INT4:
            result = INT4Quantizer.quantize(weight, self.config.group_size, self.config.symmetric)
            self.weight_quantized, self.weight_scales, self.weight_zeros, self.weight_shape, self.weight_numel = result
            
        elif self.quant_type == QuantType.INT8:
            self.weight_quantized, self.weight_scales, self.weight_zeros = INT8Quantizer.quantize(weight)
    
    def dequantize_weight(self, dtype: torch.dtype = None) -> torch.Tensor:
        """Dequantize weight tensor on-the-fly"""
        if dtype is None:
            dtype = self.config.compute_dtype
            
        if self.quant_type in [QuantType.FP32, QuantType.FP16, QuantType.BF16]:
            return self.weight_quantized.to(dtype)
            
        elif self.quant_type in [QuantType.FP8_E4M3, QuantType.FP8_E5M2]:
            return FP8Quantizer.dequantize(self.weight_quantized, self.weight_scales, dtype)
            
        elif self.quant_type == QuantType.FP4:
            return FP4Quantizer.dequantize(
                self.weight_quantized, self.weight_scales,
                self.weight_shape, self.weight_numel,
                self.config.group_size, dtype
            )
            
        elif self.quant_type == QuantType.NF4:
            return NF4Quantizer.dequantize(
                self.weight_quantized, self.weight_scales,
                self.weight_shape, self.weight_numel,
                self.config.group_size, dtype
            )
            
        elif self.quant_type == QuantType.INT4:
            return INT4Quantizer.dequantize(
                self.weight_quantized, self.weight_scales, self.weight_zeros,
                self.weight_shape, self.weight_numel,
                self.config.group_size, self.config.symmetric, dtype
            )
            
        elif self.quant_type == QuantType.INT8:
            return INT8Quantizer.dequantize(
                self.weight_quantized, self.weight_scales, self.weight_zeros, dtype
            )
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass with on-the-fly dequantization"""
        # Global Triton hook for fused quantization
        try:
            from omnimind.kernels.quant_matmul import fast_quant_matmul
            HAS_TRITON_QUANT = True
        except ImportError:
            HAS_TRITON_QUANT = False

        if HAS_TRITON_QUANT and x.is_cuda and self.quant_type in [QuantType.INT4, QuantType.NF4]:
            # Use Fused Triton Kernel for maximum speed
            return fast_quant_matmul(
                x, 
                self.weight_quantized, 
                self.weight_scales, 
                self.weight_zeros, 
                self.quant_type.value
            ) + (self.bias if self.bias is not None else 0)

        # Fallback to slow dequantize + linear
        weight = self.dequantize_weight(x.dtype)
        return F.linear(x, weight, self.bias)
    
    def memory_usage_bytes(self) -> int:
        """Calculate memory usage of quantized weight"""
        if self.weight_quantized is None:
            return 0
        
        total = self.weight_quantized.numel() * self.weight_quantized.element_size()
        
        if self.weight_scales is not None:
            total += self.weight_scales.numel() * self.weight_scales.element_size()
        
        if self.weight_zeros is not None:
            total += self.weight_zeros.numel() * self.weight_zeros.element_size()
            
        return total
    
    @classmethod
    def from_linear(
        cls,
        linear: nn.Linear,
        config: QuantConfig
    ) -> 'UnifiedQuantizedLinear':
        """Create quantized layer from existing Linear layer"""
        quantized = cls(
            linear.in_features,
            linear.out_features,
            config,
            bias=linear.bias is not None
        )
        
        # Quantize weight
        with torch.no_grad():
            quantized.quantize_weight(linear.weight.data)
            if linear.bias is not None:
                quantized.bias.data.copy_(linear.bias.data)
        
        return quantized


class ModelQuantizer:
    """
    Utility class to quantize entire models
    
    Usage:
        config = QuantConfig(quant_type=QuantType.INT4)
        quantizer = ModelQuantizer(config)
        quantized_model = quantizer.quantize(model)
    """
    
    def __init__(self, config: QuantConfig):
        self.config = config
    
    def quantize(self, model: nn.Module) -> nn.Module:
        """Quantize all Linear layers in model"""
        count = 0
        
        for name, module in model.named_modules():
            if isinstance(module, nn.Linear):
                # Create quantized replacement
                quantized = UnifiedQuantizedLinear.from_linear(module, self.config)
                
                # Replace in model
                parent_name = ".".join(name.split(".")[:-1])
                child_name = name.split(".")[-1]
                
                if parent_name:
                    parent = dict(model.named_modules())[parent_name]
                else:
                    parent = model
                    
                setattr(parent, child_name, quantized)
                count += 1
        
        print(f"✅ Quantized {count} layers to {self.config.quant_type.value}")
        return model
    
    def estimate_memory_savings(self, model: nn.Module) -> Dict[str, Any]:
        """Estimate memory savings from quantization"""
        original_bytes = 0
        quantized_bytes = 0
        
        for module in model.modules():
            if isinstance(module, nn.Linear):
                original_bytes += module.weight.numel() * 4  # FP32
                quantized_bytes += int(module.weight.numel() * self.config.bytes_per_param)
        
        return {
            "original_mb": original_bytes / 1024 / 1024,
            "quantized_mb": quantized_bytes / 1024 / 1024,
            "compression_ratio": original_bytes / max(quantized_bytes, 1),
            "memory_saved_mb": (original_bytes - quantized_bytes) / 1024 / 1024
        }


def get_quant_type(quant_str: str) -> QuantType:
    """Convert string to QuantType enum"""
    mapping = {
        "fp32": QuantType.FP32,
        "fp16": QuantType.FP16,
        "bf16": QuantType.BF16,
        "fp8": QuantType.FP8_E4M3,
        "fp8_e4m3": QuantType.FP8_E4M3,
        "fp8_e5m2": QuantType.FP8_E5M2,
        "fp4": QuantType.FP4,
        "int8": QuantType.INT8,
        "int4": QuantType.INT4,
        "nf4": QuantType.NF4,
    }
    return mapping.get(quant_str.lower(), QuantType.INT4)


def estimate_model_size(
    num_params: int,
    quant_type: Union[str, QuantType]
) -> Dict[str, float]:
    """
    Estimate model size for different quantization types
    
    Args:
        num_params: Number of model parameters
        quant_type: Quantization type
        
    Returns:
        Dict with size estimates
    """
    if isinstance(quant_type, str):
        quant_type = get_quant_type(quant_type)
    
    bytes_per_param = QUANT_SPECS[quant_type]["bytes_per_param"]
    
    # Add ~10% overhead for scales/zeros
    overhead = 1.1 if quant_type in [QuantType.INT4, QuantType.INT8, QuantType.NF4, QuantType.FP4] else 1.0
    
    size_bytes = num_params * bytes_per_param * overhead
    
    return {
        "params": num_params,
        "quant_type": quant_type.value,
        "size_bytes": size_bytes,
        "size_mb": size_bytes / 1024 / 1024,
        "size_gb": size_bytes / 1024 / 1024 / 1024,
    }


# Convenience exports
__all__ = [
    'QuantType',
    'QuantConfig',
    'QUANT_SPECS',
    'FP8Quantizer',
    'FP4Quantizer',
    'NF4Quantizer',
    'INT4Quantizer',
    'INT8Quantizer',
    'UnifiedQuantizedLinear',
    'ModelQuantizer',
    'get_quant_type',
    'estimate_model_size',
]


if __name__ == "__main__":
    print("=== OMNIMIND Advanced Quantization Test ===\n")
    
    # Test tensor
    test_weight = torch.randn(512, 1024)
    
    for quant_type in QuantType:
        config = QuantConfig(quant_type=quant_type)
        
        # Create and quantize
        layer = UnifiedQuantizedLinear(1024, 512, config)
        layer.quantize_weight(test_weight)
        
        # Dequantize and check error
        reconstructed = layer.dequantize_weight(torch.float32)
        error = (test_weight - reconstructed).abs().mean().item()
        
        mem_mb = layer.memory_usage_bytes() / 1024 / 1024
        
        print(f"{quant_type.value:12} | Memory: {mem_mb:>6.2f} MB | Mean Error: {error:.6f}")
