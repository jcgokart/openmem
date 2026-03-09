"""
P2-1: 智能触发机制
使用轻量 NLP 模型实现智能触发

============================================================
工程经验总结
============================================================

1. 【否定词处理】语义理解要考虑否定
   - 问题："决定不重要" 被误判为重要
   - 解决：检测否定词前缀，降低置信度
   - 经验：语义理解要处理否定、修饰词

2. 【置信度阈值】要有明确判断边界
   - 问题：0.5 临界值无法决定
   - 解决：设置明确阈值（如 0.6 以上触发）
   - 经验：模糊判断要有明确阈值

3. 【程度副词】修饰词影响置信度
   - 问题："非常重要" 和 "有点重要" 置信度相同
   - 解决：检测程度副词（非常/稍微）调整置信度
   - 经验：自然语言要考虑程度差异

4. 【关键词组合】多关键词加权判断
   - 问题：单个关键词误判率高
   - 解决：组合关键词 + 权重计算
   - 经验：多特征融合比单特征可靠

特性：
- 词性标注（jieba）
- 关键动词检测
- 否定词检测
- 上下文理解
- 优先级判断
"""

import jieba
import jieba.posseg as pseg
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


# ==================== 触发类型枚举 ====================

class TriggerType(Enum):
    """触发类型"""
    DECISION = "decision"       # 决策
    MILESTONE = "milestone"     # 里程碑
    IMPORTANT = "important"     # 重要
    ARCHIVE = "archive"         # 归档
    NONE = "none"               # 无触发


# ==================== 触发结果 ====================

@dataclass
class TriggerResult:
    """触发结果"""
    triggered: bool                     # 是否触发
    trigger_type: TriggerType           # 触发类型
    confidence: float                   # 置信度
    keywords: List[str]                 # 关键词
    reason: str                         # 原因
    context: Optional[str] = None       # 上下文


# ==================== 智能触发器 ====================

