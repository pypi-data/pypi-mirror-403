"""
OMNIMIND SSM Fine-tuning Module
Fine-tune OMNIMIND SSM models only
"""
import os
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass, field
import torch
import torch.nn as nn
from torch.utils.data import DataLoader


@dataclass
class FineTuneConfig:
    """SSM Fine-tuning configuration"""
    # Output
    output_dir: str = "outputs"
    
    # Training
    num_epochs: int = 3
    max_steps: int = -1
    batch_size: int = 4
    gradient_accumulation_steps: int = 4
    
    # Optimizer
    learning_rate: float = 2e-4
    weight_decay: float = 0.01
    max_grad_norm: float = 1.0
    
    # Scheduler
    warmup_ratio: float = 0.03
    lr_scheduler_type: str = "cosine"
    
    # LoRA (if using)
    use_lora: bool = True
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    lora_target_modules: list = field(default_factory=lambda: [
        "in_proj", "out_proj", "x_proj", "dt_proj",  # SSM modules
        "conv1d",  # Convolution layer
    ])
    
    # Memory optimization
    gradient_checkpointing: bool = True
    fp16: bool = True
    bf16: bool = False
    
    # Logging
    logging_steps: int = 10
    save_steps: int = 500
    eval_steps: int = 500
    
    # Data
    max_seq_length: int = 2048
    packing: bool = True  # Pack multiple samples into one sequence


class FineTuner:
    """
    Fine-tune OMNIMIND SSM models only
    
    Two modes:
    1. LoRA Fine-tuning (memory efficient, recommended)
    2. Full Fine-tuning (requires more GPU memory)
    
    Usage:
        from omnimind import FineTuner, FineTuneConfig
        
        # Convert Transformer → SSM first
        ssm_model = convert_transformer_to_ssm("meta-llama/Llama-2-7b-hf")
        
        # Then fine-tune SSM
        finetuner = FineTuner(
            model=ssm_model,
            tokenizer=tokenizer,
            config=FineTuneConfig(use_lora=True)
        )
        finetuner.train(dataset)
    """
    
    def __init__(
        self,
        model: nn.Module = None,
        tokenizer = None,
        config: FineTuneConfig = None,
        device: str = "auto",
    ):
        self.config = config or FineTuneConfig()
        self.model = model
        self.tokenizer = tokenizer
        self.device = device
        
        if self.model is None:
            raise ValueError("Must provide an OMNIMIND SSM model")
        if self.tokenizer is None:
            raise ValueError("Must provide a tokenizer")
        
        self._is_loaded = False
    
    def setup_for_training(self):
        """Setup SSM model for training"""
        try:
            # Try to import from utils, fallback to local implementation
            try:
                from omnimind.utils.loader import apply_lora, prepare_for_training, LoRAConfig
            except ImportError:
                # Fallback implementations
                def apply_lora(model, lora_config):
                    """Fallback LoRA implementation"""
                    print("⚠️ LoRA not available in this installation")
                    return model
                
                def prepare_for_training(model, gradient_checkpointing=True):
                    """Fallback training preparation"""
                    if gradient_checkpointing and hasattr(model, 'gradient_checkpointing_enable'):
                        model.gradient_checkpointing_enable()
                    return model
                
                class LoRAConfig:
                    def __init__(self, r=16, lora_alpha=32, lora_dropout=0.05, target_modules=None):
                        self.r = r
                        self.lora_alpha = lora_alpha
                        self.lora_dropout = lora_dropout
                        self.target_modules = target_modules or []
        except ImportError:
            raise ImportError("Please install omnimind utils: pip install omnimind[utils]")
        
        # Move model to device
        if self.device == "auto":
            if torch.cuda.is_available():
                self.device = "cuda"
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                self.device = "mps"
            else:
                self.device = "cpu"
        
        self.model = self.model.to(self.device)
        
        # Apply LoRA if configured
        if self.config.use_lora:
            try:
                lora_config = LoRAConfig(
                    r=self.config.lora_r,
                    lora_alpha=self.config.lora_alpha,
                    lora_dropout=self.config.lora_dropout,
                    target_modules=self.config.lora_target_modules,
                )
                self.model = apply_lora(self.model, lora_config)
                print("✅ LoRA applied successfully")
            except ImportError as e:
                print("⚠️ LoRA not available (peft not installed)")
                print("   To enable LoRA: pip install peft")
                print("   Continuing without LoRA...")
            except Exception as e:
                print(f"⚠️ LoRA application failed: {e}")
                print("   Continuing without LoRA...")
        
        # Prepare for training
        self.model = prepare_for_training(
            self.model, 
            gradient_checkpointing=self.config.gradient_checkpointing
        )
        
        self._is_loaded = True
        return self
    
    def train(self, train_dataset, eval_dataset=None):
        """
        Train/Fine-tune the model
        
        Args:
            train_dataset: Training dataset
            eval_dataset: Optional evaluation dataset
            
        Returns:
            Training results
        """
        if not self._is_loaded:
            self.setup_for_training()
        
        try:
            from transformers import Trainer, TrainingArguments, DataCollatorForLanguageModeling
        except ImportError:
            raise ImportError("Please install transformers: pip install transformers")
        
        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False,  # Causal LM
        )
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=self.config.output_dir,
            num_train_epochs=self.config.num_epochs,
            max_steps=self.config.max_steps if self.config.max_steps > 0 else -1,
            per_device_train_batch_size=self.config.batch_size,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            learning_rate=self.config.learning_rate,
            weight_decay=self.config.weight_decay,
            max_grad_norm=self.config.max_grad_norm,
            warmup_ratio=self.config.warmup_ratio,
            lr_scheduler_type=self.config.lr_scheduler_type,
            fp16=self.config.fp16 and torch.cuda.is_available(),
            bf16=self.config.bf16 and torch.cuda.is_available(),
            logging_steps=self.config.logging_steps,
            save_steps=self.config.save_steps,
            eval_steps=self.config.eval_steps if eval_dataset else None,
            evaluation_strategy="steps" if eval_dataset else "no",
            save_total_limit=3,
            report_to="none",  # Disable wandb by default
        )
        
        # Create trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            data_collator=data_collator,
        )
        
        print("\n🚀 Starting SSM fine-tuning...")
        print(f"   Model: {type(self.model).__name__}")
        print(f"   LoRA: {self.config.use_lora}")
        print(f"   Epochs: {self.config.num_epochs}")
        print(f"   Batch size: {self.config.batch_size * self.config.gradient_accumulation_steps}")
        
        # Train
        result = trainer.train()
        
        # Save final model
        self.save(os.path.join(self.config.output_dir, "final"))
        
        print(f"\n✅ Fine-tuning complete!")
        print(f"   Model saved to: {self.config.output_dir}")
        
        return result
    
    def save(self, path: str):
        """Save the fine-tuned model"""
        os.makedirs(path, exist_ok=True)
        
        # Save model
        self.model.save_pretrained(path)
        
        # Save tokenizer
        self.tokenizer.save_pretrained(path)
        
        print(f"💾 Saved to: {path}")
    
    def push_to_hub(self, repo_id: str, private: bool = True):
        """Push model to HuggingFace Hub"""
        self.model.push_to_hub(repo_id, private=private)
        self.tokenizer.push_to_hub(repo_id, private=private)
        print(f"🚀 Pushed to: https://huggingface.co/{repo_id}")


