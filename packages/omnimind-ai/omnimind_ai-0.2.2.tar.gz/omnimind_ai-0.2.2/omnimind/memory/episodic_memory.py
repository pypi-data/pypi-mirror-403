"""
OMNIMIND Memory Layer - Episodic Memory
ความจำเหตุการณ์ (Level 2)
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import sqlite3
import json
import os


@dataclass
class Episode:
    """Single episode in episodic memory"""
    id: str
    timestamp: datetime
    summary: str
    key_points: List[str]
    embedding: Optional[List[float]] = None
    importance: float = 0.5
    access_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "summary": self.summary,
            "key_points": self.key_points,
            "embedding": self.embedding,
            "importance": self.importance,
            "access_count": self.access_count,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Episode":
        return cls(
            id=data["id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            summary=data["summary"],
            key_points=data.get("key_points", []),
            embedding=data.get("embedding"),
            importance=data.get("importance", 0.5),
            access_count=data.get("access_count", 0),
            metadata=data.get("metadata", {}),
        )


class EpisodicMemory:
    """
    Episodic Memory - ความจำเหตุการณ์
    
    คุณสมบัติ:
    - เก็บบทสนทนาที่สรุปแล้ว
    - ขนาด ~10,000-100,000 episodes
    - ใช้ SQLite สำหรับ persistence
    - มี decay mechanism (ลืมตามความสำคัญ)
    """
    
    def __init__(self, db_path: str = "data/episodic.db", max_episodes: int = 100000):
        self.db_path = db_path
        self.max_episodes = max_episodes
        self._episode_counter = 0
        
        # Ensure directory exists (skip for in-memory SQLite)
        if db_path != ":memory:" and os.path.dirname(db_path):
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS episodes (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                summary TEXT NOT NULL,
                key_points TEXT,
                embedding BLOB,
                importance REAL DEFAULT 0.5,
                access_count INTEGER DEFAULT 0,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_importance ON episodes(importance DESC)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON episodes(timestamp DESC)
        """)
        
        # Get episode counter
        cursor.execute("SELECT COUNT(*) FROM episodes")
        self._episode_counter = cursor.fetchone()[0]
        
        conn.commit()
        conn.close()
    
    def _generate_id(self) -> str:
        """Generate unique episode ID"""
        self._episode_counter += 1
        return f"ep_{self._episode_counter:06d}"
    
    def add(self, summary: str, key_points: List[str] = None, 
            embedding: List[float] = None, importance: float = 0.5,
            metadata: Dict[str, Any] = None) -> Episode:
        """
        Add new episode to memory
        
        Args:
            summary: Summary of the episode
            key_points: Key points from the conversation
            embedding: Vector embedding for semantic search
            importance: Importance score (0-1)
            metadata: Additional metadata
            
        Returns:
            Created Episode object
        """
        episode = Episode(
            id=self._generate_id(),
            timestamp=datetime.now(),
            summary=summary,
            key_points=key_points or [],
            embedding=embedding,
            importance=importance,
            metadata=metadata or {}
        )
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO episodes (id, timestamp, summary, key_points, embedding, importance, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            episode.id,
            episode.timestamp.isoformat(),
            episode.summary,
            json.dumps(episode.key_points),
            json.dumps(episode.embedding) if episode.embedding else None,
            episode.importance,
            json.dumps(episode.metadata)
        ))
        
        conn.commit()
        conn.close()
        
        # Prune if over limit
        if self._episode_counter > self.max_episodes:
            self._prune_old_episodes()
        
        return episode
    
    def get(self, episode_id: str) -> Optional[Episode]:
        """Get episode by ID and increment access count"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, summary, key_points, embedding, importance, access_count, metadata
            FROM episodes WHERE id = ?
        """, (episode_id,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
        
        # Increment access count
        cursor.execute("""
            UPDATE episodes SET access_count = access_count + 1 WHERE id = ?
        """, (episode_id,))
        conn.commit()
        conn.close()
        
        return Episode(
            id=row[0],
            timestamp=datetime.fromisoformat(row[1]),
            summary=row[2],
            key_points=json.loads(row[3]) if row[3] else [],
            embedding=json.loads(row[4]) if row[4] else None,
            importance=row[5],
            access_count=row[6] + 1,
            metadata=json.loads(row[7]) if row[7] else {}
        )
    
    def search_recent(self, limit: int = 10) -> List[Episode]:
        """Get most recent episodes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, summary, key_points, embedding, importance, access_count, metadata
            FROM episodes
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        episodes = []
        for row in cursor.fetchall():
            episodes.append(Episode(
                id=row[0],
                timestamp=datetime.fromisoformat(row[1]),
                summary=row[2],
                key_points=json.loads(row[3]) if row[3] else [],
                embedding=json.loads(row[4]) if row[4] else None,
                importance=row[5],
                access_count=row[6],
                metadata=json.loads(row[7]) if row[7] else {}
            ))
        
        conn.close()
        return episodes
    
    def search_by_importance(self, min_importance: float = 0.5, limit: int = 10) -> List[Episode]:
        """Get episodes above importance threshold"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, timestamp, summary, key_points, embedding, importance, access_count, metadata
            FROM episodes
            WHERE importance >= ?
            ORDER BY importance DESC, timestamp DESC
            LIMIT ?
        """, (min_importance, limit))
        
        episodes = []
        for row in cursor.fetchall():
            episodes.append(Episode(
                id=row[0],
                timestamp=datetime.fromisoformat(row[1]),
                summary=row[2],
                key_points=json.loads(row[3]) if row[3] else [],
                embedding=json.loads(row[4]) if row[4] else None,
                importance=row[5],
                access_count=row[6],
                metadata=json.loads(row[7]) if row[7] else {}
            ))
        
        conn.close()
        return episodes
    
    def update_importance(self, episode_id: str, new_importance: float):
        """Update importance score of an episode"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE episodes SET importance = ? WHERE id = ?
        """, (new_importance, episode_id))
        
        conn.commit()
        conn.close()
    
    def apply_decay(self, decay_rate: float = 0.01):
        """Apply decay to all episode importance scores"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE episodes SET importance = importance * (1 - ?)
            WHERE importance > 0.1
        """, (decay_rate,))
        
        conn.commit()
        conn.close()
    
    def _prune_old_episodes(self, keep_ratio: float = 0.9):
        """Remove low-importance episodes when over limit"""
        keep_count = int(self.max_episodes * keep_ratio)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Delete lowest importance episodes
        cursor.execute("""
            DELETE FROM episodes WHERE id IN (
                SELECT id FROM episodes
                ORDER BY importance ASC, access_count ASC
                LIMIT ?
            )
        """, (self._episode_counter - keep_count,))
        
        conn.commit()
        conn.close()
        
        self._episode_counter = keep_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*), AVG(importance), AVG(access_count) FROM episodes")
        count, avg_importance, avg_access = cursor.fetchone()
        
        conn.close()
        
        return {
            "total_episodes": count or 0,
            "max_episodes": self.max_episodes,
            "avg_importance": round(avg_importance, 3) if avg_importance else 0,
            "avg_access_count": round(avg_access, 1) if avg_access else 0,
        }
