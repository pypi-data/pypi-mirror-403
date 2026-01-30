# OMNIMIND Conversion Package
# Model weight transfer and artifact export tools
# With SQLite storage for FTS5-level disk streaming
# And LOW-MEMORY streaming for 70B-200B models on Kaggle (30GB RAM)

from .weight_transfer import WeightTransfer, TransferConfig
from .gguf_export import export_to_gguf
from .advanced_conversion import (
    advanced_transfer as convert_model, 
    full_model_conversion,
    attention_to_ssm_weights,
    ConversionConfig,
    gpu_accelerated_svd,
    validate_conversion_compatibility,
    compute_conversion_quality_score,
    convert_and_save_to_sqlite,
    load_from_sqlite,
    convert_from_native_format,  # NEW: Convert Native Format → SSM
)

# Low-memory streaming conversion for large models
from .low_memory import (
    # Memory monitoring
    MemoryStats,
    get_memory_stats,
    check_memory_available,
    force_garbage_collect,
    memory_efficient_scope,
    MemoryMonitor,
    
    # Checkpoint handling
    ShardInfo,
    CheckpointIndex,
    find_checkpoint_files,
    
    # Streaming loading
    StreamingWeightLoader,
    
    # Streaming conversion (main functions)
    StreamingGGUFWriter,
    stream_convert_to_gguf,
    stream_convert_layer_by_layer,
    download_model_for_streaming,
    
    # Kaggle-optimized conversion (NO virtual memory support)
    kaggle_safe_convert,
    
    # Storage conversion
    convert_native_to_sqlite,
    
    # Utilities
    estimate_model_memory,
    can_convert_on_kaggle,
)

__all__ = [
    # Standard conversion
    "WeightTransfer",
    "TransferConfig",
    "convert_model",
    "full_model_conversion",
    "attention_to_ssm_weights",
    "ConversionConfig",
    "gpu_accelerated_svd",
    "validate_conversion_compatibility",
    "compute_conversion_quality_score",
    
    # SQLite storage integration
    "convert_and_save_to_sqlite",
    "load_from_sqlite",
    
    # Native Format → SSM conversion (bypass HuggingFace loading)
    "convert_from_native_format",
    
    # GGUF export
    "export_to_gguf",
    
    # === LOW-MEMORY STREAMING (for Kaggle/Colab) ===
    # Memory monitoring
    "MemoryStats",
    "get_memory_stats", 
    "check_memory_available",
    "force_garbage_collect",
    "memory_efficient_scope",
    "MemoryMonitor",
    
    # Checkpoint handling
    "ShardInfo",
    "CheckpointIndex",
    "find_checkpoint_files",
    
    # Streaming loading
    "StreamingWeightLoader",
    
    # Streaming conversion
    "StreamingGGUFWriter",
    "stream_convert_to_gguf",  # 🚀 Main function for large models
    "stream_convert_layer_by_layer",
    "download_model_for_streaming",
    
    # Kaggle-optimized (NO virtual memory)
    "kaggle_safe_convert",  # 🔥 Best for Kaggle Free Tier
    
    # Storage conversion
    "convert_native_to_sqlite",
    
    # Utilities
    "estimate_model_memory",
    "can_convert_on_kaggle",
]
