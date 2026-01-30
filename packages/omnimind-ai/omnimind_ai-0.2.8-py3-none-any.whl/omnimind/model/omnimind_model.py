"""
OMNIMIND Full Model
Complete State-Space Language Model
"""
from typing import Optional, Tuple, List, Dict, Any
import torch
import torch.nn as nn
import torch.nn.functional as F

from .config import OmnimindConfig, get_config
from .ssm_layer import OmnimindBlock, RMSNorm


class OmnimindModel(nn.Module):
    """
    OMNIMIND Language Model
    
    Architecture:
        Embedding -> [SSM Block] x N -> Norm -> LM Head
    
    Properties:
        - O(n) complexity
        - Fixed state size
        - Streaming generation
    """
    
    def __init__(self, config: OmnimindConfig):
        super().__init__()
        self.config = config
        
        # Token embedding
        self.embedding = nn.Embedding(
            config.vocab_size, 
            config.d_model,
            padding_idx=config.pad_token_id
        )
        
        # SSM layers
        self.layers = nn.ModuleList([
            OmnimindBlock(config, layer_idx=i)
            for i in range(config.n_layers)
        ])
        
        # Final normalization
        self.norm = RMSNorm(config.d_model)
        
        # Language model head
        self.lm_head = nn.Linear(config.d_model, config.vocab_size, bias=False)
        
        # Tie embeddings
        if config.tie_embeddings:
            self.lm_head.weight = self.embedding.weight
        
        # Initialize weights
        self.apply(self._init_weights)
    
    def _init_weights(self, module: nn.Module):
        """Initialize weights"""
        if isinstance(module, nn.Linear):
            nn.init.normal_(module.weight, mean=0.0, std=self.config.initializer_range)
            if module.bias is not None:
                nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            nn.init.normal_(module.weight, mean=0.0, std=self.config.initializer_range)
            if module.padding_idx is not None:
                module.weight.data[module.padding_idx].zero_()
    
    def forward(
        self,
        input_ids: torch.Tensor,
        cache: Optional[List[Tuple[torch.Tensor, torch.Tensor]]] = None,
        return_cache: bool = False
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass
        
        Args:
            input_ids: (batch, seq_len)
            cache: Optional list of (conv_state, ssm_state) per layer
            return_cache: Whether to return updated cache
            
        Returns:
            dict with:
                logits: (batch, seq_len, vocab_size)
                cache: Updated cache (if return_cache=True)
        """
        # Embed tokens
        hidden_states = self.embedding(input_ids)  # (B, L, D)
        
        # Initialize cache if needed
        if cache is None:
            cache = [None] * len(self.layers)
        
        new_cache = []
        
        # Apply SSM layers
        for layer_idx, layer in enumerate(self.layers):
            hidden_states, layer_cache = layer(hidden_states, cache[layer_idx])
            new_cache.append(layer_cache)
        
        # Final norm
        hidden_states = self.norm(hidden_states)
        
        # LM head
        logits = self.lm_head(hidden_states)
        
        result = {"logits": logits}
        if return_cache:
            result["cache"] = new_cache
        
        return result
    
    def generate(
        self,
        input_ids: torch.Tensor,
        max_new_tokens: int = 100,
        temperature: float = 1.0,
        top_k: int = 50,
        top_p: float = 0.9,
        repetition_penalty: float = 1.0,
        eos_token_id: Optional[int] = None,
    ) -> torch.Tensor:
        """
        Generate tokens autoregressively
        
        Args:
            input_ids: (batch, seq_len) initial tokens
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_k: Top-k sampling
            top_p: Nucleus sampling threshold
            repetition_penalty: Penalty for repeated tokens
            eos_token_id: Stop token
            
        Returns:
            generated: (batch, seq_len + max_new_tokens)
        """
        eos_token_id = eos_token_id or self.config.eos_token_id
        batch_size = input_ids.shape[0]
        device = input_ids.device
        
        # Process prompt to get initial cache
        with torch.no_grad():
            outputs = self.forward(input_ids, return_cache=True)
            cache = outputs["cache"]
            
            # Get next token from last position
            logits = outputs["logits"][:, -1, :]
        
        generated = input_ids.clone()
        
        for _ in range(max_new_tokens):
            # Apply repetition penalty
            if repetition_penalty != 1.0:
                for i in range(batch_size):
                    for token_id in set(generated[i].tolist()):
                        logits[i, token_id] /= repetition_penalty
            
            # Sample next token
            next_token = self._sample(
                logits, 
                temperature=temperature, 
                top_k=top_k, 
                top_p=top_p
            )
            
            # Check for EOS
            if (next_token == eos_token_id).all():
                break
            
            # Append token
            generated = torch.cat([generated, next_token.unsqueeze(1)], dim=1)
            
            # Forward one step with cache
            with torch.no_grad():
                outputs = self.forward(next_token.unsqueeze(1), cache=cache, return_cache=True)
                cache = outputs["cache"]
                logits = outputs["logits"][:, -1, :]
        
        return generated
    
    def _sample(
        self,
        logits: torch.Tensor,
        temperature: float = 1.0,
        top_k: int = 50,
        top_p: float = 0.9,
    ) -> torch.Tensor:
        """Sample from logits"""
        if temperature == 0:
            return logits.argmax(dim=-1)
        
        # Apply temperature
        logits = logits / temperature
        
        # Top-k filtering
        if top_k > 0:
            indices_to_remove = logits < torch.topk(logits, top_k)[0][..., -1, None]
            logits[indices_to_remove] = float('-inf')
        
        # Top-p (nucleus) filtering
        if top_p < 1.0:
            sorted_logits, sorted_indices = torch.sort(logits, descending=True)
            cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)
            
            # Remove tokens with cumulative probability above threshold
            sorted_indices_to_remove = cumulative_probs > top_p
            sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
            sorted_indices_to_remove[..., 0] = 0
            
            indices_to_remove = sorted_indices_to_remove.scatter(
                dim=-1, index=sorted_indices, src=sorted_indices_to_remove
            )
            logits[indices_to_remove] = float('-inf')
        
        # Sample
        probs = F.softmax(logits, dim=-1)
        next_token = torch.multinomial(probs, num_samples=1).squeeze(-1)
        
        return next_token
    
    @property
    def num_parameters(self) -> int:
        """Count total parameters"""
        return sum(p.numel() for p in self.parameters())
    
    @property
    def num_trainable_parameters(self) -> int:
        """Count trainable parameters"""
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
    
    def compile(self, mode: str = "reduce-overhead"):
        """
        Compile model with torch.compile for faster inference.
        
        Args:
            mode: Compilation mode ("default", "reduce-overhead", "max-autotune")
            
        Returns:
            Compiled model
        """
        if hasattr(torch, "compile"):
            return torch.compile(self, mode=mode)
        else:
            print("⚠️ torch.compile requires PyTorch 2.0+")
            return self
    
    @torch.inference_mode()
    def fast_generate(
        self,
        input_ids: torch.Tensor,
        max_new_tokens: int = 100,
        temperature: float = 1.0,
        top_k: int = 50,
        eos_token_id: int = None,
    ) -> torch.Tensor:
        """
        Optimized generation with pre-allocated output.
        
        ~2x faster than regular generate() for long sequences.
        """
        batch_size = input_ids.shape[0]
        device = input_ids.device
        
        # Pre-allocate output tensor
        generated = torch.empty(
            batch_size, input_ids.shape[1] + max_new_tokens,
            dtype=torch.long, device=device
        )
        generated[:, :input_ids.shape[1]] = input_ids
        gen_idx = input_ids.shape[1]
        
        # Initial forward
        outputs = self.forward(input_ids, return_cache=True)
        cache = outputs["cache"]
        logits = outputs["logits"][:, -1, :]
        
        for i in range(max_new_tokens):
            # Fast sampling (greedy or top-k only)
            if temperature == 0:
                next_token = logits.argmax(dim=-1)
            else:
                logits = logits / temperature
                if top_k > 0:
                    v, _ = torch.topk(logits, min(top_k, logits.size(-1)))
                    logits[logits < v[:, [-1]]] = float('-inf')
                probs = torch.softmax(logits, dim=-1)
                next_token = torch.multinomial(probs, 1).squeeze(-1)
            
            # Store in pre-allocated tensor
            generated[:, gen_idx] = next_token
            gen_idx += 1
            
            # Check EOS
            if eos_token_id is not None and (next_token == eos_token_id).all():
                break
            
            # Next step
            outputs = self.forward(next_token.unsqueeze(1), cache=cache, return_cache=True)
            cache = outputs["cache"]
            logits = outputs["logits"][:, -1, :]
        
        return generated[:, :gen_idx]
    
    def optimize_for_training(self, use_gradient_checkpointing: bool = True):
        """
        Apply training optimizations.
        
        - Enable gradient checkpointing for memory efficiency
        - Enable mixed precision hints
        """
        self.train()
        
        if use_gradient_checkpointing:
            # Enable gradient checkpointing for memory efficiency
            for layer in self.layers:
                layer.ssm.gradient_checkpointing = True
            print("✅ Gradient checkpointing enabled")
        
        # Enable input gradients
        self.embedding.weight.requires_grad_(True)
        
        return self


class OmnimindForCausalLM(nn.Module):
    """
    OMNIMIND for Causal Language Modeling
    
    Wrapper with loss computation for training
    """
    
    def __init__(self, config: OmnimindConfig):
        super().__init__()
        self.config = config
        self.model = OmnimindModel(config)
    
    def forward(
        self,
        input_ids: torch.Tensor,
        labels: Optional[torch.Tensor] = None,
        cache: Optional[List] = None,
        return_cache: bool = False,
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass with optional loss computation
        
        Args:
            input_ids: (batch, seq_len)
            labels: (batch, seq_len) for computing loss
            cache: Optional SSM cache
            return_cache: Whether to return cache
            
        Returns:
            dict with logits, loss (if labels provided), cache (if requested)
        """
        outputs = self.model(input_ids, cache=cache, return_cache=return_cache)
        logits = outputs["logits"]
        
        result = {"logits": logits}
        
        if labels is not None:
            # Shift for causal LM
            shift_logits = logits[..., :-1, :].contiguous()
            shift_labels = labels[..., 1:].contiguous()
            
            # Compute loss
            loss = F.cross_entropy(
                shift_logits.view(-1, self.config.vocab_size),
                shift_labels.view(-1),
                ignore_index=self.config.pad_token_id
            )
            result["loss"] = loss
        
        if return_cache and "cache" in outputs:
            result["cache"] = outputs["cache"]
        
        return result
    
    def generate(self, *args, **kwargs):
        """Delegate to inner model"""
        return self.model.generate(*args, **kwargs)
    
    def save_pretrained(self, save_directory: str):
        """
        Save model and config in HuggingFace-compatible format.
        
        Saves:
        - config.json
        - model.safetensors
        """
        import os
        import json
        from safetensors.torch import save_file
        
        os.makedirs(save_directory, exist_ok=True)
        
        # Save config.json
        config_path = os.path.join(save_directory, "config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            # Convert config to dict, ensuring JSON serialization
            config_dict = self.config.__dict__.copy()
            # Handle Enums (like ModelSize)
            for k, v in config_dict.items():
                if hasattr(v, "value"):
                    config_dict[k] = v.value
                    
            # Add auto_map or architecture info if needed for generic loading
            config_dict["architectures"] = ["OmnimindForCausalLM"]
            config_dict["model_type"] = "omnimind"
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
        # Save model.safetensors
        # Handle shared tensors (embedding <-> lm_head)
        state_dict = self.state_dict()
        if self.config.tie_embeddings:
            # Safetensors doesn't support shared storage. 
            # We must duplicate (clone) the tensor for saving or removing one.
            # Standard Practice: Remove the duplicate key if loading logic handles tying,
            # BUT for generic loading, cloning is safer so both keys exist.
            if "model.lm_head.weight" in state_dict and "model.embedding.weight" in state_dict:
                # Check if they really share memory
                if state_dict["model.lm_head.weight"].data_ptr() == state_dict["model.embedding.weight"].data_ptr():
                    state_dict["model.lm_head.weight"] = state_dict["model.lm_head.weight"].clone()
                    
        model_path = os.path.join(save_directory, "model.safetensors")
        save_file(state_dict, model_path)
        
        # Save README.md (Model Card)
        readme_content = f"""---
language:
- th
- en
tags:
- omnimind
- ssm
- state-space-model
pipeline_tag: text-generation
---

# OMNIMIND ({self.config.d_model} dim, {self.config.n_layers} layers)

This is a **State-Space Language Model** built with [OMNIMIND](https://github.com/kue-kid/omnimind).

## Usage
```python
from omnimind import create_model

model = create_model("micro")
# Load weights...
```
"""
        with open(os.path.join(save_directory, "README.md"), "w", encoding="utf-8") as f:
            f.write(readme_content)

        print(f"✅ Model saved to {save_directory}")
    
    def save_pretrained_streaming(self, save_directory: str, max_shard_size_gb: float = 2.0):
        """
        Memory-efficient save for large models on Kaggle (30GB RAM).
        
        Saves weights layer-by-layer to avoid OOM during save.
        Creates sharded safetensors files.
        
        Args:
            save_directory: Directory to save model
            max_shard_size_gb: Maximum size per shard (default 2GB)
        """
        import os
        import json
        import gc
        from safetensors.torch import save_file
        
        os.makedirs(save_directory, exist_ok=True)
        
        print(f"💾 Streaming save to {save_directory}...")
        
        # Save config.json first
        config_path = os.path.join(save_directory, "config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            config_dict = self.config.__dict__.copy()
            for k, v in config_dict.items():
                if hasattr(v, "value"):
                    config_dict[k] = v.value
            config_dict["architectures"] = ["OmnimindForCausalLM"]
            config_dict["model_type"] = "omnimind"
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
        
        # Shard weights by layer
        max_shard_bytes = int(max_shard_size_gb * 1024 * 1024 * 1024)
        weight_map = {}
        shard_idx = 0
        current_shard = {}
        current_shard_size = 0
        total_size = 0
        
        # Process parameters one at a time
        for name, param in self.named_parameters():
            # Get tensor size in bytes
            tensor = param.data.cpu()
            tensor_bytes = tensor.numel() * tensor.element_size()
            total_size += tensor_bytes
            
            # Check if we need new shard
            if current_shard_size + tensor_bytes > max_shard_bytes and current_shard:
                # Save current shard
                shard_name = f"model-{shard_idx:05d}-of-XXXXX.safetensors"
                shard_path = os.path.join(save_directory, shard_name)
                save_file(current_shard, shard_path)
                print(f"   💾 Saved shard {shard_idx}: {current_shard_size / (1024**3):.2f} GB")
                
                # Update weight map
                for tensor_name in current_shard.keys():
                    weight_map[tensor_name] = shard_name
                
                # Clear and start new shard
                del current_shard
                gc.collect()
                current_shard = {}
                current_shard_size = 0
                shard_idx += 1
            
            # Add to current shard
            current_shard[name] = tensor
            current_shard_size += tensor_bytes
            
            # Cleanup
            del tensor
        
        # Save final shard
        if current_shard:
            shard_name = f"model-{shard_idx:05d}-of-{shard_idx+1:05d}.safetensors"
            shard_path = os.path.join(save_directory, shard_name)
            save_file(current_shard, shard_path)
            print(f"   💾 Saved shard {shard_idx}: {current_shard_size / (1024**3):.2f} GB")
            
            for tensor_name in current_shard.keys():
                weight_map[tensor_name] = shard_name
            
            del current_shard
            gc.collect()
        
        # Fix shard names with correct total
        total_shards = shard_idx + 1
        for old_name in list(weight_map.values()):
            new_name = old_name.replace("XXXXX", f"{total_shards:05d}")
            if old_name != new_name:
                old_path = os.path.join(save_directory, old_name)
                new_path = os.path.join(save_directory, new_name)
                if os.path.exists(old_path):
                    os.rename(old_path, new_path)
                # Update weight map
                for k, v in weight_map.items():
                    if v == old_name:
                        weight_map[k] = new_name
        
        # Save index file
        index = {
            "metadata": {"total_size": total_size},
            "weight_map": weight_map
        }
        index_path = os.path.join(save_directory, "model.safetensors.index.json")
        with open(index_path, "w") as f:
            json.dump(index, f, indent=2)
        
        print(f"✅ Streaming save complete!")
        print(f"   📊 Total size: {total_size / (1024**3):.2f} GB")
        print(f"   📁 Shards: {total_shards}")
    
    @classmethod
    def from_config(cls, size: str = "micro") -> "OmnimindForCausalLM":
        """Create model from size name"""
        config = get_config(size)
        return cls(config)


def create_model(size: str = "micro") -> OmnimindForCausalLM:
    """Factory function to create OMNIMIND model"""
    return OmnimindForCausalLM.from_config(size)


if __name__ == "__main__":
    # Test model creation
    print("Creating OMNIMIND models...")
    
    for size in ["nano", "micro", "mini"]:
        model = create_model(size)
        params = model.model.num_parameters
        print(f"\n{size.upper()}: {params / 1e6:.1f}M parameters")
        
        # Test forward pass
        dummy_input = torch.randint(0, 1000, (2, 32))
        outputs = model(dummy_input)
        print(f"  Logits shape: {outputs['logits'].shape}")
        
        # Test with labels
        dummy_labels = torch.randint(0, 1000, (2, 32))
        outputs = model(dummy_input, labels=dummy_labels)
        print(f"  Loss: {outputs['loss'].item():.4f}")
