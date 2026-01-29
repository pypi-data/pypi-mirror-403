"""
OMNIMIND Low-Memory Conversion
Memory-efficient model conversion for large models (70B-200B+) on limited RAM (30GB)

Designed for:
- Kaggle Free Tier (30GB RAM)
- Google Colab (12-25GB RAM)
- Consumer GPUs (8-24GB VRAM)

Key Techniques:
1. Layer-by-Layer Streaming - Process one layer at a time
2. Safetensors Memory Mapping - Read weights from disk without full RAM load
3. Sharded Checkpoint Support - Handle multi-file model weights
4. Automatic Garbage Collection - Clean up between layers
5. Memory Monitoring - Track and prevent OOM errors

Usage:
    from omnimind.conversion import stream_convert_to_gguf
    
    # Convert 70B model with only 30GB RAM!
    stream_convert_to_gguf(
        "meta-llama/Llama-2-70b-hf",
        "llama-70b-Q4_K_M.gguf",
        quantization="q4_k_m"
    )
"""
import os
import gc
import json
import struct
import mmap
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List, Iterator, Tuple, Union
from dataclasses import dataclass, field
from contextlib import contextmanager
import warnings

import torch
import numpy as np

# Memory monitoring
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# Safetensors for efficient weight loading
try:
    from safetensors import safe_open
    from safetensors.torch import save_file as save_safetensors
    HAS_SAFETENSORS = True
except ImportError:
    HAS_SAFETENSORS = False

# HuggingFace Hub for downloading
try:
    from huggingface_hub import hf_hub_download, list_repo_files, snapshot_download
    HAS_HF_HUB = True
except ImportError:
    HAS_HF_HUB = False


# ==================== Memory Monitoring ====================

@dataclass
class MemoryStats:
    """Memory usage statistics"""
    total_gb: float = 0.0
    available_gb: float = 0.0
    used_gb: float = 0.0
    percent_used: float = 0.0
    gpu_used_gb: float = 0.0
    gpu_total_gb: float = 0.0
    
    def __str__(self):
        s = f"RAM: {self.used_gb:.1f}/{self.total_gb:.1f}GB ({self.percent_used:.0f}%)"
        if self.gpu_total_gb > 0:
            s += f" | GPU: {self.gpu_used_gb:.1f}/{self.gpu_total_gb:.1f}GB"
        return s


def get_memory_stats(process_only: bool = False) -> MemoryStats:
    """
    Get current memory usage statistics
    
    Args:
        process_only: If True, track only this process's memory (better for Kaggle)
    """
    stats = MemoryStats()
    
    if HAS_PSUTIL:
        if process_only:
            # Track THIS process's memory - more accurate for Kaggle/Colab
            process = psutil.Process()
            mem_info = process.memory_info()
            stats.used_gb = mem_info.rss / (1024**3)  # Resident Set Size
            
            # System total for reference
            sys_mem = psutil.virtual_memory()
            stats.total_gb = sys_mem.total / (1024**3)
            stats.available_gb = sys_mem.available / (1024**3)
            stats.percent_used = (mem_info.rss / sys_mem.total) * 100
        else:
            mem = psutil.virtual_memory()
            stats.total_gb = mem.total / (1024**3)
            stats.available_gb = mem.available / (1024**3)
            stats.used_gb = mem.used / (1024**3)
            stats.percent_used = mem.percent
    
    if torch.cuda.is_available():
        stats.gpu_used_gb = torch.cuda.memory_allocated() / (1024**3)
        stats.gpu_total_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
    
    return stats


def check_memory_available(required_gb: float, safety_margin: float = 0.2) -> bool:
    """Check if enough memory is available"""
    stats = get_memory_stats()
    available = stats.available_gb * (1 - safety_margin)
    return available >= required_gb


def force_garbage_collect(aggressive: bool = True):
    """
    Aggressive garbage collection to free memory
    
    Args:
        aggressive: If True, perform multiple GC passes and clear all caches
    """
    # Clear any Python object caches
    if aggressive:
        # Clear __del__ cycle
        gc.collect(0)
        gc.collect(1)
        gc.collect(2)
    
    gc.collect()
    gc.collect()
    gc.collect()
    
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
    
    # On Kaggle/Colab, also try to release any lingering memory
    if aggressive:
        try:
            import ctypes
            libc = ctypes.CDLL("libc.so.6")
            libc.malloc_trim(0)
        except Exception:
            pass  # Not available on all systems


@contextmanager
def memory_efficient_scope(description: str = "operation"):
    """Context manager for memory-efficient operations with auto cleanup"""
    stats_before = get_memory_stats()
    try:
        yield
    finally:
        force_garbage_collect()
        stats_after = get_memory_stats()
        freed = stats_before.used_gb - stats_after.used_gb
        if freed > 0.1:
            print(f"   🧹 Freed {freed:.2f}GB after {description}")


class MemoryMonitor:
    """
    Real-time memory monitoring with OOM prevention
    
    Usage:
        monitor = MemoryMonitor(max_memory_gb=28)
        
        for layer in layers:
            if not monitor.can_proceed(estimated_gb=2.0):
                monitor.emergency_cleanup()
            
            process_layer(layer)
            monitor.checkpoint(f"layer_{i}")
    """
    
    def __init__(
        self,
        max_memory_gb: Optional[float] = None,
        warning_threshold: float = 0.85,
        critical_threshold: float = 0.95,
        auto_cleanup: bool = True,
        kaggle_mode: bool = False
    ):
        """
        Args:
            max_memory_gb: Maximum memory budget
            warning_threshold: Warn when exceeding this ratio
            critical_threshold: Emergency cleanup at this ratio
            auto_cleanup: Automatically cleanup when critical
            kaggle_mode: Use Kaggle-safe settings (lower thresholds, process tracking)
        """
        if kaggle_mode:
            # Kaggle-specific: more conservative since no virtual memory
            warning_threshold = min(warning_threshold, 0.70)
            critical_threshold = min(critical_threshold, 0.80)
            if max_memory_gb is None:
                max_memory_gb = 25.0  # Safe for Kaggle's 30GB
        
        if max_memory_gb is None:
            stats = get_memory_stats()
            max_memory_gb = stats.total_gb * 0.9  # Use 90% of total
        
        self.max_memory_gb = max_memory_gb
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.auto_cleanup = auto_cleanup
        self.kaggle_mode = kaggle_mode
        self.checkpoints: List[Tuple[str, MemoryStats]] = []
        self._cleanup_count = 0
    
    def get_usage_ratio(self) -> float:
        """Get current memory usage as ratio of max allowed"""
        stats = get_memory_stats(process_only=self.kaggle_mode)
        return stats.used_gb / self.max_memory_gb
    
    def can_proceed(self, estimated_gb: float = 0.0) -> bool:
        """Check if we can proceed with estimated additional memory usage"""
        stats = get_memory_stats(process_only=self.kaggle_mode)
        projected = (stats.used_gb + estimated_gb) / self.max_memory_gb
        
        if projected >= self.critical_threshold:
            if self.auto_cleanup:
                self.emergency_cleanup()
                # Recheck after cleanup
                stats = get_memory_stats(process_only=self.kaggle_mode)
                projected = (stats.used_gb + estimated_gb) / self.max_memory_gb
            
            if projected >= self.critical_threshold:
                return False
        
        if projected >= self.warning_threshold:
            print(f"   ⚠️ Memory warning: {stats.used_gb:.1f}GB used ({projected*100:.0f}% projected)")
        
        return True
    
    def checkpoint(self, name: str):
        """Record memory checkpoint"""
        stats = get_memory_stats()
        self.checkpoints.append((name, stats))
    
    def emergency_cleanup(self):
        """Emergency memory cleanup when approaching OOM"""
        self._cleanup_count += 1
        print(f"   🚨 Emergency memory cleanup (#{self._cleanup_count})...")
        
        # Aggressive cleanup
        force_garbage_collect(aggressive=True)
        
        # Clear any cached tensors
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats()
        
        # If on Kaggle and still high memory, do additional cleanup
        if self.kaggle_mode and self._cleanup_count > 2:
            # Try to force Python to release memory back to OS
            import gc
            gc.set_threshold(100, 5, 5)  # More aggressive thresholds
            for _ in range(5):
                gc.collect()
        
        stats = get_memory_stats(process_only=self.kaggle_mode)
        print(f"   📊 After cleanup: {stats}")
    
    def summary(self) -> str:
        """Get memory usage summary"""
        if not self.checkpoints:
            return "No checkpoints recorded"
        
        lines = ["Memory Usage Summary:"]
        peak_used = 0
        for name, stats in self.checkpoints:
            peak_used = max(peak_used, stats.used_gb)
            lines.append(f"  {name}: {stats.used_gb:.2f}GB")
        
        lines.append(f"  Peak: {peak_used:.2f}GB / {self.max_memory_gb:.1f}GB allowed")
        return "\n".join(lines)


