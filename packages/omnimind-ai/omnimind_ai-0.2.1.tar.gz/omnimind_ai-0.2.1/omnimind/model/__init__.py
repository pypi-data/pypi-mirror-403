# OMNIMIND Model Package
# Unified high-performance model loading and optimization

from .fast_base import FastOmnimindModel, load_fast_model
from omnimind.utils.loader import TransformerLoader as ModelLoader, LoRAConfig, apply_lora, prepare_for_training
from omnimind.utils.chat_template import get_chat_template, TEMPLATES
from omnimind.utils.registry import MODEL_REGISTRY, get_model_info, get_arch_handler

# Import arch-specific patches (auto-registers)
from . import fast_llama
from . import fast_gemma

__all__ = [
    # Primary API
    "FastOmnimindModel",
    "load_fast_model",
    
    # Legacy loader
    "ModelLoader",
    "LoRAConfig",
    "apply_lora",
    "prepare_for_training",
    
    # Templates
    "get_chat_template",
    "TEMPLATES",
    
    # Registry
    "MODEL_REGISTRY",
    "get_model_info",
    "get_arch_handler",
]
