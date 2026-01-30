"""OMNIMIND Trainer
Training loop with optimizations and SQLite-based checkpointing

Features:
- Gradient accumulation
- Mixed precision training (FP16/BF16)
- Learning rate scheduling with warmup
- SQLite-based checkpointing (FTS5-level speed)
- Automatic best model tracking
"""
import os
import time
import json
import math
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, field
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR, LambdaLR
from torch.utils.data import DataLoader
from torch.cuda.amp import GradScaler, autocast

# SQLite storage for FTS5-level checkpoint performance
try:
    from omnimind.storage import SQLiteWeightStorage, WeightStorageConfig
    HAS_SQLITE_STORAGE = True
except ImportError:
    HAS_SQLITE_STORAGE = False


@dataclass
class TrainingConfig:
    """Training configuration"""
    # Basic
    output_dir: str = "checkpoints"
    num_epochs: int = 3
    max_steps: int = -1  # -1 = use epochs
    
    # Batch size
    batch_size: int = 8
    gradient_accumulation_steps: int = 4
    
    # Optimizer
    learning_rate: float = 1e-4
    weight_decay: float = 0.01
    max_grad_norm: float = 1.0
    
    # Scheduler
    warmup_steps: int = 500
    lr_scheduler: str = "cosine"  # cosine, linear, constant
    
    # Mixed precision
    fp16: bool = True
    bf16: bool = False
    
    # Logging
    logging_steps: int = 10
    save_steps: int = 500
    eval_steps: int = 500
    
    # Device
    device: str = "auto"
    
    # SQLite Storage (FTS5-level checkpointing)
    use_sqlite_storage: bool = True  # Use SQLite for checkpoints
    sqlite_compression: str = "zstd"  # none, zstd
    sqlite_cache_mb: int = 256  # LRU cache size


