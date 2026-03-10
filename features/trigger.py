"""
Smart Trigger Mechanism
Lightweight NLP-based automatic type detection for memory entries
"""

import jieba
import jieba.posseg as pseg
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


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
            TriggerType.DECISION: [
                "决定", "选择", "采用", "实施", "确定", "选定", "敲定",
                "拍板", "定下", "选定", "确定", "选择"
            ],
            TriggerType.MILESTONE: [
                "完成", "实现", "达成", "上线", "发布", "交付", "验收",
                "结束", "收尾", "完工", "竣工"
            ],
            TriggerType.IMPORTANT: [
                "重要", "关键", "核心", "注意", "记住", "务必", "必须",
                "紧急", "优先", "重点"
            ],
            TriggerType.ARCHIVE: [
                "总结", "归档", "结束", "记录一下", "保存", "存档",
                "整理", "归纳", "汇总", "记录"
            ]
        }
        
        self.negations = [
            "不", "没", "无", "非", "未", "别", "莫", "勿",
            "不要", "不用", "无需", "不必", "没有", "不是"
        ]
        
        self.intensifiers = {
            "enhance": ["非常", "特别", "极其", "相当", "十分", "格外"],
            "reduce": ["稍微", "略微", "有点", "有些", "比较", "还算"]
        }
        
        self._load_user_dict()
    
    def _load_user_dict(self):
        """Load user dictionary"""
        tech_words = [
            "微服务", "单体架构", "分布式", "容器化", "Kubernetes",
            "Docker", "CI/CD", "DevOps", "敏捷开发", "Scrum",
            "RESTful", "GraphQL", "gRPC", "WebSocket", "Redis",
            "PostgreSQL", "MongoDB", "Elasticsearch", "Kafka"
        ]
        
        for word in tech_words:
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
        ("决定使用 SQLite 作为存储引擎", True),
        ("完成了第一阶段开发", True),
        ("这个决策非常重要", True),
        ("记录一下今天的进度", True),
        ("这个决策不重要", False),
        ("不要记录这个", False),
        ("稍微有点想法", False),
        ("今天天气不错", False),
        ("我决定不采用这个方案", True),
        ("这个方案非常重要，必须记录", True),
    ]
    
    print("\n【Test Results】")
    for text, expected in test_cases:
        result = trigger.analyze(text)
        status = "✓" if result.triggered == expected else "✗"
        
        print(f"\n{status} Text: {text}")
        print(f"  Expected: {expected}, Actual: {result.triggered}")
        print(f"  Type: {result.trigger_type.value}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Keywords: {result.keywords}")
    
    print("\n" + "=" * 60)
    print("✓ Test Complete")
    print("=" * 60)