class SmartTrigger:
    """智能触发器（使用 NLP）"""
    
    def __init__(self):
        # 关键动词（按类型分类）
        self.key_verbs = {
            TriggerType.DECISION: [
                "决定", "选择", "采用", "实施", "确定", "选定", "敲定",
                "拍板", "定下", "选定", "确定", "决定", "选择"
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
        
        # 否定词
        self.negations = [
            "不", "没", "无", "非", "未", "别", "莫", "勿",
            "不要", "不用", "无需", "不必", "没有", "不是"
        ]
        
        # 程度副词（增强或减弱）
        self.intensifiers = {
            "增强": ["非常", "特别", "极其", "相当", "十分", "格外"],
            "减弱": ["稍微", "略微", "有点", "有些", "比较", "还算"]
        }
        
        # 用户词典（可扩展）
        self._load_user_dict()
    
    def _load_user_dict(self):
        """加载用户词典"""
        # 添加技术词汇
        tech_words = [
            "微服务", "单体架构", "分布式", "容器化", "Kubernetes",
            "Docker", "CI/CD", "DevOps", "敏捷开发", "Scrum",
            "RESTful", "GraphQL", "gRPC", "WebSocket", "Redis",
            "PostgreSQL", "MongoDB", "Elasticsearch", "Kafka"
        ]
        
        for word in tech_words:
            jieba.add_word(word, tag='n')
    
    def analyze(self, text: str) -> TriggerResult:
        """
        分析文本，判断是否触发
        
        Args:
            text: 输入文本
        
        Returns:
            触发结果
        """
        # 1. 分词 + 词性标注
        words = list(pseg.cut(text))
        
        # 2. 检测触发类型
        trigger_type, confidence, keywords = self._detect_trigger_type(words)
        
        # 3. 检测否定词
        has_negation, negation_word = self._detect_negation(words)
        
        # 4. 检测程度副词
        intensifier = self._detect_intensifier(words)
        
        # 5. 调整置信度
        if has_negation:
            confidence *= 0.3  # 否定词降低置信度
        
        if intensifier == "增强":
            confidence *= 1.5  # 增强副词提高置信度
        elif intensifier == "减弱":
            confidence *= 0.7  # 减弱副词降低置信度
        
        # 6. 判断是否触发
        triggered = confidence >= 0.5 and not (has_negation and confidence < 0.7)
        
        # 7. 生成原因
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
        """
        检测触发类型
        
        Args:
            words: 分词结果 [(word, flag), ...]
        
        Returns:
            (触发类型, 置信度, 关键词列表)
        """
        best_type = TriggerType.NONE
        best_confidence = 0.0
        best_keywords = []
        
        for trigger_type, verbs in self.key_verbs.items():
            matched_keywords = []
            verb_count = 0
            
            for word, flag in words:
                # 检查是否匹配关键动词
                if word in verbs:
                    matched_keywords.append(word)
                    
                    # 如果是动词，增加权重
                    if flag == 'v':
                        verb_count += 1
                    else:
                        verb_count += 0.5
            
            if matched_keywords:
                # 计算置信度
                confidence = min(0.5 + verb_count * 0.2, 1.0)
                
                if confidence > best_confidence:
                    best_type = trigger_type
                    best_confidence = confidence
                    best_keywords = matched_keywords
        
        return best_type, best_confidence, best_keywords
    
    def _detect_negation(self, words: List[Tuple[str, str]]) -> Tuple[bool, Optional[str]]:
        """
        检测否定词（检查否定词是否影响关键词）
        
        Args:
            words: 分词结果
        
        Returns:
            (是否有否定词, 否定词)
        """
        # 检查每个否定词
        for i, (word, flag) in enumerate(words):
            if word in self.negations:
                # 检查前后是否有关键词
                has_keyword_before = False
                has_keyword_after = False
                
                # 检查前面的词
                for j in range(max(0, i - 3), i):
                    w, f = words[j]
                    for trigger_type, verbs in self.key_verbs.items():
                        if w in verbs:
                            has_keyword_before = True
                            break
                
                # 检查后面的词
                for j in range(i + 1, min(len(words), i + 4)):
                    w, f = words[j]
                    for trigger_type, verbs in self.key_verbs.items():
                        if w in verbs:
                            has_keyword_after = True
                            break
                
                # 如果否定词前后都有关键词，或者否定词在关键词之前
                if has_keyword_before or has_keyword_after:
                    return True, word
        
        return False, None
    
    def _detect_intensifier(self, words: List[Tuple[str, str]]) -> Optional[str]:
        """
        检测程度副词
        
        Args:
            words: 分词结果
        
        Returns:
            "增强" 或 "减弱" 或 None
        """
        for word, flag in words:
            if word in self.intensifiers["增强"]:
                return "增强"
            elif word in self.intensifiers["减弱"]:
                return "减弱"
        
        return None
    
    def _generate_reason(self, trigger_type: TriggerType, confidence: float,
                        keywords: List[str], has_negation: bool,
                        negation_word: Optional[str], intensifier: Optional[str]) -> str:
        """
        生成触发原因
        
        Args:
            trigger_type: 触发类型
            confidence: 置信度
            keywords: 关键词
            has_negation: 是否有否定词
            negation_word: 否定词
            intensifier: 程度副词
        
        Returns:
            原因说明
        """
        if not keywords:
            return "未检测到触发关键词"
        
        parts = []
        
        # 关键词
        parts.append(f"检测到关键词: {', '.join(keywords)}")
        
        # 置信度
        parts.append(f"置信度: {confidence:.2f}")
        
        # 否定词
        if has_negation:
            parts.append(f"检测到否定词: {negation_word}")
        
        # 程度副词
        if intensifier:
            parts.append(f"程度副词: {intensifier}")
        
        # 触发类型
        if trigger_type != TriggerType.NONE:
            parts.append(f"触发类型: {trigger_type.value}")
        
        return "; ".join(parts)
    
    def should_record(self, text: str) -> bool:
        """
        判断是否应该记录（简化接口）
        
        Args:
            text: 输入文本
        
        Returns:
            是否记录
        """
        result = self.analyze(text)
        return result.triggered


# ==================== 测试代码 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("智能触发机制测试")
    print("=" * 60)
    
    trigger = SmartTrigger()
    
    # 测试用例
    test_cases = [
        # 应该触发
        ("决定使用 SQLite 作为存储引擎", True),
        ("完成了第一阶段开发", True),
        ("这个决策非常重要", True),
        ("记录一下今天的进度", True),
        
        # 不应该触发
        ("这个决策不重要", False),
        ("不要记录这个", False),
        ("稍微有点想法", False),
        ("今天天气不错", False),
        
        # 边界情况
        ("我决定不采用这个方案", True),  # 有"决定"，但后面有"不"
        ("这个方案非常重要，必须记录", True),  # 有程度副词"非常"
    ]
    
    print("\n【测试结果】")
    for text, expected in test_cases:
        result = trigger.analyze(text)
        status = "✓" if result.triggered == expected else "✗"
        
        print(f"\n{status} 文本: {text}")
        print(f"  预期: {expected}, 实际: {result.triggered}")
        print(f"  类型: {result.trigger_type.value}")
        print(f"  置信度: {result.confidence:.2f}")
        print(f"  关键词: {result.keywords}")
        print(f"  原因: {result.reason}")
    
    print("\n" + "=" * 60)
    print("✓ 测试完成")
    print("=" * 60)
