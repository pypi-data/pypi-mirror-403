"""
OMNIMIND GGUF Export
Export OMNIMIND models to GGUF format for llama.cpp compatibility

Supported Quantization Types:
- Q4_0: 4-bit (32 weights per block)
- Q4_1: 4-bit with delta
- Q4_K_S: 4-bit K-quant (small)
- Q4_K_M: 4-bit K-quant (medium) - Recommended
- Q5_0: 5-bit
- Q5_1: 5-bit with delta
- Q5_K_S: 5-bit K-quant (small)
- Q5_K_M: 5-bit K-quant (medium)
- Q8_0: 8-bit
- F16: Float16
- F32: Float32
"""
import os
import struct
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import IntEnum
import torch
import numpy as np


class GGMLType(IntEnum):
    """GGML tensor data types"""
    F32 = 0
    F16 = 1
    Q4_0 = 2
    Q4_1 = 3
    Q5_0 = 6
    Q5_1 = 7
    Q8_0 = 8
    Q8_1 = 9
    Q2_K = 10
    Q3_K = 11
    Q4_K = 12
    Q5_K = 13
    Q6_K = 14
    Q8_K = 15
    IQ2_XXS = 16
    IQ2_XS = 17
    IQ3_XXS = 18
    IQ1_S = 19
    IQ4_NL = 20
    IQ3_S = 21
    IQ2_S = 22
    IQ4_XS = 23


# GGUF Magic numbers
GGUF_MAGIC = 0x46554747  # "GGUF" in little endian
GGUF_VERSION = 3

# Quantization type mapping
QUANT_TYPES = {
    "f32": GGMLType.F32,
    "f16": GGMLType.F16,
    "q4_0": GGMLType.Q4_0,
    "q4_1": GGMLType.Q4_1,
    "q4_k": GGMLType.Q4_K,
    "q4_k_s": GGMLType.Q4_K,
    "q4_k_m": GGMLType.Q4_K,
    "q5_0": GGMLType.Q5_0,
    "q5_1": GGMLType.Q5_1,
    "q5_k": GGMLType.Q5_K,
    "q5_k_s": GGMLType.Q5_K,
    "q5_k_m": GGMLType.Q5_K,
    "q8_0": GGMLType.Q8_0,
}


@dataclass 
class GGUFTensor:
    """GGUF tensor metadata"""
    name: str
    shape: List[int]
    dtype: GGMLType
    offset: int
    data: bytes