def create_chat_dataset(
    data: list,
    tokenizer,
    max_length: int = 2048,
    system_prompt: str = None,
):
    """
    Create dataset from chat-format data
    
    Args:
        data: List of conversations, each is a list of {"role", "content"} dicts
        tokenizer: Tokenizer
        max_length: Maximum sequence length
        system_prompt: Optional system prompt
        
    Returns:
        Dataset ready for training
    """
    from torch.utils.data import Dataset
    
    class ChatDataset(Dataset):
        def __init__(self, data, tokenizer, max_length, system_prompt):
            self.data = data
            self.tokenizer = tokenizer
            self.max_length = max_length
            self.system_prompt = system_prompt
        
        def __len__(self):
            return len(self.data)
        
        def __getitem__(self, idx):
            conversation = self.data[idx]
            
            # Add system prompt if provided
            if self.system_prompt:
                conversation = [{"role": "system", "content": self.system_prompt}] + conversation
            
            # Apply chat template
            if hasattr(self.tokenizer, "apply_chat_template"):
                text = self.tokenizer.apply_chat_template(
                    conversation,
                    tokenize=False,
                    add_generation_prompt=False,
                )
            else:
                # Fallback
                text = "\n".join([f"{m['role']}: {m['content']}" for m in conversation])
            
            # Tokenize
            encoding = self.tokenizer(
                text,
                truncation=True,
                max_length=self.max_length,
                padding="max_length",
                return_tensors="pt",
            )
            
            return {
                "input_ids": encoding["input_ids"].squeeze(),
                "attention_mask": encoding["attention_mask"].squeeze(),
                "labels": encoding["input_ids"].squeeze(),
            }
    
    return ChatDataset(data, tokenizer, max_length, system_prompt)


def create_text_dataset(
    texts: list,
    tokenizer,
    max_length: int = 2048,
):
    """
    Create dataset from plain texts
    
    Args:
        texts: List of text strings
        tokenizer: Tokenizer
        max_length: Maximum sequence length
        
    Returns:
        Dataset ready for training
    """
    from torch.utils.data import Dataset
    
    class TextDataset(Dataset):
        def __init__(self, texts, tokenizer, max_length):
            self.texts = texts
            self.tokenizer = tokenizer
            self.max_length = max_length
        
        def __len__(self):
            return len(self.texts)
        
        def __getitem__(self, idx):
            text = self.texts[idx]
            
            encoding = self.tokenizer(
                text,
                truncation=True,
                max_length=self.max_length,
                padding="max_length",
                return_tensors="pt",
            )
            
            return {
                "input_ids": encoding["input_ids"].squeeze(),
                "attention_mask": encoding["attention_mask"].squeeze(),
                "labels": encoding["input_ids"].squeeze(),
            }
    
    return TextDataset(texts, tokenizer, max_length)
