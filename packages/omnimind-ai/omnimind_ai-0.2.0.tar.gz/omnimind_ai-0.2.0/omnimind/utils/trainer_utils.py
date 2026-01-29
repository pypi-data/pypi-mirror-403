"""
OMNIMIND Trainer Utilities
Enhanced training with gradient fixes, embedding LR, and memory optimization.
"""

import torch
import torch.nn as nn
from typing import Optional, Dict, Any, List
import logging

__all__ = [
    "OmnimindTrainer",
    "OmnimindTrainingArguments",
    "create_optimizer_with_embedding_lr",
    "patch_trainer",
]

logger = logging.getLogger("omnimind.trainer")

class OmnimindTrainingArguments:
    """
    Extended training arguments with Omnimind-specific options.
    
    Adds:
    - embedding_learning_rate: Separate LR for embeddings (usually lower)
    - use_gradient_checkpointing: Enable gradient checkpointing
    - gradient_accumulation_fix: Fix for gradient accumulation issues
    """
    
    def __init__(
        self,
        output_dir: str = "./outputs",
        num_train_epochs: int = 3,
        per_device_train_batch_size: int = 2,
        gradient_accumulation_steps: int = 4,
        learning_rate: float = 2e-4,
        embedding_learning_rate: Optional[float] = None,
        weight_decay: float = 0.01,
        warmup_steps: int = 10,
        logging_steps: int = 10,
        save_steps: int = 100,
        fp16: bool = False,
        bf16: bool = False,
        max_grad_norm: float = 1.0,
        use_gradient_checkpointing: bool = True,
        optim: str = "adamw_8bit",
        seed: int = 42,
        **kwargs,
    ):
        self.output_dir = output_dir
        self.num_train_epochs = num_train_epochs
        self.per_device_train_batch_size = per_device_train_batch_size
        self.gradient_accumulation_steps = gradient_accumulation_steps
        self.learning_rate = learning_rate
        self.embedding_learning_rate = embedding_learning_rate or (learning_rate * 0.1)
        self.weight_decay = weight_decay
        self.warmup_steps = warmup_steps
        self.logging_steps = logging_steps
        self.save_steps = save_steps
        self.fp16 = fp16
        self.bf16 = bf16
        self.max_grad_norm = max_grad_norm
        self.use_gradient_checkpointing = use_gradient_checkpointing
        self.optim = optim
        self.seed = seed
        self.extra_args = kwargs
    
    def to_hf_args(self):
        """Convert to HuggingFace TrainingArguments"""
        try:
            from transformers import TrainingArguments
            return TrainingArguments(
                output_dir=self.output_dir,
                num_train_epochs=self.num_train_epochs,
                per_device_train_batch_size=self.per_device_train_batch_size,
                gradient_accumulation_steps=self.gradient_accumulation_steps,
                learning_rate=self.learning_rate,
                weight_decay=self.weight_decay,
                warmup_steps=self.warmup_steps,
                logging_steps=self.logging_steps,
                save_steps=self.save_steps,
                fp16=self.fp16,
                bf16=self.bf16,
                max_grad_norm=self.max_grad_norm,
                optim=self.optim,
                seed=self.seed,
                **self.extra_args,
            )
        except ImportError:
            raise ImportError("transformers required: pip install transformers")

