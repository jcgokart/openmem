"""
Meeting Notes Organizer
Full-record + LLM summarization = Meeting-style memory

Core concept:
1. Record all conversations (raw)
2. LLM summarizes to concise notes (summaries)
3. Keep timestamps, simplify rest

Minimal note format:
## Timestamp
### Decisions
### Todos
### Records
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class RawMessage:
    """Raw message"""
    timestamp: str
    role: str
    content: str
    session_id: str


@dataclass
class Summary:
    """Meeting summary"""
    date: str
    session_id: str
    decisions: List[str]
    todos: List[str]
    records: List[str]
    raw_count: int


ORGANIZE_PROMPT = """You are a meeting notes assistant. Summarize the following conversation.

Requirements:
1. Extract key decisions and agreements
2. Extract todos (who, when)
3. Extract important facts/parameters/code standards
4. Remove filler words, duplicates, casual content
5. Keep timestamps

Output format (JSON):
[JSON]
{"decisions": ["decision1", "decision2"], "todos": ["todo1", "todo2"], "records": ["record1", "record2"]}
[/JSON]

Conversation:
{conversation}
"""


def format_conversation(messages: List[RawMessage]) -> str:
    """Format conversation"""
    lines = []
    for msg in messages:
        role = "User" if msg.role == "user" else "Assistant"
        lines.append(f"{role}: {msg.content}")
    return "\n\n".join(lines)


def parse_summary(response_text: str) -> Summary:
    """Parse LLM response"""
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
    """Format as Markdown"""
    lines = [f"## {summary.date}"]

    if summary.decisions:
        lines.append("\n### Decisions")
        for item in summary.decisions:
            lines.append(f"- {item}")

    if summary.todos:
        lines.append("\n### Todos")
        for item in summary.todos:
            lines.append(f"- {item}")

    if summary.records:
        lines.append("\n### Records")
        for item in summary.records:
            lines.append(f"- {item}")

    return "\n".join(lines)


def build_prompt(conversation: str) -> str:
    """Build prompt"""
    return ORGANIZE_PROMPT.format(conversation=conversation)


class Organizer:
    """Meeting notes organizer"""

    def __init__(self, memory_dir: str = None):
        if memory_dir is None:
            memory_dir = os.path.expanduser("~/.openmem")
        
        self.memory_dir = memory_dir
        self.raw_dir = os.path.join(memory_dir, "raw")
        self.summaries_dir = os.path.join(memory_dir, "summaries")

        os.makedirs(self.raw_dir, exist_ok=True)
        os.makedirs(self.summaries_dir, exist_ok=True)

    def add_message(self, role: str, content: str, session_id: str = None) -> str:
        """Add raw message"""
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
        """Get raw messages"""
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
        """Get raw messages from recent N days"""
        messages = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).date()
            date_str = date.strftime("%Y-%m-%d")
            messages.extend(self.get_raw_messages(date_str))
        return messages

    def save_summary(self, summary: Summary) -> str:
        """Save summary"""
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

    organizer.add_message("user", "We decided to use PostgreSQL", "test001")
    organizer.add_message("assistant", "Got it, recorded", "test001")
    organizer.add_message("user", "Use cents for money, not yuan", "test001")

    messages = organizer.get_raw_messages()
    print(f"Total {len(messages)} messages")

    conversation = format_conversation(messages)
    print("\nConversation:")
    print(conversation)

    prompt = build_prompt(conversation)
    print("\nPrompt:")
    print(prompt[:500])
