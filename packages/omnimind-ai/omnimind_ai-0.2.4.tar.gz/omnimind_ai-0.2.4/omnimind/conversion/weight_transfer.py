"""
OMNIMIND Weight Transfer
Transfer weights from Transformer models to OMNIMIND SSM

Strategy:
1. COPY: Embeddings, LayerNorm, LM Head (compatible)
2. INIT: SSM layers with smart initialization from FFN/MLP
3. FINE-TUNE: Quick training to adapt

Benefits:
- Faster than full distillation (hours → minutes)
- Preserves embeddings perfectly
- Only need to train SSM layers
"""
import os
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
import torch
import torch.nn as nn


@dataclass
class TransferConfig:
    """Weight transfer configuration"""
    # Source model
    source_model_id: str = None
    
    # Target OMNIMIND size
    target_size: str = "auto"
    
    # What to transfer
    transfer_embeddings: bool = True
    transfer_lm_head: bool = True
    transfer_norms: bool = True
    transfer_ffn_to_mlp: bool = True  # Partial FFN → MLP transfer
    
    # SSM initialization (ENHANCED)
    ssm_init_from_attention: bool = True  # Use attention patterns for init
    ssm_init_from_mlp: bool = True  # Use MLP weights for SSM projections
    ssm_init_scale: float = 0.02
    use_svd_projection: bool = True  # Use SVD for dimension reduction (more accurate)
    
    # Performance options
    cpu_only: bool = True  # Load on CPU for faster transfer (no GPU needed)
    low_memory: bool = True  # Clear source after transfer
    torch_dtype: str = "float32"  # float32 for accuracy, float16 for speed
    
    # Fine-tuning after transfer
    freeze_transferred: bool = True  # Freeze copied weights
    finetune_steps: int = 1000
    learning_rate: float = 1e-4


