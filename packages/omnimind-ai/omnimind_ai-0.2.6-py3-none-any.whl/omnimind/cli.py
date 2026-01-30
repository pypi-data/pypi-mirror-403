"""
OMNIMIND Command Line Interface (CLI)
Manage models, training, and server from the terminal

Usage:
    omnimind chat --model micro
    omnimind serve --port 8000
    omnimind train --config train_config.json
    omnimind download --model small
"""
import fire
import os
import json
from typing import Optional

# Lazy imports to keep CLI fast
def get_imports():
    from omnimind import (
        create_model, MobileInference, MobileConfig, 
        Trainer, TrainingConfig, save_lite
    )
    return create_model, MobileInference, MobileConfig, Trainer, TrainingConfig, save_lite

class OMNIMIND_CLI:
    """OMNIMIND CLI Tool"""
    
    def chat(self, model: str = "micro", quant: str = "none"):
        """Start an interactive chat session"""
        print(f"🚀 Loading OMNIMIND {model}...")
        
        # Load unified model
        from omnimind import Omnimind
        
        print(f"🧠 Initializing OMNIMIND {model} (Unified Agent)...")
        # For CLI, we can use 'auto' device
        omni = Omnimind(size=model, device="auto")
        
        print("💬 Chat started (type 'exit' to quit)")
        print("   (Tools and Senses enabled)")
        
        # History as list of dicts for agent
        history = []
        
        while True:
            try:
                user_input = input("\nYou: ")
                if user_input.lower() in ["exit", "quit"]:
                    break
                
                print("AI: ", end="", flush=True)
                
                # Agent process_turn handles reasoning, tools, and final response
                # Currently synchronous / non-streaming for full agent capabilities
                response = omni.agent.process_turn(user_input, history)
                
                print(response)
                
                # Update history (User and Assistant)
                history.append({"role": "user", "content": user_input})
                history.append({"role": "assistant", "content": response})
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
    
    def serve(self, model: str = "micro", port: int = 8000, quant: str = "none"):
        """Start API Server"""
        from omnimind.server import run_server
        run_server(model, port, quant)
    
    def download(self, model: str = "micro", output: str = "./models"):
        """Download model weights"""
        print(f"📥 Downloading OMNIMIND {model} to {output}...")
        from omnimind import create_model
        # Simulation of download logic
        create_model(model) # This triggers weight creation/download if remote
        print("✅ Download complete")
        
    def info(self):
        """Show system info"""
        import torch
        print("🧠 OMNIMIND System Info")
        print(f"   PyTorch: {torch.__version__}")
        print(f"   CUDA: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"   GPU: {torch.cuda.get_device_name()}")

def main():
    fire.Fire(OMNIMIND_CLI)

if __name__ == "__main__":
    main()
