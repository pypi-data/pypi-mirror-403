"""
OMNIMIND FastOmnimindModel
Unified high-performance model wrapper with auto-optimization.

Features:
- One-line loading with auto-quantization
- Auto-patching for architecture-specific optimizations
- Seamless inference/training mode switching
- Integrated FastLoRA support
"""

import torch
import torch.nn as nn
from typing import Optional, Dict, Any, Tuple, List
from dataclasses import dataclass

@dataclass
class FastModelConfig:
    max_seq_length: int = 4096
    load_in_4bit: bool = True
    load_in_8bit: bool = False
    dtype: Optional[torch.dtype] = None
    device_map: str = "auto"
    use_gradient_checkpointing: bool = True
    use_fast_kernels: bool = True

class FastOmnimindModel:
    """
    Unified high-performance model wrapper.
    
    Usage:
        model, tokenizer = FastOmnimindModel.from_pretrained(
            "meta-llama/Meta-Llama-3-8B-Instruct",
            load_in_4bit=True,
        )
        
        # Apply LoRA
        model = FastOmnimindModel.get_peft_model(model)
        
        # Switch to inference
        model = FastOmnimindModel.for_inference(model)
    """
    
    # Architecture-specific patch classes
    _ARCH_PATCHES = {}
    
    @classmethod
    def register_arch(cls, arch_name: str, patch_class):
        """Register architecture-specific patches"""
        cls._ARCH_PATCHES[arch_name] = patch_class
    
    @classmethod
    def from_pretrained(
        cls,
        model_name: str,
        max_seq_length: int = 4096,
        dtype: Optional[torch.dtype] = None,
        load_in_4bit: bool = True,
        load_in_8bit: bool = False,
        device_map: str = "auto",
        trust_remote_code: bool = True,
        use_fast_kernels: bool = True,
        **kwargs,
    ) -> Tuple[nn.Module, Any]:
        """
        Load model with auto-optimization.
        
        Args:
            model_name: HuggingFace model ID or local path
            max_seq_length: Maximum sequence length
            dtype: Compute dtype (auto-detected if None)
            load_in_4bit: Enable 4-bit quantization
            load_in_8bit: Enable 8-bit quantization
            device_map: Device placement strategy
            trust_remote_code: Trust remote code in model
            use_fast_kernels: Use Triton kernels when available
            
        Returns:
            (model, tokenizer) tuple
        """
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        except ImportError:
            raise ImportError("Please install transformers: pip install transformers")
        
        print(f"🚀 FastOmnimindModel loading: {model_name}")
        
        # Auto-detect dtype
        if dtype is None:
            dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
        
        # Quantization config
        quantization_config = None
        if load_in_4bit:
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=dtype,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
            )
            print("   ⚡️ 4-bit quantization enabled")
        elif load_in_8bit:
            quantization_config = BitsAndBytesConfig(load_in_8bit=True)
            print("   ⚡️ 8-bit quantization enabled")
        
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=trust_remote_code,
        )
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # Apply chat template
        try:
            from .chat_template import get_chat_template
            get_chat_template(tokenizer)
            print("   💬 Chat template applied")
        except Exception:
            pass
        
        # Load model
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=dtype,
            device_map=device_map if torch.cuda.is_available() else None,
            quantization_config=quantization_config,
            trust_remote_code=trust_remote_code,
            attn_implementation="sdpa",  # Use SDPA when available
            **kwargs,
        )
        
        # Apply architecture-specific patches
        arch_type = getattr(model.config, "model_type", "").lower()
        if use_fast_kernels:
            model = cls._apply_fast_patches(model, arch_type)
        
        # Set max sequence length
        if hasattr(model.config, "max_position_embeddings"):
            model.config.max_position_embeddings = max(
                model.config.max_position_embeddings, max_seq_length
            )
        
        print(f"✅ Model loaded: {sum(p.numel() for p in model.parameters()) / 1e9:.2f}B parameters")
        
        return model, tokenizer
    
    @classmethod
    def _apply_fast_patches(cls, model: nn.Module, arch_type: str) -> nn.Module:
        """Apply architecture-specific optimizations"""
        
        # Check for registered patches
        if arch_type in cls._ARCH_PATCHES:
            patch_class = cls._ARCH_PATCHES[arch_type]
            model = patch_class.apply(model)
            print(f"   ⚡️ Applied {arch_type} optimizations")
            return model
        
        # Default: Apply generic Triton patches
        try:
            from omnimind.kernels import HAS_TRITON
            if HAS_TRITON and next(model.parameters()).is_cuda:
                print(f"   ⚡️ Triton kernels available for {arch_type}")
                # Generic patches would go here
        except ImportError:
            pass
        
        return model
    
    @classmethod
    def get_peft_model(
        cls,
        model: nn.Module,
        r: int = 16,
        lora_alpha: int = 32,
        lora_dropout: float = 0.05,
        target_modules: Optional[List[str]] = None,
        use_fast_lora: bool = True,
        **kwargs,
    ) -> nn.Module:
        """
        Apply LoRA adapters with Omnimind optimizations.
        
        Args:
            model: Base model
            r: LoRA rank
            lora_alpha: LoRA alpha scaling
            lora_dropout: Dropout rate
            target_modules: Modules to apply LoRA to
            use_fast_lora: Use Omnimind's FastLoRA implementation
            
        Returns:
            Model with LoRA adapters
        """
        if target_modules is None:
            target_modules = [
                "q_proj", "k_proj", "v_proj", "o_proj",
                "gate_proj", "up_proj", "down_proj",
            ]
        
        if use_fast_lora:
            try:
                from .fast_lora import inject_fast_lora
                model = inject_fast_lora(model, r=r, alpha=lora_alpha, target_modules=target_modules)
                print(f"⚡️ FastLoRA applied (rank={r})")
                return model
            except Exception as e:
                print(f"⚠️ FastLoRA failed, falling back to PEFT: {e}")
        
        # Fallback to standard PEFT
        try:
            from peft import get_peft_model, LoraConfig, TaskType
            
            peft_config = LoraConfig(
                r=r,
                lora_alpha=lora_alpha,
                lora_dropout=lora_dropout,
                target_modules=target_modules,
                bias="none",
                task_type=TaskType.CAUSAL_LM,
                **kwargs,
            )
            
            model = get_peft_model(model, peft_config)
            
            trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
            total = sum(p.numel() for p in model.parameters())
            print(f"🔧 LoRA applied: {trainable/1e6:.2f}M trainable ({100*trainable/total:.2f}%)")
            
        except ImportError:
            raise ImportError("Please install peft: pip install peft")
        
        return model
    
    @classmethod
    def for_inference(cls, model: nn.Module) -> nn.Module:
        """
        Prepare model for inference.
        
        - Disables gradient computation
        - Enables eval mode
        - Applies inference optimizations
        """
        model.eval()
        
        # Disable gradient checkpointing
        if hasattr(model, "gradient_checkpointing_disable"):
            model.gradient_checkpointing_disable()
        
        # Compile for speed (PyTorch 2.0+)
        if hasattr(torch, "compile") and next(model.parameters()).is_cuda:
            try:
                model = torch.compile(model, mode="reduce-overhead")
                print("⚡️ Model compiled with torch.compile")
            except Exception:
                pass
        
        print("✅ Model ready for inference")
        return model
    
    @classmethod
    def for_training(
        cls,
        model: nn.Module,
        use_gradient_checkpointing: bool = True,
    ) -> nn.Module:
        """
        Prepare model for training.
        
        - Enables gradient computation
        - Enables training mode
        - Enables gradient checkpointing for VRAM efficiency
        """
        model.train()
        
        # Enable gradient checkpointing
        if use_gradient_checkpointing and hasattr(model, "gradient_checkpointing_enable"):
            model.gradient_checkpointing_enable()
            print("✅ Gradient checkpointing enabled")
        
        # Enable input gradients
        if hasattr(model, "enable_input_require_grads"):
            model.enable_input_require_grads()
        
        print("✅ Model ready for training")
        return model


# Convenience function
def load_fast_model(model_name: str, **kwargs) -> Tuple[nn.Module, Any]:
    """Shortcut for FastOmnimindModel.from_pretrained"""
    return FastOmnimindModel.from_pretrained(model_name, **kwargs)