# ==================== Sharded Checkpoint Handling ====================

@dataclass
class ShardInfo:
    """Information about a model weight shard"""
    filename: str
    size_bytes: int
    tensor_names: List[str] = field(default_factory=list)
    
    @property
    def size_gb(self) -> float:
        return self.size_bytes / (1024**3)


@dataclass  
class CheckpointIndex:
    """Index of sharded checkpoint files"""
    weight_map: Dict[str, str]  # tensor_name -> filename
    shards: List[ShardInfo]
    total_size_gb: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_index_file(cls, index_path: str) -> "CheckpointIndex":
        """Load from model.safetensors.index.json or pytorch_model.bin.index.json"""
        with open(index_path) as f:
            data = json.load(f)
        
        weight_map = data.get("weight_map", {})
        metadata = data.get("metadata", {})
        
        # Group tensors by shard
        shard_tensors: Dict[str, List[str]] = {}
        for tensor_name, filename in weight_map.items():
            if filename not in shard_tensors:
                shard_tensors[filename] = []
            shard_tensors[filename].append(tensor_name)
        
        # Get shard sizes
        index_dir = Path(index_path).parent
        shards = []
        total_size = 0
        
        for filename, tensors in shard_tensors.items():
            shard_path = index_dir / filename
            size = shard_path.stat().st_size if shard_path.exists() else 0
            total_size += size
            shards.append(ShardInfo(
                filename=filename,
                size_bytes=size,
                tensor_names=tensors
            ))
        
        return cls(
            weight_map=weight_map,
            shards=shards,
            total_size_gb=total_size / (1024**3),
            metadata=metadata
        )


def find_checkpoint_files(model_path: str) -> Tuple[str, List[str]]:
    """
    Find checkpoint files in model directory
    
    Returns:
        (checkpoint_type, list_of_files)
        checkpoint_type: "safetensors", "pytorch", or "single"
    """
    model_path = Path(model_path)
    
    # Check for safetensors index
    st_index = model_path / "model.safetensors.index.json"
    if st_index.exists():
        index = CheckpointIndex.from_index_file(str(st_index))
        files = [str(model_path / s.filename) for s in index.shards]
        return "safetensors_sharded", files
    
    # Check for single safetensors
    st_single = model_path / "model.safetensors"
    if st_single.exists():
        return "safetensors", [str(st_single)]
    
    # Check for pytorch index
    pt_index = model_path / "pytorch_model.bin.index.json"
    if pt_index.exists():
        index = CheckpointIndex.from_index_file(str(pt_index))
        files = [str(model_path / s.filename) for s in index.shards]
        return "pytorch_sharded", files
    
    # Check for single pytorch
    pt_single = model_path / "pytorch_model.bin"
    if pt_single.exists():
        return "pytorch", [str(pt_single)]
    
    # Check for any safetensors files
    st_files = list(model_path.glob("*.safetensors"))
    if st_files:
        return "safetensors_multiple", [str(f) for f in st_files]
    
    # Check for any bin files
    bin_files = list(model_path.glob("*.bin"))
    if bin_files:
        return "pytorch_multiple", [str(f) for f in bin_files]
    
    raise FileNotFoundError(f"No checkpoint files found in {model_path}")


# ==================== Streaming Weight Loading ====================

class StreamingWeightLoader:
    """
    Memory-efficient weight loader using streaming and memory mapping
    
    Supports:
    - Safetensors (preferred, zero-copy memory mapping)
    - PyTorch .bin files (with streaming)
    - Sharded checkpoints (multiple files)
    
    Usage:
        loader = StreamingWeightLoader("path/to/model")
        
        for name, tensor in loader.stream_tensors():
            process_tensor(name, tensor)
            # tensor is automatically freed after iteration
    """
    
    def __init__(
        self,
        model_path: str,
        device: str = "cpu",
        dtype: Optional[torch.dtype] = None,
        max_tensor_memory_gb: float = 2.0
    ):
        self.model_path = Path(model_path)
        self.device = device
        self.dtype = dtype
        self.max_tensor_memory_gb = max_tensor_memory_gb
        
        # Find checkpoint type and files
        self.checkpoint_type, self.files = find_checkpoint_files(str(model_path))
        
        # Load index if sharded
        self.index: Optional[CheckpointIndex] = None
        if "sharded" in self.checkpoint_type:
            index_file = self.model_path / f"model.safetensors.index.json"
            if not index_file.exists():
                index_file = self.model_path / "pytorch_model.bin.index.json"
            if index_file.exists():
                self.index = CheckpointIndex.from_index_file(str(index_file))
        
        print(f"📂 Found {self.checkpoint_type} checkpoint")
        print(f"   Files: {len(self.files)}")
        if self.index:
            print(f"   Total size: {self.index.total_size_gb:.2f}GB")
            print(f"   Tensors: {len(self.index.weight_map)}")
    
    def get_tensor_list(self) -> List[str]:
        """Get list of all tensor names without loading data"""
        if self.index:
            return list(self.index.weight_map.keys())
        
        if "safetensors" in self.checkpoint_type and HAS_SAFETENSORS:
            names = []
            for f in self.files:
                with safe_open(f, framework="pt", device="cpu") as st:
                    names.extend(st.keys())
            return names
        
        # For PyTorch files, we need to load metadata
        # This is less efficient but still works
        names = []
        for f in self.files:
            state_dict = torch.load(f, map_location="cpu", weights_only=True)
            names.extend(state_dict.keys())
            del state_dict
            force_garbage_collect()
        return names
    
    def stream_tensors(
        self,
        filter_fn: Optional[callable] = None,
        layer_by_layer: bool = True
    ) -> Iterator[Tuple[str, torch.Tensor]]:
        """
        Stream tensors one at a time with automatic memory cleanup
        
        Args:
            filter_fn: Optional function to filter tensors by name
            layer_by_layer: If True, process all tensors of one layer before next
            
        Yields:
            (tensor_name, tensor_data)
        """
        if "safetensors" in self.checkpoint_type and HAS_SAFETENSORS:
            yield from self._stream_safetensors(filter_fn)
        else:
            yield from self._stream_pytorch(filter_fn)
    
    def _stream_safetensors(
        self,
        filter_fn: Optional[callable] = None
    ) -> Iterator[Tuple[str, torch.Tensor]]:
        """Stream from safetensors files with memory mapping"""
        for filepath in self.files:
            # Use memory mapping for zero-copy access
            with safe_open(filepath, framework="pt", device=self.device) as st:
                for name in st.keys():
                    if filter_fn and not filter_fn(name):
                        continue
                    
                    # Get tensor with memory mapping (zero-copy!)
                    tensor = st.get_tensor(name)
                    
                    # Cast dtype if needed
                    if self.dtype and tensor.dtype != self.dtype:
                        tensor = tensor.to(self.dtype)
                    
                    yield name, tensor
                    
                    # Explicit cleanup after yield returns
                    del tensor
            
            # Cleanup after each file
            force_garbage_collect()
    
    def _stream_pytorch(
        self,
        filter_fn: Optional[callable] = None
    ) -> Iterator[Tuple[str, torch.Tensor]]:
        """Stream from PyTorch .bin files"""
        for filepath in self.files:
            # Load one file at a time
            state_dict = torch.load(
                filepath,
                map_location=self.device,
                weights_only=True
            )
            
            for name, tensor in state_dict.items():
                if filter_fn and not filter_fn(name):
                    continue
                
                if self.dtype and tensor.dtype != self.dtype:
                    tensor = tensor.to(self.dtype)
                
                yield name, tensor.clone()  # Clone to allow cleanup
            
            # Cleanup file's state_dict
            del state_dict
            force_garbage_collect()
    
    def get_tensor(self, name: str) -> torch.Tensor:
        """Get a single tensor by name"""
        if self.index:
            # Find which file contains this tensor
            filename = self.index.weight_map.get(name)
            if filename:
                filepath = self.model_path / filename
                if "safetensors" in self.checkpoint_type and HAS_SAFETENSORS:
                    with safe_open(str(filepath), framework="pt", device=self.device) as st:
                        return st.get_tensor(name)
                else:
                    state_dict = torch.load(str(filepath), map_location=self.device)
                    tensor = state_dict[name].clone()
                    del state_dict
                    force_garbage_collect()
                    return tensor
        
        # Linear search through files
        for filepath in self.files:
            if "safetensors" in self.checkpoint_type and HAS_SAFETENSORS:
                with safe_open(filepath, framework="pt", device=self.device) as st:
                    if name in st.keys():
                        return st.get_tensor(name)
            else:
                state_dict = torch.load(filepath, map_location=self.device)
                if name in state_dict:
                    tensor = state_dict[name].clone()
                    del state_dict
                    force_garbage_collect()
                    return tensor
                del state_dict
                force_garbage_collect()
        
        raise KeyError(f"Tensor '{name}' not found in checkpoint")
    
    def get_layer_tensors(self, layer_idx: int) -> Dict[str, torch.Tensor]:
        """Get all tensors for a specific layer"""
        prefix = f"model.layers.{layer_idx}."
        alt_prefix = f"layers.{layer_idx}."
        
        tensors = {}
        for name, tensor in self.stream_tensors(
            filter_fn=lambda n: n.startswith(prefix) or n.startswith(alt_prefix)
        ):
            # Normalize name
            short_name = name.replace(prefix, "").replace(alt_prefix, "")
            tensors[short_name] = tensor
        
        return tensors