class WeightTransfer:
    """
    Transfer weights from Transformer to OMNIMIND SSM
    
    Usage:
        transfer = WeightTransfer("Qwen/Qwen3-4B")
        omnimind = transfer.to_omnimind("mini")
        
        # Then fine-tune
        omnimind.train(dataset)
    """
    
    def __init__(
        self,
        source_model: str,
        config: Optional[TransferConfig] = None
    ):
        self.source_model_id = source_model
        self.config = config or TransferConfig(source_model_id=source_model)
        
        self.source = None
        self.tokenizer = None
        self.target = None
        
        # Track what was transferred
        self.transferred_layers = []
        self.initialized_layers = []
    
    def load_source(self):
        """Load source Transformer model (optimized for CPU transfer)"""
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError:
            raise ImportError("transformers required: pip install transformers")
        
        import time
        start_time = time.time()
        
        print(f"📥 Loading source: {self.source_model_id}")
        
        # Fast tokenizer loading
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.source_model_id, 
            trust_remote_code=True,
            use_fast=True
        )
        
        # Determine dtype
        dtype_map = {
            "float32": torch.float32,
            "float16": torch.float16,
            "bfloat16": torch.bfloat16,
        }
        torch_dtype = dtype_map.get(self.config.torch_dtype, torch.float32)
        
        # CPU-only mode for faster transfer (no GPU memory needed)
        if self.config.cpu_only:
            self.source = AutoModelForCausalLM.from_pretrained(
                self.source_model_id,
                trust_remote_code=True,
                torch_dtype=torch_dtype,
                device_map=None,  # Load to CPU
                low_cpu_mem_usage=True,  # Optimize CPU memory
            )
        else:
            self.source = AutoModelForCausalLM.from_pretrained(
                self.source_model_id,
                trust_remote_code=True,
                torch_dtype=torch_dtype,
                device_map="auto"
            )
        
        # Get source config
        self.source_config = self.source.config
        load_time = time.time() - start_time
        
        print(f"   Hidden size: {self.source_config.hidden_size}")
        print(f"   Num layers: {self.source_config.num_hidden_layers}")
        print(f"   Vocab size: {self.source_config.vocab_size}")
        print(f"   ⏱️ Loaded in {load_time:.1f}s")
    
    def _detect_target_size(self) -> str:
        """Auto-detect appropriate OMNIMIND size"""
        hidden = self.source_config.hidden_size
        
        size_mapping = {
            (0, 384): "nano",
            (384, 640): "micro",
            (640, 896): "small",
            (896, 1280): "mini",
            (1280, 1792): "medium",
            (1792, 2304): "standard",
            (2304, 3072): "large",
            (3072, 4608): "xlarge",
            (4608, 999999): "xxlarge",
        }
        
        for (low, high), size in size_mapping.items():
            if low <= hidden < high:
                return size
        
        return "micro"
    
    def create_target(self, size: str = "auto"):
        """Create target OMNIMIND model"""
        from omnimind.model.config import get_config
        from omnimind.model.omnimind_model import OmnimindForCausalLM
        
        if size == "auto":
            size = self._detect_target_size()
        
        config = get_config(size)
        
        # Match vocab size
        config.vocab_size = self.source_config.vocab_size
        
        # Try to match hidden size for better transfer
        if abs(config.d_model - self.source_config.hidden_size) < 256:
            config.d_model = self.source_config.hidden_size
        
        self.target = OmnimindForCausalLM(config)
        
        print(f"🎯 Target: OMNIMIND {size}")
        print(f"   d_model: {config.d_model}")
        print(f"   n_layers: {config.n_layers}")
        
        return self.target
    
    def transfer_embeddings(self):
        """Transfer embedding weights"""
        if not self.config.transfer_embeddings:
            return
        
        source_embed = self._get_embedding_weight(self.source)
        target_embed = self.target.model.embedding
        
        if source_embed is None:
            print("   ⚠️ Could not find source embeddings")
            return
        
        # Check dimensions
        src_vocab, src_dim = source_embed.shape
        tgt_vocab, tgt_dim = target_embed.weight.shape
        
        if src_vocab != tgt_vocab:
            print(f"   ⚠️ Vocab mismatch: {src_vocab} → {tgt_vocab}")
            # Copy what we can
            min_vocab = min(src_vocab, tgt_vocab)
            with torch.no_grad():
                if src_dim == tgt_dim:
                    target_embed.weight[:min_vocab] = source_embed[:min_vocab]
                else:
                    # Project if dimensions differ
                    target_embed.weight[:min_vocab, :min(src_dim, tgt_dim)] = \
                        source_embed[:min_vocab, :min(src_dim, tgt_dim)]
        else:
            with torch.no_grad():
                if src_dim == tgt_dim:
                    target_embed.weight.copy_(source_embed)
                else:
                    # Use projection if needed
                    target_embed.weight[:, :min(src_dim, tgt_dim)] = \
                        source_embed[:, :min(src_dim, tgt_dim)]
        
        self.transferred_layers.append("embedding")
        print("   ✅ Embeddings transferred")
    
    def transfer_lm_head(self):
        """Transfer LM head weights"""
        if not self.config.transfer_lm_head:
            return
        
        source_lm = self._get_lm_head_weight(self.source)
        target_lm = self.target.model.lm_head if hasattr(self.target.model, 'lm_head') else self.target.lm_head
        
        if source_lm is None:
            print("   ⚠️ Could not find source LM head")
            return
        
        with torch.no_grad():
            src_vocab, src_dim = source_lm.shape
            tgt_vocab, tgt_dim = target_lm.weight.shape
            
            min_vocab = min(src_vocab, tgt_vocab)
            min_dim = min(src_dim, tgt_dim)
            
            target_lm.weight[:min_vocab, :min_dim] = source_lm[:min_vocab, :min_dim]
        
        self.transferred_layers.append("lm_head")
        print("   ✅ LM Head transferred")
    
    def transfer_norms(self):
        """Transfer LayerNorm/RMSNorm weights"""
        if not self.config.transfer_norms:
            return
        
        # Get all norm layers from source
        source_norms = {}
        for name, module in self.source.named_modules():
            if 'norm' in name.lower() or 'ln' in name.lower():
                if hasattr(module, 'weight') and module.weight is not None:
                    source_norms[name] = module.weight.data
        
        # Try to match with target norms
        norm_count = 0
        for name, module in self.target.named_modules():
            if 'norm' in name.lower():
                if hasattr(module, 'weight'):
                    # Find matching source norm by position
                    for src_name, src_weight in source_norms.items():
                        if src_weight.shape == module.weight.shape:
                            with torch.no_grad():
                                module.weight.copy_(src_weight)
                            norm_count += 1
                            break
        
        if norm_count > 0:
            self.transferred_layers.append(f"norms ({norm_count})")
            print(f"   ✅ {norm_count} norm layers transferred")
    
    def init_ssm_from_attention(self):
        """
        Initialize SSM layers using attention patterns with PRECISE spectral mapping.
        
        Uses the improved conversion algorithm from advanced_conversion module.
        """
        if not self.config.ssm_init_from_attention:
            return
        
        # Import the improved conversion function
        try:
            from .advanced_conversion import (
                attention_to_ssm_weights, 
                ConversionConfig,
                convert_layer_attention_to_ssm
            )
            use_advanced = True
        except ImportError:
            use_advanced = False
        
        # Get attention layers from source
        attention_layers = []
        for name, module in self.source.named_modules():
            if 'attn' in name.lower() or 'attention' in name.lower():
                # Check if it has Q/K/V projections
                has_qkv = (hasattr(module, 'q_proj') or hasattr(module, 'query') or 
                          hasattr(module, 'qkv_proj'))
                if has_qkv:
                    attention_layers.append((name, module))
        
        # Get SSM layers from target
        ssm_layers = []
        for name, module in self.target.named_modules():
            if 'ssm' in name.lower() or 'selective' in name.lower():
                if hasattr(module, 'in_proj'):
                    ssm_layers.append((name, module))
        
        ssm_count = 0
        
        if use_advanced and attention_layers and ssm_layers:
            # Use precise spectral conversion
            print(f"   🔬 Using spectral attention→SSM conversion")
            
            # Configure for best quality
            conv_config = ConversionConfig(
                method="spectral",
                a_init="spectral",
                use_spectral_matching=True,
                use_procrustes_align=True,
                preserve_norm=True
            )
            
            # Match layers by index
            n_layers = min(len(attention_layers), len(ssm_layers))
            for i in range(n_layers):
                attn_name, attn_module = attention_layers[i]
                ssm_name, ssm_module = ssm_layers[i]
                
                try:
                    # Get d_state from target config or SSM module
                    d_state = getattr(ssm_module, 'd_state', 16)
                    
                    # Use the advanced conversion
                    convert_layer_attention_to_ssm(attn_module, ssm_module, d_state)
                    ssm_count += 1
                except Exception as e:
                    print(f"   ⚠️ Layer {i} conversion failed: {e}")
                    # Fallback to basic init for this layer
                    self._basic_ssm_init(ssm_module)
                    ssm_count += 1
        else:
            # Fallback to basic initialization
            for name, module in self.target.named_modules():
                if 'ssm' in name.lower() or 'selective' in name.lower():
                    self._basic_ssm_init(module)
                    ssm_count += 1
        
        self.initialized_layers.append(f"ssm ({ssm_count} layers)")
        print(f"   ✅ {ssm_count} SSM layers initialized")
    
    def _basic_ssm_init(self, module: nn.Module):
        """Basic SSM initialization fallback"""
        for pname, param in module.named_parameters():
            if param.requires_grad:
                with torch.no_grad():
                    if 'A' in pname or 'a_' in pname.lower():
                        nn.init.uniform_(param, -1.0, -0.1)
                    elif 'dt' in pname.lower():
                        nn.init.uniform_(param, 0.001, 0.1)
                    else:
                        nn.init.normal_(param, 0, self.config.ssm_init_scale)
    
    def init_ssm_from_mlp(self):
        """
        🔥 Advanced: Initialize SSM projections from MLP/FFN weights
        
        This provides better accuracy by reusing learned features.
        Uses SVD for dimension reduction when needed.
        """
        if not self.config.ssm_init_from_mlp:
            return
        
        # Collect MLP weights from source
        mlp_weights = {}
        for name, module in self.source.named_modules():
            if 'mlp' in name.lower() or 'ffn' in name.lower():
                for pname, param in module.named_parameters():
                    if 'weight' in pname:
                        mlp_weights[f"{name}.{pname}"] = param.data.clone()
        
        if not mlp_weights:
            return
        
        print(f"   🔍 Found {len(mlp_weights)} MLP weights")
        
        transferred = 0
        for name, module in self.target.named_modules():
            if 'ssm' in name.lower():
                # Find in_proj and out_proj
                if hasattr(module, 'in_proj') and hasattr(module.in_proj, 'weight'):
                    # Use gate_proj or up_proj for in_proj
                    for mlp_name, mlp_weight in mlp_weights.items():
                        if 'gate' in mlp_name.lower() or 'up' in mlp_name.lower():
                            projected = self._svd_project(
                                mlp_weight, 
                                module.in_proj.weight.shape
                            )
                            if projected is not None:
                                with torch.no_grad():
                                    module.in_proj.weight.copy_(projected)
                                transferred += 1
                            break
                
                if hasattr(module, 'out_proj') and hasattr(module.out_proj, 'weight'):
                    # Use down_proj for out_proj
                    for mlp_name, mlp_weight in mlp_weights.items():
                        if 'down' in mlp_name.lower():
                            projected = self._svd_project(
                                mlp_weight,
                                module.out_proj.weight.shape
                            )
                            if projected is not None:
                                with torch.no_grad():
                                    module.out_proj.weight.copy_(projected)
                                transferred += 1
                            break
        
        if transferred > 0:
            self.transferred_layers.append(f"mlp→ssm ({transferred})")
            print(f"   ✅ {transferred} MLP→SSM projections transferred")
    
    def _svd_project(self, source: torch.Tensor, target_shape: tuple) -> Optional[torch.Tensor]:
        """
        Use SVD for dimension reduction/expansion while preserving key features.
        
        More accurate than simple truncation or mean pooling.
        """
        if not self.config.use_svd_projection:
            # Fallback to simple truncation
            return self._simple_project(source, target_shape)
        
        try:
            src_out, src_in = source.shape
            tgt_out, tgt_in = target_shape
            
            # SVD decomposition
            U, S, Vh = torch.linalg.svd(source.float(), full_matrices=False)
            
            # Keep top-k singular values
            k_out = min(src_out, tgt_out)
            k_in = min(src_in, tgt_in)
            k = min(k_out, k_in, len(S))
            
            # Reconstruct with reduced dimensions
            U_k = U[:, :k]
            S_k = S[:k]
            Vh_k = Vh[:k, :]
            
            # Create projected matrix
            if tgt_out <= src_out and tgt_in <= src_in:
                # Reduction
                projected = U_k[:tgt_out] @ torch.diag(S_k) @ Vh_k[:, :tgt_in]
            else:
                # Need expansion - use zeros for extra dims
                projected = torch.zeros(target_shape, dtype=source.dtype)
                core = U_k[:min(tgt_out, src_out)] @ torch.diag(S_k) @ Vh_k[:, :min(tgt_in, src_in)]
                projected[:core.shape[0], :core.shape[1]] = core
            
            return projected.to(source.dtype)
            
        except Exception as e:
            print(f"   ⚠️ SVD failed: {e}, using simple projection")
            return self._simple_project(source, target_shape)
    
    def _simple_project(self, source: torch.Tensor, target_shape: tuple) -> torch.Tensor:
        """Simple truncation/padding projection"""
        src_out, src_in = source.shape
        tgt_out, tgt_in = target_shape
        
        projected = torch.zeros(target_shape, dtype=source.dtype)
        projected[:min(src_out, tgt_out), :min(src_in, tgt_in)] = \
            source[:min(src_out, tgt_out), :min(src_in, tgt_in)]
        
        return projected

    
    def _get_embedding_weight(self, model) -> Optional[torch.Tensor]:
        """Extract embedding weight from various model architectures"""
        # Common attribute names
        for attr in ['embed_tokens', 'wte', 'word_embeddings', 'embeddings', 'embed']:
            if hasattr(model, attr):
                embed = getattr(model, attr)
                if hasattr(embed, 'weight'):
                    return embed.weight.data.clone()
            if hasattr(model, 'model') and hasattr(model.model, attr):
                embed = getattr(model.model, attr)
                if hasattr(embed, 'weight'):
                    return embed.weight.data.clone()
        
        # Search recursively
        for name, module in model.named_modules():
            if 'embed' in name.lower() and hasattr(module, 'weight'):
                if len(module.weight.shape) == 2:
                    return module.weight.data.clone()
        
        return None
    
    def _get_lm_head_weight(self, model) -> Optional[torch.Tensor]:
        """Extract LM head weight"""
        for attr in ['lm_head', 'output', 'classifier']:
            if hasattr(model, attr):
                head = getattr(model, attr)
                if hasattr(head, 'weight'):
                    return head.weight.data.clone()
        
        return None
    
    def transfer(self, target_size: str = "auto") -> Tuple[nn.Module, Any]:
        """
        Full weight transfer pipeline (optimized for speed and accuracy)
        
        Returns:
            (omnimind_model, tokenizer)
        """
        import time
        import gc
        
        total_start = time.time()
        
        print("\n🔄 Starting Weight Transfer...")
        print("=" * 50)
        
        # 1. Load source
        if self.source is None:
            self.load_source()
        
        # 2. Create target
        if self.target is None:
            self.create_target(target_size)
        
        print("\n📦 Transferring weights:")
        
        # 3. Transfer embeddings
        self.transfer_embeddings()
        
        # 4. Transfer LM head
        self.transfer_lm_head()
        
        # 5. Transfer norms
        self.transfer_norms()
        
        # 6. Initialize SSM layers from attention
        self.init_ssm_from_attention()
        
        # 7. Initialize SSM projections from MLP (ENHANCED)
        self.init_ssm_from_mlp()
        
        # 8. Freeze transferred layers if requested
        if self.config.freeze_transferred:
            self._freeze_transferred()
        
        # 9. Clear source model to free memory
        if self.config.low_memory:
            print("\n🧹 Clearing source model from memory...")
            del self.source
            self.source = None
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        
        total_time = time.time() - total_start
        
        print("\n" + "=" * 50)
        print("✅ Transfer complete!")
        print(f"   Transferred: {', '.join(self.transferred_layers)}")
        print(f"   Initialized: {', '.join(self.initialized_layers)}")
        print(f"   ⏱️ Total time: {total_time:.1f}s")
        print(f"   Next step: Fine-tune SSM layers with your data")
        
        return self.target, self.tokenizer
    
    def _freeze_transferred(self):
        """Freeze transferred weights (only train SSM)"""
        frozen = 0
        
        # Freeze embeddings
        if 'embedding' in str(self.transferred_layers):
            for param in self.target.model.embedding.parameters():
                param.requires_grad = False
                frozen += 1
        
        # Freeze LM head
        if 'lm_head' in str(self.transferred_layers):
            lm_head = self.target.model.lm_head if hasattr(self.target.model, 'lm_head') else self.target.lm_head
            for param in lm_head.parameters():
                param.requires_grad = False
                frozen += 1
        
        print(f"   🔒 Frozen {frozen} transferred layers (train only SSM)")