def create_optimizer_with_embedding_lr(
    model: nn.Module,
    learning_rate: float = 2e-4,
    embedding_lr: float = 5e-5,
    weight_decay: float = 0.01,
):
    """
    Create optimizer with separate learning rate for embeddings.
    
    Embeddings often benefit from lower learning rates to prevent
    catastrophic forgetting.
    
    Args:
        model: The model
        learning_rate: Main learning rate
        embedding_lr: Learning rate for embedding layers
        weight_decay: Weight decay
        
    Returns:
        Optimizer
    """
    # Separate parameters
    embedding_params = []
    other_params = []
    
    for name, param in model.named_parameters():
        if not param.requires_grad:
            continue
            
        if "embed" in name.lower() or "lm_head" in name.lower():
            embedding_params.append(param)
            logger.debug(f"Embedding LR for: {name}")
        else:
            other_params.append(param)
    
    param_groups = [
        {"params": other_params, "lr": learning_rate, "weight_decay": weight_decay},
        {"params": embedding_params, "lr": embedding_lr, "weight_decay": weight_decay},
    ]
    
    # Try to use 8-bit optimizer
    try:
        import bitsandbytes as bnb
        optimizer = bnb.optim.AdamW8bit(param_groups)
        logger.info("Using AdamW8bit optimizer")
    except ImportError:
        optimizer = torch.optim.AdamW(param_groups)
        logger.info("Using standard AdamW optimizer")
    
    return optimizer

class OmnimindTrainer:
    """
    Enhanced trainer with Omnimind optimizations.
    
    Features:
    - Separate embedding learning rate
    - Gradient checkpointing
    - Memory optimization
    - TRL/SFT compatibility
    """
    
    def __init__(
        self,
        model: nn.Module,
        args: OmnimindTrainingArguments,
        train_dataset,
        tokenizer = None,
        data_collator = None,
        **kwargs,
    ):
        self.model = model
        self.args = args
        self.train_dataset = train_dataset
        self.tokenizer = tokenizer
        self.data_collator = data_collator
        self.kwargs = kwargs
        
        # Create optimizer with embedding LR
        self.optimizer = create_optimizer_with_embedding_lr(
            model,
            learning_rate=args.learning_rate,
            embedding_lr=args.embedding_learning_rate,
            weight_decay=args.weight_decay,
        )
        
        # Enable gradient checkpointing
        if args.use_gradient_checkpointing:
            if hasattr(model, "gradient_checkpointing_enable"):
                model.gradient_checkpointing_enable()
                logger.info("Gradient checkpointing enabled")
    
    def train(self):
        """Run training using HuggingFace Trainer internally"""
        try:
            from transformers import Trainer
            
            hf_trainer = Trainer(
                model=self.model,
                args=self.args.to_hf_args(),
                train_dataset=self.train_dataset,
                tokenizer=self.tokenizer,
                data_collator=self.data_collator,
                optimizers=(self.optimizer, None),
                **self.kwargs,
            )
            
            return hf_trainer.train()
            
        except ImportError:
            raise ImportError("transformers required: pip install transformers")

def patch_trainer():
    """
    Apply compatibility patches to TRL/Transformers trainers.
    
    Call this early in your script to fix common issues.
    """
    try:
        import trl
        from trl import SFTTrainer
        
        # Patch gradient accumulation issue
        original_init = SFTTrainer.__init__
        
        def patched_init(self, *args, **kwargs):
            # Ensure dataset_num_proc is set
            if "dataset_num_proc" not in kwargs:
                kwargs["dataset_num_proc"] = 4
            return original_init(self, *args, **kwargs)
        
        SFTTrainer.__init__ = patched_init
        logger.debug("Patched SFTTrainer")
        
    except ImportError:
        pass
    
    try:
        import transformers
        
        # Patch enable_input_require_grads for vision models
        original = transformers.PreTrainedModel.enable_input_require_grads
        
        def patched_enable(self):
            try:
                return original(self)
            except NotImplementedError:
                def hook(module, input, output):
                    if hasattr(output, "requires_grad_"):
                        output.requires_grad_(True)
                    elif isinstance(output, tuple) and hasattr(output[0], "requires_grad_"):
                        output[0].requires_grad_(True)
                
                self.get_input_embeddings().register_forward_hook(hook)
        
        transformers.PreTrainedModel.enable_input_require_grads = patched_enable
        logger.debug("Patched enable_input_require_grads")
        
    except (ImportError, AttributeError):
        pass

# Auto-patch on import
patch_trainer()
