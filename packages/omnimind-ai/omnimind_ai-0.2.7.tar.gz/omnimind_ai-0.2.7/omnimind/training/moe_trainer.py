"""
OMNIMIND MoE Training Pipeline
Training MoE-SSM models for ultra-fast inference

=== TRAINING WORKFLOW ===

1. Create MoE-SSM model (moe_ssm.py)
2. Train with this trainer
3. Convert to mobile format (moe_converter.py)
4. Deploy with ultra_fast.py → 50+ tok/s!

=== KEY TRAINING CONSIDERATIONS ===

1. Load Balancing Loss
   - Experts should be used uniformly
   - Prevents "dead experts" problem

2. Router Stability
   - Z-loss prevents very large routing logits
   - Helps convergence

3. Gradient Scaling
   - Different scales for router vs experts
   - Prevents router domination

4. Data Efficiency
   - MoE needs more data than dense
   - Use large, diverse datasets
"""

import os
import math
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Tuple, Union, Callable
from pathlib import Path
import json
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingLR
import torch.distributed as dist
from contextlib import nullcontext

try:
    from omnimind.model.moe_ssm import MoESSMModel, MoESSMConfig, create_moe_ssm_model
except ImportError:
    from moe_ssm import MoESSMModel, MoESSMConfig, create_moe_ssm_model


@dataclass
class MoETrainingConfig:
    """Configuration for MoE-SSM training"""
    
    # Model
    model_size: str = "7b"
    num_experts: int = 64
    top_k: int = 2
    
    # Training
    batch_size: int = 8
    gradient_accumulation_steps: int = 8
    max_steps: int = 100000
    warmup_steps: int = 2000
    
    # Learning rates
    learning_rate: float = 3e-4
    router_lr_multiplier: float = 0.1  # Lower LR for router
    weight_decay: float = 0.1
    
    # Loss weights
    aux_loss_weight: float = 0.01  # Weight for load balancing losses
    
    # Sequence length
    max_seq_len: int = 2048
    
    # Optimization
    use_gradient_checkpointing: bool = True
    use_mixed_precision: bool = True
    grad_clip: float = 1.0
    
    # Expert parallelism
    expert_parallel: bool = False
    expert_parallel_size: int = 1
    
    # Logging
    log_interval: int = 10
    eval_interval: int = 500
    save_interval: int = 1000
    
    # Paths
    output_dir: str = "outputs/moe_ssm"
    resume_from: Optional[str] = None


