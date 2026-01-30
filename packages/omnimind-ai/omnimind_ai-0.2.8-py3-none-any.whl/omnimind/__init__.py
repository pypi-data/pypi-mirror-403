"""
OMNIMIND - State-Space Language Model
AI ที่รันได้ทุกที่ จำได้ไม่จำกัด เรียนรู้ไม่หยุด

Usage:
    # Install
    pip install omnimind
    
    # Create SSM model from scratch
    from omnimind import create_model
    model = create_model("nano")
    
    # Convert Transformer → SSM
    from omnimind.conversion.advanced_conversion import advanced_transfer
    ssm_model, tokenizer = advanced_transfer("meta-llama/Llama-2-7b-hf")
    
    # Fine-tune SSM model
    from omnimind import FineTuner, FineTuneConfig
    finetuner = FineTuner(model=ssm_model, tokenizer=tokenizer, config=FineTuneConfig())
    finetuner.train(dataset)
"""

__version__ = "0.2.0"
__author__ = "OMNIMIND Team"

# Core imports
from .model.config import (
    OmnimindConfig, get_config, ModelSize, 
    create_custom_config, list_available_sizes, estimate_params
)
from .model.omnimind_model import OmnimindModel, OmnimindForCausalLM, create_model
from .model.ssm_layer import SelectiveSSM, OmnimindBlock

# Pure SSM Architecture - Hybrid removed for stability

# Legacy transformer loader (for conversion)
from .utils.loader import TransformerLoader as ModelLoader, apply_lora, prepare_for_training, LoRAConfig

# FastOmnimindModel (Recommended - Unified high-performance loader)
from .model.fast_base import FastOmnimindModel, load_fast_model

from .utils import (
    get_device_type, get_optimal_device, get_optimal_dtype,
    DEVICE_TYPE, HAS_CUDA, HAS_MPS, HAS_TRITON,
    check_dependencies, ensure_package, print_system_info,
)

# Training imports
from .training.dataset import SimpleTokenizer, TextDataset, StreamingDataset, create_dataloader
from .training.multilingual_tokenizer import MultilingualTokenizer
from .training.trainer import Trainer, TrainingConfig

# Chat template
from .utils.chat_template import OMNIMIND_CHAT_TEMPLATE, format_markdown_code, format_markdown_table, format_multimodal_message

# Multimodal
from .model.multimodal import (
    MultimodalConfig,
    VisionEncoder,
    AudioEncoder,
    VideoEncoder,
    CodeEncoder,
    OmnimindMultimodal,
    preprocess_image,
    preprocess_audio,
    preprocess_video
)

# SSM Fine-tuning imports
from .training.finetune import FineTuner, FineTuneConfig, create_chat_dataset, create_text_dataset

# Turbo Fine-tuning (Unsloth-style, 2-5x faster)
from .training.turbo import TurboFineTuner, TurboConfig, TurboLoRA, turbo_finetune

# Distillation (Transformer → SSM)
from .training.distillation import (
    Distiller, DistillationConfig, 
    list_available_teachers, distill_model, TEACHER_REGISTRY
)

# Mobile Optimization
from .inference.mobile import (
    MobileConfig, MobileInference, MemoryBudget,
    StreamingSSMState, quantize_model, estimate_mobile_memory, save_mobile_format,
    SUPPORTED_QUANT_TYPES
)

# Advanced Quantization
try:
    from .quantization.advanced_quantization import (
        QuantType, QuantConfig, UnifiedQuantizedLinear, ModelQuantizer,
        FP8Quantizer, FP4Quantizer, NF4Quantizer, INT4Quantizer, INT8Quantizer,
        get_quant_type, estimate_model_size
    )
except ImportError:
    pass

# Disk Streaming
try:
    from .inference.disk_streaming import (
        DiskStreamingConfig, DiskStreamingEngine,
        export_for_streaming, estimate_streaming_performance
    )
except ImportError:
    pass

# Turbo Streaming (faster disk inference)
try:
    from .model.turbo_streaming import (
        TurboStreamConfig, TurboStreamingEngine,
        create_turbo_engine, estimate_turbo_performance
    )
