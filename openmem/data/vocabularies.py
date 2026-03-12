"""
Constants Data
Bilingual (Chinese/English) constants for memory system
"""

# ==================== Stopwords ====================

STOPWORDS_ZH = {
    '的', '了', '是', '在', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你',
    '会', '着', '没有', '看', '好', '自己', '这', '为', '与', '或', '但', '而', '以', '及', '被', '把', '给', '让', '向',
    '对', '从', '由', '所', '其', '此', '那', '么', '吗', '呢', '吧', '啊', '呀', '嘛', '哦', '哈', '嗯', '唉', '喂',
    '他', '她', '它', '们', '这个', '那个', '什么', '怎么', '如何', '为什么', '哪', '哪里', '哪个', '多少', '几', '怎样',
    '可以', '能够', '应该', '必须', '需要', '想', '要', '得', '能', '会', '可', '只', '还', '再', '又', '也', '已', '已经',
    '曾', '曾经', '正在', '正', '将', '将要', '刚', '刚才', '现在', '目前', '今天', '明天', '昨天', '今年', '去年',
    '明年', '以后', '之前', '之后', '然后', '接着', '于是', '因此', '所以', '因为', '但是', '然而', '不过', '只是',
    '虽然', '即使', '除非', '只有', '只要', '无论', '不管', '既然', '既', '如此', '这样', '那样', '这么', '那么', '多么'
}

STOPWORDS_EN = {
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
    'may', 'might', 'must', 'shall', 'can', 'need', 'dare', 'ought', 'used',
    'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through',
    'during', 'before', 'after', 'above', 'below', 'between', 'under', 'again',
    'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how',
    'all', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
    'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just',
    'and', 'but', 'if', 'or', 'because', 'until', 'while', 'although', 'though',
    'this', 'that', 'these', 'those', 'it', 'its', 'they', 'them', 'their',
    'what', 'which', 'who', 'whom', 'i', 'me', 'my', 'myself', 'we', 'our', 'ours',
    'you', 'your', 'yours', 'he', 'him', 'his', 'she', 'her', 'hers', 'us', 'we'
}

STOPWORDS = STOPWORDS_ZH | STOPWORDS_EN


# ==================== Trigger Keywords ====================

TRIGGER_KEYWORDS = {
    "decision": {
        "zh": [
            "决定", "选择", "采用", "实施", "确定", "选定", "敲定",
            "拍板", "定下", "确定", "选择"
        ],
        "en": [
            "decide", "decides", "decided", "decision", "choose", "chooses", "chosen",
            "adopt", "adopts", "adopted", "adoption", "implement", "implements", "implemented",
            "determine", "determines", "determined", "settle", "settles", "settled",
            "finalize", "finalizes", "finalized", "go with"
        ]
    },
    "milestone": {
        "zh": [
            "完成", "实现", "达成", "上线", "发布", "交付", "验收",
            "结束", "收尾", "完工", "竣工"
        ],
        "en": [
            "complete", "completes", "completed", "completion",
            "finish", "finishes", "finished", "accomplish", "accomplishes", "accomplished",
            "launch", "launches", "launched", "release", "releases", "released",
            "deliver", "delivers", "delivered", "deliverable", "ship", "ships", "shipped",
            "deploy", "deploys", "deployed", "go live", "live", "done"
        ]
    },
    "important": {
        "zh": [
            "重要", "关键", "核心", "注意", "记住", "务必", "必须",
            "紧急", "优先", "重点"
        ],
        "en": [
            "important", "crucial", "critical", "key", "essential", "vital",
            "must", "must have", "required", "priority", "prioritize", "focus",
            "attention", "note", "remember", "keep in mind", "as reminder"
        ]
    },
    "archive": {
        "zh": [
            "总结", "归档", "结束", "记录", "保存", "存档",
            "整理", "归纳", "汇总"
        ],
        "en": [
            "summarize", "summarizes", "summarized", "summary",
            "archive", "archives", "archived", "record", "records", "recorded",
            "save", "saves", "saved", "document", "documents", "documented",
            "wrap up", "conclude", "concludes", "concluded", "wrap-up"
        ]
    }
}


# ==================== Negations ====================

NEGATIONS_ZH = [
    "不", "没", "无", "非", "未", "别", "莫", "勿",
    "不要", "不用", "无需", "不必", "没有", "不是"
]

NEGATIONS_EN = [
    "not", "no", "never", "none", "nothing", "neither", "nobody", "nowhere",
    "hardly", "barely", "scarcely", "dont", "doesn't", "didnt", "wont", "wouldnt",
    "cant", "cannot", "without", "minus", "without"
]

NEGATIONS = NEGATIONS_ZH + NEGATIONS_EN


# ==================== Intensifiers ====================

INTENSIFIERS = {
    "enhance": {
        "zh": ["非常", "特别", "极其", "相当", "十分", "格外"],
        "en": ["very", "really", "extremely", "absolutely", "totally", "completely", "highly", "quite", "格外"]
    },
    "reduce": {
        "zh": ["稍微", "略微", "有点", "有些", "比较", "还算"],
        "en": ["slightly", "somewhat", "a bit", "a little", "kind of", "sort of", "稍微"]
    }
}


# ==================== Tech Words (for jieba) ====================

TECH_WORDS = [
    "微服务", "单体架构", "分布式", "容器化", "Kubernetes",
    "Docker", "CI/CD", "DevOps", "敏捷开发", "Scrum",
    "RESTful", "GraphQL", "gRPC", "WebSocket", "Redis",
    "PostgreSQL", "MongoDB", "Elasticsearch", "Kafka",
    "microservice", "monolith", "distributed", "container", "kubernetes",
    "docker", "cicd", "devops", "agile", "scrum", "restful", "graphql",
    "grpc", "websocket", "redis", "postgresql", "mongodb", "elasticsearch", "kafka",
    "API", "SDK", "ORM", "JWT", "OAuth", "SQL", "NoSQL", "API"
]


# ==================== Memory Types ====================

MEMORY_TYPES = {
    "decision": {
        "zh": "决策",
        "en": "Decision",
        "description_zh": "重要决策和技术选型",
        "description_en": "Important decisions and technical choices"
    },
    "milestone": {
        "zh": "里程碑",
        "en": "Milestone",
        "description_zh": "项目重要节点和成果",
        "description_en": "Project milestones and achievements"
    },
    "issue": {
        "zh": "问题",
        "en": "Issue",
        "description_zh": "问题记录和解决方案",
        "description_en": "Issue records and solutions"
    },
    "knowledge": {
        "zh": "知识",
        "en": "Knowledge",
        "description_zh": "技术文档和知识积累",
        "description_en": "Technical documentation and knowledge"
    },
    "session": {
        "zh": "会话",
        "en": "Session",
        "description_zh": "会话记录",
        "description_en": "Session records"
    },
    "archive": {
        "zh": "归档",
        "en": "Archive",
        "description_zh": "归档内容",
        "description_en": "Archived content"
    }
}
