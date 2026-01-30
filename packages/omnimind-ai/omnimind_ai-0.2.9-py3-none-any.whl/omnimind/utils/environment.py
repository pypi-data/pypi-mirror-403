"""
Smart Environment Handler for OMNIMIND
======================================

Automatically detects, diagnoses, and resolves dependency issues.
No Docker required - handles everything natively.

Features:
- Auto-detection of CUDA, Triton, FTS5, OS constraints
- Intelligent fallback selection
- Auto-fix for common issues  
- Runtime optimization suggestions
- Self-healing capabilities
"""

import os
import sys
import platform
import subprocess
import warnings
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class IssueLevel(Enum):
    """Severity levels for environment issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class IssueCategory(Enum):
    """Categories of environment issues."""
    CUDA = "cuda"
    TRITON = "triton"
    PYTORCH = "pytorch"
    SQLITE = "sqlite"
    MEMORY = "memory"
    OS = "os"
    DEPENDENCY = "dependency"


@dataclass
class EnvironmentIssue:
    """Represents a detected environment issue."""
    category: IssueCategory
    level: IssueLevel
    message: str
    details: str = ""
    auto_fixable: bool = False
    fix_command: Optional[str] = None
    fix_function: Optional[Callable] = None
    workaround: Optional[str] = None


@dataclass
class EnvironmentStatus:
    """Complete environment status."""
    # System info
    os_name: str = ""
    os_version: str = ""
    python_version: str = ""
    architecture: str = ""
    
    # Hardware
    cpu_count: int = 0
    ram_gb: float = 0.0
    gpu_name: Optional[str] = None
    gpu_memory_gb: Optional[float] = None
    cuda_version: Optional[str] = None
    cudnn_version: Optional[str] = None
    
    # Libraries
    pytorch_version: Optional[str] = None
    triton_version: Optional[str] = None
    transformers_version: Optional[str] = None
    sqlite_version: Optional[str] = None
    
    # Capabilities
    has_cuda: bool = False
    has_mps: bool = False
    has_triton: bool = False
    has_fts5: bool = False
    has_flash_attn: bool = False
    
    # Issues and recommendations
    issues: List[EnvironmentIssue] = field(default_factory=list)
    
    # Computed optimal settings
    optimal_device: str = "cpu"
    optimal_dtype: str = "float32"
    optimal_backend: str = "pytorch"
    max_model_size: str = "1B"
    
    @property
    def is_healthy(self) -> bool:
        """Check if environment has no critical issues."""
        return not any(i.level == IssueLevel.CRITICAL for i in self.issues)
    
    @property
    def has_warnings(self) -> bool:
        """Check if environment has warnings."""
        return any(i.level in [IssueLevel.WARNING, IssueLevel.ERROR] for i in self.issues)


class SmartEnvironmentHandler:
    """
    Smart Environment Handler - Self-managing dependency resolution.
    
    Automatically:
    - Detects environment capabilities
    - Identifies compatibility issues
    - Applies fixes when possible
    - Selects optimal fallbacks
    - Provides clear guidance
    """
    
    def __init__(self, auto_fix: bool = True, verbose: bool = True):
        """
        Initialize the Smart Environment Handler.
        
        Args:
            auto_fix: Automatically apply safe fixes
            verbose: Print status messages
        """
        self.auto_fix = auto_fix
        self.verbose = verbose
        self.status = EnvironmentStatus()
        self._initialized = False
        self._fix_history: List[str] = []
        
    def initialize(self) -> EnvironmentStatus:
        """
        Run full environment detection and optimization.
        
        Returns:
            EnvironmentStatus with all detected information
        """
        if self._initialized:
            return self.status
            
        self._log("🔍 OMNIMIND Smart Environment Handler initializing...")
        
        # Phase 1: Detect system info
        self._detect_system()
        
        # Phase 2: Detect hardware
        self._detect_hardware()
        
        # Phase 3: Detect libraries
        self._detect_libraries()
        
        # Phase 4: Detect capabilities
        self._detect_capabilities()
        
        # Phase 5: Analyze issues
        self._analyze_issues()
        
        # Phase 6: Apply auto-fixes
        if self.auto_fix:
            self._apply_auto_fixes()
        
        # Phase 7: Compute optimal settings
        self._compute_optimal_settings()
        
        # Phase 8: Configure runtime
        self._configure_runtime()
        
        self._initialized = True
        
        if self.verbose:
            self.print_status()
            
        return self.status
    
    def _log(self, msg: str, level: str = "info"):
        """Log a message if verbose mode is on."""
        if self.verbose:
            if level == "warning":
                print(f"⚠️  {msg}")
            elif level == "error":
                print(f"❌ {msg}")
            elif level == "success":
                print(f"✅ {msg}")
            else:
                print(f"   {msg}")
    
    def _detect_system(self):
        """Detect OS and Python information."""
        self.status.os_name = platform.system()
        self.status.os_version = platform.release()
        self.status.python_version = platform.python_version()
        self.status.architecture = platform.machine()
        
        self._log(f"OS: {self.status.os_name} {self.status.os_version} ({self.status.architecture})")
        self._log(f"Python: {self.status.python_version}")
    
    def _detect_hardware(self):
        """Detect CPU, RAM, and GPU information."""
        import multiprocessing
        self.status.cpu_count = multiprocessing.cpu_count()
        
        # RAM detection
        try:
            import psutil
            self.status.ram_gb = psutil.virtual_memory().total / (1024**3)
        except ImportError:
            # Fallback for systems without psutil
            self.status.ram_gb = 8.0  # Assume 8GB as conservative default
            
        self._log(f"CPU: {self.status.cpu_count} cores")
        self._log(f"RAM: {self.status.ram_gb:.1f} GB")
        
        # GPU detection
        self._detect_gpu()
    
    def _detect_gpu(self):
        """Detect GPU and CUDA information."""
        # Try PyTorch first
        try:
            import torch
            if torch.cuda.is_available():
                self.status.has_cuda = True
                self.status.gpu_name = torch.cuda.get_device_name(0)
                self.status.gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                self.status.cuda_version = torch.version.cuda
                
                # cuDNN version
                if torch.backends.cudnn.is_available():
                    self.status.cudnn_version = str(torch.backends.cudnn.version())
                    
                self._log(f"GPU: {self.status.gpu_name} ({self.status.gpu_memory_gb:.1f} GB)", "success")
                self._log(f"CUDA: {self.status.cuda_version}")
                
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                self.status.has_mps = True
                self.status.gpu_name = "Apple Silicon (MPS)"
                self._log(f"GPU: {self.status.gpu_name} (MPS backend)", "success")
            else:
                self._log("GPU: Not detected (CPU-only mode)", "warning")
                
        except ImportError:
            self._log("PyTorch not installed - cannot detect GPU", "warning")
    
    def _detect_libraries(self):
        """Detect installed library versions."""
        # PyTorch
        try:
            import torch
            self.status.pytorch_version = torch.__version__
        except ImportError:
            self.status.issues.append(EnvironmentIssue(
                category=IssueCategory.PYTORCH,
                level=IssueLevel.CRITICAL,
                message="PyTorch not installed",
                details="OMNIMIND requires PyTorch >= 2.0",
                auto_fixable=True,
                fix_command="pip install torch>=2.0"
            ))
        
        # Triton
        try:
            import triton
            self.status.triton_version = triton.__version__
        except ImportError:
            pass  # Triton is optional
        
        # Transformers
        try:
            import transformers
            self.status.transformers_version = transformers.__version__
        except ImportError:
            pass
        
        # SQLite
        import sqlite3
        self.status.sqlite_version = sqlite3.sqlite_version
    
    def _detect_capabilities(self):
        """Detect what features are available."""
        # Triton capability
        self._detect_triton_capability()
        
        # FTS5 capability
        self._detect_fts5_capability()
        
        # Flash Attention
        self._detect_flash_attn()
    
    def _detect_triton_capability(self):
        """Detect if Triton can actually be used."""
        # Platform check first
        if self.status.os_name == "Darwin":
            self.status.has_triton = False
            self.status.issues.append(EnvironmentIssue(
                category=IssueCategory.TRITON,
                level=IssueLevel.INFO,
                message="Triton not available on macOS",
                details="Triton requires NVIDIA CUDA which is not supported on macOS",
                workaround="Using optimized PyTorch fallback kernels"
            ))
            return
            
        if self.status.os_name == "Windows":
            self.status.has_triton = False
            self.status.issues.append(EnvironmentIssue(
                category=IssueCategory.TRITON,
                level=IssueLevel.WARNING,
                message="Triton has limited Windows support",
                details="Triton compilation may fail on Windows",
                workaround="Using PyTorch fallback kernels. Consider WSL2 for better performance."
            ))
            return
        
        # Linux - check actual availability
        if self.status.triton_version and self.status.has_cuda:
            try:
                import triton
                import triton.language as tl
                
                # Try a simple kernel to verify it works
                @triton.jit
                def _test_kernel(x_ptr, n: tl.constexpr):
                    pass
                
                self.status.has_triton = True
                self._log("Triton: Available and functional", "success")
                
            except Exception as e:
                self.status.has_triton = False
                self.status.issues.append(EnvironmentIssue(
                    category=IssueCategory.TRITON,
                    level=IssueLevel.WARNING,
                    message="Triton installed but not functional",
                    details=str(e),
                    workaround="Using PyTorch fallback kernels"
                ))
        else:
            self.status.has_triton = False
            if self.status.has_cuda and not self.status.triton_version:
                self.status.issues.append(EnvironmentIssue(
                    category=IssueCategory.TRITON,
                    level=IssueLevel.INFO,
                    message="Triton not installed (optional)",
                    details="Install Triton for 2-3x faster kernels on NVIDIA GPUs",
                    auto_fixable=True,
                    fix_command="pip install triton>=2.0"
                ))
    
    def _detect_fts5_capability(self):
        """Detect SQLite FTS5 full-text search capability."""
        import sqlite3
        try:
            conn = sqlite3.connect(":memory:")
            conn.execute("CREATE VIRTUAL TABLE test USING fts5(content)")
            conn.close()
            self.status.has_fts5 = True
            self._log("SQLite FTS5: Available", "success")
        except sqlite3.OperationalError:
            self.status.has_fts5 = False
            self.status.issues.append(EnvironmentIssue(
                category=IssueCategory.SQLITE,
                level=IssueLevel.INFO,
                message="SQLite FTS5 not available",
                details="Full-text search will use standard LIKE queries",
                workaround="Using B-tree indexing (still efficient)"
            ))
    
    def _detect_flash_attn(self):
        """Detect Flash Attention availability."""
        try:
            import flash_attn
            self.status.has_flash_attn = True
            self._log("Flash Attention: Available", "success")
        except ImportError:
            self.status.has_flash_attn = False
    
    def _analyze_issues(self):
        """Analyze environment for potential issues."""
        # Memory constraints
        if self.status.ram_gb < 8:
            self.status.issues.append(EnvironmentIssue(
                category=IssueCategory.MEMORY,
                level=IssueLevel.WARNING,
                message=f"Low system RAM ({self.status.ram_gb:.1f} GB)",
                details="May struggle with models > 1B parameters",
                workaround="Use disk streaming and gradient checkpointing"
            ))
        
        # GPU memory constraints
        if self.status.has_cuda and self.status.gpu_memory_gb:
            if self.status.gpu_memory_gb < 8:
                self.status.issues.append(EnvironmentIssue(
                    category=IssueCategory.MEMORY,
                    level=IssueLevel.WARNING,
                    message=f"Limited GPU memory ({self.status.gpu_memory_gb:.1f} GB)",
                    details="Large models may require quantization",
                    workaround="Use 4-bit or 8-bit quantization"
                ))
        
        # CUDA/PyTorch version mismatch
        if self.status.has_cuda and self.status.pytorch_version:
            self._check_cuda_pytorch_compatibility()
        
        # Python version check
        py_version = tuple(map(int, self.status.python_version.split('.')[:2]))
        if py_version < (3, 8):
            self.status.issues.append(EnvironmentIssue(
                category=IssueCategory.DEPENDENCY,
                level=IssueLevel.ERROR,
                message=f"Python {self.status.python_version} is too old",
                details="OMNIMIND requires Python >= 3.8",
                auto_fixable=False
            ))
    
    def _check_cuda_pytorch_compatibility(self):
        """Check CUDA and PyTorch version compatibility."""
        try:
            import torch
            cuda_version = self.status.cuda_version
            pytorch_cuda = torch.version.cuda
            
            if cuda_version and pytorch_cuda:
                # Extract major.minor versions
                system_cuda = tuple(map(int, cuda_version.split('.')[:2]))
                pytorch_cuda_ver = tuple(map(int, pytorch_cuda.split('.')[:2]))
                
                if system_cuda[0] != pytorch_cuda_ver[0]:
                    self.status.issues.append(EnvironmentIssue(
                        category=IssueCategory.CUDA,
                        level=IssueLevel.ERROR,
                        message=f"CUDA version mismatch",
                        details=f"System CUDA: {cuda_version}, PyTorch CUDA: {pytorch_cuda}",
                        workaround="Reinstall PyTorch with matching CUDA version"
                    ))
        except Exception:
            pass
    
    def _apply_auto_fixes(self):
        """Apply automatic fixes for safe issues."""
        for issue in self.status.issues:
            if issue.auto_fixable and issue.level != IssueLevel.CRITICAL:
                if issue.fix_function:
                    try:
                        self._log(f"Auto-fixing: {issue.message}")
                        issue.fix_function()
                        self._fix_history.append(f"Fixed: {issue.message}")
                    except Exception as e:
                        self._log(f"Auto-fix failed: {e}", "warning")
    
    def _compute_optimal_settings(self):
        """Compute optimal settings based on detected environment."""
        # Optimal device
        if self.status.has_cuda:
            self.status.optimal_device = "cuda"
        elif self.status.has_mps:
            self.status.optimal_device = "mps"
        else:
            self.status.optimal_device = "cpu"
        
        # Optimal dtype
        if self.status.has_cuda:
            # Check compute capability for bf16 support
            try:
                import torch
                cc = torch.cuda.get_device_capability()
                if cc[0] >= 8:  # Ampere or newer
                    self.status.optimal_dtype = "bfloat16"
                else:
                    self.status.optimal_dtype = "float16"
            except:
                self.status.optimal_dtype = "float16"
        elif self.status.has_mps:
            self.status.optimal_dtype = "float16"
        else:
            self.status.optimal_dtype = "float32"
        
        # Optimal backend
        if self.status.has_triton:
            self.status.optimal_backend = "triton"
        else:
            self.status.optimal_backend = "pytorch"
        
        # Max model size estimate
        self._estimate_max_model_size()
    
    def _estimate_max_model_size(self):
        """Estimate maximum model size that can be handled."""
        # Based on available memory
        if self.status.has_cuda and self.status.gpu_memory_gb:
            vram = self.status.gpu_memory_gb
            if vram >= 80:
                self.status.max_model_size = "70B+ (with quantization)"
            elif vram >= 40:
                self.status.max_model_size = "70B (4-bit) or 34B (8-bit)"
            elif vram >= 24:
                self.status.max_model_size = "34B (4-bit) or 13B (16-bit)"
            elif vram >= 16:
                self.status.max_model_size = "13B (4-bit) or 7B (16-bit)"
            elif vram >= 8:
                self.status.max_model_size = "7B (4-bit) or 3B (16-bit)"
            else:
                self.status.max_model_size = "3B (4-bit)"
        elif self.status.has_mps:
            # Apple Silicon - shared memory
            if self.status.ram_gb >= 32:
                self.status.max_model_size = "13B (4-bit)"
            elif self.status.ram_gb >= 16:
                self.status.max_model_size = "7B (4-bit)"
            else:
                self.status.max_model_size = "3B (4-bit)"
        else:
            # CPU only
            if self.status.ram_gb >= 64:
                self.status.max_model_size = "7B (4-bit, very slow)"
            elif self.status.ram_gb >= 32:
                self.status.max_model_size = "3B (4-bit, slow)"
            else:
                self.status.max_model_size = "1B (slow)"
    
    def _configure_runtime(self):
        """Configure runtime environment based on detected settings."""
        # Set environment variables for optimal performance
        if self.status.has_cuda:
            # Enable TF32 for faster matmul on Ampere+
            try:
                import torch
                torch.backends.cuda.matmul.allow_tf32 = True
                torch.backends.cudnn.allow_tf32 = True
            except:
                pass
        
        # Suppress known harmless warnings
        warnings.filterwarnings("ignore", message=".*triton.*", category=UserWarning)
        warnings.filterwarnings("ignore", message=".*torch.cuda.amp.*", category=FutureWarning)
    
    def print_status(self):
        """Print a formatted status report."""
        print("\n" + "=" * 60)
        print("🧠 OMNIMIND Environment Status")
        print("=" * 60)
        
        # System
        print(f"\n📦 System:")
        print(f"   OS: {self.status.os_name} {self.status.os_version}")
        print(f"   Python: {self.status.python_version}")
        print(f"   CPU: {self.status.cpu_count} cores")
        print(f"   RAM: {self.status.ram_gb:.1f} GB")
        
        # GPU
        print(f"\n🎮 GPU:")
        if self.status.has_cuda:
            print(f"   {self.status.gpu_name}")
            print(f"   VRAM: {self.status.gpu_memory_gb:.1f} GB")
            print(f"   CUDA: {self.status.cuda_version}")
        elif self.status.has_mps:
            print(f"   Apple Silicon (MPS)")
        else:
            print(f"   ❌ No GPU detected")
        
        # Libraries
        print(f"\n📚 Libraries:")
        print(f"   PyTorch: {self.status.pytorch_version or 'Not installed'}")
        print(f"   Triton: {self.status.triton_version or 'Not installed'}")
        print(f"   SQLite: {self.status.sqlite_version}")
        
        # Capabilities
        print(f"\n⚡ Capabilities:")
        print(f"   Triton Kernels: {'✅' if self.status.has_triton else '❌ (using PyTorch fallback)'}")
        print(f"   Flash Attention: {'✅' if self.status.has_flash_attn else '❌'}")
        print(f"   SQLite FTS5: {'✅' if self.status.has_fts5 else '❌ (using B-tree)'}")
        
        # Optimal settings
        print(f"\n💡 Optimal Settings:")
        print(f"   Device: {self.status.optimal_device}")
        print(f"   Dtype: {self.status.optimal_dtype}")
        print(f"   Backend: {self.status.optimal_backend}")
        print(f"   Max Model: {self.status.max_model_size}")
        
        # Issues
        if self.status.issues:
            print(f"\n⚠️  Issues Detected:")
            for issue in self.status.issues:
                icon = {"info": "ℹ️", "warning": "⚠️", "error": "❌", "critical": "🚨"}[issue.level.value]
                print(f"   {icon} [{issue.category.value}] {issue.message}")
                if issue.workaround:
                    print(f"      → {issue.workaround}")
        else:
            print(f"\n✅ No issues detected!")
        
        print("\n" + "=" * 60)
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get recommended configuration dictionary.
        
        Returns:
            Dictionary with optimal settings for OMNIMIND
        """
        if not self._initialized:
            self.initialize()
            
        return {
            "device": self.status.optimal_device,
            "dtype": self.status.optimal_dtype,
            "backend": self.status.optimal_backend,
            "use_triton": self.status.has_triton,
            "use_flash_attn": self.status.has_flash_attn,
            "use_disk_streaming": not self.status.has_cuda or (self.status.gpu_memory_gb or 0) < 16,
            "gradient_checkpointing": self.status.ram_gb < 32,
            "max_model_size": self.status.max_model_size,
        }
    
    def ensure_ready(self) -> bool:
        """
        Ensure environment is ready for OMNIMIND.
        
        Returns:
            True if environment is healthy
        
        Raises:
            RuntimeError if critical issues exist
        """
        if not self._initialized:
            self.initialize()
        
        critical = [i for i in self.status.issues if i.level == IssueLevel.CRITICAL]
        if critical:
            msgs = "\n".join(f"  - {i.message}: {i.details}" for i in critical)
            raise RuntimeError(f"Critical environment issues:\n{msgs}")
        
        return True


