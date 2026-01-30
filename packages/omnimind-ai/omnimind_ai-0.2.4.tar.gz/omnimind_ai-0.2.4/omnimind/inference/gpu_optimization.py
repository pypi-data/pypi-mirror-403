"""
OMNIMIND GPU Optimization
Maximize performance with Tensor Core, torch.compile, and mixed precision

Optimizations:
1. TF32/FP16/BF16 for Tensor Core usage
2. torch.compile for kernel fusion
3. Flash Attention (if available)
4. Memory efficient gradients
5. CUDA graph capture
"""
import os
from typing import Optional, Literal
from dataclasses import dataclass
import torch
import torch.nn as nn


@dataclass
class GPUConfig:
    """GPU optimization configuration"""
    # Precision
    dtype: Literal["fp32", "tf32", "fp16", "bf16", "fp8"] = "bf16"
    
    # Tensor Core
    allow_tf32: bool = True  # Use TF32 for FP32 ops
    
    # Compilation
    compile_model: bool = True
    compile_mode: Literal["default", "reduce-overhead", "max-autotune"] = "max-autotune"
    
    # Memory
    gradient_checkpointing: bool = True
    memory_efficient_attention: bool = True
    
    # CUDA
    cuda_graphs: bool = False  # Experimental
    channels_last: bool = True  # Better memory layout
    
    # Benchmarking
    cudnn_benchmark: bool = True


def enable_tensor_cores():
    """Enable TF32 for Tensor Core acceleration on FP32 ops"""
    if torch.cuda.is_available():
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        print("✅ TF32 enabled for Tensor Core")


def get_optimal_dtype(device: str = "auto") -> torch.dtype:
    """Get optimal dtype for current GPU"""
    if device == "auto":
        if torch.cuda.is_available():
            # Check GPU capability
            capability = torch.cuda.get_device_capability()
            
            if capability[0] >= 8:  # Ampere or newer
                return torch.bfloat16  # BF16 is better for training
            elif capability[0] >= 7:  # Volta/Turing
                return torch.float16
            else:
                return torch.float32
        else:
            return torch.float32
    
    return torch.float32


def optimize_model(
    model: nn.Module,
    config: Optional[GPUConfig] = None,
    device: str = "auto"
) -> nn.Module:
    """
    Apply all GPU optimizations to model
    
    Args:
        model: OMNIMIND model
        config: GPU configuration
        device: Device to use
        
    Returns:
        Optimized model
        
    Example:
        model = optimize_model(model, GPUConfig(compile_model=True))
    """
    config = config or GPUConfig()
    
    print("🚀 Applying GPU optimizations...")
    
    # 1. Determine device
    if device == "auto":
        if torch.cuda.is_available():
            device = "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"
    
    # 2. Enable Tensor Core (TF32)
    if config.allow_tf32 and device == "cuda":
        enable_tensor_cores()
    
    # 3. Set cuDNN benchmark
    if config.cudnn_benchmark and device == "cuda":
        torch.backends.cudnn.benchmark = True
        print("✅ cuDNN benchmark enabled")
    
    # 4. Convert dtype
    if config.dtype != "fp32":
        dtype_map = {
            "tf32": torch.float32,  # TF32 uses FP32 tensors
            "fp16": torch.float16,
            "bf16": torch.bfloat16,
        }
        dtype = dtype_map.get(config.dtype, torch.float32)
        model = model.to(dtype=dtype)
        print(f"✅ Model converted to {config.dtype.upper()}")
    
    # 5. Move to device
    model = model.to(device)
    print(f"✅ Model moved to {device}")
    
    # 6. Channels last memory format (better for conv ops)
    if config.channels_last and device == "cuda":
        try:
            model = model.to(memory_format=torch.channels_last)
            print("✅ Channels last memory format enabled")
        except:
            pass  # Not all models support this
    
    # 7. Gradient checkpointing
    if config.gradient_checkpointing:
        if hasattr(model, 'gradient_checkpointing_enable'):
            model.gradient_checkpointing_enable()
            print("✅ Gradient checkpointing enabled")
    
    # 8. torch.compile (PyTorch 2.0+)
    if config.compile_model and hasattr(torch, 'compile'):
        try:
            model = torch.compile(model, mode=config.compile_mode)
            print(f"✅ torch.compile enabled (mode={config.compile_mode})")
        except Exception as e:
            print(f"⚠️ torch.compile failed: {e}")
    
    return model