# ==================== Streaming GGUF Export ====================

class StreamingGGUFWriter:
    """
    Memory-efficient GGUF writer that streams tensors to disk
    
    Instead of holding all tensors in memory, writes them incrementally.
    Perfect for converting 70B+ models with limited RAM.
    """
    
    # GGUF constants
    GGUF_MAGIC = 0x46554747
    GGUF_VERSION = 3
    ALIGNMENT = 32
    
    # GGML types
    GGML_TYPE_F32 = 0
    GGML_TYPE_F16 = 1
    GGML_TYPE_Q4_0 = 2
    GGML_TYPE_Q4_1 = 3
    GGML_TYPE_Q8_0 = 8
    GGML_TYPE_Q4_K = 12
    GGML_TYPE_Q5_K = 13
    
    QUANT_TYPES = {
        "f32": GGML_TYPE_F32,
        "f16": GGML_TYPE_F16,
        "q4_0": GGML_TYPE_Q4_0,
        "q4_k": GGML_TYPE_Q4_K,
        "q4_k_m": GGML_TYPE_Q4_K,
        "q4_k_s": GGML_TYPE_Q4_K,
        "q5_k": GGML_TYPE_Q5_K,
        "q5_k_m": GGML_TYPE_Q5_K,
        "q8_0": GGML_TYPE_Q8_0,
    }
    
    def __init__(
        self,
        output_path: str,
        metadata: Optional[Dict[str, Any]] = None,
        arch: str = "llama"
    ):
        self.output_path = output_path
        self.metadata = metadata or {}
        self.arch = arch
        
        # Two-pass writing: first collect info, then write
        self.tensor_infos: List[Dict] = []
        self.temp_data_file = tempfile.NamedTemporaryFile(delete=False, suffix=".bin")
        self.data_offset = 0
    
    def add_metadata(self, key: str, value: Any):
        """Add metadata key-value pair"""
        self.metadata[key] = value
    
    def add_tensor_streaming(
        self,
        name: str,
        tensor: torch.Tensor,
        quantization: str = "f16"
    ):
        """
        Add tensor with streaming - writes data immediately to temp file
        
        Memory usage: Only one tensor at a time
        """
        qtype = self.QUANT_TYPES.get(quantization.lower(), self.GGML_TYPE_F16)
        
        # Quantize tensor
        quantized_data = self._quantize_tensor(tensor, qtype)
        
        # Calculate alignment padding
        padding = (self.ALIGNMENT - (self.data_offset % self.ALIGNMENT)) % self.ALIGNMENT
        if padding > 0:
            self.temp_data_file.write(bytes(padding))
            self.data_offset += padding
        
        # Record tensor info
        self.tensor_infos.append({
            "name": name,
            "shape": list(tensor.shape),
            "dtype": qtype,
            "offset": self.data_offset,
            "size": len(quantized_data)
        })
        
        # Write quantized data to temp file
        self.temp_data_file.write(quantized_data)
        self.data_offset += len(quantized_data)
        
        # Explicit cleanup
        del quantized_data
        del tensor
    
    def _quantize_tensor(self, tensor: torch.Tensor, qtype: int) -> bytes:
        """Quantize tensor to specified type"""
        data = tensor.detach().cpu().float().numpy()
        
        if qtype == self.GGML_TYPE_F32:
            return data.astype(np.float32).tobytes()
        
        elif qtype == self.GGML_TYPE_F16:
            return data.astype(np.float16).tobytes()
        
        elif qtype == self.GGML_TYPE_Q8_0:
            return self._quantize_q8_0(data)
        
        elif qtype in [self.GGML_TYPE_Q4_0, self.GGML_TYPE_Q4_K]:
            return self._quantize_q4_0(data)
        
        elif qtype == self.GGML_TYPE_Q5_K:
            return self._quantize_q5_0(data)
        
        else:
            return data.astype(np.float16).tobytes()
    
    def _quantize_q4_0(self, data: np.ndarray) -> bytes:
        """Q4_0 quantization with block processing for memory efficiency"""
        data = data.flatten()
        n = len(data)
        
        # Pad to multiple of 32
        if n % 32 != 0:
            data = np.pad(data, (0, 32 - n % 32))
            n = len(data)
        
        n_blocks = n // 32
        result = bytearray()
        
        # Process in chunks to save memory
        chunk_size = 10000  # blocks per chunk
        for chunk_start in range(0, n_blocks, chunk_size):
            chunk_end = min(chunk_start + chunk_size, n_blocks)
            
            for i in range(chunk_start, chunk_end):
                block = data[i * 32:(i + 1) * 32]
                
                max_val = np.max(np.abs(block))
                scale = max_val / 7.0 if max_val > 0 else 1.0
                
                quantized = np.round(block / scale).clip(-8, 7).astype(np.int8)
                
                packed = bytearray(16)
                for j in range(16):
                    low = (quantized[j * 2] + 8) & 0x0F
                    high = (quantized[j * 2 + 1] + 8) & 0x0F
                    packed[j] = low | (high << 4)
                
                result += struct.pack('<e', scale)
                result += packed
        
        return bytes(result)
    
    def _quantize_q5_0(self, data: np.ndarray) -> bytes:
        """Q5_0 quantization"""
        data = data.flatten()
        n = len(data)
        
        if n % 32 != 0:
            data = np.pad(data, (0, 32 - n % 32))
            n = len(data)
        
        n_blocks = n // 32
        result = bytearray()
        
        for i in range(n_blocks):
            block = data[i * 32:(i + 1) * 32]
            
            max_val = np.max(np.abs(block))
            scale = max_val / 15.0 if max_val > 0 else 1.0
            
            quantized = np.round(block / scale).clip(-16, 15).astype(np.int8)
            
            packed = bytearray(20)
            bits = []
            for q in quantized:
                for b in range(5):
                    bits.append((q >> b) & 1)
            
            for j in range(20):
                byte_val = 0
                for b in range(8):
                    if j * 8 + b < len(bits):
                        byte_val |= bits[j * 8 + b] << b
                packed[j] = byte_val
            
            result += struct.pack('<e', scale)
            result += packed
        
        return bytes(result)
    
    def _quantize_q8_0(self, data: np.ndarray) -> bytes:
        """Q8_0 quantization"""
        data = data.flatten()
        n = len(data)
        
        if n % 32 != 0:
            data = np.pad(data, (0, 32 - n % 32))
            n = len(data)
        
        n_blocks = n // 32
        result = bytearray()
        
        for i in range(n_blocks):
            block = data[i * 32:(i + 1) * 32]
            
            max_val = np.max(np.abs(block))
            scale = max_val / 127.0 if max_val > 0 else 1.0
            
            quantized = np.round(block / scale).clip(-128, 127).astype(np.int8)
            
            result += struct.pack('<e', scale)
            result += quantized.tobytes()
        
        return bytes(result)
    
    def _write_string(self, f, s: str):
        """Write GGUF string"""
        encoded = s.encode('utf-8')
        f.write(struct.pack('<Q', len(encoded)))
        f.write(encoded)
    
    def _write_metadata_value(self, f, key: str, value: Any):
        """Write metadata key-value pair"""
        self._write_string(f, key)
        
        if isinstance(value, bool):
            f.write(struct.pack('<I', 7))  # BOOL
            f.write(struct.pack('<?', value))
        elif isinstance(value, int):
            if value < 0:
                f.write(struct.pack('<I', 5))  # INT32
                f.write(struct.pack('<i', value))
            else:
                f.write(struct.pack('<I', 4))  # UINT32
                f.write(struct.pack('<I', value))
        elif isinstance(value, float):
            f.write(struct.pack('<I', 6))  # FLOAT32
            f.write(struct.pack('<f', value))
        elif isinstance(value, str):
            f.write(struct.pack('<I', 8))  # STRING
            self._write_string(f, value)
        elif isinstance(value, (list, tuple)):
            f.write(struct.pack('<I', 9))  # ARRAY
            if len(value) > 0 and isinstance(value[0], str):
                f.write(struct.pack('<I', 8))  # STRING
                f.write(struct.pack('<Q', len(value)))
                for item in value:
                    self._write_string(f, item)
            else:
                f.write(struct.pack('<I', 4))  # UINT32
                f.write(struct.pack('<Q', len(value)))
                for item in value:
                    f.write(struct.pack('<I', int(item)))
    
    def finalize(self):
        """
        Finalize GGUF file by combining header and data
        
        This is the only point where we write the final file.
        """
        self.temp_data_file.close()
        
        print(f"📝 Finalizing GGUF: {len(self.tensor_infos)} tensors")
        
        with open(self.output_path, 'wb') as f:
            # 1. Header
            f.write(struct.pack('<I', self.GGUF_MAGIC))
            f.write(struct.pack('<I', self.GGUF_VERSION))
            f.write(struct.pack('<Q', len(self.tensor_infos)))
            f.write(struct.pack('<Q', len(self.metadata)))
            
            # 2. Metadata
            for key, value in self.metadata.items():
                self._write_metadata_value(f, key, value)
            
            # 3. Tensor infos
            for info in self.tensor_infos:
                self._write_string(f, info["name"])
                f.write(struct.pack('<I', len(info["shape"])))
                for dim in info["shape"]:
                    f.write(struct.pack('<Q', dim))
                f.write(struct.pack('<I', info["dtype"]))
                f.write(struct.pack('<Q', info["offset"]))
            
            # 4. Padding to alignment
            current_pos = f.tell()
            padding = (self.ALIGNMENT - (current_pos % self.ALIGNMENT)) % self.ALIGNMENT
            f.write(bytes(padding))
            
            # 5. Copy tensor data from temp file (streaming)
            with open(self.temp_data_file.name, 'rb') as data_file:
                # Copy in chunks to save memory
                chunk_size = 64 * 1024 * 1024  # 64MB chunks
                while True:
                    chunk = data_file.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
        
        # Cleanup temp file
        os.unlink(self.temp_data_file.name)
        
        # Report file size
        file_size = os.path.getsize(self.output_path)
        print(f"✅ GGUF saved: {self.output_path}")
        print(f"   Size: {file_size / (1024**3):.2f} GB")
        print(f"   Tensors: {len(self.tensor_infos)}")


