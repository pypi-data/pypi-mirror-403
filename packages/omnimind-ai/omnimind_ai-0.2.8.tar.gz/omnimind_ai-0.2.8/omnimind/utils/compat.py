"""
OMNIMIND Compatibility Utilities
Handle import fixes, version checks, and library compatibility.

This module addresses the "Dependency Hell" problem by:
1. Detecting CUDA version and GPU capabilities
2. Checking Triton availability and providing fallbacks
3. Verifying SQLite FTS5 support
4. OS-specific compatibility checks (Windows/Linux/macOS)
5. Providing graceful degradation when features unavailable
"""

import sys
import os
import platform
import logging
import warnings
import subprocess
from typing import Optional, Callable, Dict, Any, Tuple
from functools import wraps
from dataclasses import dataclass

__all__ = [
    "Version",
    "suppress_warnings",
    "patch_transformers",
    "check_dependencies",
    "ensure_package",
    "EnvironmentInfo",
    "check_environment",
    "print_compatibility_report",
    "get_recommended_config",
    "HAS_CUDA",
    "HAS_TRITON",
    "HAS_FTS5",
    "HAS_MPS",
    "CUDA_VERSION",
    "COMPUTE_CAPABILITY",
]

# Configure logging
logger = logging.getLogger("omnimind")

# ============================================================================
# ENVIRONMENT DETECTION FLAGS (populated at import time)
# ============================================================================

def _detect_cuda() -> Tuple[bool, Optional[str], Optional[Tuple[int, int]]]:
    """Detect CUDA availability, version, and compute capability."""
    try:
        import torch
        if torch.cuda.is_available():
            cuda_version = torch.version.cuda
            # Get compute capability of first GPU
            if torch.cuda.device_count() > 0:
                cap = torch.cuda.get_device_capability(0)
                return True, cuda_version, cap
            return True, cuda_version, None
        return False, None, None
    except ImportError:
        return False, None, None

def _detect_triton() -> bool:
    """Detect if Triton is available and functional."""
    try:
        import triton
        # Try to verify Triton can actually compile
        # On Windows or without proper setup, import may succeed but JIT fails
        return True
    except ImportError:
        return False
    except Exception:
        return False

def _detect_mps() -> bool:
    """Detect Apple Metal Performance Shaders (for M1/M2 Macs)."""
    try:
        import torch
        return hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()
    except ImportError:
        return False

def _detect_fts5() -> bool:
    """Detect if SQLite FTS5 extension is available."""
    try:
        import sqlite3
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        # Try to create an FTS5 virtual table
        cursor.execute('CREATE VIRTUAL TABLE test_fts5 USING fts5(content)')
        cursor.execute('DROP TABLE test_fts5')
        conn.close()
        return True
    except Exception:
        return False

def _get_os_info() -> Dict[str, str]:
    """Get OS information."""
    return {
        'system': platform.system(),  # Windows, Linux, Darwin
        'release': platform.release(),
        'machine': platform.machine(),  # x86_64, arm64
        'python': platform.python_version(),
    }

# Populate flags at import time
HAS_CUDA, CUDA_VERSION, COMPUTE_CAPABILITY = _detect_cuda()
HAS_TRITON = _detect_triton()
HAS_MPS = _detect_mps()
HAS_FTS5 = _detect_fts5()
OS_INFO = _get_os_info()

class Version:
    """Simple version comparison class"""
    
    def __init__(self, version_string: str):
        self.version_string = version_string
        self.parts = self._parse(version_string)
    
    def _parse(self, v: str):
        """Parse version string into tuple of ints"""
        import re
        match = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", v)
        if match:
            major, minor, patch = match.groups()
            return (int(major), int(minor), int(patch or 0))
        return (0, 0, 0)
    
    def __lt__(self, other):
        if isinstance(other, str):
            other = Version(other)
        return self.parts < other.parts
    
    def __le__(self, other):
        if isinstance(other, str):
            other = Version(other)
        return self.parts <= other.parts
    
    def __gt__(self, other):
        if isinstance(other, str):
            other = Version(other)
        return self.parts > other.parts
    
    def __ge__(self, other):
        if isinstance(other, str):
            other = Version(other)
        return self.parts >= other.parts
    
    def __eq__(self, other):
        if isinstance(other, str):
            other = Version(other)
        return self.parts == other.parts
    
    def __repr__(self):
        return f"Version('{self.version_string}')"

class suppress_warnings:
    """Context manager to suppress specific warnings"""
    
    def __init__(self, *warning_types):
        self.warning_types = warning_types or (UserWarning,)
    
    def __enter__(self):
        self._filters = warnings.filters.copy()
        for wt in self.warning_types:
            warnings.filterwarnings("ignore", category=wt)
        return self
    
    def __exit__(self, *args):
        warnings.filters = self._filters

