"""
OMNIMIND Model Registry
Centralized registration for model architectures and specialized behaviors.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Type, Any

class QuantType(Enum):
    NONE = "none"
    INT4 = "int4"  # Omnimind Turbo
    INT8 = "int8"
    FP8 = "fp8"

@dataclass
class ModelVariant:
    org: str
    name: str
    size: str
    arch: str  # llama, mistral, deepseek, omnimind
    quant: QuantType = QuantType.NONE
    tags: List[str] = field(default_factory=list)
    
    @property
    def full_name(self) -> str:
        return f"{self.org}/{self.name}"

MODEL_REGISTRY: Dict[str, ModelVariant] = {}

def register_model(
    org: str,
    name: str,
    size: str,
    arch: str,
    quant: QuantType = QuantType.NONE,
    tags: List[str] = None
):
    """Register a model variant"""
    key = f"{org}/{name}"
    MODEL_REGISTRY[key] = ModelVariant(
        org=org, name=name, size=size, arch=arch, quant=quant, tags=tags or []
    )

def get_model_info(model_id: str) -> Optional[ModelVariant]:
    """Get info for a registered model"""
    return MODEL_REGISTRY.get(model_id)

# ==============================================================================
# Architecture Handling
# ==============================================================================

class ArchitectureHandler:
    """Base handler for model architectures"""
    @staticmethod
    def apply_patches(model: Any):
        pass

class DeepSeekHandler(ArchitectureHandler):
    """DeepSeek-specific optimizations (MoE, Multi-Head Latent Attention)"""
    @staticmethod
    def apply_patches(model: Any):
        print("⚡️ Applying DeepSeek optimizations (MLA + MoE)...")
        # In real impl: Patch attention and experts

class LlamaHandler(ArchitectureHandler):
    """Llama-specific optimizations (RoPE, GQA)"""
    @staticmethod
    def apply_patches(model: Any):
        print("⚡️ Applying Llama optimizations (Fast RoPE)...")
        from omnimind.kernels import fast_rope_embedding
        # Patch RoPE
        # model.layers...self_attn.rope = fast_rope_embedding

ARCH_HANDLERS = {
    "deepseek": DeepSeekHandler,
    "llama": LlamaHandler,
    "mistral": LlamaHandler, # Mistral is compatible
}

def get_arch_handler(arch: str) -> Type[ArchitectureHandler]:
    return ARCH_HANDLERS.get(arch, ArchitectureHandler)

# ==============================================================================
# Pre-register common models
# ==============================================================================

# DeepSeek
register_model("deepseek-ai", "deepseek-coder-6.7b-instruct", "6.7B", "deepseek", tags=["instruct"])
register_model("deepseek-ai", "deepseek-llm-67b-chat", "67B", "deepseek", tags=["chat"])

# Llama-3
register_model("meta-llama", "Meta-Llama-3-8B-Instruct", "8B", "llama", tags=["instruct"])
register_model("meta-llama", "Meta-Llama-3-70B-Instruct", "70B", "llama", tags=["instruct"])

# Omnimind (Ours)
register_model("omnimind", "omnimind-7b-pro", "7B", "omnimind", QuantType.INT4, tags=["turbo"])