class OptimizedInference:
    """
    GPU-optimized inference wrapper
    
    Features:
    - Automatic mixed precision
    - torch.compile
    - CUDA graphs (optional)
    - Batched generation
    """
    
    def __init__(
        self,
        model: nn.Module,
        config: Optional[GPUConfig] = None
    ):
        self.config = config or GPUConfig()
        self.model = optimize_model(model, self.config)
        self.device = next(model.parameters()).device
        
        # Determine autocast dtype
        self.autocast_dtype = {
            "fp16": torch.float16,
            "bf16": torch.bfloat16,
            "tf32": torch.float32,
            "fp32": torch.float32,
        }.get(self.config.dtype, torch.float16)
        
        # CUDA graph capture (experimental)
        self.cuda_graph = None
        self.static_input = None
        self.static_output = None
    
    @torch.inference_mode()
    def forward(self, input_ids: torch.Tensor) -> torch.Tensor:
        """Optimized forward pass"""
        input_ids = input_ids.to(self.device)
        
        # Use autocast for mixed precision
        if self.device.type == "cuda":
            with torch.cuda.amp.autocast(dtype=self.autocast_dtype):
                return self.model(input_ids)
        else:
            return self.model(input_ids)
    
    def generate(
        self,
        input_ids: torch.Tensor,
        max_new_tokens: int = 100,
        temperature: float = 1.0,
        top_p: float = 0.9
    ) -> torch.Tensor:
        """Optimized generation"""
        input_ids = input_ids.to(self.device)
        
        with torch.inference_mode():
            if self.device.type == "cuda":
                with torch.cuda.amp.autocast(dtype=self.autocast_dtype):
                    return self._generate_tokens(
                        input_ids, max_new_tokens, temperature, top_p
                    )
            else:
                return self._generate_tokens(
                    input_ids, max_new_tokens, temperature, top_p
                )
    
    def _generate_tokens(self, input_ids, max_new_tokens, temperature, top_p):
        """Token generation loop"""
        generated = input_ids
        
        for _ in range(max_new_tokens):
            outputs = self.model(generated)
            logits = outputs["logits"] if isinstance(outputs, dict) else outputs
            
            next_logits = logits[:, -1, :] / temperature
            
            # Top-p sampling
            sorted_logits, sorted_indices = torch.sort(next_logits, descending=True)
            probs = torch.softmax(sorted_logits, dim=-1)
            cumsum = torch.cumsum(probs, dim=-1)
            
            mask = cumsum > top_p
            mask[:, 1:] = mask[:, :-1].clone()
            mask[:, 0] = False
            
            sorted_logits[mask] = float('-inf')
            probs = torch.softmax(sorted_logits, dim=-1)
            
            next_token = torch.multinomial(probs, 1)
            next_token = sorted_indices.gather(-1, next_token)
            
            generated = torch.cat([generated, next_token], dim=-1)
            
            # Check EOS (assuming 2 is EOS)
            if (next_token == 2).all():
                break
        
        return generated
    
    def benchmark(self, input_size: tuple = (1, 128), warmup: int = 10, runs: int = 100):
        """Benchmark inference speed"""
        import time
        
        # Create dummy input
        dummy = torch.randint(0, 1000, input_size, device=self.device)
        
        # Warmup
        for _ in range(warmup):
            _ = self.forward(dummy)
        
        if self.device.type == "cuda":
            torch.cuda.synchronize()
        
        # Benchmark
        start = time.perf_counter()
        for _ in range(runs):
            _ = self.forward(dummy)
        
        if self.device.type == "cuda":
            torch.cuda.synchronize()
        
        elapsed = time.perf_counter() - start
        tokens_per_sec = (runs * input_size[1]) / elapsed
        
        print(f"\n📊 Benchmark Results:")
        print(f"   Input: {input_size}")
        print(f"   Runs: {runs}")
        print(f"   Time: {elapsed:.2f}s")
        print(f"   Throughput: {tokens_per_sec:.0f} tokens/sec")
        
        return tokens_per_sec


def quick_optimize(model: nn.Module) -> nn.Module:
    """
    Quick one-liner optimization
    
    Example:
        model = quick_optimize(model)
    """
    return optimize_model(model, GPUConfig())


# Convenience functions
def to_fp16(model: nn.Module) -> nn.Module:
    """Convert model to FP16"""
    return optimize_model(model, GPUConfig(dtype="fp16", compile_model=False))


def to_bf16(model: nn.Module) -> nn.Module:
    """Convert model to BF16"""
    return optimize_model(model, GPUConfig(dtype="bf16", compile_model=False))


def compile_model(model: nn.Module, mode: str = "max-autotune") -> nn.Module:
    """Compile model with torch.compile"""
    return optimize_model(model, GPUConfig(dtype="fp32", compile_model=True, compile_mode=mode))


if __name__ == "__main__":
    print("GPU Optimization Example:")
    print()
    print("  from omnimind import create_model")
    print("  from omnimind.gpu import optimize_model, GPUConfig")
    print()
    print("  model = create_model('micro')")
    print("  model = optimize_model(model, GPUConfig(")
    print("      dtype='bf16',")
    print("      compile_model=True,")
    print("      compile_mode='max-autotune'")
    print("  ))")