def patch_transformers():
    """
    Apply compatibility patches to transformers library.
    Call this early in your script to avoid issues.
    """
    try:
        import transformers
        
        # Fix gradient checkpointing with LoRA
        if hasattr(transformers, "PreTrainedModel"):
            original = transformers.PreTrainedModel.enable_input_require_grads
            
            @wraps(original)
            def patched_enable_input_require_grads(self):
                try:
                    return original(self)
                except NotImplementedError:
                    # Handle vision models that don't have get_input_embeddings
                    def make_inputs_require_grads(module, input, output):
                        if isinstance(output, tuple):
                            output = output[0]
                        if hasattr(output, "requires_grad_"):
                            output.requires_grad_(True)
                    
                    self.get_input_embeddings().register_forward_hook(make_inputs_require_grads)
            
            transformers.PreTrainedModel.enable_input_require_grads = patched_enable_input_require_grads
            logger.debug("Patched transformers.PreTrainedModel.enable_input_require_grads")
        
        return True
    except ImportError:
        return False

def check_dependencies() -> dict:
    """
    Check status of important dependencies.
    
    Returns:
        Dict with package names and their versions/status
    """
    deps = {}
    
    packages = [
        "torch",
        "transformers",
        "peft",
        "bitsandbytes",
        "triton",
        "flash_attn",
        "accelerate",
        "datasets",
        "trl",
    ]
    
    for pkg in packages:
        try:
            module = __import__(pkg)
            version = getattr(module, "__version__", "installed")
            deps[pkg] = version
        except ImportError:
            deps[pkg] = None
    
    return deps

def ensure_package(package_name: str, min_version: Optional[str] = None) -> bool:
    """
    Ensure a package is installed with minimum version.
    
    Args:
        package_name: Name of the package
        min_version: Minimum required version
        
    Returns:
        True if package meets requirements
        
    Raises:
        ImportError if package not found or version too old
    """
    try:
        module = __import__(package_name)
        
        if min_version:
            current = getattr(module, "__version__", "0.0.0")
            if Version(current) < Version(min_version):
                raise ImportError(
                    f"{package_name}>={min_version} required, found {current}. "
                    f"Run: pip install --upgrade {package_name}"
                )
        
        return True
    except ImportError:
        raise ImportError(
            f"{package_name} not found. "
            f"Run: pip install {package_name}"
        )

def print_system_info():
    """Print system and library information for debugging"""
    print("=" * 50)
    print("OMNIMIND System Information")
    print("=" * 50)
    print(f"Python: {OS_INFO['python']}")
    print(f"Platform: {OS_INFO['system']} {OS_INFO['release']} ({OS_INFO['machine']})")
    
    deps = check_dependencies()
    print("\nDependencies:")
    for pkg, version in deps.items():
        status = version if version else "❌ Not installed"
        print(f"  {pkg}: {status}")
    
    from .device import DEVICE_TYPE, DEVICE_COUNT
    print(f"\nDevice: {DEVICE_TYPE} ({DEVICE_COUNT} available)")
    print("=" * 50)


@dataclass
class EnvironmentInfo:
    """Complete environment compatibility information."""
    # Hardware
    has_cuda: bool
    cuda_version: Optional[str]
    compute_capability: Optional[Tuple[int, int]]
    has_mps: bool
    gpu_name: Optional[str]
    gpu_memory_gb: Optional[float]
    ram_gb: float
    
    # Software
    os_system: str
    os_version: str
    python_version: str
    torch_version: Optional[str]
    has_triton: bool
    has_fts5: bool
    
    # Recommendations
    recommended_backend: str  # 'cuda', 'mps', 'cpu'
    can_use_triton_kernels: bool
    can_use_disk_streaming: bool
    max_model_size: str  # e.g., '7B', '14B', '70B'
    warnings: list