class MoETrainer:
    """
    Trainer for MoE-SSM Models
    
    Handles:
    - Load balancing losses
    - Router gradient scaling
    - Expert parallelism
    - Checkpointing
    """
    
    def __init__(
        self,
        model: MoESSMModel,
        config: MoETrainingConfig,
        train_dataloader: DataLoader,
        eval_dataloader: Optional[DataLoader] = None
    ):
        self.model = model
        self.config = config
        self.train_dataloader = train_dataloader
        self.eval_dataloader = eval_dataloader
        
        # Setup device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = self.model.to(self.device)
        
        # Setup optimizer with different LR for router
        self.optimizer = self._create_optimizer()
        
        # Setup scheduler
        self.scheduler = CosineAnnealingLR(
            self.optimizer,
            T_max=config.max_steps - config.warmup_steps,
            eta_min=config.learning_rate * 0.1
        )
        
        # Mixed precision
        self.scaler = torch.amp.GradScaler(device='cuda') if config.use_mixed_precision else None
        
        # Gradient checkpointing
        if config.use_gradient_checkpointing:
            self.model.gradient_checkpointing_enable() if hasattr(self.model, 'gradient_checkpointing_enable') else None
        
        # Training state
        self.step = 0
        self.best_loss = float('inf')
        
        # Create output dir
        os.makedirs(config.output_dir, exist_ok=True)
        
        print(f"🚀 MoE Trainer initialized")
        print(f"   Model: {config.model_size}")
        print(f"   Experts: {config.num_experts} (top-{config.top_k})")
        print(f"   Device: {self.device}")
    
    def _create_optimizer(self) -> AdamW:
        """Create optimizer with separate param groups"""
        # Separate router parameters for lower learning rate
        router_params = []
        other_params = []
        
        for name, param in self.model.named_parameters():
            if 'router' in name or 'gate' in name:
                router_params.append(param)
            else:
                other_params.append(param)
        
        param_groups = [
            {
                "params": other_params,
                "lr": self.config.learning_rate,
                "weight_decay": self.config.weight_decay
            },
            {
                "params": router_params,
                "lr": self.config.learning_rate * self.config.router_lr_multiplier,
                "weight_decay": 0.0  # No weight decay for router
            }
        ]
        
        return AdamW(param_groups, betas=(0.9, 0.95))
    
    def _compute_loss(
        self,
        logits: torch.Tensor,
        labels: torch.Tensor,
        aux_losses: Dict[str, torch.Tensor]
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        """Compute total loss including auxiliary losses"""
        # Main language modeling loss
        shift_logits = logits[:, :-1, :].contiguous()
        shift_labels = labels[:, 1:].contiguous()
        
        lm_loss = F.cross_entropy(
            shift_logits.view(-1, shift_logits.size(-1)),
            shift_labels.view(-1),
            ignore_index=-100
        )
        
        # Add auxiliary losses
        total_loss = lm_loss
        loss_dict = {"lm_loss": lm_loss.item()}
        
        for name, loss in aux_losses.items():
            if isinstance(loss, torch.Tensor) and loss.requires_grad:
                weighted_loss = loss * self.config.aux_loss_weight
                total_loss = total_loss + weighted_loss
                loss_dict[name] = loss.item()
        
        loss_dict["total_loss"] = total_loss.item()
        
        return total_loss, loss_dict
    
    def _warmup_lr(self):
        """Linear warmup"""
        if self.step < self.config.warmup_steps:
            lr_scale = self.step / self.config.warmup_steps
            for param_group in self.optimizer.param_groups:
                param_group['lr'] = param_group['lr'] * lr_scale
    
    def train_step(self, batch: Dict[str, torch.Tensor]) -> Dict[str, float]:
        """Single training step"""
        self.model.train()
        
        input_ids = batch["input_ids"].to(self.device)
        labels = batch.get("labels", input_ids).to(self.device)
        
        # Mixed precision context
        ctx = torch.autocast(device_type=str(self.device), dtype=torch.bfloat16) if self.config.use_mixed_precision else nullcontext()
        
        with ctx:
            # Forward pass
            outputs = self.model(input_ids, training=True)
            
            # Compute loss
            loss, loss_dict = self._compute_loss(
                outputs["logits"],
                labels,
                outputs.get("aux_losses", {})
            )
            
            # Scale for gradient accumulation
            loss = loss / self.config.gradient_accumulation_steps
        
        # Backward pass
        if self.scaler:
            self.scaler.scale(loss).backward()
        else:
            loss.backward()
        
        return loss_dict
    
    def train(self):
        """Main training loop"""
        print(f"🏃 Starting training for {self.config.max_steps} steps")
        
        data_iter = iter(self.train_dataloader)
        accumulation_steps = 0
        accumulated_loss = {}
        
        start_time = time.time()
        
        while self.step < self.config.max_steps:
            # Get batch
            try:
                batch = next(data_iter)
            except StopIteration:
                data_iter = iter(self.train_dataloader)
                batch = next(data_iter)
            
            # Training step
            loss_dict = self.train_step(batch)
            
            # Accumulate losses for logging
            for k, v in loss_dict.items():
                accumulated_loss[k] = accumulated_loss.get(k, 0) + v
            
            accumulation_steps += 1
            
            # Update weights after accumulation
            if accumulation_steps >= self.config.gradient_accumulation_steps:
                # Gradient clipping
                if self.config.grad_clip > 0:
                    if self.scaler:
                        self.scaler.unscale_(self.optimizer)
                    torch.nn.utils.clip_grad_norm_(
                        self.model.parameters(),
                        self.config.grad_clip
                    )
                
                # Optimizer step
                if self.scaler:
                    self.scaler.step(self.optimizer)
                    self.scaler.update()
                else:
                    self.optimizer.step()
                
                self.optimizer.zero_grad()
                
                # Update learning rate
                self._warmup_lr()
                if self.step >= self.config.warmup_steps:
                    self.scheduler.step()
                
                self.step += 1
                
                # Logging
                if self.step % self.config.log_interval == 0:
                    avg_loss = {k: v / accumulation_steps for k, v in accumulated_loss.items()}
                    elapsed = time.time() - start_time
                    tokens_per_sec = (
                        self.step * self.config.batch_size * 
                        self.config.gradient_accumulation_steps * 
                        self.config.max_seq_len
                    ) / elapsed
                    
                    print(f"Step {self.step}/{self.config.max_steps} | "
                          f"Loss: {avg_loss['total_loss']:.4f} | "
                          f"LM: {avg_loss['lm_loss']:.4f} | "
                          f"Tokens/s: {tokens_per_sec:.0f}")
                
                # Evaluation
                if self.eval_dataloader and self.step % self.config.eval_interval == 0:
                    eval_loss = self.evaluate()
                    print(f"📊 Eval loss: {eval_loss:.4f}")
                    
                    if eval_loss < self.best_loss:
                        self.best_loss = eval_loss
                        self.save_checkpoint("best")
                
                # Checkpointing
                if self.step % self.config.save_interval == 0:
                    self.save_checkpoint(f"step_{self.step}")
                
                # Reset accumulation
                accumulation_steps = 0
                accumulated_loss = {}
        
        # Final save
        self.save_checkpoint("final")
        print(f"✅ Training complete!")
    
    def evaluate(self) -> float:
        """Evaluate on eval dataset"""
        self.model.eval()
        total_loss = 0
        num_batches = 0
        
        with torch.no_grad():
            for batch in self.eval_dataloader:
                input_ids = batch["input_ids"].to(self.device)
                labels = batch.get("labels", input_ids).to(self.device)
                
                outputs = self.model(input_ids, training=False)
                loss, _ = self._compute_loss(
                    outputs["logits"],
                    labels,
                    {}
                )
                
                total_loss += loss.item()
                num_batches += 1
                
                if num_batches >= 50:  # Limit eval batches
                    break
        
        return total_loss / max(num_batches, 1)
    
    def save_checkpoint(self, name: str):
        """Save training checkpoint"""
        path = os.path.join(self.config.output_dir, f"checkpoint_{name}")
        os.makedirs(path, exist_ok=True)
        
        # Save model
        torch.save(self.model.state_dict(), os.path.join(path, "model.pt"))
        
        # Save optimizer
        torch.save({
            "optimizer": self.optimizer.state_dict(),
            "scheduler": self.scheduler.state_dict(),
            "step": self.step,
            "best_loss": self.best_loss,
        }, os.path.join(path, "training_state.pt"))
        
        # Save config
        config_dict = {
            "model_config": self.model.config.__dict__,
            "training_config": self.config.__dict__,
        }
        with open(os.path.join(path, "config.json"), "w") as f:
            json.dump(config_dict, f, indent=2, default=str)
        
        print(f"💾 Saved checkpoint: {path}")
    
    def load_checkpoint(self, path: str):
        """Load from checkpoint"""
        # Load model
        self.model.load_state_dict(
            torch.load(os.path.join(path, "model.pt"), map_location=self.device)
        )
        
        # Load training state
        state = torch.load(os.path.join(path, "training_state.pt"), map_location=self.device)
        self.optimizer.load_state_dict(state["optimizer"])
        self.scheduler.load_state_dict(state["scheduler"])
        self.step = state["step"]
        self.best_loss = state["best_loss"]
        
        print(f"📂 Loaded checkpoint from step {self.step}")


class MoEConverter:
    """
    Convert trained MoE-SSM model to mobile format
    
    Performs:
    1. Quantization (INT4/NF4)
    2. Expert chunking for disk streaming
    3. Index generation for fast loading
    """
    
    def __init__(self, model: MoESSMModel, output_dir: str):
        self.model = model
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def convert(
        self,
        quant_type: str = "nf4",
        group_size: int = 128,
        create_draft_model: bool = True
    ) -> str:
        """
        Convert model to mobile-optimized format
        
        Args:
            quant_type: Quantization type (nf4, int4, int8)
            group_size: Quantization group size
            create_draft_model: Create separate draft model for speculative decoding
            
        Returns:
            Path to output directory
        """
        print(f"🔄 Converting model to mobile format ({quant_type})")
        
        # 1. Quantize and save experts
        expert_index = self._save_experts(quant_type, group_size)
        
        # 2. Save core weights (embedding, SSM, norms)
        core_index = self._save_core_weights(quant_type, group_size)
        
        # 3. Save router weights (small, always in memory)
        router_index = self._save_router_weights()
        
        # 4. Create main index
        self._create_index(expert_index, core_index, router_index)
        
        # 5. Create draft model if requested
        if create_draft_model:
            self._create_draft_model()
        
        # 6. Save config
        self._save_config(quant_type)
        
        print(f"✅ Conversion complete: {self.output_dir}")
        self._report_sizes()
        
        return str(self.output_dir)
    
    def _save_experts(
        self,
        quant_type: str,
        group_size: int
    ) -> List[Dict[str, Any]]:
        """Save expert weights to separate files"""
        from omnimind.quantization.advanced_quantization import NF4Quantizer, INT4Quantizer
        
        expert_index = []
        
        for layer_idx, layer in enumerate(self.model.layers):
            moe = layer.moe
            
            for expert_idx, expert in enumerate(moe.experts):
                # Gather expert weights
                weights = {
                    "gate": expert.gate_proj.weight.data,
                    "up": expert.up_proj.weight.data,
                    "down": expert.down_proj.weight.data,
                }
                
                # Quantize
                quantized = {}
                for name, weight in weights.items():
                    if quant_type == "nf4":
                        packed, scales, shape, numel = NF4Quantizer.quantize(weight, group_size)
                    else:
                        packed, scales, zeros, shape, numel = INT4Quantizer.quantize(weight, group_size)
                        quantized[f"{name}_zeros"] = zeros
                    
                    quantized[f"{name}_packed"] = packed
                    quantized[f"{name}_scales"] = scales
                    quantized[f"{name}_shape"] = shape
                    quantized[f"{name}_numel"] = numel
                
                # Save to file
                expert_file = f"expert_L{layer_idx}_E{expert_idx}.pt"
                torch.save(quantized, self.output_dir / expert_file)
                
                expert_index.append({
                    "layer_idx": layer_idx,
                    "expert_idx": expert_idx,
                    "file": expert_file,
                    "size_bytes": (self.output_dir / expert_file).stat().st_size
                })
        
        return expert_index
    
    def _save_core_weights(
        self,
        quant_type: str,
        group_size: int
    ) -> Dict[str, Any]:
        """Save core model weights (embedding, SSM, norms)"""
        core_weights = {
            "embedding": self.model.embedding.weight.data,
            "lm_head": self.model.lm_head.weight.data,
            "norm": self.model.norm.weight.data if hasattr(self.model.norm, 'weight') else None,
        }
        
        # SSM weights per layer
        ssm_weights = []
        for layer in self.model.layers:
            ssm = layer.ssm
            ssm_weights.append({
                "in_proj": ssm.in_proj.weight.data,
                "out_proj": ssm.out_proj.weight.data,
                "x_proj": ssm.x_proj.weight.data,
                "A_log": ssm.A_log.data,
                "D": ssm.D.data,
                "conv1d": ssm.conv1d.weight.data,
            })
        
        core_weights["ssm_layers"] = ssm_weights
        
        torch.save(core_weights, self.output_dir / "core_weights.pt")
        
        return {
            "file": "core_weights.pt",
            "size_bytes": (self.output_dir / "core_weights.pt").stat().st_size
        }
    
    def _save_router_weights(self) -> Dict[str, Any]:
        """Save router weights (kept in memory always)"""
        router_weights = []
        
        for layer in self.model.layers:
            router_weights.append({
                "gate": layer.moe.router.gate.weight.data
            })
        
        torch.save(router_weights, self.output_dir / "router_weights.pt")
        
        return {
            "file": "router_weights.pt",
            "size_bytes": (self.output_dir / "router_weights.pt").stat().st_size
        }
    
    def _create_index(
        self,
        expert_index: List[Dict],
        core_index: Dict,
        router_index: Dict
    ):
        """Create main index file for fast loading"""
        config = self.model.config
        
        index = {
            "version": "1.0",
            "model_type": "omnimind_moe_ssm",
            "config": {
                "d_model": config.d_model,
                "n_layers": config.n_layers,
                "d_state": config.d_state,
                "num_experts": config.num_experts,
                "top_k": config.top_k,
                "vocab_size": config.vocab_size,
            },
            "experts": expert_index,
            "core": core_index,
            "router": router_index,
            "total_size_bytes": sum(e["size_bytes"] for e in expert_index) + 
                               core_index["size_bytes"] + 
                               router_index["size_bytes"]
        }
        
        with open(self.output_dir / "model_index.json", "w") as f:
            json.dump(index, f, indent=2)
    
    def _create_draft_model(self):
        """Create small draft model for speculative decoding"""
        # Extract draft heads if available
        if self.model.draft_heads:
            draft_weights = {
                "head_weights": [h.weight.data for h in self.model.draft_heads]
            }
        else:
            # Create simple draft model
            draft_weights = {
                "embedding": self.model.embedding.weight.data[:, :256],  # Reduced dim
                "lm_head": self.model.lm_head.weight.data[:, :256],
            }
        
        torch.save(draft_weights, self.output_dir / "draft_model.pt")
        print(f"   Created draft model for speculative decoding")
    
    def _save_config(self, quant_type: str):
        """Save inference config"""
        config = {
            "quant_type": quant_type,
            "inference_settings": {
                "recommended_cache_mb": 2048,
                "recommended_prefetch": 4,
                "supports_speculative": True,
                "supports_layer_skip": self.model.config.enable_layer_skip,
            },
            "estimated_speed": {
                "warmup_s": 5.0,
                "tokens_per_sec": 50.0,
                "ram_mb": 4096,
            }
        }
        
        with open(self.output_dir / "inference_config.json", "w") as f:
            json.dump(config, f, indent=2)
    
    def _report_sizes(self):
        """Report file sizes"""
        total_size = 0
        
        for file in self.output_dir.iterdir():
            size = file.stat().st_size
            total_size += size
            print(f"   {file.name}: {size / 1024 / 1024:.1f} MB")
        
        print(f"   TOTAL: {total_size / 1024 / 1024 / 1024:.2f} GB")


def train_moe_ssm(
    train_data: Union[Dataset, DataLoader],
    model_size: str = "7b",
    num_experts: int = 64,
    top_k: int = 2,
    output_dir: str = "outputs/moe_ssm",
    **kwargs
) -> MoESSMModel:
    """
    High-level training function for MoE-SSM
    
    Args:
        train_data: Training dataset or dataloader
        model_size: "1b", "7b", "13b", "30b", "70b"
        num_experts: Number of experts
        top_k: Experts per token
        output_dir: Output directory
        **kwargs: Additional training config options
        
    Returns:
        Trained model
    """
    # Create model
    model = create_moe_ssm_model(model_size, num_experts, top_k)
    
    # Create dataloader if needed
    if isinstance(train_data, Dataset):
        train_dataloader = DataLoader(
            train_data,
            batch_size=kwargs.get("batch_size", 8),
            shuffle=True,
            num_workers=4
        )
    else:
        train_dataloader = train_data
    
    # Create config
    config = MoETrainingConfig(
        model_size=model_size,
        num_experts=num_experts,
        top_k=top_k,
        output_dir=output_dir,
        **{k: v for k, v in kwargs.items() if hasattr(MoETrainingConfig, k)}
    )
    
    # Train
    trainer = MoETrainer(model, config, train_dataloader)
    trainer.train()
    
    return model


def convert_to_mobile(
    model: MoESSMModel,
    output_dir: str,
    quant_type: str = "nf4"
) -> str:
    """
    Convert trained model to mobile format
    
    Args:
        model: Trained MoE-SSM model
        output_dir: Output directory
        quant_type: Quantization type
        
    Returns:
        Path to converted model
    """
    converter = MoEConverter(model, output_dir)
    return converter.convert(quant_type)


# Exports
__all__ = [
    'MoETrainingConfig',
    'MoETrainer',
    'MoEConverter',
    'train_moe_ssm',
    'convert_to_mobile',
]


if __name__ == "__main__":
    print("=== OMNIMIND MoE Training Pipeline ===\n")
    
    # Example usage (would need actual data)
    print("Example usage:")
    print("""
    from .moe_trainer import train_moe_ssm, convert_to_mobile
    
    # 1. Train model
    model = train_moe_ssm(
        train_data=my_dataset,
        model_size="7b",
        num_experts=64,
        top_k=2,
        max_steps=100000
    )
    
    # 2. Convert to mobile
    convert_to_mobile(model, "output/7b_mobile", quant_type="nf4")
    
    # 3. Deploy with ultra-fast engine!
    from omnimind.inference.ultra_fast import UltraFastEngine
    engine = UltraFastEngine.from_path("output/7b_mobile")
    """)
