"""
OMNIMIND HuggingFace Hub Utilities
Helper functions for interacting with HuggingFace Hub.
"""

import os
from typing import Optional, Dict, Any
from pathlib import Path

__all__ = [
    "login_hf",
    "push_to_hub",
    "download_model",
    "get_model_info",
]

def login_hf(token: Optional[str] = None):
    """
    Login to HuggingFace Hub.
    
    Args:
        token: HF API token (uses cached token if None)
    """
    try:
        from huggingface_hub import login
        
        if token:
            login(token=token)
        else:
            # Try to use cached token
            login()
        
        print("✅ Logged in to HuggingFace Hub")
        return True
    except Exception as e:
        print(f"❌ HuggingFace login failed: {e}")
        return False

def push_to_hub(
    model,
    tokenizer,
    repo_id: str,
    private: bool = True,
    commit_message: str = "Upload model",
    **kwargs,
):
    """
    Push model and tokenizer to HuggingFace Hub.
    
    Args:
        model: The model to push
        tokenizer: The tokenizer to push
        repo_id: Repository ID (e.g., "username/model-name")
        private: Make repository private
        commit_message: Commit message
        
    Returns:
        URL of the uploaded model
    """
    try:
        from huggingface_hub import HfApi
        
        api = HfApi()
        
        # Create repo if it doesn't exist
        api.create_repo(repo_id, private=private, exist_ok=True)
        
        # Push model
        model.push_to_hub(
            repo_id,
            commit_message=commit_message,
            **kwargs
        )
        
        # Push tokenizer
        tokenizer.push_to_hub(
            repo_id,
            commit_message=commit_message,
        )
        
        url = f"https://huggingface.co/{repo_id}"
        print(f"✅ Model uploaded to {url}")
        return url
        
    except Exception as e:
        print(f"❌ Push failed: {e}")
        return None

def download_model(
    repo_id: str,
    local_dir: Optional[str] = None,
    revision: str = "main",
) -> str:
    """
    Download model from HuggingFace Hub.
    
    Args:
        repo_id: Repository ID
        local_dir: Local directory to save (default: HF cache)
        revision: Git revision/branch
        
    Returns:
        Path to downloaded model
    """
    try:
        from huggingface_hub import snapshot_download
        
        path = snapshot_download(
            repo_id,
            local_dir=local_dir,
            revision=revision,
        )
        
        print(f"✅ Downloaded to {path}")
        return path
        
    except Exception as e:
        print(f"❌ Download failed: {e}")
        return None

def get_model_info(repo_id: str) -> Optional[Dict[str, Any]]:
    """
    Get information about a model on HuggingFace Hub.
    
    Args:
        repo_id: Repository ID
        
    Returns:
        Dict with model info or None if not found
    """
    try:
        from huggingface_hub import HfApi
        
        api = HfApi()
        info = api.model_info(repo_id)
        
        return {
            "id": info.id,
            "author": info.author,
            "downloads": info.downloads,
            "likes": info.likes,
            "tags": info.tags,
            "pipeline_tag": info.pipeline_tag,
            "library_name": info.library_name,
        }
        
    except Exception:
        return None

def save_pretrained_merged(
    model,
    tokenizer,
    save_path: str,
    safe_serialization: bool = True,
):
    """
    Save model with merged LoRA weights.
    
    Args:
        model: PeftModel or regular model
        tokenizer: Tokenizer
        save_path: Path to save
        safe_serialization: Use safetensors format
    """
    save_path = Path(save_path)
    save_path.mkdir(parents=True, exist_ok=True)
    
    # Check if it's a PEFT model
    if hasattr(model, "merge_and_unload"):
        print("🔄 Merging LoRA weights...")
        model = model.merge_and_unload()
    
    # Save model
    model.save_pretrained(
        save_path,
        safe_serialization=safe_serialization,
    )
    
    # Save tokenizer
    tokenizer.save_pretrained(save_path)
    
    print(f"✅ Saved merged model to {save_path}")
    return str(save_path)