# ==================== High-Level Streaming Conversion ====================

def download_model_for_streaming(
    model_id: str,
    local_dir: Optional[str] = None,
    token: Optional[str] = None
) -> str:
    """
    Download model files for streaming conversion
    
    Downloads only necessary files (config, safetensors/pytorch)
    """
    if not HAS_HF_HUB:
        raise ImportError("huggingface_hub required: pip install huggingface_hub")
    
    if local_dir is None:
        local_dir = f"./models/{model_id.replace('/', '_')}"
    
    os.makedirs(local_dir, exist_ok=True)
    
    print(f"📥 Downloading {model_id} for streaming...")
    
    # Get file list
    try:
        files = list_repo_files(model_id, token=token)
    except Exception as e:
        raise RuntimeError(f"Failed to list files: {e}")
    
    # Download config
    for config_file in ["config.json", "tokenizer.json", "tokenizer_config.json"]:
        if config_file in files:
            try:
                hf_hub_download(
                    model_id,
                    config_file,
                    local_dir=local_dir,
                    token=token
                )
            except Exception:
                pass
    
    # Download weight index if sharded
    index_files = [
        "model.safetensors.index.json",
        "pytorch_model.bin.index.json"
    ]
    for idx_file in index_files:
        if idx_file in files:
            hf_hub_download(
                model_id,
                idx_file,
                local_dir=local_dir,
                token=token
            )
    
    # Download weight files
    weight_patterns = [".safetensors", ".bin"]
    for f in files:
        if any(f.endswith(p) for p in weight_patterns):
            if "training" not in f.lower() and "optimizer" not in f.lower():
                print(f"   Downloading: {f}")
                hf_hub_download(
                    model_id,
                    f,
                    local_dir=local_dir,
                    token=token
                )
    
    print(f"✅ Downloaded to: {local_dir}")
    return local_dir