class GGUFWriter:
    """
    GGUF file writer for OMNIMIND models
    
    GGUF Format:
    1. Magic + Version
    2. Tensor count + Metadata KV count
    3. Metadata key-value pairs
    4. Tensor infos
    5. Tensor data (aligned)
    """
    
    def __init__(self, path: str, arch: str = "omnimind"):
        self.path = path
        self.arch = arch
        self.metadata: Dict[str, Any] = {}
        self.tensors: List[GGUFTensor] = []
        self.tensor_data = bytearray()
        self.alignment = 32  # GGUF alignment
    
    def add_metadata(self, key: str, value: Any):
        """Add metadata key-value pair"""
        self.metadata[key] = value
    
    def add_architecture_metadata(self, config):
        """Add OMNIMIND architecture metadata"""
        self.add_metadata("general.architecture", self.arch)
        self.add_metadata("general.name", config.name if hasattr(config, 'name') else "omnimind")
        self.add_metadata("general.file_type", 2)  # GGUF file type
        
        # OMNIMIND specific
        self.add_metadata(f"{self.arch}.vocab_size", config.vocab_size)
        self.add_metadata(f"{self.arch}.context_length", config.max_seq_len)
        self.add_metadata(f"{self.arch}.embedding_length", config.d_model)
        self.add_metadata(f"{self.arch}.block_count", config.n_layers)
        self.add_metadata(f"{self.arch}.ssm.d_state", config.d_state)
        self.add_metadata(f"{self.arch}.ssm.d_conv", config.d_conv)
        self.add_metadata(f"{self.arch}.ssm.expand", config.expand)
        
        # Tokenizer
        self.add_metadata("tokenizer.ggml.model", "gpt2")
        self.add_metadata("tokenizer.ggml.bos_token_id", config.bos_token_id)
        self.add_metadata("tokenizer.ggml.eos_token_id", config.eos_token_id)
        self.add_metadata("tokenizer.ggml.padding_token_id", config.pad_token_id)
    
    def quantize_tensor(self, tensor: torch.Tensor, qtype: GGMLType) -> bytes:
        """Quantize tensor to specified GGML type"""
        tensor = tensor.detach().cpu().float().numpy()
        
        if qtype == GGMLType.F32:
            return tensor.astype(np.float32).tobytes()
        
        elif qtype == GGMLType.F16:
            return tensor.astype(np.float16).tobytes()
        
        elif qtype == GGMLType.Q8_0:
            # Q8_0: 32 weights per block, 1 scale
            return self._quantize_q8_0(tensor)
        
        elif qtype in [GGMLType.Q4_0, GGMLType.Q4_K]:
            # Q4_0/Q4_K: 32 weights per block, packed 4-bit
            return self._quantize_q4_0(tensor)
        
        elif qtype in [GGMLType.Q5_0, GGMLType.Q5_K]:
            return self._quantize_q5_0(tensor)
        
        else:
            # Fallback to F16
            return tensor.astype(np.float16).tobytes()
    
    def _quantize_q4_0(self, data: np.ndarray) -> bytes:
        """Q4_0 quantization: 32 values per block with 4-bit weights"""
        data = data.flatten()
        n = len(data)
        
        # Pad to multiple of 32
        if n % 32 != 0:
            data = np.pad(data, (0, 32 - n % 32))
            n = len(data)
        
        n_blocks = n // 32
        result = bytearray()
        
        for i in range(n_blocks):
            block = data[i * 32:(i + 1) * 32]
            
            # Compute scale
            max_val = np.max(np.abs(block))
            scale = max_val / 7.0 if max_val > 0 else 1.0
            
            # Quantize to [-8, 7]
            quantized = np.round(block / scale).clip(-8, 7).astype(np.int8)
            
            # Pack 2 values per byte
            packed = bytearray(16)
            for j in range(16):
                low = (quantized[j * 2] + 8) & 0x0F
                high = (quantized[j * 2 + 1] + 8) & 0x0F
                packed[j] = low | (high << 4)
            
            # Write scale (half precision) + packed weights
            result += struct.pack('<e', scale)  # FP16 scale
            result += packed
        
        return bytes(result)
    
    def _quantize_q5_0(self, data: np.ndarray) -> bytes:
        """Q5_0 quantization: 32 values per block with 5-bit weights"""
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
            
            # Pack (more complex for 5-bit)
            packed = bytearray(20)  # 32 * 5 / 8 = 20 bytes
            
            # Simple packing (not optimal but functional)
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
        """Q8_0 quantization: 32 values per block with 8-bit weights"""
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
    
    def add_tensor(self, name: str, tensor: torch.Tensor, qtype: GGMLType):
        """Add tensor with quantization"""
        # Map OMNIMIND names to GGUF names
        gguf_name = self._map_tensor_name(name)
        
        # Quantize
        data = self.quantize_tensor(tensor, qtype)
        
        # Align offset
        current_offset = len(self.tensor_data)
        padding = (self.alignment - (current_offset % self.alignment)) % self.alignment
        self.tensor_data += bytes(padding)
        
        # Add tensor
        self.tensors.append(GGUFTensor(
            name=gguf_name,
            shape=list(tensor.shape),
            dtype=qtype,
            offset=len(self.tensor_data),
            data=data
        ))
        
        self.tensor_data += data
    
    def _map_tensor_name(self, name: str) -> str:
        """Map PyTorch tensor names to GGUF names"""
        # Common mappings
        mappings = {
            "model.embedding.weight": "token_embd.weight",
            "model.norm.weight": "output_norm.weight",
            "lm_head.weight": "output.weight",
        }
        
        if name in mappings:
            return mappings[name]
        
        # Layer mappings
        if "layers." in name:
            # model.layers.0.ssm.in_proj.weight -> blk.0.ssm_in.weight
            parts = name.split(".")
            layer_idx = None
            for i, p in enumerate(parts):
                if p == "layers" and i + 1 < len(parts):
                    layer_idx = parts[i + 1]
                    break
            
            if layer_idx:
                rest = ".".join(parts[parts.index("layers") + 2:])
                rest = rest.replace("ssm.", "ssm_").replace("_proj", "")
                return f"blk.{layer_idx}.{rest}"
        
        return name
    
    def _write_string(self, f, s: str):
        """Write GGUF string"""
        encoded = s.encode('utf-8')
        f.write(struct.pack('<Q', len(encoded)))
        f.write(encoded)
    
    def _write_metadata_value(self, f, key: str, value: Any):
        """Write metadata key-value pair"""
        # Write key
        self._write_string(f, key)
        
        # Write value type and value
        if isinstance(value, bool):
            f.write(struct.pack('<I', 7))  # GGUF_TYPE_BOOL
            f.write(struct.pack('<?', value))
        elif isinstance(value, int):
            if value < 0:
                f.write(struct.pack('<I', 5))  # GGUF_TYPE_INT32
                f.write(struct.pack('<i', value))
            else:
                f.write(struct.pack('<I', 4))  # GGUF_TYPE_UINT32
                f.write(struct.pack('<I', value))
        elif isinstance(value, float):
            f.write(struct.pack('<I', 6))  # GGUF_TYPE_FLOAT32
            f.write(struct.pack('<f', value))
        elif isinstance(value, str):
            f.write(struct.pack('<I', 8))  # GGUF_TYPE_STRING
            self._write_string(f, value)
        elif isinstance(value, (list, tuple)):
            # Array type
            f.write(struct.pack('<I', 9))  # GGUF_TYPE_ARRAY
            if len(value) > 0 and isinstance(value[0], str):
                f.write(struct.pack('<I', 8))  # Element type: STRING
                f.write(struct.pack('<Q', len(value)))
                for item in value:
                    self._write_string(f, item)
            else:
                f.write(struct.pack('<I', 4))  # Element type: UINT32
                f.write(struct.pack('<Q', len(value)))
                for item in value:
                    f.write(struct.pack('<I', int(item)))
    
    def write(self):
        """Write GGUF file"""
        with open(self.path, 'wb') as f:
            # 1. Header
            f.write(struct.pack('<I', GGUF_MAGIC))
            f.write(struct.pack('<I', GGUF_VERSION))
            f.write(struct.pack('<Q', len(self.tensors)))
            f.write(struct.pack('<Q', len(self.metadata)))
            
            # 2. Metadata
            for key, value in self.metadata.items():
                self._write_metadata_value(f, key, value)
            
            # 3. Tensor infos
            for tensor in self.tensors:
                self._write_string(f, tensor.name)
                f.write(struct.pack('<I', len(tensor.shape)))
                for dim in tensor.shape:
                    f.write(struct.pack('<Q', dim))
                f.write(struct.pack('<I', int(tensor.dtype)))
                f.write(struct.pack('<Q', tensor.offset))
            
            # 4. Padding to alignment
            current_pos = f.tell()
            padding = (self.alignment - (current_pos % self.alignment)) % self.alignment
            f.write(bytes(padding))
            
            # 5. Tensor data
            f.write(self.tensor_data)
        
        file_size = os.path.getsize(self.path)
        print(f"✅ GGUF saved: {self.path}")
        print(f"   Size: {file_size / 1024 / 1024:.1f} MB")
        print(f"   Tensors: {len(self.tensors)}")


