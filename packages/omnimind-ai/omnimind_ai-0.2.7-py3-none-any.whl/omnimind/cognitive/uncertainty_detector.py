"""
OMNIMIND Cognitive Layer - Uncertainty Detector
ระบบตรวจจับความไม่แน่ใจ
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ConfidenceLevel(Enum):
    """Confidence levels for responses"""
    HIGH = "high"           # ≥85% - ตอบได้เลย
    MEDIUM = "medium"       # 60-85% - ตอบได้แต่บอกว่าไม่แน่ใจ
    LOW = "low"             # 40-60% - ถามกลับหรือบอกว่าไม่รู้
    VERY_LOW = "very_low"   # <40% - ปฏิเสธตอบ


@dataclass
class UncertaintyScore:
    """Uncertainty analysis result"""
    overall_score: float  # 0-1, ยิ่งสูงยิ่งไม่แน่ใจ
    confidence_level: ConfidenceLevel
    
    # Component scores
    memory_confidence: float    # มีใน memory ไหม
    source_reliability: float   # แหล่งเชื่อถือได้ไหม
    consistency_score: float    # ขัดแย้งกับสิ่งที่รู้ไหม
    recency_score: float        # ข้อมูลเก่าแค่ไหน
    
    # Recommendations
    should_answer: bool
    should_clarify: bool
    should_admit_uncertainty: bool
    uncertainty_phrases: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "confidence_level": self.confidence_level.value,
            "memory_confidence": self.memory_confidence,
            "source_reliability": self.source_reliability,
            "consistency_score": self.consistency_score,
            "recency_score": self.recency_score,
            "should_answer": self.should_answer,
            "should_clarify": self.should_clarify,
            "should_admit_uncertainty": self.should_admit_uncertainty,
        }


class UncertaintyDetector:
    """
    Uncertainty Detector - ระบบรู้ว่าไม่รู้อะไร
    
    ประเมิน:
    - Memory confidence: มีข้อมูลใน memory ไหม
    - Source reliability: แหล่งข้อมูลเชื่อถือได้ไหม
    - Consistency: ขัดแย้งกับความรู้ที่มีไหม
    - Recency: ข้อมูลอัพเดทล่าสุดเมื่อไหร่
    """
    
    def __init__(self, 
                 uncertainty_threshold: float = 0.6,
                 high_confidence_threshold: float = 0.85):
        self.uncertainty_threshold = uncertainty_threshold
        self.high_confidence_threshold = high_confidence_threshold
        
        # Thai phrases for expressing uncertainty
        self.uncertainty_phrases = {
            ConfidenceLevel.HIGH: [],
            ConfidenceLevel.MEDIUM: [
                "ผมค่อนข้างมั่นใจว่า...",
                "จากความเข้าใจของผม...",
                "น่าจะเป็น...",
            ],
            ConfidenceLevel.LOW: [
                "ผมไม่แน่ใจนัก แต่...",
                "อาจจะเป็น...",
                "ผมไม่มีข้อมูลที่ชัดเจน...",
                "คุณช่วยให้รายละเอียดเพิ่มได้ไหม?",
            ],
            ConfidenceLevel.VERY_LOW: [
                "ผมไม่มีข้อมูลเกี่ยวกับเรื่องนี้",
                "ผมไม่สามารถตอบได้อย่างมั่นใจ",
                "ผมไม่รู้เรื่องนี้",
                "ขอโทษครับ ผมไม่มีความรู้ในเรื่องนี้",
            ],
        }
    
    def evaluate(self,
                 query: str,
                 memory_results: List[Tuple[Any, float]] = None,
                 knowledge_results: List[Tuple[Any, float]] = None,
                 context_available: bool = True) -> UncertaintyScore:
        """
        Evaluate uncertainty for a given query
        
        Args:
            query: User's question
            memory_results: Results from memory search (item, similarity)
            knowledge_results: Results from knowledge search (item, similarity)
            context_available: Is relevant context available
            
        Returns:
            UncertaintyScore with detailed analysis
        """
        # Calculate component scores
        memory_conf = self._eval_memory_confidence(memory_results)
        source_rel = self._eval_source_reliability(knowledge_results)
        consistency = self._eval_consistency(memory_results, knowledge_results)
        recency = self._eval_recency(memory_results, knowledge_results)
        
        # Calculate overall confidence (inverse of uncertainty)
        # Weighted average
        weights = [0.35, 0.25, 0.25, 0.15]
        overall_confidence = (
            memory_conf * weights[0] +
            source_rel * weights[1] +
            consistency * weights[2] +
            recency * weights[3]
        )
        
        # Boost confidence if we have good context
        if context_available and overall_confidence > 0.3:
            overall_confidence = min(overall_confidence + 0.1, 1.0)
        
        # Uncertainty is inverse of confidence
        overall_uncertainty = 1 - overall_confidence
        
        # Determine confidence level
        if overall_confidence >= self.high_confidence_threshold:
            level = ConfidenceLevel.HIGH
        elif overall_confidence >= self.uncertainty_threshold:
            level = ConfidenceLevel.MEDIUM
        elif overall_confidence >= 0.4:
            level = ConfidenceLevel.LOW
        else:
            level = ConfidenceLevel.VERY_LOW
        
        # Determine actions
        should_answer = level in [ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM]
        should_clarify = level == ConfidenceLevel.LOW
        should_admit = level in [ConfidenceLevel.LOW, ConfidenceLevel.VERY_LOW]
        
        return UncertaintyScore(
            overall_score=overall_uncertainty,
            confidence_level=level,
            memory_confidence=memory_conf,
            source_reliability=source_rel,
            consistency_score=consistency,
            recency_score=recency,
            should_answer=should_answer,
            should_clarify=should_clarify,
            should_admit_uncertainty=should_admit,
            uncertainty_phrases=self.uncertainty_phrases[level],
        )
    
    def _eval_memory_confidence(self, memory_results: List[Tuple[Any, float]] = None) -> float:
        """Evaluate confidence based on memory search results"""
        if not memory_results:
            return 0.3  # Low confidence if no memory
        
        # Best match similarity
        best_similarity = max(score for _, score in memory_results) if memory_results else 0
        
        # More results = higher confidence
        result_bonus = min(len(memory_results) * 0.05, 0.2)
        
        return min(best_similarity + result_bonus, 1.0)
    
    def _eval_source_reliability(self, knowledge_results: List[Tuple[Any, float]] = None) -> float:
        """Evaluate reliability of knowledge sources"""
        if not knowledge_results:
            return 0.5  # Neutral if no knowledge
        
        # Average confidence of knowledge entries
        confidences = []
        for entry, _ in knowledge_results:
            if hasattr(entry, 'confidence'):
                confidences.append(entry.confidence)
        
        if confidences:
            return sum(confidences) / len(confidences)
        return 0.5
    
    def _eval_consistency(self, 
                         memory_results: List[Tuple[Any, float]] = None,
                         knowledge_results: List[Tuple[Any, float]] = None) -> float:
        """Evaluate consistency between memory and knowledge"""
        # For now, assume consistent if both have results
        has_memory = memory_results and len(memory_results) > 0
        has_knowledge = knowledge_results and len(knowledge_results) > 0
        
        if has_memory and has_knowledge:
            return 0.9  # High consistency
        elif has_memory or has_knowledge:
            return 0.7  # Medium consistency
        else:
            return 0.5  # Unknown
    
    def _eval_recency(self,
                     memory_results: List[Tuple[Any, float]] = None,
                     knowledge_results: List[Tuple[Any, float]] = None) -> float:
        """Evaluate recency of information"""
        # Placeholder - would need timestamps in actual implementation
        if memory_results:
            return 0.8  # Memory is recent
        return 0.6  # Knowledge might be outdated
    
    def get_uncertainty_prefix(self, score: UncertaintyScore) -> str:
        """Get appropriate uncertainty prefix for response"""
        if not score.uncertainty_phrases:
            return ""
        
        import random
        return random.choice(score.uncertainty_phrases)
    
    def should_ask_clarification(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Check if query needs clarification
        
        Returns:
            (should_ask, clarification_question)
        """
        # Simple heuristics
        ambiguous_words = ["มัน", "นี่", "นั่น", "เขา", "เธอ", "อันนั้น"]
        
        query_lower = query.lower()
        
        for word in ambiguous_words:
            if word in query_lower and len(query.split()) < 5:
                return True, f"คุณหมายถึง'{word}' ว่าอะไรครับ?"
        
        # Too short query
        if len(query.split()) < 2:
            return True, "ช่วยขยายความหน่อยได้ไหมครับ?"
        
        return False, None
