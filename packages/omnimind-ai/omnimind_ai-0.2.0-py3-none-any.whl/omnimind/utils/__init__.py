# OMNIMIND Utilities Package

from .device import (
    get_device_type,
    get_device_count,
    get_optimal_device,
    get_optimal_dtype,
    DEVICE_TYPE,
    DEVICE_COUNT,
    HAS_CUDA,
    HAS_MPS,
    HAS_TRITON,
    is_hip,
    is_mps,
)

from .compat import (
    Version,
    suppress_warnings,
    patch_transformers,
    check_dependencies,
    ensure_package,
    print_system_info,
)

from .packing import (
    pack_sequences,
    create_packing_collator,
    PackedDataset,
)

from .hf_hub import (
    login_hf,
    push_to_hub,
    download_model,
    get_model_info,
    save_pretrained_merged,
)

from .trainer_utils import (
    OmnimindTrainer,
    OmnimindTrainingArguments,
    create_optimizer_with_embedding_lr,
    patch_trainer,
)

from .save_utils import (
    save_model,
    save_merged_model,
    merge_lora_weights,
    save_to_gguf,
)

from .tokenizer_utils import (
    load_tokenizer,
    fix_tokenizer,
    add_special_tokens,
    check_tokenizer,
    fix_chat_template,
    resize_model_embeddings,
    prepare_tokenizer_for_training,
)

from .logging import (
    get_logger,
    setup_logging,
    get_training_logger,
    get_inference_logger,
    get_model_logger,
    get_storage_logger,
    log_model_info,
    log_training_step,
    log_inference_stats,
    LogContext,
    ColoredFormatter,
    JSONFormatter,
)

from .environment import (
    SmartEnvironmentHandler,
    EnvironmentStatus,
    EnvironmentIssue,
    IssueLevel,
    IssueCategory,
    get_environment_handler,
    auto_configure,
    check_and_report,
    ensure_omnimind_ready,
)

__all__ = [
    # Device
    "get_device_type",
    "get_device_count",
    "get_optimal_device",
    "get_optimal_dtype",
    "DEVICE_TYPE",
    "DEVICE_COUNT",
    "HAS_CUDA",
    "HAS_MPS",
    "HAS_TRITON",
    "is_hip",
    "is_mps",
    
    # Compatibility
    "Version",
    "suppress_warnings",
    "patch_transformers",
    "check_dependencies",
    "ensure_package",
    "print_system_info",
    
    # Packing
    "pack_sequences",
    "create_packing_collator",
    "PackedDataset",
    
    # HF Hub
    "login_hf",
    "push_to_hub",
    "download_model",
    "get_model_info",
    "save_pretrained_merged",
    
    # Trainer
    "OmnimindTrainer",
    "OmnimindTrainingArguments",
    "create_optimizer_with_embedding_lr",
    "patch_trainer",
    
    # Save
    "save_model",
    "save_merged_model",
    "merge_lora_weights",
    "save_to_gguf",
    
    # Tokenizer
    "load_tokenizer",
    "fix_tokenizer",
    "add_special_tokens",
    "check_tokenizer",
    "fix_chat_template",
    "resize_model_embeddings",
    "prepare_tokenizer_for_training",
    
    # Logging
    "get_logger",
    "setup_logging",
    "get_training_logger",
    "get_inference_logger",
    "get_model_logger",
    "get_storage_logger",
    "log_model_info",
    "log_training_step",
    "log_inference_stats",
    "LogContext",
    "ColoredFormatter",
    "JSONFormatter",
    
    # Smart Environment Handler
    "SmartEnvironmentHandler",
    "EnvironmentStatus",
    "EnvironmentIssue",
    "IssueLevel",
    "IssueCategory",
    "get_environment_handler",
    "auto_configure",
    "check_and_report",
    "ensure_omnimind_ready",
]