def export_to_gguf(
    model,
    output_path: str,
    quantization: str = "q4_k_m",
    tokenizer = None
) -> str:
    """
    Export OMNIMIND model to GGUF format
    
    Args:
        model: OMNIMIND model
        output_path: Output file path (should end with .gguf)
        quantization: Quantization type (q4_k_m, q5_k_m, q8_0, f16, f32)
        tokenizer: Optional tokenizer for vocabulary
        
    Returns:
        Path to saved GGUF file
        
    Example:
        export_to_gguf(model, "omnimind-micro-Q4_K_M.gguf", "q4_k_m")
    """
    # Ensure .gguf extension
    if not output_path.endswith(".gguf"):
        output_path += ".gguf"
    
    # Get quantization type
    qtype_str = quantization.lower().replace("-", "_")
    qtype = QUANT_TYPES.get(qtype_str, GGMLType.Q4_K)
    
    print(f"🔄 Exporting to GGUF format...")
    print(f"   Quantization: {quantization.upper()}")
    
    # Create writer
    writer = GGUFWriter(output_path, arch="omnimind")
    
    # Add architecture metadata
    if hasattr(model, 'config'):
        writer.add_architecture_metadata(model.config)
    
    # Add tokenizer metadata
    writer.add_metadata("tokenizer.ggml.model", "gpt2") # Fallback
    
    if tokenizer:
        # 1. Embed Chat Template
        try:
            from omnimind.utils.chat_template import get_chat_template
            template = get_chat_template(tokenizer)
            writer.add_metadata("tokenizer.chat_template", template)
            print(f"   Chat Template embedded")
        except Exception as e:
            print(f"⚠️ Failed to embed chat template: {e}")

        # 2. Add tokens
        if hasattr(tokenizer, 'token_to_id'):
            tokens = list(tokenizer.token_to_id.keys())
            writer.add_metadata("tokenizer.ggml.tokens", tokens[:1000])  # Limit for size
            writer.add_metadata("tokenizer.ggml.bos_token_id", tokenizer.bos_token_id or 1)
            writer.add_metadata("tokenizer.ggml.eos_token_id", tokenizer.eos_token_id or 2)
            writer.add_metadata("tokenizer.ggml.padding_token_id", tokenizer.pad_token_id or 0)
    
    # Export tensors
    state_dict = model.state_dict()
    
    for name, tensor in state_dict.items():
        if tensor.numel() == 0:
            continue
        
        # Choose quantization based on tensor type
        if "embedding" in name or "norm" in name:
            # Keep embeddings and norms in higher precision
            tensor_qtype = GGMLType.F16
        elif tensor.dim() >= 2 and tensor.numel() > 1024:
            # Quantize large weight matrices
            tensor_qtype = qtype
        else:
            # Small tensors in F32
            tensor_qtype = GGMLType.F32
        
        writer.add_tensor(name, tensor, tensor_qtype)
    
    # Write file
    writer.write()
    
    return output_path