class Trainer:
    """
    OMNIMIND Trainer
    
    Features:
    - Gradient accumulation
    - Mixed precision training
    - Learning rate scheduling
    - Checkpointing
    - Logging
    """
    
    def __init__(
        self,
        model: nn.Module,
        train_dataloader: DataLoader,
        config: TrainingConfig,
        eval_dataloader: Optional[DataLoader] = None,
    ):
        self.model = model
        self.train_dataloader = train_dataloader
        self.eval_dataloader = eval_dataloader
        self.config = config
        
        # Setup device
        if config.device == "auto":
            if torch.cuda.is_available():
                self.device = torch.device("cuda")
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                self.device = torch.device("mps")
            else:
                self.device = torch.device("cpu")
        else:
            self.device = torch.device(config.device)
        
        self.model.to(self.device)
        
        # Setup optimizer
        self.optimizer = self._create_optimizer()
        
        # Setup scheduler
        self.scheduler = self._create_scheduler()
        
        # Mixed precision
        self.scaler = GradScaler() if config.fp16 and self.device.type == "cuda" else None
        
        # State
        self.global_step = 0
        self.epoch = 0
        self.best_loss = float('inf')
        
        # Create output directory
        os.makedirs(config.output_dir, exist_ok=True)
        
        # SQLite storage for FTS5-level checkpointing
        self.sqlite_storage = None
        if config.use_sqlite_storage and HAS_SQLITE_STORAGE:
            db_path = os.path.join(config.output_dir, "checkpoints.db")
            storage_config = WeightStorageConfig(
                compression=config.sqlite_compression,
                cache_size_mb=config.sqlite_cache_mb,
            )
            self.sqlite_storage = SQLiteWeightStorage(db_path, storage_config)
            print(f"📦 Using SQLite storage: {db_path}")
    
    def _create_optimizer(self) -> AdamW:
        """Create AdamW optimizer with weight decay"""
        # Separate parameters that should/shouldn't have weight decay
        no_decay = ["bias", "norm", "LayerNorm"]
        
        param_groups = [
            {
                "params": [p for n, p in self.model.named_parameters() 
                          if not any(nd in n for nd in no_decay) and p.requires_grad],
                "weight_decay": self.config.weight_decay,
            },
            {
                "params": [p for n, p in self.model.named_parameters() 
                          if any(nd in n for nd in no_decay) and p.requires_grad],
                "weight_decay": 0.0,
            },
        ]
        
        return AdamW(param_groups, lr=self.config.learning_rate)
    
    def _create_scheduler(self) -> LambdaLR:
        """Create learning rate scheduler with warmup"""
        total_steps = self._get_total_steps()
        warmup_steps = self.config.warmup_steps
        
        def lr_lambda(current_step: int) -> float:
            # Warmup
            if current_step < warmup_steps:
                return float(current_step) / float(max(1, warmup_steps))
            
            # Cosine decay
            if self.config.lr_scheduler == "cosine":
                progress = float(current_step - warmup_steps) / float(max(1, total_steps - warmup_steps))
                return max(0.0, 0.5 * (1.0 + math.cos(math.pi * progress)))
            
            # Linear decay
            elif self.config.lr_scheduler == "linear":
                progress = float(current_step - warmup_steps) / float(max(1, total_steps - warmup_steps))
                return max(0.0, 1.0 - progress)
            
            # Constant
            return 1.0
        
        return LambdaLR(self.optimizer, lr_lambda)
    
    def _get_total_steps(self) -> int:
        """Calculate total training steps"""
        if self.config.max_steps > 0:
            return self.config.max_steps
        
        steps_per_epoch = len(self.train_dataloader) // self.config.gradient_accumulation_steps
        return steps_per_epoch * self.config.num_epochs
    
    def train(self) -> Dict[str, float]:
        """Run training loop"""
        print(f"🚀 Starting training on {self.device}")
        print(f"   Total steps: {self._get_total_steps()}")
        print(f"   Batch size: {self.config.batch_size}")
        print(f"   Gradient accumulation: {self.config.gradient_accumulation_steps}")
        print(f"   Effective batch: {self.config.batch_size * self.config.gradient_accumulation_steps}")
        
        self.model.train()
        
        total_loss = 0.0
        step_loss = 0.0
        start_time = time.time()
        
        for epoch in range(self.config.num_epochs):
            self.epoch = epoch
            print(f"\n📅 Epoch {epoch + 1}/{self.config.num_epochs}")
            
            for step, batch in enumerate(self.train_dataloader):
                # Move to device
                batch = {k: v.to(self.device) for k, v in batch.items()}
                
                # Forward pass
                loss = self._training_step(batch)
                step_loss += loss
                
                # Gradient accumulation
                if (step + 1) % self.config.gradient_accumulation_steps == 0:
                    # Gradient clipping
                    if self.scaler:
                        self.scaler.unscale_(self.optimizer)
                    torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.config.max_grad_norm)
                    
                    # Optimizer step
                    if self.scaler:
                        self.scaler.step(self.optimizer)
                        self.scaler.update()
                    else:
                        self.optimizer.step()
                    
                    self.scheduler.step()
                    self.optimizer.zero_grad()
                    
                    self.global_step += 1
                    total_loss += step_loss / self.config.gradient_accumulation_steps
                    
                    # Logging
                    if self.global_step % self.config.logging_steps == 0:
                        avg_loss = step_loss / self.config.gradient_accumulation_steps
                        lr = self.scheduler.get_last_lr()[0]
                        elapsed = time.time() - start_time
                        steps_per_sec = self.global_step / elapsed
                        
                        print(f"   Step {self.global_step}: loss={avg_loss:.4f}, lr={lr:.2e}, {steps_per_sec:.1f} steps/s")
                    
                    step_loss = 0.0
                    
                    # Save checkpoint
                    if self.global_step % self.config.save_steps == 0:
                        self.save_checkpoint()
                    
                    # Evaluation
                    if self.eval_dataloader and self.global_step % self.config.eval_steps == 0:
                        eval_loss = self.evaluate()
                        print(f"   📊 Eval loss: {eval_loss:.4f}")
                        self.model.train()
                    
                    # Max steps check
                    if self.config.max_steps > 0 and self.global_step >= self.config.max_steps:
                        break
            
            if self.config.max_steps > 0 and self.global_step >= self.config.max_steps:
                break
        
        # Final save
        self.save_checkpoint(final=True)
        
        avg_train_loss = total_loss / self.global_step if self.global_step > 0 else 0
        
        print(f"\n✅ Training complete!")
        print(f"   Total steps: {self.global_step}")
        print(f"   Average loss: {avg_train_loss:.4f}")
        
        return {"train_loss": avg_train_loss}
    
    def _training_step(self, batch: Dict[str, torch.Tensor]) -> float:
        """Single training step"""
        if self.scaler:
            with autocast():
                outputs = self.model(**batch)
                loss = outputs["loss"] / self.config.gradient_accumulation_steps
            self.scaler.scale(loss).backward()
        else:
            outputs = self.model(**batch)
            loss = outputs["loss"] / self.config.gradient_accumulation_steps
            loss.backward()
        
        return loss.item() * self.config.gradient_accumulation_steps
    
    @torch.no_grad()
    def evaluate(self) -> float:
        """Run evaluation"""
        self.model.eval()
        total_loss = 0.0
        num_batches = 0
        
        for batch in self.eval_dataloader:
            batch = {k: v.to(self.device) for k, v in batch.items()}
            outputs = self.model(**batch)
            total_loss += outputs["loss"].item()
            num_batches += 1
        
        return total_loss / num_batches if num_batches > 0 else 0
    
    def save_checkpoint(self, final: bool = False, loss: Optional[float] = None):
        """Save model checkpoint using SQLite or traditional format"""
        # Use SQLite storage if available (FTS5-level speed)
        if self.sqlite_storage is not None:
            metrics = {
                "global_step": self.global_step,
                "epoch": self.epoch,
                "is_final": final,
            }
            
            # Get model config if available
            model_config = None
            if hasattr(self.model, 'config'):
                model_config = vars(self.model.config) if hasattr(self.model.config, '__dict__') else None
            
            checkpoint_id = self.sqlite_storage.save_model(
                self.model,
                model_config=model_config,
                epoch=self.epoch,
                step=self.global_step,
                loss=loss,
                metrics=metrics
            )
            
            # Save optimizer state separately (smaller, changes often)
            opt_path = os.path.join(self.config.output_dir, "optimizer_state.pt")
            torch.save({
                "optimizer": self.optimizer.state_dict(),
                "scheduler": self.scheduler.state_dict(),
                "global_step": self.global_step,
                "epoch": self.epoch,
            }, opt_path)
            
            print(f"   💾 SQLite checkpoint #{checkpoint_id} (step={self.global_step})")
            return
        
        # Fallback to traditional checkpoint
        if final:
            path = os.path.join(self.config.output_dir, "final_model")
        else:
            path = os.path.join(self.config.output_dir, f"checkpoint-{self.global_step}")
        
        os.makedirs(path, exist_ok=True)
        
        # Save model
        torch.save(self.model.state_dict(), os.path.join(path, "model.pt"))
        
        # Save optimizer & scheduler
        torch.save({
            "optimizer": self.optimizer.state_dict(),
            "scheduler": self.scheduler.state_dict(),
            "global_step": self.global_step,
            "epoch": self.epoch,
        }, os.path.join(path, "trainer_state.pt"))
        
        # Save config
        with open(os.path.join(path, "config.json"), "w") as f:
            json.dump(vars(self.config), f, indent=2)
        
        print(f"   💾 Saved checkpoint: {path}")
    
    def load_checkpoint(self, path: str = None, checkpoint_id: int = None, load_best: bool = False):
        """
        Load from checkpoint
        
        Args:
            path: Traditional checkpoint path
            checkpoint_id: SQLite checkpoint ID
            load_best: Load best checkpoint by loss
        """
        # SQLite storage loading
        if self.sqlite_storage is not None:
            if load_best:
                best_cp = self.sqlite_storage.get_best_checkpoint("loss", minimize=True)
                if best_cp:
                    checkpoint_id = best_cp["id"]
                    print(f"   🏆 Loading best checkpoint (loss={best_cp.get('loss', '?')})")
            
            if checkpoint_id is not None or load_best:
                stats = self.sqlite_storage.load_model(self.model, str(self.device))
                print(f"   📂 SQLite load: {stats['loaded']} weights, cache hit rate: {stats['cache_hit_rate']:.1%}")
                
                # Load optimizer state
                opt_path = os.path.join(self.config.output_dir, "optimizer_state.pt")
                if os.path.exists(opt_path):
                    state = torch.load(opt_path, map_location=self.device)
                    self.optimizer.load_state_dict(state["optimizer"])
                    self.scheduler.load_state_dict(state["scheduler"])
                    self.global_step = state["global_step"]
                    self.epoch = state["epoch"]
                return
        
        # Traditional checkpoint loading
        if path:
            self.model.load_state_dict(torch.load(os.path.join(path, "model.pt"), map_location=self.device))
            
            state = torch.load(os.path.join(path, "trainer_state.pt"), map_location=self.device)
            self.optimizer.load_state_dict(state["optimizer"])
            self.scheduler.load_state_dict(state["scheduler"])
            self.global_step = state["global_step"]
            self.epoch = state["epoch"]
            
            print(f"   📂 Loaded checkpoint: {path}")
    
    def get_storage_stats(self) -> Optional[Dict]:
        """Get SQLite storage statistics"""
        if self.sqlite_storage:
            return self.sqlite_storage.get_storage_stats()
        return None
    
    def list_checkpoints(self):
        """List all available checkpoints"""
        if self.sqlite_storage:
            return self.sqlite_storage.list_checkpoints()
        
        # List traditional checkpoints
        checkpoints = []
        for item in os.listdir(self.config.output_dir):
            if item.startswith("checkpoint-"):
                checkpoints.append(item)
        return sorted(checkpoints)