def transfer_to_omnimind(
    source_model: str,
    target_size: str = "auto",
    freeze_transferred: bool = True
) -> Tuple[nn.Module, Any]:
    """
    Quick function to transfer Transformer weights to OMNIMIND
    
    Args:
        source_model: HuggingFace model ID (e.g., "Qwen/Qwen3-4B")
        target_size: OMNIMIND size or "auto"
        freeze_transferred: Freeze copied weights (train only SSM)
        
    Returns:
        (omnimind_model, tokenizer)
        
    Example:
        model, tokenizer = transfer_to_omnimind("Qwen/Qwen3-4B")
        
        # Fine-tune SSM layers (fast!)
        trainer.train(model, dataset)
    """
    config = TransferConfig(
        source_model_id=source_model,
        freeze_transferred=freeze_transferred
    )
    
    transfer = WeightTransfer(source_model, config)
    return transfer.transfer(target_size)


# Convenience functions
def from_qwen(model_id: str, size: str = "auto"):
    """Transfer from Qwen model"""
    return transfer_to_omnimind(model_id, size)


def from_llama(model_id: str, size: str = "auto"):
    """Transfer from Llama model"""
    return transfer_to_omnimind(model_id, size)


def from_gemma(model_id: str, size: str = "auto"):
    """Transfer from Gemma model"""
    return transfer_to_omnimind(model_id, size)


if __name__ == "__main__":
    print("Weight Transfer Example:")
    print()
    print("  from omnimind import transfer_to_omnimind")
    print()
    print("  # Transfer Qwen weights to OMNIMIND")
    print("  model, tokenizer = transfer_to_omnimind('Qwen/Qwen3-4B')")
    print()
    print("  # Then fine-tune only SSM layers (fast!)")
    print("  trainer.train(model, dataset)")
