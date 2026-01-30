"""
OMNIMIND Tokenizer Utilities
Tokenizer loading, fixing, and optimization.
"""

import os
import logging
from typing import Optional, List, Dict, Any

__all__ = [
    "load_tokenizer",
    "fix_tokenizer",
    "add_special_tokens",
    "check_tokenizer",
    "fix_chat_template",
]

logger = logging.getLogger("omnimind.tokenizer")

def load_tokenizer(
    model_name: str,
    model_max_length: Optional[int] = None,
    padding_side: str = "right",
    trust_remote_code: bool = True,
    fix: bool = True,
    cache_dir: Optional[str] = None,
):
    """
    Load tokenizer with automatic fixes.
    
    Args:
        model_name: HuggingFace model name or path
        model_max_length: Maximum sequence length
        padding_side: "left" or "right"
        trust_remote_code: Trust remote code
        fix: Apply automatic fixes
        cache_dir: Cache directory
        
    Returns:
        Tokenizer with fixes applied
    """
    try:
        from transformers import AutoTokenizer
    except ImportError:
        raise ImportError("transformers required: pip install transformers")
    
    print(f"🔄 Loading tokenizer: {model_name}")
    
    kwargs = {
        "trust_remote_code": trust_remote_code,
        "padding_side": padding_side,
    }
    
    if cache_dir:
        kwargs["cache_dir"] = cache_dir
    
    if model_max_length:
        kwargs["model_max_length"] = model_max_length
    
    tokenizer = AutoTokenizer.from_pretrained(model_name, **kwargs)
    
    if fix:
        tokenizer = fix_tokenizer(tokenizer)
    
    print(f"✅ Tokenizer loaded: {len(tokenizer)} tokens")
    return tokenizer

def fix_tokenizer(tokenizer):
    """
    Apply common fixes to tokenizer.
    
    Fixes:
    - Missing pad token (set to eos_token)
    - Missing chat template
    - Incorrect special token settings
    """
    # Fix pad token
    if tokenizer.pad_token is None:
        if tokenizer.eos_token:
            tokenizer.pad_token = tokenizer.eos_token
            tokenizer.pad_token_id = tokenizer.eos_token_id
            logger.info("Set pad_token = eos_token")
        else:
            tokenizer.add_special_tokens({"pad_token": "<pad>"})
            logger.info("Added <pad> token")
    
    # Fix chat template
    fix_chat_template(tokenizer)
    
    return tokenizer

def add_special_tokens(
    tokenizer,
    tokens: List[str],
    special: bool = True,
) -> int:
    """
    Add special tokens to tokenizer.
    
    Args:
        tokenizer: The tokenizer
        tokens: List of tokens to add
        special: Add as special tokens
        
    Returns:
        Number of tokens added
    """
    if special:
        added = tokenizer.add_special_tokens({"additional_special_tokens": tokens})
    else:
        added = tokenizer.add_tokens(tokens)
    
    logger.info(f"Added {added} tokens to tokenizer")
    return added

def check_tokenizer(
    tokenizer,
    model = None,
    test_texts: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Check tokenizer for common issues.
    
    Args:
        tokenizer: Tokenizer to check
        model: Optional model to check embedding size match
        test_texts: Optional test texts for encoding
        
    Returns:
        Dict with check results
    """
    results = {
        "vocab_size": len(tokenizer),
        "has_pad_token": tokenizer.pad_token is not None,
        "has_eos_token": tokenizer.eos_token is not None,
        "has_bos_token": tokenizer.bos_token is not None,
        "has_chat_template": tokenizer.chat_template is not None,
        "padding_side": tokenizer.padding_side,
        "issues": [],
    }
    
    # Check pad token
    if not results["has_pad_token"]:
        results["issues"].append("Missing pad_token")
    
    # Check chat template
    if not results["has_chat_template"]:
        results["issues"].append("Missing chat_template")
    
    # Check model embedding size match
    if model is not None:
        try:
            embed_size = model.get_input_embeddings().weight.shape[0]
            if embed_size != len(tokenizer):
                results["issues"].append(
                    f"Tokenizer size ({len(tokenizer)}) != embedding size ({embed_size})"
                )
                results["embedding_mismatch"] = True
            else:
                results["embedding_mismatch"] = False
        except:
            pass
    
    # Test encoding if texts provided
    if test_texts:
        results["encoding_tests"] = []
        for text in test_texts:
            try:
                encoded = tokenizer.encode(text)
                decoded = tokenizer.decode(encoded)
                roundtrip_ok = text.strip() == decoded.strip()
                results["encoding_tests"].append({
                    "text": text[:50],
                    "token_count": len(encoded),
                    "roundtrip_ok": roundtrip_ok,
                })
            except Exception as e:
                results["encoding_tests"].append({
                    "text": text[:50],
                    "error": str(e),
                })
    
    # Print summary
    if results["issues"]:
        print(f"⚠️ Tokenizer issues: {results['issues']}")
    else:
        print("✅ Tokenizer looks good")
    
    return results

def fix_chat_template(tokenizer):
    """
    Fix or add chat template to tokenizer.
    
    Auto-detects the appropriate template based on model name.
    """
    if tokenizer.chat_template is not None:
        return tokenizer
    
    try:
        from .chat_template import get_chat_template
        get_chat_template(tokenizer)
        logger.info("Applied chat template based on model type")
    except Exception as e:
        logger.debug(f"Could not apply chat template: {e}")
        # Apply generic ChatML template
        tokenizer.chat_template = (
            "{% for message in messages %}"
            "{{'<|im_start|>' + message['role'] + '\n' + message['content'] + '<|im_end|>\n'}}"
            "{% endfor %}"
            "{% if add_generation_prompt %}"
            "{{ '<|im_start|>assistant\n' }}"
            "{% endif %}"
        )
        logger.info("Applied generic ChatML template")
    
    return tokenizer

def resize_model_embeddings(model, tokenizer):
    """
    Resize model embeddings to match tokenizer.
    
    Call this after adding new tokens to tokenizer.
    """
    old_size = model.get_input_embeddings().weight.shape[0]
    new_size = len(tokenizer)
    
    if old_size != new_size:
        model.resize_token_embeddings(new_size)
        print(f"📐 Resized embeddings: {old_size} → {new_size}")
        
        # Initialize new embeddings with mean of existing
        if new_size > old_size:
            with torch.no_grad():
                embeddings = model.get_input_embeddings().weight
                mean_embed = embeddings[:old_size].mean(dim=0)
                embeddings[old_size:] = mean_embed
            print("   New tokens initialized with mean embedding")
    
    return model

def prepare_tokenizer_for_training(tokenizer):
    """
    Prepare tokenizer for training.
    
    Ensures proper settings for efficient training.
    """
    # Right padding is usually best for causal LM
    if tokenizer.padding_side != "right":
        tokenizer.padding_side = "right"
        logger.info("Set padding_side = 'right'")
    
    # Ensure truncation is enabled
    tokenizer.truncation_side = "right"
    
    return tokenizer

# Import torch only when resize is called
import torch
