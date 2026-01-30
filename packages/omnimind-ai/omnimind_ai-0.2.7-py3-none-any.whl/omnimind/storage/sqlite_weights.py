"""
OMNIMIND SQLite-based Weight Storage
FTS5-level performance for model weight streaming

Key Features:
- B-tree indexed access O(log n) - same as SQLite FTS5
- Built-in LRU page cache
- Optional zstd compression
- Cross-platform (iOS/Android/Desktop)
- Supports training checkpoints AND inference streaming

Performance Target:
- Layer access: 1-10ms (vs 50-200ms with sequential file)
- Random access: O(log n) via B-tree index
- Memory-mapped I/O when available

Usage:
    # For Training - save checkpoints
    storage = SQLiteWeightStorage("model.db")
    storage.save_model(model, epoch=5)
    
    # For Inference - stream weights
    storage = SQLiteWeightStorage("model.db", read_only=True)
    weight = storage.get_layer_weight("layers.0.in_proj")
    
    # For Conversion - export from Transformer
    storage.import_from_state_dict(converted_weights)
"""

import sqlite3
import torch
import numpy as np
import io
import json
import threading
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple, Any, Iterator, Union
from contextlib import contextmanager
from collections import OrderedDict

# Optional zstd compression
try:
    import zstd
    HAS_ZSTD = True
except ImportError:
    try:
        import zstandard as zstd
        HAS_ZSTD = True
    except ImportError:
        HAS_ZSTD = False


# Schema version for migrations
SCHEMA_VERSION = 2

# Max blob size for SQLite (500MB to be safe, SQLite limit is ~1GB)
MAX_BLOB_SIZE = 500 * 1024 * 1024  # 500MB

# SQL Schema - optimized for FTS5-like performance
SCHEMA = """
-- Model metadata
CREATE TABLE IF NOT EXISTS model_info (
    key TEXT PRIMARY KEY,
    value TEXT
);

-- Layer weights with B-tree index (FTS5-like access pattern)
CREATE TABLE IF NOT EXISTS weights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    layer_name TEXT UNIQUE NOT NULL,
    tensor_shape TEXT NOT NULL,
    tensor_dtype TEXT NOT NULL,
    compression TEXT DEFAULT 'none',
    data BLOB NOT NULL,
    checksum TEXT,
    created_at REAL DEFAULT (julianday('now')),
    updated_at REAL DEFAULT (julianday('now'))
);

-- B-tree index for fast layer lookup (critical for FTS5-level speed)
CREATE INDEX IF NOT EXISTS idx_weights_layer_name ON weights(layer_name);

-- Chunks for large tensors (>500MB) that exceed SQLite blob limit
CREATE TABLE IF NOT EXISTS weight_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    layer_name TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    total_chunks INTEGER NOT NULL,
    tensor_shape TEXT NOT NULL,
    tensor_dtype TEXT NOT NULL,
    compression TEXT DEFAULT 'none',
    data BLOB NOT NULL,
    created_at REAL DEFAULT (julianday('now')),
    UNIQUE(layer_name, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_chunks_layer_name ON weight_chunks(layer_name);

-- Training checkpoints
CREATE TABLE IF NOT EXISTS checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    epoch INTEGER NOT NULL,
    step INTEGER DEFAULT 0,
    loss REAL,
    metrics TEXT,
    created_at REAL DEFAULT (julianday('now'))
);

-- Checkpoint-weight association (for versioning)
CREATE TABLE IF NOT EXISTS checkpoint_weights (
    checkpoint_id INTEGER,
    weight_id INTEGER,
    FOREIGN KEY (checkpoint_id) REFERENCES checkpoints(id),
    FOREIGN KEY (weight_id) REFERENCES weights(id),
    PRIMARY KEY (checkpoint_id, weight_id)
);

-- Conversion history
CREATE TABLE IF NOT EXISTS conversion_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_model TEXT,
    conversion_config TEXT,
    quality_scores TEXT,
    created_at REAL DEFAULT (julianday('now'))
);
"""


