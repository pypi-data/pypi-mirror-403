"""
OMNIMIND Transformer Model Loader (Legacy)
Load Transformer models from HuggingFace for conversion to SSM
รองรับ: Llama, Gemma, Qwen, Phi, Mistral, etc.

NOTE: This is for legacy compatibility. For SSM models, use:
    from omnimind.conversion.advanced_conversion import advanced_transfer
    ssm_model, tokenizer = advanced_transfer("model-name")
"""
import os
from typing import Optional, Dict, Any, Union, List
from dataclasses import dataclass
import torch
import torch.nn as nn


@dataclass
class ModelInfo:
    """Information about supported models"""
    name: str
    hf_id: str
    type: str  # "causal_lm", "ssm"
    size: str  # "1b", "3b", "7b", etc.
    context_length: int = 4096


# Supported Transformer models for conversion
SUPPORTED_MODELS = {
    # Llama family
    "llama-3.2-1b": ModelInfo("Llama 3.2 1B", "meta-llama/Llama-3.2-1B", "causal_lm", "1b", 131072),
    "llama-3.2-3b": ModelInfo("Llama 3.2 3B", "meta-llama/Llama-3.2-3B", "causal_lm", "3b", 131072),
    
    # Llama family (examples)
    "llama-2-7b": ModelInfo("Llama 2 7B", "meta-llama/Llama-2-7b-hf", "causal_lm", "7b", 4096),
    
    # Gemma family
    "gemma-2-2b": ModelInfo("Gemma 2 2B", "google/gemma-2-2b", "causal_lm", "2b", 8192),
    "gemma-2-9b": ModelInfo("Gemma 2 9B", "google/gemma-2-9b", "causal_lm", "9b", 8192),
    
    # Qwen family
    "qwen2.5-0.5b": ModelInfo("Qwen 2.5 0.5B", "Qwen/Qwen2.5-0.5B", "causal_lm", "0.5b", 32768),
    "qwen2.5-1.5b": ModelInfo("Qwen 2.5 1.5B", "Qwen/Qwen2.5-1.5B", "causal_lm", "1.5b", 32768),
    "qwen2.5-3b": ModelInfo("Qwen 2.5 3B", "Qwen/Qwen2.5-3B", "causal_lm", "3b", 32768),
    
    # Phi family
    "phi-3-mini": ModelInfo("Phi 3 Mini", "microsoft/Phi-3-mini-4k-instruct", "causal_lm", "3.8b", 4096),
    
    # Mistral family
    "mistral-7b": ModelInfo("Mistral 7B", "mistralai/Mistral-7B-v0.3", "causal_lm", "7b", 32768),
}


