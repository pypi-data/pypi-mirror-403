"""
OMNIMIND Model Configuration
Model variants from TINY (1M) to XXLARGE (13B+)

Scales:
- TINY:     ~1M params   - Embedded/IoT
- NANO:     ~10M params  - Mobile/Edge
- MICRO:    ~50M params  - Laptop
- SMALL:    ~125M params - Desktop  
- MINI:     ~350M params - Workstation
- MEDIUM:   ~770M params - Single GPU
- STANDARD: ~1.5B params - Multi-GPU
- LARGE:    ~3B params   - Server
- XLARGE:   ~7B params   - Data Center
- XXLARGE:  ~13B params  - Cloud
"""
from dataclasses import dataclass
from typing import Optional, Union
from enum import Enum


class ModelSize(Enum):
    """Model size variants - Production scale from 1M to 13B+"""
    TINY = "tiny"           # ~1M params - Embedded/IoT
    NANO = "nano"           # ~10M params - Mobile/Edge
    MICRO = "micro"         # ~50M params - Laptop  
    SMALL = "small"         # ~125M params - Desktop
    MINI = "mini"           # ~350M params - Workstation
    MEDIUM = "medium"       # ~770M params - Single GPU
    STANDARD = "standard"   # ~1.5B params - Multi-GPU
    LARGE = "large"         # ~3B params - Server
    XLARGE = "xlarge"       # ~7B params - Data Center
    XXLARGE = "xxlarge"     # ~13B params - Cloud
    MEGA = "mega"           # ~70B params - Cluster
    GIGANTIC = "gigantic"   # ~175B params - Supercomputer
    TITAN = "titan"         # ~225B+ params - Planetary Scale