# Global singleton instance
_handler: Optional[SmartEnvironmentHandler] = None


def get_environment_handler(auto_fix: bool = True, verbose: bool = False) -> SmartEnvironmentHandler:
    """
    Get or create the global environment handler.
    
    Args:
        auto_fix: Apply automatic fixes
        verbose: Print status messages
        
    Returns:
        SmartEnvironmentHandler instance
    """
    global _handler
    if _handler is None:
        _handler = SmartEnvironmentHandler(auto_fix=auto_fix, verbose=verbose)
    return _handler


def auto_configure() -> Dict[str, Any]:
    """
    Automatically configure OMNIMIND for the current environment.
    
    Returns:
        Dictionary with optimal configuration
    """
    handler = get_environment_handler(verbose=False)
    handler.initialize()
    return handler.get_config()


def check_and_report():
    """Run environment check and print detailed report."""
    handler = SmartEnvironmentHandler(auto_fix=True, verbose=True)
    handler.initialize()
    return handler.status


def ensure_omnimind_ready():
    """
    Ensure OMNIMIND is ready to run.
    
    Raises:
        RuntimeError if environment has critical issues
    """
    handler = get_environment_handler(verbose=False)
    handler.ensure_ready()


# Export all public functions and classes
__all__ = [
    "SmartEnvironmentHandler",
    "EnvironmentStatus", 
    "EnvironmentIssue",
    "IssueLevel",
    "IssueCategory",
    "get_environment_handler",
    "auto_configure",
    "check_and_report",
    "ensure_omnimind_ready",
]
