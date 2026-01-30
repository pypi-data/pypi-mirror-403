#!/usr/bin/env python3
"""
OMNIMIND Inference Script
Generate text with trained model
"""
import argparse
import os
import sys

import torch

from omnimind.model.config import get_config
from omnimind.model.omnimind_model import OmnimindForCausalLM
from omnimind.training.dataset import SimpleTokenizer


def main():
    parser = argparse.ArgumentParser(description="OMNIMIND Inference")
    
    parser.add_argument("--checkpoint", type=str, required=True,
                       help="Path to model checkpoint")
    parser.add_argument("--prompt", type=str, default="สวัสดี",
                       help="Input prompt")
    parser.add_argument("--max-tokens", type=int, default=100,
                       help="Maximum tokens to generate")
    parser.add_argument("--temperature", type=float, default=0.8,
                       help="Sampling temperature")
    parser.add_argument("--top-k", type=int, default=50,
                       help="Top-k sampling")
    parser.add_argument("--top-p", type=float, default=0.9,
                       help="Nucleus sampling threshold")
    parser.add_argument("--device", type=str, default="auto",
                       help="Device (auto/cpu/cuda/mps)")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🧠 OMNIMIND Inference")
    print("=" * 60)
    
    # Setup device
    if args.device == "auto":
        if torch.cuda.is_available():
            device = torch.device("cuda")
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            device = torch.device("mps")
        else:
            device = torch.device("cpu")
    else:
        device = torch.device(args.device)
    
    print(f"\n🖥️  Device: {device}")
    
    # Load config
    config_path = os.path.join(args.checkpoint, "config.json")
    if os.path.exists(config_path):
        import json
        with open(config_path) as f:
            config_dict = json.load(f)
        # Recreate config (simplified)
        config = get_config("nano")  # Default, would load from saved config
    else:
        config = get_config("nano")
    
    # Create model
    print(f"\n📦 Loading model from: {args.checkpoint}")
    model = OmnimindForCausalLM(config)
    
    # Load weights
    model_path = os.path.join(args.checkpoint, "model.pt")
    if os.path.exists(model_path):
        model.load_state_dict(torch.load(model_path, map_location=device))
        print("   ✅ Weights loaded")
    else:
        print("   ⚠️ No weights found, using random initialization")
    
    model.to(device)
    model.eval()
    
    # Create tokenizer
    tokenizer = SimpleTokenizer(vocab_size=config.vocab_size)
    
    # Encode prompt
    print(f"\n💬 Prompt: {args.prompt}")
    input_ids = tokenizer.encode(args.prompt, add_special_tokens=True)
    input_ids = torch.tensor([input_ids], device=device)
    
    # Generate
    print(f"\n🔄 Generating (max {args.max_tokens} tokens)...")
    
    with torch.no_grad():
        output_ids = model.generate(
            input_ids,
            max_new_tokens=args.max_tokens,
            temperature=args.temperature,
            top_k=args.top_k,
            top_p=args.top_p,
        )
    
    # Decode
    output_text = tokenizer.decode(output_ids[0].tolist(), skip_special_tokens=True)
    
    print("\n" + "=" * 60)
    print("📝 Generated:")
    print("=" * 60)
    print(output_text)
    print("=" * 60)


def interactive_mode():
    """Interactive chat mode"""
    parser = argparse.ArgumentParser(description="OMNIMIND Interactive")
    parser.add_argument("--checkpoint", type=str, required=True)
    parser.add_argument("--device", type=str, default="auto")
    args = parser.parse_args()
    
    # Setup device
    if args.device == "auto":
        if torch.cuda.is_available():
            device = torch.device("cuda")
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            device = torch.device("mps")
        else:
            device = torch.device("cpu")
    else:
        device = torch.device(args.device)
    
    # Load model
    config = get_config("nano")
    model = OmnimindForCausalLM(config)
    
    model_path = os.path.join(args.checkpoint, "model.pt")
    if os.path.exists(model_path):
        model.load_state_dict(torch.load(model_path, map_location=device))
    
    model.to(device)
    model.eval()
    
    tokenizer = SimpleTokenizer(vocab_size=config.vocab_size)
    
    print("\n🧠 OMNIMIND Interactive Mode")
    print("Type 'quit' to exit\n")
    
    while True:
        try:
            prompt = input("You: ").strip()
            if prompt.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not prompt:
                continue
            
            input_ids = tokenizer.encode(prompt, add_special_tokens=True)
            input_ids = torch.tensor([input_ids], device=device)
            
            with torch.no_grad():
                output_ids = model.generate(
                    input_ids,
                    max_new_tokens=100,
                    temperature=0.8,
                )
            
            output_text = tokenizer.decode(output_ids[0].tolist(), skip_special_tokens=True)
            print(f"OMNIMIND: {output_text}\n")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break


if __name__ == "__main__":
    main()