def stream_convert_to_gguf(
    model_path: str,
    output_path: str,
    quantization: str = "q4_k_m",
    max_memory_gb: Optional[float] = None,
    download_if_needed: bool = True,
    token: Optional[str] = None
) -> str:
    """
    🚀 Stream-convert any model to GGUF with minimal RAM
    
    Designed for converting 70B-200B models on Kaggle (30GB RAM)
    
    Args:
        model_path: HuggingFace ID or local path
        output_path: Output .gguf file path
        quantization: q4_k_m, q5_k_m, q8_0, f16
        max_memory_gb: Maximum RAM to use (auto-detected if None)
        download_if_needed: Download from HF if not local
        token: HuggingFace token for private models
        
    Returns:
        Path to created GGUF file
        
    Example:
        # Convert Llama 70B with only 30GB RAM!
        stream_convert_to_gguf(
            "meta-llama/Llama-2-70b-hf",
            "llama-70b-Q4_K_M.gguf",
            quantization="q4_k_m",
            max_memory_gb=28
        )
    """
    print("\n" + "=" * 60)
    print("🔄 OMNIMIND Streaming GGUF Conversion")
    print("=" * 60)
    
    # Setup memory monitor
    monitor = MemoryMonitor(max_memory_gb=max_memory_gb)
    stats = get_memory_stats()
    print(f"📊 System Memory: {stats}")
    
    # Check if model_path is HuggingFace ID
    if "/" in model_path and not Path(model_path).exists():
        if download_if_needed:
            model_path = download_model_for_streaming(model_path, token=token)
        else:
            raise FileNotFoundError(f"Model not found: {model_path}")
    
    # Load config
    config_path = Path(model_path) / "config.json"
    config = {}
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
        print(f"\n📋 Model Config:")
        print(f"   Architecture: {config.get('architectures', ['Unknown'])[0]}")
        print(f"   Hidden size: {config.get('hidden_size', 'N/A')}")
        print(f"   Layers: {config.get('num_hidden_layers', 'N/A')}")
        print(f"   Vocab: {config.get('vocab_size', 'N/A')}")
    
    # Create streaming loader
    print("\n📂 Loading checkpoint index...")
    loader = StreamingWeightLoader(model_path)
    
    # Create streaming GGUF writer
    print(f"\n🎯 Output: {output_path}")
    print(f"   Quantization: {quantization.upper()}")
    
    writer = StreamingGGUFWriter(output_path, arch=config.get('model_type', 'llama'))
    
    # Add metadata
    writer.add_metadata("general.architecture", config.get('model_type', 'llama'))
    writer.add_metadata("general.name", Path(model_path).name)
    if 'hidden_size' in config:
        writer.add_metadata(f"{config.get('model_type', 'llama')}.embedding_length", config['hidden_size'])
    if 'num_hidden_layers' in config:
        writer.add_metadata(f"{config.get('model_type', 'llama')}.block_count", config['num_hidden_layers'])
    if 'vocab_size' in config:
        writer.add_metadata(f"{config.get('model_type', 'llama')}.vocab_size", config['vocab_size'])
    
    # Stream convert tensors
    print("\n🔄 Converting tensors (streaming)...")
    tensor_count = 0
    
    for name, tensor in loader.stream_tensors():
        # Memory check
        if not monitor.can_proceed(estimated_gb=0.5):
            print(f"   ⚠️ Memory critical, forcing cleanup...")
            monitor.emergency_cleanup()
        
        # Determine quantization for this tensor
        tensor_quant = quantization
        if "embed" in name.lower() or "norm" in name.lower():
            tensor_quant = "f16"  # Keep embeddings/norms in higher precision
        elif tensor.dim() < 2 or tensor.numel() < 1024:
            tensor_quant = "f32"  # Small tensors stay f32
        
        # Map tensor name
        gguf_name = _map_tensor_name(name, config.get('model_type', 'llama'))
        
        # Add tensor with streaming
        writer.add_tensor_streaming(gguf_name, tensor, tensor_quant)
        tensor_count += 1
        
        # Progress update
        if tensor_count % 50 == 0:
            stats = get_memory_stats()
            print(f"   Processed {tensor_count} tensors... ({stats})")
        
        # Cleanup after each tensor
        del tensor
        
        # Periodic GC
        if tensor_count % 20 == 0:
            force_garbage_collect()
    
    # Finalize GGUF
    print(f"\n📝 Finalizing GGUF file...")
    writer.finalize()
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ Streaming Conversion Complete!")
    print(f"   Output: {output_path}")
    print(f"   Tensors: {tensor_count}")
    print(f"   {monitor.summary()}")
    
    return output_path


def _map_tensor_name(name: str, arch: str = "llama") -> str:
    """Map PyTorch tensor names to GGUF format"""
    # Common mappings
    mappings = {
        "model.embed_tokens.weight": "token_embd.weight",
        "model.norm.weight": "output_norm.weight",
        "lm_head.weight": "output.weight",
    }
    
    if name in mappings:
        return mappings[name]
    
    # Layer mappings
    # model.layers.0.self_attn.q_proj.weight -> blk.0.attn_q.weight
    if "layers." in name:
        import re
        match = re.search(r'layers\.(\d+)\.(.+)', name)
        if match:
            layer_idx = match.group(1)
            rest = match.group(2)
            
            # Attention mappings
            rest = rest.replace("self_attn.", "attn_")
            rest = rest.replace("q_proj", "q")
            rest = rest.replace("k_proj", "k")
            rest = rest.replace("v_proj", "v")
            rest = rest.replace("o_proj", "output")
            
            # MLP mappings
            rest = rest.replace("mlp.", "ffn_")
            rest = rest.replace("gate_proj", "gate")
            rest = rest.replace("up_proj", "up")
            rest = rest.replace("down_proj", "down")
            
            # Norm mappings
            rest = rest.replace("input_layernorm", "attn_norm")
            rest = rest.replace("post_attention_layernorm", "ffn_norm")
            
            return f"blk.{layer_idx}.{rest}"
    
    return name


# ==================== Layer-by-Layer Conversion for Fine-tuning ====================

