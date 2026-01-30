"""
OMNIMIND Save Utilities
Comprehensive model saving, merging, and export functionality.
"""

import os
import gc
import torch
import shutil
from pathlib import Path
from typing import Optional, List, Union

__all__ = [
    "save_model",
    "save_merged_model",
    "merge_lora_weights",
    "save_to_gguf",
    "push_to_hub",
]

def merge_lora_weights(model) -> torch.nn.Module:
    """
    Merge LoRA weights back into base model.
    
    Args:
        model: PeftModel with LoRA adapters
        
    Returns:
        Model with merged weights
    """
    if hasattr(model, "merge_and_unload"):
        print("🔄 Merging LoRA weights...")
        model = model.merge_and_unload()
        gc.collect()
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
        print("✅ LoRA weights merged")
    return model

def save_model(
    model,
    tokenizer,
    save_path: str,
    save_method: str = "lora",
    safe_serialization: bool = True,
    push_to_hub: bool = False,
    hub_repo_id: Optional[str] = None,
    hub_token: Optional[str] = None,
    private: bool = True,
):
    """
    Save model with flexible options.
    
    Args:
        model: The model to save
        tokenizer: The tokenizer
        save_path: Local save directory
        save_method: "lora", "merged_16bit", or "merged_4bit"
        safe_serialization: Use safetensors format
        push_to_hub: Also push to HuggingFace Hub
        hub_repo_id: HuggingFace repository ID
        hub_token: HuggingFace token
        private: Make repo private
    """
    save_path = Path(save_path)
    save_path.mkdir(parents=True, exist_ok=True)
    
    print(f"💾 Saving model ({save_method})...")
    
    if save_method == "lora":
        # Save only LoRA adapters
        if hasattr(model, "save_pretrained"):
            model.save_pretrained(
                save_path,
                safe_serialization=safe_serialization,
            )
    
    elif save_method == "merged_16bit":
        # Merge and save in float16
        merged = merge_lora_weights(model)
        merged.save_pretrained(
            save_path,
            safe_serialization=safe_serialization,
        )
    
    elif save_method == "merged_4bit":
        # Save with 4-bit quantization info
        if hasattr(model, "save_pretrained"):
            model.save_pretrained(
                save_path,
                safe_serialization=safe_serialization,
            )
    
    # Save tokenizer
    if tokenizer:
        tokenizer.save_pretrained(save_path)
    
    print(f"✅ Model saved to {save_path}")
    
    # Push to hub
    if push_to_hub and hub_repo_id:
        _push_to_hub(save_path, hub_repo_id, hub_token, private)
    
    return str(save_path)

def save_merged_model(
    model,
    tokenizer,
    save_path: str,
    dtype: torch.dtype = torch.float16,
    safe_serialization: bool = True,
):
    """
    Save model with merged LoRA weights in specified dtype.
    
    This is the recommended method for exporting to GGUF/llama.cpp.
    """
    save_path = Path(save_path)
    save_path.mkdir(parents=True, exist_ok=True)
    
    # Merge LoRA
    model = merge_lora_weights(model)
    
    # Convert to target dtype if needed
    if dtype:
        model = model.to(dtype)
    
    # Save
    model.save_pretrained(
        save_path,
        safe_serialization=safe_serialization,
    )
    
    if tokenizer:
        tokenizer.save_pretrained(save_path)
    
    print(f"✅ Merged model saved to {save_path}")
    return str(save_path)

def save_to_gguf(
    model_path: str,
    output_path: str,
    quantization: str = "q4_k_m",
    use_llama_cpp: bool = True,
):
    """
    Convert model to GGUF format.
    
    Args:
        model_path: Path to saved model
        output_path: Output GGUF file path
        quantization: Quantization method (q4_k_m, q5_k_m, q8_0, f16)
        use_llama_cpp: Use llama.cpp convert script
        
    Returns:
        Path to GGUF file
    """
    # Try Omnimind's built-in export first
    try:
        from omnimind.conversion.gguf_export import export_to_gguf
        from transformers import AutoModelForCausalLM, AutoTokenizer
        
        print(f"🔄 Converting to GGUF ({quantization})...")
        
        model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16)
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        
        return export_to_gguf(model, output_path, quantization, tokenizer)
        
    except Exception as e:
        print(f"⚠️ Built-in export failed: {e}")
    
    # Fallback to llama.cpp
    if use_llama_cpp:
        print("🔄 Falling back to llama.cpp conversion...")
        try:
            import subprocess
            
            # Check if llama.cpp is available
            result = subprocess.run(
                ["python", "-m", "llama_cpp.convert", model_path, "--outfile", output_path],
                capture_output=True,
                text=True,
            )
            
            if result.returncode == 0:
                # Quantize
                subprocess.run([
                    "llama-quantize", output_path, 
                    output_path.replace(".gguf", f"-{quantization}.gguf"),
                    quantization.upper()
                ])
                print(f"✅ GGUF saved to {output_path}")
                return output_path
                
        except Exception as e:
            print(f"❌ llama.cpp conversion failed: {e}")
    
    print("❌ GGUF conversion failed. Please use llama.cpp manually.")
    return None

def _push_to_hub(
    local_path: str,
    repo_id: str,
    token: Optional[str] = None,
    private: bool = True,
):
    """Push local model to HuggingFace Hub"""
    try:
        from huggingface_hub import HfApi, upload_folder
        
        api = HfApi(token=token)
        api.create_repo(repo_id, private=private, exist_ok=True)
        
        upload_folder(
            folder_path=local_path,
            repo_id=repo_id,
            token=token,
        )
        
        url = f"https://huggingface.co/{repo_id}"
        print(f"✅ Pushed to {url}")
        return url
        
    except Exception as e:
        print(f"❌ Push failed: {e}")
        return None

def push_to_hub(
    model,
    tokenizer,
    repo_id: str,
    save_method: str = "lora",
    token: Optional[str] = None,
    private: bool = True,
    commit_message: str = "Upload model trained with Omnimind",
):
    """
    Save and push model to HuggingFace Hub.
    
    Args:
        model: Model to push
        tokenizer: Tokenizer to push
        repo_id: HuggingFace repository ID
        save_method: "lora", "merged_16bit", "merged_4bit"
        token: HuggingFace token
        private: Make repository private
        commit_message: Commit message
    """
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Save locally first
        save_model(model, tokenizer, tmp_dir, save_method)
        
        # Push
        return _push_to_hub(tmp_dir, repo_id, token, private)
