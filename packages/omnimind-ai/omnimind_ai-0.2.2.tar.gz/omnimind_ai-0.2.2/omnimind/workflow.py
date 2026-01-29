"""
OMNIMIND Unified Workflow
Complete pipeline: Convert → Train → Export

Integrates:
- Transformer → SSM Conversion with stability fixes
- Training with SQLite-based checkpointing (FTS5-level speed)
- Export for mobile/disk streaming inference

Usage:
    from omnimind.workflow import OmnimindWorkflow
    
    # Full workflow: convert → train → export
    workflow = OmnimindWorkflow("Qwen/Qwen2.5-3B", output_dir="my_model")
    
    # Step 1: Convert Transformer to SSM
    workflow.convert(load_in_4bit=True)
    
    # Step 2: Finetune on your data
    workflow.train(train_data, epochs=3)
    
    # Step 3: Export for deployment
    workflow.export(format="sqlite")  # FTS5-level disk streaming
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, Union, List
from dataclasses import dataclass, field
import torch
import torch.nn as nn


@dataclass
class WorkflowConfig:
    """Configuration for the complete OMNIMIND workflow"""
    
    # Conversion settings
    source_model: str = ""
    load_in_4bit: bool = True
    load_in_8bit: bool = False
    
    # Training settings
    num_epochs: int = 3
    batch_size: int = 8
    learning_rate: float = 1e-4
    gradient_accumulation_steps: int = 4
    
    # Storage settings (FTS5-level)
    use_sqlite_storage: bool = True
    sqlite_compression: str = "zstd"
    sqlite_cache_mb: int = 256
    
    # Output
    output_dir: str = "omnimind_output"
    
    # Device
    device: str = "auto"


class OmnimindWorkflow:
    """
    Unified workflow for OMNIMIND model development
    
    Provides a simple interface for the complete pipeline:
    1. Convert: Transformer → SSM with knowledge transfer
    2. Train: Finetune with SQLite checkpointing
    3. Export: Save for mobile/disk streaming deployment
    
    Example:
        workflow = OmnimindWorkflow("Qwen/Qwen2.5-3B")
        workflow.convert()
        workflow.train(my_dataset)
        workflow.export("sqlite")  # FTS5-level performance
    """
    
    def __init__(
        self,
        source_model: str,
        output_dir: str = "omnimind_output",
        config: Optional[WorkflowConfig] = None
    ):
        self.source_model = source_model
        self.output_dir = Path(output_dir)
        self.config = config or WorkflowConfig(
            source_model=source_model,
            output_dir=output_dir
        )
        
        # State
        self.model = None
        self.tokenizer = None
        self.trainer = None
        self.conversion_stats = None
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Paths
        self.sqlite_path = self.output_dir / "model.db"
        self.checkpoint_dir = self.output_dir / "checkpoints"
        
        print(f"🧠 OMNIMIND Workflow initialized")
        print(f"   Source: {source_model}")
        print(f"   Output: {output_dir}")
    
    def convert(
        self,
        load_in_4bit: bool = None,
        load_in_8bit: bool = None,
        save_to_sqlite: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Step 1: Convert Transformer to SSM
        
        Args:
            load_in_4bit: Use 4-bit quantization for source model
            load_in_8bit: Use 8-bit quantization for source model
            save_to_sqlite: Save converted model to SQLite (FTS5-level)
            **kwargs: Additional conversion args
            
        Returns:
            Conversion statistics
        """
        from omnimind.conversion import (
            convert_model,
            convert_and_save_to_sqlite,
            compute_conversion_quality_score
        )
        
        print("\n" + "=" * 60)
        print("📥 STEP 1: CONVERSION (Transformer → SSM)")
        print("=" * 60)
        
        load_in_4bit = load_in_4bit if load_in_4bit is not None else self.config.load_in_4bit
        load_in_8bit = load_in_8bit if load_in_8bit is not None else self.config.load_in_8bit
        
        if save_to_sqlite and self.config.use_sqlite_storage:
            # Convert and save directly to SQLite
            result = convert_and_save_to_sqlite(
                self.source_model,
                str(self.sqlite_path),
                compression=self.config.sqlite_compression,
                load_in_4bit=load_in_4bit,
                load_in_8bit=load_in_8bit,
                **kwargs
            )
            self.model = result["model"]
            self.tokenizer = result["tokenizer"]
            self.conversion_stats = result
        else:
            # Convert without SQLite save
            self.model, self.tokenizer = convert_model(
                self.source_model,
                load_in_4bit=load_in_4bit,
                load_in_8bit=load_in_8bit,
                **kwargs
            )
            self.conversion_stats = {
                "quality_scores": compute_conversion_quality_score({}, self.model.state_dict())
            }
        
        # Save tokenizer
        tokenizer_path = self.output_dir / "tokenizer"
        if self.tokenizer:
            self.tokenizer.save_pretrained(str(tokenizer_path))
            print(f"   💬 Tokenizer saved: {tokenizer_path}")
        
        return self.conversion_stats
    
    def train(
        self,
        train_dataset,
        eval_dataset=None,
        num_epochs: int = None,
        batch_size: int = None,
        learning_rate: float = None,
        **kwargs
    ) -> Dict[str, float]:
        """
        Step 2: Train/Finetune the converted model
        
        Uses SQLite-based checkpointing for FTS5-level save/load speed.
        
        Args:
            train_dataset: Training dataset (or DataLoader)
            eval_dataset: Optional evaluation dataset
            num_epochs: Number of training epochs
            batch_size: Batch size
            learning_rate: Learning rate
            **kwargs: Additional training args
            
        Returns:
            Training metrics
        """
        from omnimind.training import Trainer, TrainingConfig
        from torch.utils.data import DataLoader
        
        if self.model is None:
            raise RuntimeError("No model loaded. Call convert() first.")
        
        print("\n" + "=" * 60)
        print("🏋️ STEP 2: TRAINING")
        print("=" * 60)
        
        # Create dataloaders if needed
        batch_size = batch_size or self.config.batch_size
        
        if not isinstance(train_dataset, DataLoader):
            train_dataloader = DataLoader(
                train_dataset,
                batch_size=batch_size,
                shuffle=True,
                num_workers=0
            )
        else:
            train_dataloader = train_dataset
        
        eval_dataloader = None
        if eval_dataset is not None:
            if not isinstance(eval_dataset, DataLoader):
                eval_dataloader = DataLoader(
                    eval_dataset,
                    batch_size=batch_size,
                    shuffle=False,
                    num_workers=0
                )
            else:
                eval_dataloader = eval_dataset
        
        # Training config with SQLite storage
        train_config = TrainingConfig(
            output_dir=str(self.checkpoint_dir),
            num_epochs=num_epochs or self.config.num_epochs,
            batch_size=batch_size,
            learning_rate=learning_rate or self.config.learning_rate,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            use_sqlite_storage=self.config.use_sqlite_storage,
            sqlite_compression=self.config.sqlite_compression,
            sqlite_cache_mb=self.config.sqlite_cache_mb,
            device=self.config.device,
            **kwargs
        )
        
        # Create trainer
        self.trainer = Trainer(
            model=self.model,
            train_dataloader=train_dataloader,
            config=train_config,
            eval_dataloader=eval_dataloader
        )
        
        # Train
        metrics = self.trainer.train()
        
        return metrics
    
    def export(
        self,
        format: str = "sqlite",
        output_path: str = None,
        quantization: str = None,
        **kwargs
    ) -> str:
        """
        Step 3: Export model for deployment
        
        Formats:
        - "sqlite": SQLite database with FTS5-level performance
        - "pytorch": Standard PyTorch format
        - "gguf": GGUF format for llama.cpp (future)
        
        Args:
            format: Export format
            output_path: Custom output path
            quantization: Quantization type (int4, int8, none)
            **kwargs: Format-specific args
            
        Returns:
            Path to exported model
        """
        if self.model is None:
            raise RuntimeError("No model loaded. Call convert() or load() first.")
        
        print("\n" + "=" * 60)
        print("📤 STEP 3: EXPORT")
        print("=" * 60)
        
        if format == "sqlite":
            from omnimind.storage import SQLiteWeightStorage, WeightStorageConfig
            
            export_path = output_path or str(self.output_dir / "model_export.db")
            
            storage_config = WeightStorageConfig(
                compression=self.config.sqlite_compression,
                cache_size_mb=self.config.sqlite_cache_mb
            )
            storage = SQLiteWeightStorage(export_path, storage_config)
            
            # Get model config
            model_config = None
            if hasattr(self.model, 'config'):
                cfg = self.model.config
                model_config = {
                    "source_model": self.source_model,
                    "d_model": getattr(cfg, 'd_model', None),
                    "n_layers": getattr(cfg, 'n_layers', None),
                    "d_state": getattr(cfg, 'd_state', None),
                    "vocab_size": getattr(cfg, 'vocab_size', None),
                }
            
            storage.save_model(self.model, model_config=model_config)
            stats = storage.get_storage_stats()
            storage.close()
            
            print(f"   ✅ Exported to SQLite: {export_path}")
            print(f"   💾 Size: {stats['total_mb']:.1f} MB")
            print(f"   🗜️ Compression: {self.config.sqlite_compression}")
            
            return export_path
            
        elif format == "pytorch":
            export_path = output_path or str(self.output_dir / "model.pt")
            torch.save(self.model.state_dict(), export_path)
            
            # Save config
            config_path = str(self.output_dir / "config.json")
            if hasattr(self.model, 'config'):
                with open(config_path, 'w') as f:
                    json.dump(vars(self.model.config), f, indent=2, default=str)
            
            print(f"   ✅ Exported to PyTorch: {export_path}")
            return export_path
            
        elif format == "gguf":
            from omnimind.conversion import export_to_gguf
            export_path = output_path or str(self.output_dir / "model.gguf")
            export_to_gguf(self.model, export_path, **kwargs)
            print(f"   ✅ Exported to GGUF: {export_path}")
            return export_path
            
        else:
            raise ValueError(f"Unknown export format: {format}")
    
    def load(self, path: str = None, format: str = "sqlite") -> nn.Module:
        """
        Load a previously saved model
        
        Args:
            path: Path to model (defaults to workflow output)
            format: Format to load from
            
        Returns:
            Loaded model
        """
        print(f"📂 Loading model...")
        
        if format == "sqlite":
            from omnimind.conversion import load_from_sqlite
            
            path = path or str(self.sqlite_path)
            self.model = load_from_sqlite(path, device=self.config.device)
            
        elif format == "pytorch":
            if self.model is None:
                raise RuntimeError("Model architecture not initialized")
            
            path = path or str(self.output_dir / "model.pt")
            self.model.load_state_dict(torch.load(path))
        
        return self.model
    
    def load_best_checkpoint(self) -> nn.Module:
        """Load the best checkpoint based on loss"""
        if self.trainer and self.trainer.sqlite_storage:
            self.trainer.load_checkpoint(load_best=True)
            self.model = self.trainer.model
            return self.model
        raise RuntimeError("No trainer with SQLite storage available")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get workflow statistics"""
        stats = {
            "source_model": self.source_model,
            "output_dir": str(self.output_dir),
            "model_loaded": self.model is not None,
        }
        
        if self.conversion_stats:
            stats["conversion"] = self.conversion_stats
        
        if self.trainer:
            stats["training"] = {
                "global_step": self.trainer.global_step,
                "epoch": self.trainer.epoch,
            }
            if self.trainer.sqlite_storage:
                stats["storage"] = self.trainer.get_storage_stats()
        
        return stats


# ==================== Quick Functions ====================

def convert_and_train(
    source_model: str,
    train_dataset,
    output_dir: str = "omnimind_output",
    num_epochs: int = 3,
    load_in_4bit: bool = True,
    **kwargs
) -> OmnimindWorkflow:
    """
    Quick function: Convert and train in one call
    
    Example:
        workflow = convert_and_train(
            "Qwen/Qwen2.5-3B",
            my_dataset,
            num_epochs=3
        )
        workflow.export("sqlite")
    """
    workflow = OmnimindWorkflow(source_model, output_dir)
    workflow.convert(load_in_4bit=load_in_4bit)
    workflow.train(train_dataset, num_epochs=num_epochs, **kwargs)
    return workflow


def quick_convert(
    source_model: str,
    output_path: str,
    load_in_4bit: bool = True,
    compression: str = "zstd"
) -> str:
    """
    Quick function: Just convert and save to SQLite
    
    Example:
        path = quick_convert("Qwen/Qwen2.5-3B", "models/qwen.db")
    """
    from omnimind.conversion import convert_and_save_to_sqlite
    
    result = convert_and_save_to_sqlite(
        source_model,
        output_path,
        compression=compression,
        load_in_4bit=load_in_4bit
    )
    return result["storage_path"]
