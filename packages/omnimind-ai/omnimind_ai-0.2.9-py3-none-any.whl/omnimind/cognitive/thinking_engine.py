"""
OMNIMIND Cognitive Layer - Thinking Engine
เครื่องยนต์การคิด - 6 ขั้นตอน
"""
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re

from .uncertainty_detector import UncertaintyDetector, UncertaintyScore, ConfidenceLevel
from .anti_repetition import AntiRepetition


class ResponseStrategy(Enum):
    """Response strategies"""
    DIRECT_ANSWER = "direct"          # ตอบตรงๆ
    ASK_CLARIFICATION = "clarify"     # ถามกลับ
    ADMIT_UNCERTAINTY = "uncertain"   # บอกว่าไม่แน่ใจ
    DECLINE = "decline"               # ปฏิเสธตอบ
    REQUEST_INFO = "request_info"     # ขอข้อมูลเพิ่ม


@dataclass
class Intent:
    """Extracted intent from user input"""
    primary: str  # Main intent
    secondary: List[str] = field(default_factory=list)
    confidence: float = 0.8


@dataclass
class ThinkingResult:
    """Result of thinking process"""
    # Understanding
    intent: Intent
    entities: Dict[str, str]
    
    # Reasoning
    context_used: str
    uncertainty: UncertaintyScore
    
    # Decision
    strategy: ResponseStrategy
    response_prefix: str
    
    # Generation hints
    repetition_penalty: float
    suggested_topics: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent.primary,
            "strategy": self.strategy.value,
            "uncertainty": self.uncertainty.overall_score,
            "confidence_level": self.uncertainty.confidence_level.value,
        }


