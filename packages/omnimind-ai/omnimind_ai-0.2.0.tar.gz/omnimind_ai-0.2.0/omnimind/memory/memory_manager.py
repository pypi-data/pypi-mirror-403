"""
OMNIMIND Memory Layer - Memory Manager
จัดการ Memory ทั้ง 3 ระดับ
"""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from .working_memory import WorkingMemory, MemorySlot
from .episodic_memory import EpisodicMemory, Episode
from .semantic_memory import SemanticMemory, KnowledgeEntry


@dataclass
class MemoryContext:
    """Context retrieved from all memory levels"""
    working: str
    episodes: List[Episode]
    knowledge: List[Tuple[KnowledgeEntry, float]]
    
    def to_prompt(self) -> str:
        """Convert to prompt-friendly format"""
        parts = []
        
        # Working memory context
        if self.working:
            parts.append("### บริบทปัจจุบัน ###")
            parts.append(self.working)
        
        # Relevant episodes
        if self.episodes:
            parts.append("\n### ประวัติที่เกี่ยวข้อง ###")
            for ep in self.episodes[:3]:  # Top 3
                parts.append(f"- {ep.summary}")
        
        # Relevant knowledge
        if self.knowledge:
            parts.append("\n### ความรู้ที่เกี่ยวข้อง ###")
            for entry, score in self.knowledge[:3]:  # Top 3
                if score > 0.3:  # Only include relevant
                    parts.append(f"- {entry.content} (confidence: {entry.confidence:.0%})")
        
        return "\n".join(parts)


class MemoryManager:
    """
    Memory Manager - Unified memory operations
    
    จัดการ:
    - Working Memory (ระยะสั้น)
    - Episodic Memory (เหตุการณ์)
    - Semantic Memory (ความรู้)
    
    Operations:
    - Write: เพิ่มข้อมูลใหม่
    - Read: ดึงข้อมูลที่เกี่ยวข้อง
    - Compress: บีบอัดและย้าย working → episodic
    - Forget: ลบข้อมูลที่ไม่สำคัญ
    """
    
    def __init__(self, 
                 working_memory: WorkingMemory = None,
                 episodic_memory: EpisodicMemory = None,
                 semantic_memory: SemanticMemory = None):
        
        self.working = working_memory or WorkingMemory()
        self.episodic = episodic_memory or EpisodicMemory()
        self.semantic = semantic_memory or SemanticMemory()
    
    # ==================== WRITE OPERATIONS ====================
    
    def add_message(self, content: str, role: str, 
                   token_count: int = 0) -> Optional[Episode]:
        """
        Add a message to working memory
        Automatically compresses to episodic if working memory overflows
        
        Args:
            content: Message content
            role: 'user' or 'assistant'
            token_count: Number of tokens
            
        Returns:
            Episode if compression occurred, None otherwise
        """
        evicted = self.working.add(content, role, token_count)
        
        # If slots were evicted, compress them to episodic memory
        if evicted:
            return self._compress_to_episode(evicted)
        
        return None
    
    def add_knowledge(self, content: str, category: str = "general",
                     confidence: float = 0.8, source: str = "user") -> KnowledgeEntry:
        """
        Add knowledge to semantic memory
        
        Args:
            content: Knowledge content
            category: Category of knowledge
            confidence: Confidence score
            source: Source of knowledge
            
        Returns:
            Created KnowledgeEntry
        """
        return self.semantic.add(content, category, confidence, source)
    
    def _compress_to_episode(self, slots: List[MemorySlot]) -> Episode:
        """Compress working memory slots to an episode"""
        # Create summary
        user_messages = [s.content for s in slots if s.role == "user"]
        assistant_messages = [s.content for s in slots if s.role == "assistant"]
        
        summary_parts = []
        if user_messages:
            summary_parts.append(f"User ถาม: {user_messages[0][:100]}")
        if assistant_messages:
            summary_parts.append(f"AI ตอบ: {assistant_messages[0][:100]}")
        
        summary = " | ".join(summary_parts) if summary_parts else "บทสนทนา"
        
        # Extract key points
        key_points = []
        for slot in slots:
            if len(slot.content) > 20:
                key_points.append(slot.content[:50] + "...")
        
        # Calculate importance based on content length and variety
        importance = min(0.5 + (len(slots) * 0.1), 0.9)
        
        # Create episode
        return self.episodic.add(
            summary=summary,
            key_points=key_points[:5],  # Max 5 key points
            importance=importance,
            metadata={"slot_count": len(slots)}
        )
    
    # ==================== READ OPERATIONS ====================
    
    def retrieve(self, query: str, 
                include_working: bool = True,
                include_episodic: bool = True,
                include_semantic: bool = True,
                max_episodes: int = 5,
                max_knowledge: int = 5) -> MemoryContext:
        """
        Retrieve relevant context from all memory levels
        
        Args:
            query: Search query (usually current user input)
            include_working: Include working memory
            include_episodic: Search episodic memory
            include_semantic: Search semantic memory
            max_episodes: Max episodes to retrieve
            max_knowledge: Max knowledge entries to retrieve
            
        Returns:
            MemoryContext with all relevant information
        """
        # Working memory
        working_context = ""
        if include_working:
            working_context = self.working.get_context()
        
        # Episodic memory - recent and relevant
        episodes = []
        if include_episodic:
            # Get recent episodes
            episodes = self.episodic.search_recent(limit=max_episodes)
        
        # Semantic memory - search by query
        knowledge = []
        if include_semantic:
            knowledge = self.semantic.search(query, limit=max_knowledge)
        
        return MemoryContext(
            working=working_context,
            episodes=episodes,
            knowledge=knowledge
        )
    
    def get_working_context(self) -> str:
        """Get current working memory context"""
        return self.working.get_context()
    
    def get_recent_episodes(self, limit: int = 5) -> List[Episode]:
        """Get recent episodes"""
        return self.episodic.search_recent(limit=limit)
    
    def search_knowledge(self, query: str, limit: int = 5) -> List[Tuple[KnowledgeEntry, float]]:
        """Search semantic memory"""
        return self.semantic.search(query, limit=limit)
    
    # ==================== MAINTENANCE OPERATIONS ====================
    
    def reset_session(self):
        """Reset working memory for new session"""
        # Compress remaining working memory to episode
        if self.working.slots:
            self._compress_to_episode(self.working.slots)
        
        # Clear working memory
        self.working.clear()
    
    def apply_decay(self, decay_rate: float = 0.01):
        """Apply importance decay to episodic memory"""
        self.episodic.apply_decay(decay_rate)
    
    def update_knowledge_confidence(self, entry_id: str, feedback: str):
        """
        Update knowledge confidence based on feedback
        
        Args:
            entry_id: Knowledge entry ID
            feedback: 'positive', 'negative', or 'correction'
        """
        if feedback == "positive":
            current = 0.8  # Default, should fetch actual
            new_confidence = min(current + 0.1, 1.0)
        elif feedback == "negative":
            current = 0.8
            new_confidence = max(current - 0.2, 0.1)
        else:  # correction
            new_confidence = 0.3  # Mark as uncertain
        
        self.semantic.update_confidence(entry_id, new_confidence)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics from all memory levels"""
        return {
            "working_memory": self.working.get_stats(),
            "episodic_memory": self.episodic.get_stats(),
            "semantic_memory": self.semantic.get_stats(),
        }