except ImportError:
    pass

# Sparse Experts (MoE for efficient inference)
try:
    from .model.sparse_experts import (
        SparseConfig, SparseStreamingEngine,
        estimate_sparse_performance
    )
except ImportError:
    pass

# Ultra-Fast Inference
try:
    from .inference.ultra_fast import (
        UltraFastConfig, UltraFastEngine,
        estimate_ultra_fast_performance
    )
except ImportError:
    pass

# GGUF Export
from .conversion.gguf_export import (
    export_to_gguf, save_gguf_q4_k_m, save_gguf_q5_k_m, 
    save_gguf_q8_0, save_gguf_f16, QUANT_TYPES
)

# Weight Transfer
from .conversion.weight_transfer import (
    WeightTransfer, TransferConfig, transfer_to_omnimind,
    from_qwen, from_llama, from_gemma
)

# Advanced Conversion (Attention → SSM with mathematical approximation)
from .conversion.advanced_conversion import (
    AdvancedWeightTransfer, advanced_transfer as convert_model,
    attention_to_ssm_weights, full_model_conversion,
    convert_and_save_to_sqlite, load_from_sqlite
)

# Low-Memory Streaming Conversion (for 70B-200B models on Kaggle 30GB RAM)
from .conversion.low_memory import (
    # Main functions - use these!
    stream_convert_to_gguf,        # 🚀 Convert huge models with minimal RAM
    stream_convert_layer_by_layer,  # Layer-by-layer for fine-tuning prep
    download_model_for_streaming,   # 📥 Download only what's needed for streaming
    can_convert_on_kaggle,          # Check if model fits in Kaggle RAM
    estimate_model_memory,          # Estimate memory requirements
    convert_native_to_sqlite,       # Convert native format to SQLite
    
    # Memory utilities
    MemoryMonitor,
    get_memory_stats,
    force_garbage_collect,
    memory_efficient_scope,
    
    # Streaming loader
    StreamingWeightLoader,
    StreamingGGUFWriter,
)

# SQLite Storage (FTS5-level disk streaming)
from .storage import (
    SQLiteWeightStorage, WeightStorageConfig,
    create_weight_storage, open_weight_storage
)

# Unified Workflow
from .workflow import (
    OmnimindWorkflow, WorkflowConfig,
    convert_and_train, quick_convert
)

# OMNIMIND Lite (.oml) - Ultra-compact mobile format
from .model.lite import (
    save_lite, load_lite, OMLInference, estimate_lite_size
)

# GPU Optimization
from .inference.gpu_optimization import (
    GPUConfig, optimize_model, OptimizedInference, 
    quick_optimize, to_fp16, to_bf16, compile_model
)

# Memory imports (optional)
try:
    from .memory.memory_manager import MemoryManager
    from .memory.working_memory import WorkingMemory
except ImportError:
    pass

# Cognitive imports (optional)
try:
    from .cognitive.thinking_engine import ThinkingEngine
    from .cognitive.uncertainty_detector import UncertaintyDetector
except ImportError:
    pass

# Real-time
from .cognitive.realtime import RealtimeAgent, RealtimeConfig

# Generation & Creation
from .generation.document_generator import DocumentGenerator, DocumentConfig
from .generation.media_generator import OmnimindCreativeLab, get_creative_tools

# Music & Singing
from .model.music import OmnimindMusic, MusicConfig, SymbolicMusicEncoder, SingingVoiceEncoder

# Tools & Function Calling
from .cognitive.tool_use import ToolAgent, ToolRegistry
from .cognitive.standard_tools import (
    VisionTools, MathTools, CodeInterpreter, Translator, 
    WebSearch, DateTimeTool, get_standard_tools
)

# Server (optional - requires fastapi/pydantic)
try:
    from .server import run_server
except ImportError:
    run_server = None

# CLI (optional - requires fire)
try:
    from .cli import OMNIMIND_CLI
except ImportError:
    OMNIMIND_CLI = None

# DPO & Evaluator
from .training.dpo import DPOTrainer, DPOConfig, train_dpo
from .training.evaluator import Evaluator, evaluate_model