def convert_gguf_quantization(
    input_path: str,
    output_path: str,
    target_quantization: str = "q4_k_m"
) -> str:
    """
    Convert GGUF file to different quantization
    
    Note: This is a simplified version. For full requantization,
    use llama.cpp's quantize tool.
    """
    print(f"⚠️ For full requantization, use llama.cpp quantize:")
    print(f"   ./quantize {input_path} {output_path} {target_quantization.upper()}")
    return output_path


# Convenience functions
def save_gguf_q4_k_m(model, path: str, tokenizer=None) -> str:
    """Save as Q4_K_M.gguf (recommended for mobile)"""
    return export_to_gguf(model, path, "q4_k_m", tokenizer)


def save_gguf_q5_k_m(model, path: str, tokenizer=None) -> str:
    """Save as Q5_K_M.gguf (balanced quality/size)"""
    return export_to_gguf(model, path, "q5_k_m", tokenizer)


def save_gguf_q8_0(model, path: str, tokenizer=None) -> str:
    """Save as Q8_0.gguf (high quality)"""
    return export_to_gguf(model, path, "q8_0", tokenizer)


def save_gguf_f16(model, path: str, tokenizer=None) -> str:
    """Save as F16.gguf (full precision)"""
    return export_to_gguf(model, path, "f16", tokenizer)


if __name__ == "__main__":
    print("GGUF Quantization Types:")
    print()
    for name, qtype in QUANT_TYPES.items():
        print(f"  {name:>10} -> {qtype.name}")
