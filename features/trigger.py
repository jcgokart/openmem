"""
Smart Trigger Mechanism
Lightweight NLP-based automatic type detection for memory entries
"""

import jieba
import jieba.posseg as pseg
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from openmem.data.vocabularies import TRIGGER_KEYWORDS, NEGATIONS, INTENSIFIERS, TECH_WORDS


class TriggerType(Enum):
    """Trigger type enumeration"""
    DECISION = "decision"
    MILESTONE = "milestone"
    IMPORTANT = "important"
    ARCHIVE = "archive"
    NONE = "none"


@dataclass
class TriggerResult:
    """Trigger result"""
    triggered: bool
    trigger_type: TriggerType
    confidence: float
    keywords: List[str]
    reason: str
    context: Optional[str] = None


class SmartTrigger:
    """Smart Trigger using NLP"""
    
    def __init__(self):
        self.key_verbs = {
            TriggerType.DECISION: TRIGGER_KEYWORDS["decision"]["zh"] + TRIGGER_KEYWORDS["decision"]["en"],
            TriggerType.MILESTONE: TRIGGER_KEYWORDS["milestone"]["zh"] + TRIGGER_KEYWORDS["milestone"]["en"],
            TriggerType.IMPORTANT: TRIGGER_KEYWORDS["important"]["zh"] + TRIGGER_KEYWORDS["important"]["en"],
            TriggerType.ARCHIVE: TRIGGER_KEYWORDS["archive"]["zh"] + TRIGGER_KEYWORDS["archive"]["en"],
        }
        
        self.negations = NEGATIONS
        
        self.intensifiers = {
            "enhance": INTENSIFIERS["enhance"]["zh"] + INTENSIFIERS["enhance"]["en"],
            "reduce": INTENSIFIERS["reduce"]["zh"] + INTENSIFIERS["reduce"]["en"],
        }
        
        self._load_user_dict()
    
    def _load_user_dict(self):
        """Load user dictionary"""
        for word in TECH_WORDS:
            jieba.add_word(word, tag='n')
    
    def analyze(self, text: str) -> TriggerResult:
        """Analyze text and determine trigger type"""
        words = list(pseg.cut(text))
        
        trigger_type, confidence, keywords = self._detect_trigger_type(words)
        
        has_negation, negation_word = self._detect_negation(words)
        
        intensifier = self._detect_intensifier(words)
        
        if has_negation:
            confidence *= 0.3
        
        if intensifier == "enhance":
            confidence *= 1.5
        elif intensifier == "reduce":
            confidence *= 0.7
        
        triggered = confidence >= 0.5 and not (has_negation and confidence < 0.7)
        
        reason = self._generate_reason(
            trigger_type, confidence, keywords, 
            has_negation, negation_word, intensifier
        )
        
        return TriggerResult(
            triggered=triggered,
            trigger_type=trigger_type if triggered else TriggerType.NONE,
            confidence=min(confidence, 1.0),
            keywords=keywords,
            reason=reason,
            context=text[:100] if len(text) > 100 else text
        )
    
    def _detect_trigger_type(self, words: List[Tuple[str, str]]) -> Tuple[TriggerType, float, List[str]]:
        """Detect trigger type from words"""
        best_type = TriggerType.NONE
        best_confidence = 0.0
        best_keywords = []
        
        for trigger_type, verbs in self.key_verbs.items():
            matched_keywords = []
            verb_count = 0
            
            for word, flag in words:
                if word in verbs:
                    matched_keywords.append(word)
                    
                    if flag == 'v':
                        verb_count += 1
                    else:
                        verb_count += 0.5
            
            if matched_keywords:
                confidence = min(0.5 + verb_count * 0.2, 1.0)
                
                if confidence > best_confidence:
                    best_type = trigger_type
                    best_confidence = confidence
                    best_keywords = matched_keywords
        
        return best_type, best_confidence, best_keywords
    
    def _detect_negation(self, words: List[Tuple[str, str]]) -> Tuple[bool, Optional[str]]:
        """Detect negation words"""
        for i, (word, flag) in enumerate(words):
            if word in self.negations:
                has_keyword_before = False
                has_keyword_after = False
                
                for j in range(max(0, i - 3), i):
                    w, f = words[j]
                    for trigger_type, verbs in self.key_verbs.items():
                        if w in verbs:
                            has_keyword_before = True
                            break
                
                for j in range(i + 1, min(len(words), i + 4)):
                    w, f = words[j]
                    for trigger_type, verbs in self.key_verbs.items():
                        if w in verbs:
                            has_keyword_after = True
                            break
                
                if has_keyword_before or has_keyword_after:
                    return True, word
        
        return False, None
    
    def _detect_intensifier(self, words: List[Tuple[str, str]]) -> Optional[str]:
        """Detect intensifiers"""
        for word, flag in words:
            if word in self.intensifiers["enhance"]:
                return "enhance"
            elif word in self.intensifiers["reduce"]:
                return "reduce"
        
        return None
    
    def _generate_reason(self, trigger_type: TriggerType, confidence: float,
                        keywords: List[str], has_negation: bool,
                        negation_word: Optional[str], intensifier: Optional[str]) -> str:
        """Generate trigger reason"""
        if not keywords:
            return "No trigger keywords detected"
        
        parts = []
        parts.append(f"Keywords: {', '.join(keywords)}")
        parts.append(f"Confidence: {confidence:.2f}")
        
        if has_negation:
            parts.append(f"Negation: {negation_word}")
        
        if intensifier:
            parts.append(f"Intensifier: {intensifier}")
        
        if trigger_type != TriggerType.NONE:
            parts.append(f"Type: {trigger_type.value}")
        
        return "; ".join(parts)
    
    def should_record(self, text: str) -> bool:
        """Check if text should be recorded"""
        result = self.analyze(text)
        return result.triggered


if __name__ == "__main__":
    print("=" * 60)
    print("Smart Trigger Test")
    print("=" * 60)
    
    trigger = SmartTrigger()
    
    test_cases = [
        ("Decided to use SQLite as storage engine", True),
        ("we decided to use PostgreSQL", True),
        ("Completed first phase development", True),
        ("completed first phase", True),
        ("This decision is very important", True),
        ("very important decision", True),
        ("Record today's progress", True),
        ("take a note", True),
        ("This decision is not important", False),
        ("not important", False),
        ("Don't record this", False),
        ("dont record this", False),
        ("Somewhat think", False),
        ("somewhat think", False),
        ("The weather is nice today", False),
        ("the weather is nice", False),
    ]
    
    print("\n[Test Results]")
    for text, expected in test_cases:
        result = trigger.analyze(text)
        status = "PASS" if result.triggered == expected else "FAIL"
        
        print(f"\n{status} Text: {text}")
        print(f"  Expected: {expected}, Actual: {result.triggered}")
        print(f"  Type: {result.trigger_type.value}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Keywords: {result.keywords}")
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)
