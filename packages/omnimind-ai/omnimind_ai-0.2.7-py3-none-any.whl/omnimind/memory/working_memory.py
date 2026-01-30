"""
OMNIMIND Memory Layer - Working Memory
ความจำระยะสั้น (Level 1)
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class MemorySlot:
    """Single slot in working memory"""
    content: str
    role: str  # 'user' or 'assistant'
    timestamp: datetime = field(default_factory=datetime.now)
    token_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "token_count": self.token_count,
            "metadata": self.metadata,
        }


class WorkingMemory:
    """
    Working Memory - ความจำใช้งานปัจจุบัน
    
    คุณสมบัติ:
    - เก็บบทสนทนาปัจจุบัน
    - ขนาดคงที่ (~1-2K tokens)
    - อยู่ใน memory (in-memory)
    - เมื่อเต็ม → compress แล้วส่งไป Episodic Memory
    """
    
    def __init__(self, max_tokens: int = 2000, max_slots: int = 10):
        self.max_tokens = max_tokens
        self.max_slots = max_slots
        self.slots: List[MemorySlot] = []
        self.total_tokens = 0
        self._state_summary: Optional[str] = None
    
    def add(self, content: str, role: str, token_count: int = 0, metadata: Dict[str, Any] = None) -> Optional[List[MemorySlot]]:
        """
        Add new content to working memory
        
        Args:
            content: Text content
            role: 'user' or 'assistant'
            token_count: Number of tokens (estimate if not provided)
            metadata: Additional metadata
            
        Returns:
            List of evicted slots if memory was full, None otherwise
        """
        if token_count == 0:
            # Rough estimate: ~4 chars per token for Thai
            token_count = len(content) // 3
        
        slot = MemorySlot(
            content=content,
            role=role,
            token_count=token_count,
            metadata=metadata or {}
        )
        
        evicted = []
        
        # Check if we need to evict old slots
        while (self.total_tokens + token_count > self.max_tokens or 
               len(self.slots) >= self.max_slots) and self.slots:
            old_slot = self.slots.pop(0)
            self.total_tokens -= old_slot.token_count
            evicted.append(old_slot)
        
        # Add new slot
        self.slots.append(slot)
        self.total_tokens += token_count
        
        return evicted if evicted else None
    
    def get_context(self, max_tokens: Optional[int] = None) -> str:
        """
        Get conversation context as formatted string
        
        Args:
            max_tokens: Limit tokens (uses all if None)
            
        Returns:
            Formatted conversation context
        """
        context_parts = []
        token_count = 0
        
        # Include state summary if exists
        if self._state_summary:
            context_parts.append(f"[บริบทก่อนหน้า: {self._state_summary}]")
        
        # Add slots from oldest to newest
        for slot in self.slots:
            if max_tokens and token_count + slot.token_count > max_tokens:
                break
            
            role_name = "User" if slot.role == "user" else "Assistant"
            context_parts.append(f"{role_name}: {slot.content}")
            token_count += slot.token_count
        
        return "\n".join(context_parts)
    
    def get_messages(self) -> List[Dict[str, str]]:
        """Get messages in chat format"""
        return [{"role": s.role, "content": s.content} for s in self.slots]
    
    def set_state_summary(self, summary: str):
        """Set compressed state summary from previous context"""
        self._state_summary = summary
    
    def get_last_n(self, n: int) -> List[MemorySlot]:
        """Get last N slots"""
        return self.slots[-n:] if n <= len(self.slots) else self.slots.copy()
    
    def clear(self):
        """Clear all working memory"""
        self.slots = []
        self.total_tokens = 0
        self._state_summary = None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        return {
            "slots_used": len(self.slots),
            "max_slots": self.max_slots,
            "tokens_used": self.total_tokens,
            "max_tokens": self.max_tokens,
            "has_summary": self._state_summary is not None,
        }
    
    def compress_to_summary(self) -> str:
        """
        Create a summary of current working memory
        (To be called before clearing and moving to episodic)
        
        Returns:
            Summary text
        """
        if not self.slots:
            return ""
        
        # Simple summary: list key topics discussed
        topics = []
        for slot in self.slots:
            if slot.role == "user":
                # Extract first sentence or first 50 chars
                text = slot.content[:100].split('.')[0]
                if text:
                    topics.append(text)
        
        summary = f"สนทนาเกี่ยวกับ: {'; '.join(topics[-3:])}"  # Last 3 topics
        return summary
