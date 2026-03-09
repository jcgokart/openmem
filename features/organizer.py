"""
P2-2: 会议纪要整理器
全量记录 + LLM 提炼 = 会议纪要式记忆

核心思路：
1. 全量记录对话（raw）
2. LLM 提炼成精炼纪要（summaries）
3. 保留时间标签，其他简化

极简纪要格式：
## 时间
### 决策
### 待办
### 记录
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class RawMessage:
    """原始消息"""
    timestamp: str
    role: str
    content: str
    session_id: str


@dataclass
class Summary:
    """会议纪要"""
    date: str
    session_id: str
    decisions: List[str]
    todos: List[str]
    records: List[str]
    raw_count: int


ORGANIZE_PROMPT = """你是一个会议纪要助手。把以下对话整理成精炼记录。

要求：
1. 提取关键决策和约定
2. 提取待办事项（谁负责、何时完成）
3. 提取重要事实/参数/代码规范
4. 去掉废话、重复、口语化内容
5. 保留时间标签

输出格式（JSON）：
{
    "decisions": ["决策1", "决策2"],
    "todos": ["待办1", "待办2"],
    "records": ["重要记录1", "重要记录2"]
}

对话内容：
{conversation}
"""


def format_conversation(messages: List[RawMessage]) -> str:
    """格式化对话"""
    lines = []
    for msg in messages:
        role = "用户" if msg.role == "user" else "助手"
        lines.append(f"{role}: {msg.content}")
    return "\n\n".join(lines)


def parse_summary(response_text: str) -> Summary:
    """解析 LLM 响应"""
    try:
        data = json.loads(response_text)
        return Summary(
            date=datetime.now().strftime("%Y-%m-%d"),
            session_id="",
            decisions=data.get("decisions", []),
            todos=data.get("todos", []),
            records=data.get("records", []),
            raw_count=0
        )
    except json.JSONDecodeError:
        return Summary(
            date=datetime.now().strftime("%Y-%m-%d"),
            session_id="",
            decisions=[],
            todos=[],
            records=[response_text],
            raw_count=0
        )


def format_summary_md(summary: Summary) -> str:
    """格式化为 Markdown"""
    lines = [f"## {summary.date}"]

    if summary.decisions:
        lines.append("\n### 决策")
        for item in summary.decisions:
            lines.append(f"- {item}")

    if summary.todos:
        lines.append("\n### 待办")
        for item in summary.todos:
            lines.append(f"- {item}")

    if summary.records:
        lines.append("\n### 记录")
        for item in summary.records:
            lines.append(f"- {item}")

    return "\n".join(lines)


def build_prompt(conversation: str) -> str:
    """构建 prompt"""
    return ORGANIZE_PROMPT.format(conversation=conversation)


class Organizer:
    """会议纪要整理器"""

    def __init__(self, memory_dir: str = None):
        if memory_dir is None:
            memory_dir = os.path.expanduser("~/.trae-memory")
        
        self.memory_dir = memory_dir
        self.raw_dir = os.path.join(memory_dir, "raw")
        self.summaries_dir = os.path.join(memory_dir, "summaries")

        os.makedirs(self.raw_dir, exist_ok=True)
        os.makedirs(self.summaries_dir, exist_ok=True)

    def add_message(self, role: str, content: str, session_id: str = None) -> str:
        """添加原始消息"""
        if session_id is None:
            session_id = datetime.now().strftime("%Y%m%d%H%M%S")

        message = RawMessage(
            timestamp=datetime.now().isoformat(),
            role=role,
            content=content,
            session_id=session_id
        )

        date = datetime.now().strftime("%Y-%m-%d")
        filepath = os.path.join(self.raw_dir, f"{date}.jsonl")

        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(message), ensure_ascii=False) + "\n")

        return session_id

    def get_raw_messages(self, date: str = None, session_id: str = None) -> List[RawMessage]:
        """获取原始消息"""
        messages = []

        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        filepath = os.path.join(self.raw_dir, f"{date}.jsonl")
        if not os.path.exists(filepath):
            return messages

        with open(filepath, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                msg = RawMessage(**json.loads(line))
                if session_id is None or msg.session_id == session_id:
                    messages.append(msg)

        return messages

    def get_recent_raw(self, days: int = 1) -> List[RawMessage]:
        """获取最近 N 天的原始消息"""
        messages = []
        for i in range(days):
            date = (datetime.now().replace(hour=0, minute=0, second=0)).date()
            date_str = date.strftime("%Y-%m-%d")
            messages.extend(self.get_raw_messages(date_str))
        return messages

    def save_summary(self, summary: Summary) -> str:
        """保存纪要"""
        filepath = os.path.join(
            self.summaries_dir,
            f"{summary.date}.md"
        )

        content = format_summary_md(summary)

        with open(filepath, "a", encoding="utf-8") as f:
            f.write("\n\n" + content)

        return filepath


if __name__ == "__main__":
    organizer = Organizer()

    organizer.add_message("user", "我们决定用 PostgreSQL 数据库", "test001")
    organizer.add_message("assistant", "好的，记下来", "test001")
    organizer.add_message("user", "金额用分不用元", "test001")

    messages = organizer.get_raw_messages()
    print(f"共 {len(messages)} 条消息")

    conversation = format_conversation(messages)
    print("\n对话：")
    print(conversation)

    prompt = build_prompt(conversation)
    print("\nPrompt：")
    print(prompt[:500])