class TransformerLoader:
    """
    Load Transformer models from HuggingFace for conversion to SSM
    
    Usage:
        loader = TransformerLoader()
        model, tokenizer = loader.load("llama-2-7b")
        
        # Or load by HuggingFace ID directly
        model, tokenizer = loader.load_from_hf("meta-llama/Llama-2-7b-hf")
        
        # Then convert to SSM
        from omnimind.conversion.advanced_conversion import advanced_transfer
        ssm_model, tokenizer = advanced_transfer("meta-llama/Llama-2-7b-hf")
    """
    
    def __init__(self, 
                 device: str = "auto",
                 torch_dtype: str = "auto",
                 load_in_4bit: bool = False,
                 load_in_8bit: bool = False):
        self.device = self._get_device(device)
        self.torch_dtype = self._get_dtype(torch_dtype)
        self.load_in_4bit = load_in_4bit
        self.load_in_8bit = load_in_8bit
    
    def _get_device(self, device: str) -> torch.device:
        if device == "auto":
            if torch.cuda.is_available():
                return torch.device("cuda")
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return torch.device("mps")
            return torch.device("cpu")
        return torch.device(device)
    
    def _get_dtype(self, dtype: str) -> torch.dtype:
        if dtype == "auto":
            if torch.cuda.is_available():
                return torch.bfloat16
            return torch.float32
        dtype_map = {
            "float32": torch.float32,
            "float16": torch.float16,
            "bfloat16": torch.bfloat16,
        }
        return dtype_map.get(dtype, torch.float32)
    
    def load(self, model_name: str, **kwargs) -> tuple:
        """
        Load model by short name
        
        Args:
            model_name: Short name (e.g., "llama-2-7b", "llama-3.2-1b")
            **kwargs: Additional arguments for loading
            
        Returns:
            (model, tokenizer) tuple
        """
        if model_name not in SUPPORTED_MODELS:
            available = list(SUPPORTED_MODELS.keys())
            raise ValueError(f"Unknown model: {model_name}. Available: {available}")
        
        model_info = SUPPORTED_MODELS[model_name]
        return self.load_from_hf(model_info.hf_id, **kwargs)
    
    def load_from_hf(self, model_id: str, **kwargs) -> tuple:
        """
        Load model from HuggingFace by model ID
        
        Args:
            model_id: HuggingFace model ID (e.g., "meta-llama/Llama-2-7b-hf")
            **kwargs: Additional arguments
            
        Returns:
            (model, tokenizer) tuple
        """
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        except ImportError:
            raise ImportError("Please install transformers: pip install transformers")
        
        print(f"🔄 Loading model: {model_id}")
        print(f"   Device: {self.device}")
        print(f"   Dtype: {self.torch_dtype}")
        
        # Quantization config
        quantization_config = None
        if self.load_in_4bit:
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=self.torch_dtype,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
            )
            print("   4-bit quantization enabled")
        elif self.load_in_8bit:
            quantization_config = BitsAndBytesConfig(load_in_8bit=True)
            print("   8-bit quantization enabled")
        
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            trust_remote_code=True,
        )
        
        # Ensure pad token
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # Load model
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=self.torch_dtype,
            device_map="auto" if self.device.type == "cuda" else None,
            quantization_config=quantization_config,
            trust_remote_code=True,
            **kwargs
        )
        
        # Move to device if not using device_map
        if self.device.type != "cuda":
            model = model.to(self.device)
            
        # =========================================================
        # OMNIMIND Optimization Layer (Integration)
        # =========================================================
        try:
            from .registry import get_arch_handler
            # Detect arch from config
            arch_type = getattr(model.config, "model_type", "llama")
            handler = get_arch_handler(arch_type)
            
            # Apply patches (RoPE, CrossEntropy, etc.)
            handler.apply_patches(model)
            print(f"⚡️ Optimized for {arch_type} architecture")
        except Exception as e:
            print(f"⚠️ Optimization failed: {e}")
        # =========================================================
        
        print(f"✅ Model loaded: {model_id}")
        print(f"   Parameters: {sum(p.numel() for p in model.parameters()) / 1e6:.1f}M")
        
        return model, tokenizer
    
    @staticmethod
    def list_models() -> Dict[str, ModelInfo]:
        """List all supported Transformer models"""
        return SUPPORTED_MODELS
    
    @staticmethod
    def print_models():
        """Print supported Transformer models"""
        print("\n📋 Supported Transformer Models for Conversion:\n")
        print(f"{'Name':<20} {'HuggingFace ID':<40} {'Size':<10}")
        print("-" * 70)
        for name, info in SUPPORTED_MODELS.items():
            print(f"{name:<20} {info.hf_id:<40} {info.size:<10}")


class LoRAConfig:
    """LoRA Configuration"""
    def __init__(
        self,
        r: int = 16,
        lora_alpha: int = 32,
        lora_dropout: float = 0.05,
        target_modules: List[str] = None,
        bias: str = "none",
    ):
        self.r = r
        self.lora_alpha = lora_alpha
        self.lora_dropout = lora_dropout
        self.target_modules = target_modules or [
            "in_proj", "out_proj", "x_proj", "dt_proj",  # SSM modules
            "conv1d",  # Convolution layer
        ]
        self.bias = bias


def apply_lora(model: nn.Module, config: LoRAConfig) -> nn.Module:
    """
    Apply LoRA adapters to model for efficient fine-tuning
    
    Args:
        model: Pre-trained model
        config: LoRA configuration
        
    Returns:
        Model with LoRA adapters
    """
    try:
        from peft import get_peft_model, LoraConfig, TaskType
    except ImportError:
        raise ImportError("Please install peft: pip install peft")
    
    peft_config = LoraConfig(
        r=config.r,
        lora_alpha=config.lora_alpha,
        lora_dropout=config.lora_dropout,
        target_modules=config.target_modules,
        bias=config.bias,
        task_type=TaskType.CAUSAL_LM,
    )
    
    model = get_peft_model(model, peft_config)
    
    # Print trainable parameters
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"🔧 LoRA applied:")
    print(f"   Trainable: {trainable_params / 1e6:.2f}M ({100 * trainable_params / total_params:.2f}%)")
    
    return model


def prepare_for_training(model: nn.Module, gradient_checkpointing: bool = True) -> nn.Module:
    """
    Prepare model for training
    
    Args:
        model: Model to prepare
        gradient_checkpointing: Enable gradient checkpointing for memory efficiency
        
    Returns:
        Prepared model
    """
    # Enable gradient checkpointing
    if gradient_checkpointing and hasattr(model, "gradient_checkpointing_enable"):
        model.gradient_checkpointing_enable()
        print("✅ Gradient checkpointing enabled")
    
    # Enable input gradients
    if hasattr(model, "enable_input_require_grads"):
        model.enable_input_require_grads()
    
    return model


if __name__ == "__main__":
    # Print available models
    ModelLoader.print_models()