@dataclass
class WeightStorageConfig:
    """Configuration for SQLite weight storage"""
    # Compression
    compression: str = "zstd"  # none, zstd, lz4
    compression_level: int = 3  # 1-22 for zstd
    
    # Cache settings (LRU like SQLite page cache)
    cache_size_mb: int = 256  # In-memory cache size
    max_cached_layers: int = 8  # Max layers in cache
    
    # I/O settings
    use_mmap: bool = True  # Memory-mapped I/O
    page_size: int = 4096  # SQLite page size
    wal_mode: bool = True  # Write-Ahead Logging for concurrent access
    
    # Checkpointing
    auto_checkpoint: bool = True
    checkpoint_interval: int = 1000  # Steps between auto-checkpoints


class LRUWeightCache:
    """LRU cache for weight tensors - mimics SQLite's page cache"""
    
    def __init__(self, max_size_mb: int = 256, max_items: int = 8):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_items = max_items
        self.cache: OrderedDict[str, torch.Tensor] = OrderedDict()
        self.current_size = 0
        self.lock = threading.RLock()
        
        # Stats
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[torch.Tensor]:
        with self.lock:
            if key in self.cache:
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                self.hits += 1
                return self.cache[key]
            self.misses += 1
            return None
    
    def put(self, key: str, tensor: torch.Tensor):
        with self.lock:
            tensor_size = tensor.numel() * tensor.element_size()
            
            # Remove if already exists
            if key in self.cache:
                old_size = self.cache[key].numel() * self.cache[key].element_size()
                self.current_size -= old_size
                del self.cache[key]
            
            # Evict old entries if needed
            while (self.current_size + tensor_size > self.max_size_bytes or 
                   len(self.cache) >= self.max_items) and self.cache:
                oldest_key, oldest_tensor = self.cache.popitem(last=False)
                self.current_size -= oldest_tensor.numel() * oldest_tensor.element_size()
            
            # Add new entry
            self.cache[key] = tensor
            self.current_size += tensor_size
    
    def clear(self):
        with self.lock:
            self.cache.clear()
            self.current_size = 0
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