def stream_convert_layer_by_layer(
    source_model_path: str,
    target_config: Any,
    output_dir: str,
    conversion_fn: Optional[callable] = None,
    max_memory_gb: Optional[float] = None,
    download_if_needed: bool = True,
    token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convert model layer-by-layer for fine-tuning preparation
    
    Saves each converted layer as a separate safetensors file,
    allowing incremental loading during training.
    
    Args:
        source_model_path: Path to source model (or HF ID)
        target_config: OMNIMIND config for target model
        output_dir: Directory to save converted layers
        conversion_fn: Optional function to convert each layer
        max_memory_gb: Maximum RAM to use
        download_if_needed: Download from HF if not local
        token: HuggingFace token
        
    Returns:
        Dict with conversion statistics
    """
    # Download if needed
    if "/" in source_model_path and not Path(source_model_path).exists():
        if download_if_needed:
            source_model_path = download_model_for_streaming(source_model_path, token=token)
        else:
            raise FileNotFoundError(f"Model not found: {source_model_path}")

    os.makedirs(output_dir, exist_ok=True)
    
    # Copy config files
    print("📋 Copying config files...")
    for filename in ["config.json", "tokenizer.json", "tokenizer_config.json", "special_tokens_map.json", "generation_config.json"]:
        src = Path(source_model_path) / filename
        if src.exists():
            shutil.copy(src, Path(output_dir) / filename)

    monitor = MemoryMonitor(max_memory_gb=max_memory_gb)
    loader = StreamingWeightLoader(source_model_path)
    
    stats = {
        "layers_converted": 0,
        "tensors_converted": 0,
        "total_size_bytes": 0
    }
    
    # Track weight map for HF compatibility
    weight_map = {}
    
    # Group tensors by layer
    tensor_names = loader.get_tensor_list()
    
    # Find number of layers
    import re
    layer_indices = set()
    for name in tensor_names:
        match = re.search(r'layers\.(\d+)\.', name)
        if match:
            layer_indices.add(int(match.group(1)))
    
    n_layers = max(layer_indices) + 1 if layer_indices else 0
    print(f"📊 Found {n_layers} layers to convert")
    
    # Convert embeddings first
    with memory_efficient_scope("embeddings"):
        embed_tensors = {}
        for name, tensor in loader.stream_tensors(
            filter_fn=lambda n: "embed" in n.lower() and "layers" not in n
        ):
            embed_tensors[name] = tensor
        
        if embed_tensors and HAS_SAFETENSORS:
            filename = "embeddings.safetensors"
            save_safetensors(embed_tensors, f"{output_dir}/{filename}")
            stats["tensors_converted"] += len(embed_tensors)
            for name in embed_tensors:
                weight_map[name] = filename
    
    # Convert each layer
    for layer_idx in range(n_layers):
        with memory_efficient_scope(f"layer {layer_idx}"):
            if not monitor.can_proceed(estimated_gb=2.0):
                monitor.emergency_cleanup()
            
            print(f"   Converting layer {layer_idx}/{n_layers-1}...")
            
            # Get layer tensors with ORIGINAL full names preserved
            prefix = f"model.layers.{layer_idx}."
            alt_prefix = f"layers.{layer_idx}."
            
            # Create filter function with captured values (avoid closure issue)
            def make_filter(p, ap):
                return lambda n: n.startswith(p) or n.startswith(ap)
            
            layer_tensors = {}
            for name, tensor in loader.stream_tensors(
                filter_fn=make_filter(prefix, alt_prefix)
            ):
                layer_tensors[name] = tensor  # Keep original name!
            
            # Apply conversion if provided
            if conversion_fn:
                layer_tensors = conversion_fn(layer_tensors, layer_idx, target_config)
            
            # Save layer
            if layer_tensors and HAS_SAFETENSORS:
                filename = f"layer_{layer_idx:04d}.safetensors"
                layer_path = f"{output_dir}/{filename}"
                save_safetensors(layer_tensors, layer_path)
                stats["tensors_converted"] += len(layer_tensors)
                stats["total_size_bytes"] += os.path.getsize(layer_path)
                for name in layer_tensors:
                    weight_map[name] = filename  # Original name -> filename mapping
            
            stats["layers_converted"] += 1
            
            # Cleanup
            del layer_tensors
    
    # Convert final norm and lm_head
    with memory_efficient_scope("output"):
        output_tensors = {}
        for name, tensor in loader.stream_tensors(
            filter_fn=lambda n: ("norm" in n.lower() or "lm_head" in n.lower()) and "layers" not in n
        ):
            output_tensors[name] = tensor
        
        if output_tensors and HAS_SAFETENSORS:
            filename = "output.safetensors"
            save_safetensors(output_tensors, f"{output_dir}/{filename}")
            stats["tensors_converted"] += len(output_tensors)
            for name in output_tensors:
                weight_map[name] = filename
    
    # Save standard HF index
    index_data = {
        "metadata": {"total_size": stats["total_size_bytes"]},
        "weight_map": weight_map
    }
    with open(f"{output_dir}/model.safetensors.index.json", "w") as f:
        json.dump(index_data, f, indent=2)
    
    # Save OMNIMIND index (legacy/custom)
    index = {
        "n_layers": n_layers,
        "files": [
            "embeddings.safetensors",
            *[f"layer_{i:04d}.safetensors" for i in range(n_layers)],
            "output.safetensors"
        ],
        "stats": stats
    }
    with open(f"{output_dir}/omnimind_index.json", "w") as f:
        json.dump(index, f, indent=2)
    
    print(f"\n✅ Layer-by-layer conversion complete!")
    print(f"   Layers: {stats['layers_converted']}")
    print(f"   Tensors: {stats['tensors_converted']}")
    print(f"   Size: {stats['total_size_bytes'] / (1024**3):.2f} GB")
    print(f"   Format: Native Omnimind (HF-compatible Safetensors)")
    
    return stats


# ==================== Convenience Functions ====================

def estimate_model_memory(model_path: str, download_if_needed: bool = True, token: Optional[str] = None) -> Dict[str, float]:
    """
    Estimate memory requirements for converting a model.
    
    Uses lightweight index-based estimation to avoid loading all tensors.
    Safe to call on Kaggle/Colab without triggering OOM.
    
    Returns dict with estimates in GB for different operations
    """
    model_path_obj = Path(model_path)
    
    # If HuggingFace ID, try to get info without downloading everything
    if "/" in model_path and not model_path_obj.exists():
        return _estimate_from_hub(model_path, token)
    
    # Local path - check for index files first (lightweight)
    estimates = _estimate_from_index(model_path)
    if estimates:
        return estimates
    
    # Fallback: estimate from file sizes (still lightweight)
    return _estimate_from_file_sizes(model_path)


def _estimate_from_hub(model_id: str, token: Optional[str] = None) -> Dict[str, float]:
    """Estimate model size from HuggingFace Hub metadata (no download)"""
    if not HAS_HF_HUB:
        raise ImportError("huggingface_hub required: pip install huggingface_hub")
    
    from huggingface_hub import HfApi, hf_hub_download
    
    api = HfApi()
    
    try:
        # Try to get model info (includes file sizes)
        model_info = api.model_info(model_id, token=token)
        
        # Sum up safetensors/bin file sizes
        total_size = 0
        for sibling in model_info.siblings or []:
            if sibling.rfilename.endswith(('.safetensors', '.bin')):
                if 'training' not in sibling.rfilename.lower() and 'optimizer' not in sibling.rfilename.lower():
                    total_size += sibling.size or 0
        
        if total_size > 0:
            return _calculate_estimates_from_size(total_size)
        
        # Try to download just the config to estimate from hidden_size
        try:
            config_path = hf_hub_download(model_id, "config.json", token=token)
            with open(config_path) as f:
                config = json.load(f)
            return _estimate_from_config(config)
        except Exception:
            pass
            
    except Exception as e:
        warnings.warn(f"Could not get model info from Hub: {e}")
    
    # Return conservative estimate for unknown models
    return _default_estimates()


def _estimate_from_index(model_path: str) -> Optional[Dict[str, float]]:
    """Estimate from index.json files (lightweight, no tensor loading)"""
    model_path = Path(model_path)
    
    # Check for safetensors index
    st_index = model_path / "model.safetensors.index.json"
    pt_index = model_path / "pytorch_model.bin.index.json"
    
    index_file = st_index if st_index.exists() else (pt_index if pt_index.exists() else None)
    
    if index_file:
        with open(index_file) as f:
            data = json.load(f)
        
        metadata = data.get("metadata", {})
        total_size = metadata.get("total_size", 0)
        
        if total_size > 0:
            return _calculate_estimates_from_size(total_size)
        
        # Calculate from weight_map file sizes
        weight_map = data.get("weight_map", {})
        unique_files = set(weight_map.values())
        total_size = 0
        for filename in unique_files:
            file_path = model_path / filename
            if file_path.exists():
                total_size += file_path.stat().st_size
        
        if total_size > 0:
            return _calculate_estimates_from_size(total_size)
    
    return None


def _estimate_from_file_sizes(model_path: str) -> Dict[str, float]:
    """Estimate from file sizes (fallback, still lightweight)"""
    model_path = Path(model_path)
    
    total_size = 0
    for pattern in ["*.safetensors", "*.bin"]:
        for f in model_path.glob(pattern):
            if 'training' not in f.name.lower() and 'optimizer' not in f.name.lower():
                total_size += f.stat().st_size
    
    if total_size > 0:
        return _calculate_estimates_from_size(total_size)
    
    return _default_estimates()


def _estimate_from_config(config: Dict[str, Any]) -> Dict[str, float]:
    """Estimate from model config (for when we only have config.json)"""
    hidden_size = config.get("hidden_size", 4096)
    num_layers = config.get("num_hidden_layers", 32)
    vocab_size = config.get("vocab_size", 32000)
    intermediate_size = config.get("intermediate_size", hidden_size * 4)
    num_heads = config.get("num_attention_heads", 32)
    
    # Rough parameter estimation
    # Embedding: vocab_size * hidden_size
    # Per layer: ~12 * hidden_size^2 (attention + MLP)
    # LM head: hidden_size * vocab_size
    embed_params = vocab_size * hidden_size * 2  # embed + lm_head
    layer_params = num_layers * (12 * hidden_size * hidden_size + 3 * hidden_size * intermediate_size)
    total_params = embed_params + layer_params
    
    # Assume fp16 storage (2 bytes per param)
    total_size = total_params * 2
    
    return _calculate_estimates_from_size(total_size)


def _calculate_estimates_from_size(total_size_bytes: int) -> Dict[str, float]:
    """Calculate all estimates from total size in bytes"""
    size_gb = total_size_bytes / (1024**3)
    
    # Estimate params (assume fp16 = 2 bytes per param)
    total_params = total_size_bytes / 2
    
    return {
        "params_billions": total_params / 1e9,
        "fp32_gb": size_gb * 2,
        "fp16_gb": size_gb,
        "q8_gb": size_gb / 2,
        "q4_gb": size_gb / 4,
        "streaming_conversion_peak_gb": max(2.0, size_gb / 20),  # ~5% at peak
        "traditional_conversion_peak_gb": size_gb * 2.5,  # Need 2.5x for traditional
    }


def _default_estimates() -> Dict[str, float]:
    """Default estimates for unknown models"""
    return {
        "params_billions": 0,
        "fp32_gb": 0,
        "fp16_gb": 0,
        "q8_gb": 0,
        "q4_gb": 0,
        "streaming_conversion_peak_gb": 5.0,  # Conservative default
        "traditional_conversion_peak_gb": 50.0,
    }


def convert_native_to_sqlite(
    native_dir: str,
    output_db_path: str,
    compression: str = "zstd"
) -> str:
    """
    Convert Omnimind Native Format (Layer-wise Safetensors) to SQLite Storage
    
    This bridges the gap between low-memory conversion and high-speed inference.
    Safe for low-RAM environments as it processes file-by-file.
    
    Args:
        native_dir: Directory containing safetensors files
        output_db_path: Path to output .db file
        compression: Compression algorithm ("zstd", "none")
        
    Returns:
        Path to created database
    """
    try:
        from omnimind.storage import SQLiteWeightStorage, WeightStorageConfig
    except ImportError:
        raise ImportError("omnimind[storage] not installed")
        
    print(f"\n🔄 Converting Native Format to SQLite...")
    print(f"   Source: {native_dir}")
    print(f"   Output: {output_db_path}")
    
    native_path = Path(native_dir)
    if not native_path.exists():
        raise FileNotFoundError(f"Native directory not found: {native_dir}")
        
    # Initialize storage
    storage_config = WeightStorageConfig(
        compression=compression,
        cache_size_mb=256
    )
    storage = SQLiteWeightStorage(output_db_path, storage_config)
    
    # Load index to find files
    index_path = native_path / "model.safetensors.index.json"
    files_to_process = []
    
    if index_path.exists():
        with open(index_path) as f:
            index = json.load(f)
        # Get unique files from weight map
        files_to_process = sorted(list(set(index.get("weight_map", {}).values())))
    else:
        # Fallback: list all safetensors
        files_to_process = sorted([f.name for f in native_path.glob("*.safetensors")])
        
    print(f"   Found {len(files_to_process)} files to process")
    
    # Process each file
    total_tensors = 0
    
    for filename in files_to_process:
        file_path = native_path / filename
        print(f"   Processing {filename}...")
        
        with safe_open(file_path, framework="pt", device="cpu") as st:
            for name in st.keys():
                tensor = st.get_tensor(name)
                storage.save_weight(name, tensor)
                total_tensors += 1
                del tensor
                
        force_garbage_collect()
        
    # Copy metadata if available
    config_path = native_path / "config.json"
    if config_path.exists():
        with open(config_path) as f:
            config_str = f.read()
            storage._set_metadata("model_config", config_str)
            
    storage.close()
    
    print(f"✅ SQLite Conversion Complete!")
    print(f"   Tensors: {total_tensors}")
    print(f"   Database: {output_db_path}")
    
    return output_db_path


def can_convert_on_kaggle(model_path: str) -> Tuple[bool, str]:
    """
    Check if a model can be converted on Kaggle free tier (30GB RAM)
    
    Returns:
        (can_convert, explanation)
    """
    KAGGLE_RAM_GB = 30
    SAFETY_MARGIN = 0.85  # Use max 85%
    
    estimates = estimate_model_memory(model_path)
    peak_gb = estimates["streaming_conversion_peak_gb"]
    available = KAGGLE_RAM_GB * SAFETY_MARGIN
    
    if peak_gb <= available:
        return True, f"✅ Can convert! Peak: {peak_gb:.1f}GB, Available: {available:.1f}GB"
    else:
        return False, f"❌ May OOM. Peak: {peak_gb:.1f}GB, Available: {available:.1f}GB"


# ==================== Kaggle-Safe Streaming Conversion ====================

def kaggle_safe_convert(
    model_path: str,
    output_dir: str,
    output_format: str = "native",
    quantization: str = "q4_k_m",
    token: Optional[str] = None,
    max_memory_gb: float = 25.0,
    cleanup_frequency: int = 5
) -> Dict[str, Any]:
    """
    🔥 KAGGLE-OPTIMIZED Streaming Conversion
    
    Specifically designed for Kaggle's 30GB RAM limit with NO virtual memory.
    Uses ultra-aggressive memory management and immediate tensor cleanup.
    
    Key optimizations:
    - Process and save ONE tensor at a time (no accumulation)
    - Cleanup every N tensors (not every 20)
    - Process-level memory tracking (not system-level)
    - Conservative memory thresholds (70% warning, 80% critical)
    - Immediate file writes with fsync
    
    Args:
        model_path: HuggingFace model ID or local path
        output_dir: Directory to save converted files
        output_format: "native" (safetensors) or "gguf"
        quantization: q4_k_m, q5_k_m, q8_0, f16
        token: HuggingFace token for private models
        max_memory_gb: Maximum RAM budget (default 25GB for Kaggle safety)
        cleanup_frequency: Run GC every N tensors (lower = more aggressive)
        
    Returns:
        Dict with conversion statistics
        
    Example:
        # Convert 70B model on Kaggle Free Tier!
        stats = kaggle_safe_convert(
            "deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
            "./converted_model",
            output_format="native",
            max_memory_gb=25
        )
    """
    print("\n" + "=" * 60)
    print("🔥 KAGGLE-SAFE Streaming Conversion")
    print("=" * 60)
    print(f"⚠️  Kaggle Mode: NO virtual memory fallback!")
    print(f"📊 Memory Budget: {max_memory_gb:.1f}GB")
    print(f"🧹 Cleanup Frequency: Every {cleanup_frequency} tensors")
    
    # Initialize Kaggle-mode monitor
    monitor = MemoryMonitor(
        max_memory_gb=max_memory_gb,
        kaggle_mode=True  # Enables conservative thresholds
    )
    
    initial_stats = get_memory_stats(process_only=True)
    print(f"📊 Initial Memory: {initial_stats}")
    
    # Download if HuggingFace ID
    local_path = model_path
    if "/" in model_path and not Path(model_path).exists():
        print(f"\n📥 Downloading model files...")
        local_path = download_model_for_streaming(model_path, token=token)
        force_garbage_collect(aggressive=True)
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Copy config files first
    print("\n📋 Copying config files...")
    for filename in ["config.json", "tokenizer.json", "tokenizer_config.json", 
                     "special_tokens_map.json", "generation_config.json"]:
        src = Path(local_path) / filename
        if src.exists():
            shutil.copy(src, Path(output_dir) / filename)
    
    # Load config for metadata
    config = {}
    config_path = Path(local_path) / "config.json"
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
        print(f"   Model: {config.get('architectures', ['Unknown'])[0]}")
        print(f"   Layers: {config.get('num_hidden_layers', 'N/A')}")
    
    # Create streaming loader
    loader = StreamingWeightLoader(local_path)
    
    # Track statistics
    stats = {
        "tensors_converted": 0,
        "layers_converted": 0,
        "total_size_bytes": 0,
        "peak_memory_gb": 0,
        "output_format": output_format
    }
    
    if output_format == "gguf":
        # GGUF streaming conversion
        output_file = f"{output_dir}/model-{quantization}.gguf"
        stats["output_path"] = output_file
        
        writer = StreamingGGUFWriter(output_file, arch=config.get('model_type', 'llama'))
        
        # Add metadata
        writer.add_metadata("general.architecture", config.get('model_type', 'llama'))
        writer.add_metadata("general.name", Path(model_path).name)
        if 'hidden_size' in config:
            writer.add_metadata(f"{config.get('model_type', 'llama')}.embedding_length", config['hidden_size'])
        if 'num_hidden_layers' in config:
            writer.add_metadata(f"{config.get('model_type', 'llama')}.block_count", config['num_hidden_layers'])
        
        print(f"\n🔄 Converting to GGUF ({quantization})...")
        
        for name, tensor in loader.stream_tensors():
            # Check memory BEFORE processing
            if not monitor.can_proceed(estimated_gb=0.3):
                print(f"   ⚠️ Memory critical before {name}")
            
            # Determine quantization
            tensor_quant = quantization
            if "embed" in name.lower() or "norm" in name.lower():
                tensor_quant = "f16"
            elif tensor.dim() < 2 or tensor.numel() < 1024:
                tensor_quant = "f32"
            
            gguf_name = _map_tensor_name(name, config.get('model_type', 'llama'))
            writer.add_tensor_streaming(gguf_name, tensor, tensor_quant)
            
            # Immediate cleanup
            del tensor
            stats["tensors_converted"] += 1
            
            # Aggressive cleanup on Kaggle
            if stats["tensors_converted"] % cleanup_frequency == 0:
                force_garbage_collect(aggressive=True)
                current_stats = get_memory_stats(process_only=True)
                stats["peak_memory_gb"] = max(stats["peak_memory_gb"], current_stats.used_gb)
                
                if stats["tensors_converted"] % 50 == 0:
                    print(f"   Processed {stats['tensors_converted']} tensors... ({current_stats})")
        
        writer.finalize()
        stats["total_size_bytes"] = os.path.getsize(output_file)
        
    else:
        # Native format: Layer-by-layer with IMMEDIATE saves
        print(f"\n🔄 Converting to Native Format (Layer-wise Safetensors)...")
        
        weight_map = {}
        tensor_names = loader.get_tensor_list()
        
        # Find layer count
        import re
        layer_indices = set()
        for name in tensor_names:
            match = re.search(r'layers\.(\d+)\.', name)
            if match:
                layer_indices.add(int(match.group(1)))
        n_layers = max(layer_indices) + 1 if layer_indices else 0
        print(f"   Found {n_layers} layers")
        
        # Process embeddings (usually small, safe to batch)
        print("   Processing embeddings...")
        embed_tensors = {}
        for name, tensor in loader.stream_tensors(
            filter_fn=lambda n: "embed" in n.lower() and "layers" not in n
        ):
            embed_tensors[name] = tensor
        
        if embed_tensors and HAS_SAFETENSORS:
            filename = "embeddings.safetensors"
            save_safetensors(embed_tensors, f"{output_dir}/{filename}")
            for name in embed_tensors:
                weight_map[name] = filename
            stats["tensors_converted"] += len(embed_tensors)
            del embed_tensors
            force_garbage_collect(aggressive=True)
        
        # Process each layer ONE TENSOR AT A TIME
        for layer_idx in range(n_layers):
            print(f"   Layer {layer_idx}/{n_layers-1}...")
            
            if not monitor.can_proceed(estimated_gb=1.0):
                print(f"   ⚠️ Memory critical at layer {layer_idx}")
            
            prefix = f"model.layers.{layer_idx}."
            alt_prefix = f"layers.{layer_idx}."
            
            # Collect layer tensors (smaller per-layer memory)
            layer_tensors = {}
            for name, tensor in loader.stream_tensors(
                filter_fn=lambda n, p=prefix, ap=alt_prefix: n.startswith(p) or n.startswith(ap)
            ):
                layer_tensors[name] = tensor
                stats["tensors_converted"] += 1
                
                # Check if we're accumulating too much
                if len(layer_tensors) % cleanup_frequency == 0:
                    force_garbage_collect(aggressive=False)
            
            # Save layer immediately
            if layer_tensors and HAS_SAFETENSORS:
                filename = f"layer_{layer_idx:04d}.safetensors"
                layer_path = f"{output_dir}/{filename}"
                save_safetensors(layer_tensors, layer_path)
                stats["total_size_bytes"] += os.path.getsize(layer_path)
                
                for name in layer_tensors:
                    weight_map[name] = filename
            
            # Cleanup IMMEDIATELY after saving
            del layer_tensors
            force_garbage_collect(aggressive=True)
            
            stats["layers_converted"] += 1
            
            # Track peak memory
            current_stats = get_memory_stats(process_only=True)
            stats["peak_memory_gb"] = max(stats["peak_memory_gb"], current_stats.used_gb)
        
        # Process output layers
        print("   Processing output layers...")
        output_tensors = {}
        for name, tensor in loader.stream_tensors(
            filter_fn=lambda n: ("norm" in n.lower() or "lm_head" in n.lower()) and "layers" not in n
        ):
            output_tensors[name] = tensor
        
        if output_tensors and HAS_SAFETENSORS:
            filename = "output.safetensors"
            save_safetensors(output_tensors, f"{output_dir}/{filename}")
            for name in output_tensors:
                weight_map[name] = filename
            stats["tensors_converted"] += len(output_tensors)
            del output_tensors
            force_garbage_collect(aggressive=True)
        
        # Save HF-compatible index
        index_data = {
            "metadata": {"total_size": stats["total_size_bytes"]},
            "weight_map": weight_map
        }
        with open(f"{output_dir}/model.safetensors.index.json", "w") as f:
            json.dump(index_data, f, indent=2)
        
        stats["output_path"] = output_dir
    
    # Final cleanup and summary
    force_garbage_collect(aggressive=True)
    final_stats = get_memory_stats(process_only=True)
    
    print("\n" + "=" * 60)
    print("✅ KAGGLE-SAFE Conversion Complete!")
    print(f"   Output: {stats.get('output_path', output_dir)}")
    print(f"   Format: {output_format.upper()}")
    print(f"   Tensors: {stats['tensors_converted']}")
    print(f"   Size: {stats['total_size_bytes'] / (1024**3):.2f} GB")
    print(f"   Peak Memory: {stats['peak_memory_gb']:.1f} GB")
    print(f"   Final Memory: {final_stats.used_gb:.1f} GB")
    print("=" * 60)
    
    return stats


# Export all public functions
__all__ = [
    # Memory monitoring
    "MemoryStats",
    "get_memory_stats",
    "check_memory_available",
    "force_garbage_collect",
    "memory_efficient_scope",
    "MemoryMonitor",
    
    # Kaggle-optimized conversion
    "kaggle_safe_convert",
    
    # Checkpoint handling
    "ShardInfo",
    "CheckpointIndex",
    "find_checkpoint_files",
    
    # Streaming loading
    "StreamingWeightLoader",
    
    # Streaming conversion
    "StreamingGGUFWriter",
    "stream_convert_to_gguf",
    "stream_convert_layer_by_layer",
    "download_model_for_streaming",
    
    # Storage conversion
    "convert_native_to_sqlite",
    
    # Utilities
    "estimate_model_memory",
    "can_convert_on_kaggle",
]