class ThinkingEngine:
    """
    Thinking Engine - เครื่องยนต์การคิด
    
    6 ขั้นตอน:
    1. Understand - เข้าใจ input
    2. Retrieve - ดึงข้อมูลจาก memory
    3. Reason - วิเคราะห์
    4. Evaluate Uncertainty - ประเมินความไม่แน่ใจ
    5. Decide - ตัดสินใจ strategy
    6. Generate - สร้างคำตอบ
    """
    
    def __init__(self, 
                 uncertainty_detector: UncertaintyDetector = None,
                 anti_repetition: AntiRepetition = None):
        self.uncertainty = uncertainty_detector or UncertaintyDetector()
        self.anti_repetition = anti_repetition or AntiRepetition()
        
        # Intent keywords mapping
        self.intent_keywords = {
            "question": ["อะไร", "ทำไม", "อย่างไร", "ยังไง", "เมื่อไหร่", "ที่ไหน", "ใคร", "?", "ไหม", "หรือ"],
            "command": ["ช่วย", "ทำ", "สร้าง", "หา", "ค้น", "แปล", "เขียน", "อธิบาย"],
            "greeting": ["สวัสดี", "หวัดดี", "ดี", "hello", "hi"],
            "thanks": ["ขอบคุณ", "ขอบใจ", "thanks", "thank"],
            "feedback": ["ดี", "เยี่ยม", "แย่", "ผิด", "ถูก"],
            "clarification": ["หมายความ", "คือ", "แปลว่า"],
        }
    
    def think(self, 
              user_input: str,
              memory_context: str = "",
              knowledge_results: List[Tuple[Any, float]] = None) -> ThinkingResult:
        """
        Main thinking process
        
        Args:
            user_input: User's input text
            memory_context: Context from memory layer
            knowledge_results: Knowledge search results
            
        Returns:
            ThinkingResult with all analysis
        """
        # Step 1: Understand
        intent = self._understand(user_input)
        entities = self._extract_entities(user_input)
        
        # Step 2: Retrieve (already done by memory layer, we just use it)
        context = memory_context
        
        # Step 3: Reason
        # Combine understanding with context
        
        # Step 4: Evaluate Uncertainty
        uncertainty_score = self.uncertainty.evaluate(
            query=user_input,
            memory_results=[(context, 0.8)] if context else None,
            knowledge_results=knowledge_results,
            context_available=bool(context)
        )
        
        # Step 5: Decide
        strategy = self._decide_strategy(intent, uncertainty_score)
        response_prefix = self._get_response_prefix(strategy, uncertainty_score)
        
        # Step 6: Prepare for generation
        rep_score = self.anti_repetition.check_repetition(user_input)
        
        return ThinkingResult(
            intent=intent,
            entities=entities,
            context_used=context,
            uncertainty=uncertainty_score,
            strategy=strategy,
            response_prefix=response_prefix,
            repetition_penalty=rep_score.penalty_factor,
            suggested_topics=self._suggest_topics(intent, entities),
        )
    
    def _understand(self, text: str) -> Intent:
        """Step 1: Understand - Extract intent from text"""
        text_lower = text.lower()
        
        # Score each intent category
        intent_scores = {}
        for intent_type, keywords in self.intent_keywords.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                intent_scores[intent_type] = score
        
        # Determine primary intent
        if intent_scores:
            primary = max(intent_scores.keys(), key=lambda k: intent_scores[k])
            secondary = [k for k in intent_scores.keys() if k != primary]
            confidence = min(intent_scores[primary] / 3, 1.0)
        else:
            primary = "general"
            secondary = []
            confidence = 0.5
        
        return Intent(primary=primary, secondary=secondary, confidence=confidence)
    
    def _extract_entities(self, text: str) -> Dict[str, str]:
        """Extract named entities from text"""
        entities = {}
        
        # Simple pattern matching for Thai
        # Numbers
        numbers = re.findall(r'\d+', text)
        if numbers:
            entities["numbers"] = numbers
        
        # Code-related
        code_patterns = re.findall(r'`[^`]+`|```[\s\S]*?```', text)
        if code_patterns:
            entities["code"] = code_patterns
        
        # References (this, that, etc.)
        if any(word in text for word in ["นี้", "นั้น", "มัน"]):
            entities["has_reference"] = "true"
        
        return entities
    
    def _decide_strategy(self, intent: Intent, uncertainty: UncertaintyScore) -> ResponseStrategy:
        """Step 5: Decide response strategy"""
        
        # If very uncertain, admit it
        if uncertainty.confidence_level == ConfidenceLevel.VERY_LOW:
            return ResponseStrategy.ADMIT_UNCERTAINTY
        
        # If need clarification
        if uncertainty.should_clarify:
            return ResponseStrategy.ASK_CLARIFICATION
        
        # If greeting or thanks, respond directly
        if intent.primary in ["greeting", "thanks"]:
            return ResponseStrategy.DIRECT_ANSWER
        
        # If confident enough, answer directly
        if uncertainty.should_answer:
            if uncertainty.should_admit_uncertainty:
                return ResponseStrategy.ADMIT_UNCERTAINTY
            return ResponseStrategy.DIRECT_ANSWER
        
        # Default: request more info
        return ResponseStrategy.REQUEST_INFO
    
    def _get_response_prefix(self, strategy: ResponseStrategy, 
                            uncertainty: UncertaintyScore) -> str:
        """Get appropriate response prefix"""
        if strategy == ResponseStrategy.DIRECT_ANSWER:
            return ""
        
        elif strategy == ResponseStrategy.ASK_CLARIFICATION:
            return "เพื่อให้ตอบได้ตรงจุดกว่านี้ "
        
        elif strategy == ResponseStrategy.ADMIT_UNCERTAINTY:
            if uncertainty.uncertainty_phrases:
                import random
                return random.choice(uncertainty.uncertainty_phrases) + " "
            return "ผมไม่แน่ใจนัก แต่ "
        
        elif strategy == ResponseStrategy.DECLINE:
            return "ขอโทษครับ ผมไม่สามารถตอบคำถามนี้ได้ "
        
        elif strategy == ResponseStrategy.REQUEST_INFO:
            return "ช่วยให้รายละเอียดเพิ่มเติมได้ไหมครับ? "
        
        return ""
    
    def _suggest_topics(self, intent: Intent, entities: Dict[str, str]) -> List[str]:
        """Suggest related topics to explore"""
        topics = []
        
        if intent.primary == "question":
            topics.append("รายละเอียดเพิ่มเติม")
            topics.append("ตัวอย่าง")
        
        if "code" in entities:
            topics.append("การอธิบาย code")
            topics.append("การปรับปรุง code")
        
        return topics
    
    def record_output(self, output: str):
        """Record output for anti-repetition tracking"""
        self.anti_repetition.add_output(output)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics"""
        return {
            "anti_repetition": self.anti_repetition.get_stats(),
        }
    
    def reset(self):
        """Reset engine state"""
        self.anti_repetition.reset()
