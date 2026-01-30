#!/usr/bin/env python3
"""
OMNIMIND Training Script
Train the State-Space Model from scratch
"""
import argparse
import os
import sys

import torch

from omnimind.model.config import get_config, OmnimindConfig
from omnimind.model.omnimind_model import OmnimindForCausalLM
from omnimind.training.dataset import SimpleTokenizer, TextDataset, create_dataloader
from omnimind.training.trainer import Trainer, TrainingConfig


def main():
    parser = argparse.ArgumentParser(description="Train OMNIMIND")
    
    # Model
    parser.add_argument("--model-size", type=str, default="nano", 
                       choices=["nano", "micro", "mini", "standard"],
                       help="Model size variant")
    
    # Data
    parser.add_argument("--data-path", type=str, required=True,
                       help="Path to training data (txt/json/jsonl)")
    parser.add_argument("--max-seq-len", type=int, default=512,
                       help="Maximum sequence length")
    
    # Training
    parser.add_argument("--batch-size", type=int, default=4,
                       help="Training batch size")
    parser.add_argument("--gradient-accumulation", type=int, default=8,
                       help="Gradient accumulation steps")
    parser.add_argument("--epochs", type=int, default=3,
                       help="Number of training epochs")
    parser.add_argument("--max-steps", type=int, default=-1,
                       help="Maximum training steps (-1 for full epochs)")
    parser.add_argument("--lr", type=float, default=1e-4,
                       help="Learning rate")
    
    # Output
    parser.add_argument("--output-dir", type=str, default="checkpoints",
                       help="Output directory for checkpoints")
    
    # Hardware
    parser.add_argument("--device", type=str, default="auto",
                       help="Device (auto/cpu/cuda/mps)")
    parser.add_argument("--fp16", action="store_true",
                       help="Use FP16 mixed precision")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🧠 OMNIMIND Training")
    print("=" * 60)
    
    # Create model config
    print(f"\n📦 Creating {args.model_size.upper()} model...")
    model_config = get_config(args.model_size)
    model_config.max_seq_len = args.max_seq_len
    
    # Create model
    model = OmnimindForCausalLM(model_config)
    num_params = model.model.num_parameters
    print(f"   Parameters: {num_params / 1e6:.1f}M")
    
    # Create tokenizer
    print(f"\n📝 Loading tokenizer...")
    tokenizer = SimpleTokenizer(vocab_size=model_config.vocab_size)
    
    # Load dataset
    print(f"\n📂 Loading dataset from: {args.data_path}")
    if not os.path.exists(args.data_path):
        print(f"❌ Error: Data path not found: {args.data_path}")
        print("\nTo test, create a sample data file:")
        print(f'  echo "สวัสดีครับ นี่คือข้อมูลทดสอบสำหรับ OMNIMIND" > {args.data_path}')
        return
    
    dataset = TextDataset(
        data_path=args.data_path,
        tokenizer=tokenizer,
        max_seq_len=args.max_seq_len,
    )
    print(f"   Samples: {len(dataset)}")
    
    if len(dataset) == 0:
        print("❌ Error: No data samples found. Check your data file.")
        return
    
    # Create dataloader
    train_dataloader = create_dataloader(
        dataset,
        batch_size=args.batch_size,
        shuffle=True,
    )
    
    # Create training config
    train_config = TrainingConfig(
        output_dir=args.output_dir,
        num_epochs=args.epochs,
        max_steps=args.max_steps,
        batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation,
        learning_rate=args.lr,
        fp16=args.fp16 and torch.cuda.is_available(),
        device=args.device,
    )
    
    # Create trainer
    trainer = Trainer(
        model=model,
        train_dataloader=train_dataloader,
        config=train_config,
    )
    
    # Train!
    print("\n" + "=" * 60)
    results = trainer.train()
    print("=" * 60)
    
    print(f"\n📊 Final Results:")
    for key, value in results.items():
        print(f"   {key}: {value:.4f}")
    
    print(f"\n✅ Model saved to: {args.output_dir}")


if __name__ == "__main__":
    main()