class SQLiteWeightStorage:
    """
    SQLite-based weight storage with FTS5-level performance
    
    Provides:
    - O(log n) layer access via B-tree index
    - LRU caching like SQLite page cache
    - Compression for storage efficiency
    - Training checkpoint support
    - Conversion history tracking
    """
    
    def __init__(
        self, 
        db_path: str,
        config: Optional[WeightStorageConfig] = None,
        read_only: bool = False
    ):
        self.db_path = Path(db_path)
        self.config = config or WeightStorageConfig()
        self.read_only = read_only
        
        # Ensure parent directory exists
        if not read_only:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize connection
        self._init_connection()
        
        # Initialize LRU cache
        self.cache = LRUWeightCache(
            max_size_mb=self.config.cache_size_mb,
            max_items=self.config.max_cached_layers
        )
        
        # Thread-local connections for concurrent access
        self._local = threading.local()
    
    def _init_connection(self):
        """Initialize SQLite connection with optimizations"""
        uri = f"file:{self.db_path}"
        if self.read_only:
            uri += "?mode=ro"
        
        self.conn = sqlite3.connect(
            uri if self.read_only else str(self.db_path),
            uri=self.read_only,
            check_same_thread=False,
            isolation_level=None  # Autocommit for reads
        )
        
        # Optimize for performance (FTS5-like settings)
        cursor = self.conn.cursor()
        
        # Enable WAL mode for concurrent reads
        if self.config.wal_mode and not self.read_only:
            cursor.execute("PRAGMA journal_mode=WAL")
        
        # Set page size
        cursor.execute(f"PRAGMA page_size={self.config.page_size}")
        
        # Enable memory-mapped I/O
        if self.config.use_mmap:
            cursor.execute("PRAGMA mmap_size=268435456")  # 256MB mmap
        
        # Cache size (negative = KB)
        cache_kb = self.config.cache_size_mb * 1024
        cursor.execute(f"PRAGMA cache_size=-{cache_kb}")
        
        # Synchronous mode (normal for balance of speed/safety)
        cursor.execute("PRAGMA synchronous=NORMAL")
        
        # Temp store in memory
        cursor.execute("PRAGMA temp_store=MEMORY")
        
        # Initialize schema
        if not self.read_only:
            cursor.executescript(SCHEMA)
            self._set_metadata("schema_version", str(SCHEMA_VERSION))
        
        cursor.close()
    
    @contextmanager
    def _get_cursor(self):
        """Get thread-safe cursor"""
        cursor = self.conn.cursor()
        try:
            yield cursor
        finally:
            cursor.close()
    
    def _compress(self, data: bytes) -> Tuple[bytes, str]:
        """Compress data if enabled"""
        if self.config.compression == "zstd" and HAS_ZSTD:
            compressed = zstd.compress(data, self.config.compression_level)
            return compressed, "zstd"
        return data, "none"
    
    def _decompress(self, data: bytes, compression: str) -> bytes:
        """Decompress data"""
        if compression == "zstd" and HAS_ZSTD:
            return zstd.decompress(data)
        return data
    
    # Dtypes that NumPy doesn't support natively
    _SPECIAL_DTYPES = {
        torch.bfloat16,
        torch.float8_e4m3fn,
        torch.float8_e4m3fnuz,
        torch.float8_e5m2,
        torch.float8_e5m2fnuz,
    }
    
    def _tensor_to_bytes(self, tensor: torch.Tensor) -> bytes:
        """
        Convert tensor to bytes.
        
        Handles special dtypes (BFloat16, Float8) that NumPy doesn't support
        by converting to Float32 first. The original dtype is preserved in
        the database and restored on load.
        """
        buffer = io.BytesIO()
        
        # Check if dtype is not supported by NumPy
        tensor_cpu = tensor.detach().cpu()
        
        if tensor_cpu.dtype in self._SPECIAL_DTYPES:
            # Convert to float32 for NumPy compatibility
            # Original dtype is stored in the database and restored on load
            tensor_cpu = tensor_cpu.to(torch.float32)
        
        # Use numpy for efficient serialization
        try:
            np_array = tensor_cpu.numpy()
        except TypeError as e:
            # Fallback: try converting to float32 if still failing
            np_array = tensor_cpu.to(torch.float32).numpy()
        
        np.save(buffer, np_array, allow_pickle=False)
        return buffer.getvalue()
    
    def _bytes_to_tensor(
        self, 
        data: bytes, 
        shape: List[int], 
        dtype: str,
        device: str = "cpu"
    ) -> torch.Tensor:
        """
        Convert bytes to tensor.
        
        Restores the original dtype that was stored in the database,
        including special dtypes like BFloat16 and Float8.
        """
        buffer = io.BytesIO(data)
        np_array = np.load(buffer, allow_pickle=False)
        tensor = torch.from_numpy(np_array)
        
        # Restore original dtype if it was a special type
        # dtype string format: "torch.bfloat16", "torch.float8_e4m3fn", etc.
        try:
            # Parse dtype string to get actual torch dtype
            if dtype.startswith("torch."):
                dtype_name = dtype.replace("torch.", "")
                if hasattr(torch, dtype_name):
                    target_dtype = getattr(torch, dtype_name)
                    tensor = tensor.to(target_dtype)
        except Exception:
            # If conversion fails, keep as loaded dtype
            pass
        
        return tensor.to(device)
    
    def _set_metadata(self, key: str, value: str):
        """Set model metadata"""
        with self._get_cursor() as cursor:
            cursor.execute(
                "INSERT OR REPLACE INTO model_info (key, value) VALUES (?, ?)",
                (key, value)
            )
            self.conn.commit()
    
    def _get_metadata(self, key: str) -> Optional[str]:
        """Get model metadata"""
        with self._get_cursor() as cursor:
            cursor.execute("SELECT value FROM model_info WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else None
    
    # ==================== Core Weight Operations ====================
    
    def save_weight(
        self, 
        layer_name: str, 
        tensor: torch.Tensor,
        checksum: Optional[str] = None
    ) -> int:
        """
        Save a single weight tensor
        
        Returns weight_id for checkpoint association.
        Automatically chunks large tensors (>500MB) to avoid SQLite blob limit.
        """
        if self.read_only:
            raise RuntimeError("Storage is read-only")
        
        # Serialize tensor
        data = self._tensor_to_bytes(tensor)
        compressed_data, compression = self._compress(data)
        
        shape = json.dumps(list(tensor.shape))
        dtype = str(tensor.dtype)
        
        # Check if we need to chunk (blob > MAX_BLOB_SIZE)
        if len(compressed_data) > MAX_BLOB_SIZE:
            return self._save_weight_chunked(
                layer_name, tensor, compressed_data, 
                compression, shape, dtype, checksum
            )
        
        with self._get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO weights (layer_name, tensor_shape, tensor_dtype, compression, data, checksum, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, julianday('now'))
                ON CONFLICT(layer_name) DO UPDATE SET
                    tensor_shape = excluded.tensor_shape,
                    tensor_dtype = excluded.tensor_dtype,
                    compression = excluded.compression,
                    data = excluded.data,
                    checksum = excluded.checksum,
                    updated_at = julianday('now')
            """, (layer_name, shape, dtype, compression, compressed_data, checksum))
            self.conn.commit()
            
            # Get the weight_id
            cursor.execute("SELECT id FROM weights WHERE layer_name = ?", (layer_name,))
            weight_id = cursor.fetchone()[0]
        
        # Update cache
        self.cache.put(layer_name, tensor)
        
        return weight_id
    
    def _save_weight_chunked(
        self,
        layer_name: str,
        tensor: torch.Tensor,
        compressed_data: bytes,
        compression: str,
        shape: str,
        dtype: str,
        checksum: Optional[str]
    ) -> int:
        """
        Save a large tensor by chunking it into multiple rows.
        Used when tensor exceeds MAX_BLOB_SIZE (500MB).
        """
        # Calculate number of chunks needed
        total_size = len(compressed_data)
        num_chunks = (total_size + MAX_BLOB_SIZE - 1) // MAX_BLOB_SIZE
        
        with self._get_cursor() as cursor:
            # First, delete any existing chunks for this layer
            cursor.execute("DELETE FROM weight_chunks WHERE layer_name = ?", (layer_name,))
            
            # Also remove from main weights table if exists (to avoid confusion)
            cursor.execute("DELETE FROM weights WHERE layer_name = ?", (layer_name,))
            
            # Save chunks
            for i in range(num_chunks):
                start = i * MAX_BLOB_SIZE
                end = min(start + MAX_BLOB_SIZE, total_size)
                chunk_data = compressed_data[start:end]
                
                cursor.execute("""
                    INSERT INTO weight_chunks 
                    (layer_name, chunk_index, total_chunks, tensor_shape, tensor_dtype, compression, data)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (layer_name, i, num_chunks, shape, dtype, compression, chunk_data))
            
            self.conn.commit()
        
        # Update cache
        self.cache.put(layer_name, tensor)
        
        # Return -1 to indicate chunked storage (no single weight_id)
        return -1
    
    def get_weight(
        self, 
        layer_name: str, 
        device: str = "cpu"
    ) -> Optional[torch.Tensor]:
        """
        Get a weight tensor by layer name
        
        Uses B-tree index for O(log n) access - FTS5 level!
        Automatically handles chunked tensors (large weights >500MB).
        """
        # Check cache first (O(1))
        cached = self.cache.get(layer_name)
        if cached is not None:
            return cached.to(device) if device != "cpu" else cached
        
        # Query main weights table (O(log n) with B-tree index)
        with self._get_cursor() as cursor:
            cursor.execute("""
                SELECT tensor_shape, tensor_dtype, compression, data 
                FROM weights 
                WHERE layer_name = ?
            """, (layer_name,))
            row = cursor.fetchone()
        
        if row is not None:
            # Found in main table (non-chunked)
            shape = json.loads(row[0])
            dtype = row[1]
            compression = row[2]
            compressed_data = row[3]
            
            # Decompress and convert
            data = self._decompress(compressed_data, compression)
            tensor = self._bytes_to_tensor(data, shape, dtype, device)
            
            # Cache for future access
            self.cache.put(layer_name, tensor.cpu() if device != "cpu" else tensor)
            
            return tensor
        
        # Check chunked table for large tensors
        return self._get_weight_chunked(layer_name, device)
    
    def _get_weight_chunked(
        self,
        layer_name: str,
        device: str = "cpu"
    ) -> Optional[torch.Tensor]:
        """
        Get a chunked weight tensor by reassembling chunks.
        Used for large tensors that were split due to SQLite blob limit.
        """
        with self._get_cursor() as cursor:
            cursor.execute("""
                SELECT chunk_index, total_chunks, tensor_shape, tensor_dtype, compression, data
                FROM weight_chunks
                WHERE layer_name = ?
                ORDER BY chunk_index
            """, (layer_name,))
            rows = cursor.fetchall()
        
        if not rows:
            return None
        
        # Reassemble chunks
        total_chunks = rows[0][1]
        shape = json.loads(rows[0][2])
        dtype = rows[0][3]
        compression = rows[0][4]
        
        # Verify we have all chunks
        if len(rows) != total_chunks:
            raise RuntimeError(
                f"Missing chunks for {layer_name}: found {len(rows)}/{total_chunks}"
            )
        
        # Concatenate all chunk data
        compressed_data = b''.join(row[5] for row in rows)
        
        # Decompress and convert
        data = self._decompress(compressed_data, compression)
        tensor = self._bytes_to_tensor(data, shape, dtype, device)
        
        # Cache for future access
        self.cache.put(layer_name, tensor.cpu() if device != "cpu" else tensor)
        
        return tensor
    
    def get_layer_names(self) -> List[str]:
        """Get all layer names (for iteration), including chunked layers"""
        with self._get_cursor() as cursor:
            # Get from main weights table
            cursor.execute("SELECT layer_name FROM weights ORDER BY id")
            names = [row[0] for row in cursor.fetchall()]
            
            # Also get unique layer names from chunks table
            cursor.execute("SELECT DISTINCT layer_name FROM weight_chunks ORDER BY layer_name")
            chunked_names = [row[0] for row in cursor.fetchall()]
            
            # Combine (chunked names not in main table)
            all_names = names + [n for n in chunked_names if n not in names]
            return all_names
    
    def layer_exists(self, layer_name: str) -> bool:
        """Check if layer exists (fast index lookup), including chunked layers"""
        with self._get_cursor() as cursor:
            # Check main table
            cursor.execute(
                "SELECT 1 FROM weights WHERE layer_name = ? LIMIT 1", 
                (layer_name,)
            )
            if cursor.fetchone() is not None:
                return True
            
            # Check chunks table
            cursor.execute(
                "SELECT 1 FROM weight_chunks WHERE layer_name = ? LIMIT 1",
                (layer_name,)
            )
            return cursor.fetchone() is not None
    
    # ==================== Model Operations ====================
    
    def save_model(
        self, 
        model: torch.nn.Module,
        model_config: Optional[Dict] = None,
        epoch: Optional[int] = None,
        step: int = 0,
        loss: Optional[float] = None,
        metrics: Optional[Dict] = None
    ) -> Optional[int]:
        """
        Save entire model with optional checkpoint
        
        Returns checkpoint_id if epoch specified
        """
        if self.read_only:
            raise RuntimeError("Storage is read-only")
        
        # Save model config
        if model_config:
            self._set_metadata("model_config", json.dumps(model_config))
        
        # Save all weights
        weight_ids = []
        state_dict = model.state_dict()
        
        print(f"💾 Saving {len(state_dict)} weight tensors...")
        start_time = time.time()
        
        for name, tensor in state_dict.items():
            weight_id = self.save_weight(name, tensor)
            weight_ids.append(weight_id)
        
        elapsed = time.time() - start_time
        print(f"✅ Saved in {elapsed:.2f}s")
        
        # Create checkpoint if epoch specified
        checkpoint_id = None
        if epoch is not None:
            checkpoint_id = self._create_checkpoint(
                epoch, step, loss, metrics, weight_ids
            )
        
        return checkpoint_id
    
    def load_model(
        self, 
        model: torch.nn.Module,
        device: str = "cpu",
        strict: bool = True
    ) -> Dict[str, Any]:
        """
        Load weights into model
        
        Returns load statistics
        """
        state_dict = model.state_dict()
        loaded = 0
        skipped = 0
        missing = []
        
        print(f"📂 Loading weights into model...")
        start_time = time.time()
        
        for name in state_dict.keys():
            tensor = self.get_weight(name, device)
            if tensor is not None:
                if tensor.shape == state_dict[name].shape:
                    state_dict[name].copy_(tensor)
                    loaded += 1
                else:
                    skipped += 1
                    missing.append(f"{name}: shape mismatch")
            else:
                skipped += 1
                missing.append(name)
        
        if strict and missing:
            raise RuntimeError(f"Missing weights: {missing[:5]}...")
        
        model.load_state_dict(state_dict, strict=False)
        
        elapsed = time.time() - start_time
        print(f"✅ Loaded {loaded}/{loaded+skipped} weights in {elapsed:.2f}s")
        print(f"📊 Cache hit rate: {self.cache.hit_rate:.1%}")
        
        return {
            "loaded": loaded,
            "skipped": skipped,
            "missing": missing,
            "elapsed_seconds": elapsed,
            "cache_hit_rate": self.cache.hit_rate
        }
    
    def import_from_state_dict(
        self, 
        state_dict: Dict[str, torch.Tensor],
        model_config: Optional[Dict] = None,
        source_info: Optional[str] = None
    ):
        """
        Import weights from a state dict (for conversion)
        
        Used after Transformer -> SSM conversion
        """
        if self.read_only:
            raise RuntimeError("Storage is read-only")
        
        if model_config:
            self._set_metadata("model_config", json.dumps(model_config))
        
        if source_info:
            self._set_metadata("source_model", source_info)
        
        print(f"📥 Importing {len(state_dict)} tensors...")
        start_time = time.time()
        
        for name, tensor in state_dict.items():
            self.save_weight(name, tensor)
        
        elapsed = time.time() - start_time
        total_size = sum(t.numel() * t.element_size() for t in state_dict.values())
        
        print(f"✅ Imported {total_size / 1024 / 1024:.1f} MB in {elapsed:.2f}s")
    
    # ==================== Checkpoint Operations ====================
    
    def _create_checkpoint(
        self,
        epoch: int,
        step: int,
        loss: Optional[float],
        metrics: Optional[Dict],
        weight_ids: List[int]
    ) -> int:
        """Create a training checkpoint"""
        metrics_json = json.dumps(metrics) if metrics else None
        
        with self._get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO checkpoints (epoch, step, loss, metrics)
                VALUES (?, ?, ?, ?)
            """, (epoch, step, loss, metrics_json))
            
            checkpoint_id = cursor.lastrowid
            
            # Associate weights with checkpoint
            for weight_id in weight_ids:
                cursor.execute("""
                    INSERT INTO checkpoint_weights (checkpoint_id, weight_id)
                    VALUES (?, ?)
                """, (checkpoint_id, weight_id))
            
            self.conn.commit()
        
        print(f"📌 Created checkpoint {checkpoint_id} (epoch={epoch}, step={step})")
        return checkpoint_id
    
    def list_checkpoints(self) -> List[Dict]:
        """List all checkpoints"""
        with self._get_cursor() as cursor:
            cursor.execute("""
                SELECT id, epoch, step, loss, metrics, created_at
                FROM checkpoints
                ORDER BY created_at DESC
            """)
            
            checkpoints = []
            for row in cursor.fetchall():
                checkpoints.append({
                    "id": row[0],
                    "epoch": row[1],
                    "step": row[2],
                    "loss": row[3],
                    "metrics": json.loads(row[4]) if row[4] else None,
                    "created_at": row[5]
                })
            
            return checkpoints
    
    def get_best_checkpoint(self, metric: str = "loss", minimize: bool = True) -> Optional[Dict]:
        """Get best checkpoint by metric"""
        checkpoints = self.list_checkpoints()
        if not checkpoints:
            return None
        
        def get_metric(cp):
            if metric == "loss":
                return cp.get("loss") or float('inf')
            return cp.get("metrics", {}).get(metric, float('inf') if minimize else float('-inf'))
        
        return min(checkpoints, key=get_metric) if minimize else max(checkpoints, key=get_metric)
    
    # ==================== Conversion Tracking ====================
    
    def log_conversion(
        self,
        source_model: str,
        config: Dict,
        quality_scores: Dict
    ):
        """Log a conversion operation"""
        with self._get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO conversion_log (source_model, conversion_config, quality_scores)
                VALUES (?, ?, ?)
            """, (source_model, json.dumps(config), json.dumps(quality_scores)))
            self.conn.commit()
    
    # ==================== Streaming Interface ====================
    
    def stream_layers(
        self, 
        device: str = "cpu",
        prefetch: int = 2
    ) -> Iterator[Tuple[str, torch.Tensor]]:
        """
        Stream layers one by one (for inference with minimal memory)
        
        Yields (layer_name, tensor) pairs
        """
        layer_names = self.get_layer_names()
        
        # Prefetch first N layers
        prefetch_queue = []
        
        for i, name in enumerate(layer_names):
            # Start prefetch for upcoming layers
            if i + prefetch < len(layer_names):
                # This would be async in production
                pass
            
            tensor = self.get_weight(name, device)
            if tensor is not None:
                yield name, tensor
    
    # ==================== Utilities ====================
    
    def get_storage_stats(self) -> Dict:
        """Get storage statistics"""
        with self._get_cursor() as cursor:
            # Total weights
            cursor.execute("SELECT COUNT(*), SUM(LENGTH(data)) FROM weights")
            count, total_bytes = cursor.fetchone()
            
            # Compression ratio
            cursor.execute("""
                SELECT compression, COUNT(*), SUM(LENGTH(data))
                FROM weights 
                GROUP BY compression
            """)
            compression_stats = {row[0]: {"count": row[1], "bytes": row[2]} 
                                for row in cursor.fetchall()}
        
        return {
            "total_weights": count or 0,
            "total_bytes": total_bytes or 0,
            "total_mb": (total_bytes or 0) / 1024 / 1024,
            "compression_stats": compression_stats,
            "cache_hit_rate": self.cache.hit_rate,
            "cache_size_mb": self.cache.current_size / 1024 / 1024
        }
    
    def vacuum(self):
        """Optimize database (reclaim space)"""
        if not self.read_only:
            self.conn.execute("VACUUM")
            print("🧹 Database vacuumed")
    
    def close(self):
        """Close connection"""
        self.cache.clear()
        self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# ==================== Integration Helpers ====================

def create_weight_storage(
    path: str,
    compression: str = "zstd",
    cache_size_mb: int = 256
) -> SQLiteWeightStorage:
    """Create a new weight storage"""
    config = WeightStorageConfig(
        compression=compression,
        cache_size_mb=cache_size_mb
    )
    return SQLiteWeightStorage(path, config)


def open_weight_storage(path: str, cache_size_mb: int = 256) -> SQLiteWeightStorage:
    """Open existing weight storage for reading"""
    config = WeightStorageConfig(cache_size_mb=cache_size_mb)
    return SQLiteWeightStorage(path, config, read_only=True)
