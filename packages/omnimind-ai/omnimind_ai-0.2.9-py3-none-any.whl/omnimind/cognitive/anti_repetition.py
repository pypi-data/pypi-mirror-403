"""
OMNIMIND Cognitive Layer - Anti-Repetition Module
ระบบป้องกันการตอบซ้ำ
"""
from typing import List, Dict, Any, Set, Tuple
from dataclasses import dataclass, field
from collections import Counter
import re


@dataclass
class RepetitionScore:
    """Repetition analysis result"""
    has_repetition: bool
    repetition_score: float  # 0-1, ยิ่งสูงยิ่งซ้ำ
    repeated_phrases: List[str]
    penalty_factor: float  # Factor to apply to logits
    suggestion: str


class AntiRepetition:
    """
    Anti-Repetition Module - ป้องกันการตอบซ้ำ
    
    ทำหน้าที่:
    - Track recent outputs
    - Detect repeated patterns (n-grams)
    - Calculate repetition penalty
    - Encourage diversity
    """
    
    def __init__(self, 
                 ngram_size: int = 3,
                 max_recent_outputs: int = 20,
                 base_penalty: float = 1.2):
        self.ngram_size = ngram_size
        self.max_recent_outputs = max_recent_outputs
        self.base_penalty = base_penalty
        
        # Track recent outputs
        self.recent_outputs: List[str] = []
        self.recent_ngrams: Set[tuple] = set()
        
        # Track phrase frequencies
        self.phrase_counter: Counter = Counter()
    
    def add_output(self, text: str):
        """
        Add new output to tracking
        
        Args:
            text: Generated output text
        """
        self.recent_outputs.append(text)
        
        # Keep only recent outputs
        if len(self.recent_outputs) > self.max_recent_outputs:
            old_text = self.recent_outputs.pop(0)
            # Remove old ngrams
            old_ngrams = self._extract_ngrams(old_text)
            self.recent_ngrams -= old_ngrams
        
        # Add new ngrams
        new_ngrams = self._extract_ngrams(text)
        self.recent_ngrams.update(new_ngrams)
        
        # Update phrase frequencies
        phrases = self._extract_phrases(text)
        self.phrase_counter.update(phrases)
    
    def check_repetition(self, text: str) -> RepetitionScore:
        """
        Check if text contains repetition
        
        Args:
            text: Text to check (usually before outputting)
            
        Returns:
            RepetitionScore with analysis
        """
        # Extract n-grams from text
        text_ngrams = self._extract_ngrams(text)
        
        # Find overlapping ngrams with recent outputs
        overlap = text_ngrams & self.recent_ngrams
        
        # Calculate repetition score
        if not text_ngrams:
            return RepetitionScore(
                has_repetition=False,
                repetition_score=0.0,
                repeated_phrases=[],
                penalty_factor=1.0,
                suggestion=""
            )
        
        repetition_score = len(overlap) / len(text_ngrams)
        
        # Get repeated phrases
        repeated = [" ".join(ngram) for ngram in list(overlap)[:5]]
        
        # Check for internal repetition (loops)
        internal_rep = self._check_internal_repetition(text)
        if internal_rep > 0:
            repetition_score = max(repetition_score, internal_rep)
        
        # Calculate penalty
        if repetition_score > 0.5:
            penalty = self.base_penalty * (1 + repetition_score)
        elif repetition_score > 0.3:
            penalty = self.base_penalty
        else:
            penalty = 1.0
        
        # Generate suggestion
        suggestion = ""
        if repetition_score > 0.5:
            suggestion = "ควรเปลี่ยนคำหรือโครงสร้างประโยค"
        elif repetition_score > 0.3:
            suggestion = "มีการซ้ำบ้าง แต่ยังยอมรับได้"
        
        return RepetitionScore(
            has_repetition=repetition_score > 0.3,
            repetition_score=repetition_score,
            repeated_phrases=repeated,
            penalty_factor=penalty,
            suggestion=suggestion
        )
    
    def get_penalty_tokens(self, recent_tokens: List[int] = None) -> Dict[int, float]:
        """
        Get token penalties for generation
        
        Args:
            recent_tokens: Recently generated token IDs
            
        Returns:
            Dict mapping token_id to penalty multiplier
        """
        penalties = {}
        
        if recent_tokens:
            # Apply increasing penalty for more frequent tokens
            token_counts = Counter(recent_tokens)
            for token_id, count in token_counts.items():
                if count > 2:
                    penalties[token_id] = self.base_penalty ** count
        
        return penalties
    
    def _extract_ngrams(self, text: str) -> Set[tuple]:
        """Extract n-grams from text"""
        # Tokenize (simple word-based)
        words = self._tokenize(text)
        
        if len(words) < self.ngram_size:
            return set()
        
        ngrams = set()
        for i in range(len(words) - self.ngram_size + 1):
            ngram = tuple(words[i:i + self.ngram_size])
            ngrams.add(ngram)
        
        return ngrams
    
    def _extract_phrases(self, text: str) -> List[str]:
        """Extract meaningful phrases from text"""
        # Split into sentences/clauses
        phrases = re.split(r'[。.!?！？\n]', text)
        return [p.strip() for p in phrases if len(p.strip()) > 10]
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization (word-based)"""
        # Remove special characters
        text = re.sub(r'[^\w\s]', '', text.lower())
        # Split on whitespace for English, character-level might be better for Thai
        words = text.split()
        return words
    
    def _check_internal_repetition(self, text: str) -> float:
        """Check for internal repetition (loops) within text"""
        words = self._tokenize(text)
        
        if len(words) < 10:
            return 0.0
        
        # Check for repeated sequences
        for pattern_len in range(3, min(len(words) // 2, 10)):
            for start in range(len(words) - pattern_len * 2):
                pattern = words[start:start + pattern_len]
                
                # Count how many times this pattern appears
                count = 0
                for i in range(start, len(words) - pattern_len + 1, pattern_len):
                    if words[i:i + pattern_len] == pattern:
                        count += 1
                
                if count >= 3:
                    # Found a loop
                    return 0.8
                elif count >= 2:
                    return 0.4
        
        return 0.0
    
    def suggest_alternatives(self, phrase: str) -> List[str]:
        """
        Suggest alternative phrasings (placeholder)
        
        In real implementation, this could use a thesaurus or LLM
        """
        # Simple word substitutions for Thai
        substitutions = {
            "ใช่": ["ถูกต้อง", "ครับ", "ค่ะ"],
            "ไม่ใช่": ["ไม่ถูกต้อง", "ไม่ครับ", "ไม่ค่ะ"],
            "ดี": ["ยอดเยี่ยม", "วิเศษ", "เยี่ยม"],
            "มาก": ["อย่างมาก", "มากเลย", "สุดๆ"],
        }
        
        alternatives = []
        for word, subs in substitutions.items():
            if word in phrase:
                for sub in subs:
                    alternatives.append(phrase.replace(word, sub))
        
        return alternatives[:3]  # Return top 3
    
    def reset(self):
        """Reset all tracking"""
        self.recent_outputs = []
        self.recent_ngrams = set()
        self.phrase_counter = Counter()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get module statistics"""
        return {
            "tracked_outputs": len(self.recent_outputs),
            "unique_ngrams": len(self.recent_ngrams),
            "top_phrases": self.phrase_counter.most_common(5),
        }