# Pure SSM - No SparseAttention (Hybrid removed)

# Unified Model
from .unified import Omnimind, OmnimindLite, load_omnimind

# Public API
__all__ = [
    "__version__",
    # Config
    "OmnimindConfig", "get_config", "ModelSize", 
    "create_custom_config", "list_available_sizes", "estimate_params",
    # Model
    "OmnimindModel", "OmnimindForCausalLM", "create_model", "SelectiveSSM", "OmnimindBlock",
    # Loader
    "ModelLoader", "apply_lora", "prepare_for_training", "LoRAConfig",
    # Training
    "SimpleTokenizer", "MultilingualTokenizer", "TextDataset", "StreamingDataset", "create_dataloader", "Trainer", "TrainingConfig",
    # SSM Fine-tuning
    "FineTuner", "FineTuneConfig", "create_chat_dataset", "create_text_dataset",
    # Distillation
    "Distiller", "DistillationConfig", "list_available_teachers", "distill_model", "TEACHER_REGISTRY",
    # Mobile Optimization
    "MobileConfig", "MobileInference", "StreamingSSMState", "quantize_model", "estimate_mobile_memory", "save_mobile_format",
    # Chat Template & Markdown
    "OMNIMIND_CHAT_TEMPLATE", "format_markdown_code", "format_markdown_table", "format_multimodal_message",
    # Multimodal
    "MultimodalConfig", "VisionEncoder", "AudioEncoder", "VideoEncoder", "CodeEncoder",
    "OmnimindMultimodal", "preprocess_image", "preprocess_audio", "preprocess_video",
    # Music & Singing
    "OmnimindMusic", "MusicConfig", "SymbolicMusicEncoder", "SingingVoiceEncoder",
    # GGUF Export
    "export_to_gguf", "save_gguf_q4_k_m", "save_gguf_q5_k_m", "save_gguf_q8_0", "save_gguf_f16",
    # Weight Transfer
    "transfer_to_omnimind", "from_qwen", "from_llama", "from_gemma",
    # Advanced Conversion
    "AdvancedWeightTransfer", "convert_model", "attention_to_ssm_weights", "full_model_conversion",
    "convert_and_save_to_sqlite", "load_from_sqlite",
    # Low-Memory Streaming (for Kaggle/Colab with 30GB RAM)
    "stream_convert_to_gguf", "stream_convert_layer_by_layer", "download_model_for_streaming",
    "can_convert_on_kaggle", "estimate_model_memory", "convert_native_to_sqlite",
    "MemoryMonitor", "get_memory_stats", "force_garbage_collect", "memory_efficient_scope",
    "StreamingWeightLoader", "StreamingGGUFWriter",
    # SQLite Storage (FTS5-level)
    "SQLiteWeightStorage", "WeightStorageConfig", "create_weight_storage", "open_weight_storage",
    # Workflow
    "OmnimindWorkflow", "WorkflowConfig", "convert_and_train", "quick_convert",
    # Pure SSM (Hybrid removed)
    "SelectiveSSM",
    # Lite (.oml)
    "save_lite", "load_lite", "OMLInference", "estimate_lite_size",
    # GPU Optimization
    "GPUConfig", "optimize_model", "OptimizedInference", "quick_optimize", "to_fp16", "to_bf16", "compile_model",
    # Turbo Fine-tuning
    "TurboFineTuner", "TurboConfig", "TurboLoRA", "turbo_finetune",
    # Server & CLI
    "run_server", "OMNIMIND_CLI",
    # DPO & Evaluator
    "DPOTrainer", "DPOConfig", "train_dpo", "Evaluator", "evaluate_model",
    # Function Calling & Tools
    "ToolAgent", "ToolRegistry", "VisionTools", "MathTools", "CodeInterpreter", "Translator", 
    "WebSearch", "DateTimeTool", "get_standard_tools",
    # Real-time
    "RealtimeAgent", "RealtimeConfig",
    # Generation & Creation
    "DocumentGenerator", "DocumentConfig", "OmnimindCreativeLab", "get_creative_tools",
    # Unified Model (The "One Model")
    "Omnimind", "OmnimindLite", "load_omnimind",
]