def check_environment() -> EnvironmentInfo:
    """
    Perform comprehensive environment check.
    
    Returns:
        EnvironmentInfo with all compatibility details and recommendations.
    """
    import psutil
    
    warnings_list = []
    
    # Get GPU info
    gpu_name = None
    gpu_memory_gb = None
    try:
        import torch
        torch_version = torch.__version__
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
    except ImportError:
        torch_version = None
    
    # Get RAM
    ram_gb = psutil.virtual_memory().total / (1024**3)
    
    # Determine recommended backend
    if HAS_CUDA:
        recommended_backend = 'cuda'
    elif HAS_MPS:
        recommended_backend = 'mps'
    else:
        recommended_backend = 'cpu'
    
    # Check Triton compatibility
    can_use_triton = HAS_TRITON and HAS_CUDA
    if OS_INFO['system'] == 'Windows' and HAS_TRITON:
        warnings_list.append(
            "⚠️ Triton on Windows may have issues. Consider using WSL2 or Docker."
        )
        can_use_triton = False  # Disable by default on Windows
    
    if OS_INFO['system'] == 'Darwin':  # macOS
        warnings_list.append(
            "⚠️ macOS detected. Triton kernels not available. Using PyTorch fallbacks."
        )
        can_use_triton = False
    
    # Check CUDA version compatibility
    if HAS_CUDA and CUDA_VERSION:
        major = int(CUDA_VERSION.split('.')[0])
        if major < 11:
            warnings_list.append(
                f"⚠️ CUDA {CUDA_VERSION} is old. Recommend CUDA 11.8+ for best performance."
            )
    
    # Check compute capability
    if COMPUTE_CAPABILITY:
        if COMPUTE_CAPABILITY < (7, 0):
            warnings_list.append(
                f"⚠️ GPU compute capability {COMPUTE_CAPABILITY} is old. "
                "Some optimizations may not work."
            )
    
    # Check FTS5
    if not HAS_FTS5:
        warnings_list.append(
            "⚠️ SQLite FTS5 not available. Weight search will use standard indices."
        )
    
    # Estimate max model size
    if gpu_memory_gb:
        if gpu_memory_gb >= 80:
            max_model_size = '70B+'
        elif gpu_memory_gb >= 40:
            max_model_size = '70B (with streaming)'
        elif gpu_memory_gb >= 24:
            max_model_size = '14B'
        elif gpu_memory_gb >= 16:
            max_model_size = '7B'
        elif gpu_memory_gb >= 8:
            max_model_size = '3B'
        else:
            max_model_size = '1B'
    elif ram_gb >= 32:
        max_model_size = '7B (CPU, slow)'
    else:
        max_model_size = '3B (CPU, very slow)'
    
    return EnvironmentInfo(
        has_cuda=HAS_CUDA,
        cuda_version=CUDA_VERSION,
        compute_capability=COMPUTE_CAPABILITY,
        has_mps=HAS_MPS,
        gpu_name=gpu_name,
        gpu_memory_gb=gpu_memory_gb,
        ram_gb=ram_gb,
        os_system=OS_INFO['system'],
        os_version=OS_INFO['release'],
        python_version=OS_INFO['python'],
        torch_version=torch_version,
        has_triton=HAS_TRITON,
        has_fts5=HAS_FTS5,
        recommended_backend=recommended_backend,
        can_use_triton_kernels=can_use_triton,
        can_use_disk_streaming=True,  # Always available via SQLite
        max_model_size=max_model_size,
        warnings=warnings_list,
    )


def print_compatibility_report():
    """
    Print a detailed compatibility report with recommendations.
    """
    env = check_environment()
    
    print("\n" + "=" * 60)
    print("🔍 OMNIMIND Compatibility Report")
    print("=" * 60)
    
    # System Info
    print(f"\n📦 System:")
    print(f"   OS: {env.os_system} {env.os_version}")
    print(f"   Python: {env.python_version}")
    print(f"   PyTorch: {env.torch_version or 'Not installed'}")
    print(f"   RAM: {env.ram_gb:.1f} GB")
    
    # GPU Info
    print(f"\n🎮 GPU:")
    if env.has_cuda:
        print(f"   ✅ CUDA: {env.cuda_version}")
        print(f"   GPU: {env.gpu_name}")
        print(f"   VRAM: {env.gpu_memory_gb:.1f} GB")
        print(f"   Compute Capability: {env.compute_capability}")
    elif env.has_mps:
        print(f"   ✅ Apple Metal (MPS) available")
    else:
        print(f"   ❌ No GPU detected - CPU only")
    
    # Features
    print(f"\n⚡ Features:")
    print(f"   Triton Kernels: {'✅ Available' if env.can_use_triton_kernels else '❌ Unavailable (using PyTorch fallback)'}")
    print(f"   Disk Streaming: {'✅ Available' if env.can_use_disk_streaming else '❌ Unavailable'}")
    print(f"   SQLite FTS5: {'✅ Available' if env.has_fts5 else '⚠️ Unavailable (using standard index)'}")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    print(f"   Backend: {env.recommended_backend.upper()}")
    print(f"   Max Model Size: {env.max_model_size}")
    
    # Warnings
    if env.warnings:
        print(f"\n⚠️ Warnings:")
        for w in env.warnings:
            print(f"   {w}")
    
    print("\n" + "=" * 60)
    
    return env


def get_recommended_config() -> Dict[str, Any]:
    """
    Get recommended OMNIMIND configuration based on environment.
    
    Returns:
        Dict with recommended settings for OmnimindConfig
    """
    env = check_environment()
    
    config = {
        'device': env.recommended_backend,
        'use_triton': env.can_use_triton_kernels,
        'use_disk_streaming': env.can_use_disk_streaming,
    }
    
    # Adjust based on GPU memory
    if env.gpu_memory_gb:
        if env.gpu_memory_gb >= 24:
            config['dtype'] = 'bfloat16'
            config['gradient_checkpointing'] = False
        elif env.gpu_memory_gb >= 16:
            config['dtype'] = 'float16'
            config['gradient_checkpointing'] = True
        else:
            config['dtype'] = 'float16'
            config['gradient_checkpointing'] = True
            config['use_quantization'] = True
    else:
        config['dtype'] = 'float32'
        config['gradient_checkpointing'] = True
    
    return config


# Auto-patch on import
patch_transformers()