@dataclass
class OmnimindConfig:
    """
    OMNIMIND Model Configuration
    
    State-Space Model ที่ออกแบบสำหรับ:
    - O(n) complexity
    - Constant memory
    - รันบน edge device ได้
    """
    # Model size
    name: str = "omnimind-micro"
    size: ModelSize = ModelSize.MICRO
    
    # Architecture dimensions
    d_model: int = 512       # Hidden dimension
    n_layers: int = 12       # Number of SSM layers
    d_state: int = 16        # SSM state dimension
    d_conv: int = 4          # Convolution width
    expand: int = 2          # Expansion factor for inner dimension
    n_heads: int = 8         # Number of heads (unused in Pure SSM unless Multi-head SSM)
    
    # Vocabulary
    vocab_size: int = 32000  # Vocabulary size (can be overridden)
    pad_token_id: int = 0
    bos_token_id: int = 1
    eos_token_id: int = 2
    
    # Sequence
    max_seq_len: int = 8192  # Maximum sequence length
    
    # Training
    dropout: float = 0.1
    tie_embeddings: bool = True
    
    # SSM specific
    dt_rank: str = "auto"    # Δ rank (auto = d_model // 16)
    dt_min: float = 0.001
    dt_max: float = 0.1
    dt_init: str = "random"  # "random" or "constant"
    dt_scale: float = 1.0
    dt_init_floor: float = 1e-4
    
    # RoPE (unused in Pure SSM)
    rope_theta: float = 10000.0
    
    # Initialization
    initializer_range: float = 0.02
    
    @property
    def d_inner(self) -> int:
        """Inner dimension (expanded)"""
        return self.d_model * self.expand
    
    @property
    def dt_rank_value(self) -> int:
        """Actual dt_rank value"""
        if self.dt_rank == "auto":
            return max(self.d_model // 16, 1)
        return int(self.dt_rank)


# Predefined configurations for each size
OMNIMIND_CONFIGS = {
    ModelSize.TINY: OmnimindConfig(
        name="omnimind-tiny",
        size=ModelSize.TINY,
        d_model=128,
        n_layers=4,
        d_state=8,
        n_heads=4,
        expand=2,
        vocab_size=32000,
        max_seq_len=2048,
    ),
    ModelSize.NANO: OmnimindConfig(
        name="omnimind-nano",
        size=ModelSize.NANO,
        d_model=256,
        n_layers=6,
        d_state=8,
        n_heads=4,
        expand=2,
        vocab_size=32000,
        max_seq_len=4096,
    ),
    ModelSize.MICRO: OmnimindConfig(
        name="omnimind-micro",
        size=ModelSize.MICRO,
        d_model=512,
        n_layers=12,
        d_state=16,
        n_heads=8,
        expand=2,
        vocab_size=32000,
        max_seq_len=8192,
    ),
    ModelSize.SMALL: OmnimindConfig(
        name="omnimind-small",
        size=ModelSize.SMALL,
        d_model=768,
        n_layers=12,
        d_state=16,
        n_heads=12,
        expand=2,
        vocab_size=32000,
        max_seq_len=8192,
    ),
    ModelSize.MINI: OmnimindConfig(
        name="omnimind-mini",
        size=ModelSize.MINI,
        d_model=1024,
        n_layers=24,
        d_state=16,
        n_heads=16,
        expand=2,
        vocab_size=32000,
        max_seq_len=16384,
    ),
    ModelSize.MEDIUM: OmnimindConfig(
        name="omnimind-medium",
        size=ModelSize.MEDIUM,
        d_model=1536,
        n_layers=24,
        d_state=24,
        n_heads=16,
        expand=2,
        vocab_size=32000,
        max_seq_len=16384,
    ),
    ModelSize.STANDARD: OmnimindConfig(
        name="omnimind-standard",
        size=ModelSize.STANDARD,
        d_model=2048,
        n_layers=24,
        d_state=32,
        n_heads=16,
        expand=2,
        vocab_size=32000,
        max_seq_len=32768,
    ),
    ModelSize.LARGE: OmnimindConfig(
        name="omnimind-large",
        size=ModelSize.LARGE,
        d_model=2560,
        n_layers=32,
        d_state=32,
        n_heads=20,
        expand=2,
        vocab_size=65536,
        max_seq_len=32768,
    ),
    ModelSize.XLARGE: OmnimindConfig(
        name="omnimind-xlarge",
        size=ModelSize.XLARGE,
        d_model=4096,
        n_layers=32,
        d_state=64,
        n_heads=32,
        expand=2,
        vocab_size=65536,
        max_seq_len=65536,
    ),
    ModelSize.XXLARGE: OmnimindConfig(
        name="omnimind-xxlarge",
        size=ModelSize.XXLARGE,
        d_model=5120,
        n_layers=40,
        d_state=64,
        n_heads=40,
        expand=2,
        vocab_size=65536,
        max_seq_len=131072,
    ),
    ModelSize.MEGA: OmnimindConfig(
        name="omnimind-mega",
        size=ModelSize.MEGA,
        d_model=8192,
        n_layers=96,           # Increased from 80
        d_state=128,
        n_heads=64,
        expand=2,
        vocab_size=65536,
        max_seq_len=131072,
    ),
    ModelSize.GIGANTIC: OmnimindConfig(
        name="omnimind-gigantic",
        size=ModelSize.GIGANTIC,
        d_model=14336,         # Increased from 12288
        n_layers=104,          # Increased from 96
        d_state=128,
        n_heads=112,
        expand=2,
        vocab_size=65536,
        max_seq_len=131072,
    ),
    ModelSize.TITAN: OmnimindConfig(
        name="omnimind-titan",
        size=ModelSize.TITAN,
        d_model=16384,         # Increased from 14336
        n_layers=128,          # Increased from 104
        d_state=256,
        n_heads=128,
        expand=2,
        vocab_size=65536,
        max_seq_len=262144,
    ),
}


# Size aliases for convenience
SIZE_ALIASES = {
    # Standard names
    "tiny": ModelSize.TINY,
    "nano": ModelSize.NANO,
    "micro": ModelSize.MICRO,
    "small": ModelSize.SMALL,
    "mini": ModelSize.MINI,
    "medium": ModelSize.MEDIUM,
    "standard": ModelSize.STANDARD,
    "large": ModelSize.LARGE,
    "xlarge": ModelSize.XLARGE,
    "xxlarge": ModelSize.XXLARGE,
    
    # Short aliases
    "xs": ModelSize.TINY,
    "s": ModelSize.SMALL,
    "m": ModelSize.MEDIUM,
    "l": ModelSize.LARGE,
    "xl": ModelSize.XLARGE,
    "xxl": ModelSize.XXLARGE,
    
    # Parameter-based aliases
    "1m": ModelSize.TINY,
    "10m": ModelSize.NANO,
    "50m": ModelSize.MICRO,
    "125m": ModelSize.SMALL,
    "350m": ModelSize.MINI,
    "770m": ModelSize.MEDIUM,
    "1.5b": ModelSize.STANDARD,
    "1b": ModelSize.STANDARD,
    "3b": ModelSize.LARGE,
    "7b": ModelSize.XLARGE,
    "13b": ModelSize.XXLARGE,
    "70b": ModelSize.MEGA,
    "175b": ModelSize.GIGANTIC,
    "200b": ModelSize.TITAN,
    "225b": ModelSize.TITAN,
}


def get_config(size: Union[str, ModelSize] = "micro") -> OmnimindConfig:
    """
    Get configuration by size name
    
    Args:
        size: Size name, alias, or ModelSize enum
        
    Examples:
        get_config("micro")
        get_config("7b")
        get_config("xl")
        get_config(ModelSize.LARGE)
    """
    if isinstance(size, ModelSize):
        return OMNIMIND_CONFIGS[size]
    
    # Normalize
    size_lower = size.lower().strip()
    
    # Check alias
    if size_lower in SIZE_ALIASES:
        return OMNIMIND_CONFIGS[SIZE_ALIASES[size_lower]]
    
    # Try direct enum
    try:
        size_enum = ModelSize(size_lower)
        return OMNIMIND_CONFIGS[size_enum]
    except ValueError:
        available = list(SIZE_ALIASES.keys())
        raise ValueError(f"Unknown size '{size}'. Available: {available}")


def create_custom_config(
    d_model: int,
    n_layers: int,
    d_state: int = 16,
    n_heads: int = 8,
    vocab_size: int = 32000,
    max_seq_len: int = 8192,
    **kwargs
) -> OmnimindConfig:
    """
    Create a custom OMNIMIND configuration
    
    Args:
        d_model: Hidden dimension
        n_layers: Number of layers
        d_state: SSM state dimension
        n_heads: Number of attention heads
        vocab_size: Vocabulary size
        max_seq_len: Maximum sequence length
        
    Returns:
        Custom OmnimindConfig
    """
    return OmnimindConfig(
        name=f"omnimind-custom-{d_model}x{n_layers}",
        size=ModelSize.MICRO,  # Placeholder
        d_model=d_model,
        n_layers=n_layers,
        d_state=d_state,
        n_heads=n_heads,
        vocab_size=vocab_size,
        max_seq_len=max_seq_len,
        **kwargs
    )


def estimate_params(config: OmnimindConfig) -> int:
    """Estimate total parameters"""
    # Embedding
    embed_params = config.vocab_size * config.d_model
    
    # Per layer (approximate)
    # SSM: in_proj + x_proj + dt_proj + out_proj + A + D
    ssm_params_per_layer = (
        config.d_model * config.d_inner * 2 +  # in_proj
        config.d_inner * (config.dt_rank_value + config.d_state * 2) +  # x_proj
        config.dt_rank_value * config.d_inner +  # dt_proj
        config.d_inner * config.d_model +  # out_proj
        config.d_inner * config.d_state +  # A
        config.d_inner  # D
    )
    
    # Convolution
    conv_params_per_layer = config.d_inner * config.d_conv
    
    # Norm
    norm_params_per_layer = config.d_model * 2
    
    total_per_layer = ssm_params_per_layer + conv_params_per_layer + norm_params_per_layer
    
    # LM Head (if not tied)
    lm_head = 0 if config.tie_embeddings else config.vocab_size * config.d_model
    
    # Final norm
    final_norm = config.d_model
    
    total = embed_params + (total_per_layer * config.n_layers) + lm_head + final_norm
    
    return total


def list_available_sizes() -> dict:
    """List all available model sizes with parameter counts"""
    sizes = {}
    for size, config in OMNIMIND_CONFIGS.items():
        params = estimate_params(config)
        sizes[config.name] = {
            "size": size.value,
            "d_model": config.d_model,
            "n_layers": config.n_layers,
            "params": params,
            "params_human": f"{params / 1e6:.1f}M" if params < 1e9 else f"{params / 1e9:.1f}B",
            "max_seq_len": config.max_seq_len,
        }
    return sizes


if __name__ == "__main__":
    # Print all configs
    print("OMNIMIND Model Sizes:\n")
    print(f"{'Name':<22} {'Params':<12} {'d_model':<8} {'Layers':<8} {'MaxSeq':<10}")
    print("-" * 60)
    
    for size, config in OMNIMIND_CONFIGS.items():
        params = estimate_params(config)
        param_str = f"{params / 1e6:.1f}M" if params < 1e9 else f"{params / 1e9:.1f}B"
        print(f"{config.name:<22} {param_str:<12} {config.d_model:<8} {config.n_layers:<8} {config.max_seq_len:<10}")
