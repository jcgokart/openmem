# OpenMem

# Project-level Memory system for AI-powered development.

## Why OpenMem?

**The Problem We Solved**

While using AI-powered development tools like OpenClaw, we experienced a critical issue: **important conversations and decisions were frequently lost**. The trigger-based memory system missed crucial context daily - technical decisions, problem-solving insights, and creative breakthroughs disappeared into the void.

**Our Development Environment Has Evolved**

The IDE is no longer just a code editor. It's become our **primary workspace** where we:
- Discuss architecture with AI
- Debug complex problems  
- Capture fleeting insights
- Make critical technical decisions

Only polished outcomes become documentation (MD/Word/PDF). But the **golden moments** - the sparks of insight during live problem-solving - deserve to be preserved too.

**Our Solution: Full Recording + Smart Organization**

Instead of relying on imperfect triggers, we record **everything** and organize intelligently. This approach:
- ✅ Never misses important context
- ✅ Captures the complete thinking process
- ✅ Turns conversations into actionable knowledge
- ✅ Works across all development scenarios

**Four Usage Scenarios**

1. **IDE Integration** (Trae / VS Code) - Your daily driver
2. **Code Editor** - Lightweight editing sessions  
3. **CLI Tools** - Command-line development
4. **AI Assistant** (OpenClaw) - Enhanced memory for your AI partner

**Why We Built This**

We're developers who faced the same pain point. After replacing our own OpenClaw memory with this system and seeing dramatic improvements, we knew we had to share it.

**Learn from OpenClaw, Evolve Beyond**

OpenClaw showed us the way. We're continuing that evolution - breaking context limitations, preserving knowledge, and making every conversation count.

---

## Features

- 🎯 **Project-level Memory** - Independent memory space per project
- 🔍 **Full-text Search** - Chinese tokenization (jieba) + FTS5 + BM25 ranking
- 🌐 **Global/Project Layers** - Flexible like Poetry
- 📦 **Template Init** - minimal / standard / full
- ⚙️ **Config Inheritance** - extends global config
- 📝 **Rules Generation** - Auto-generate IDE-readable rules
- 🔒 **Encrypted Backup** - Local encrypted storage (future)
- ⏮️ **Version Control** - Git-like versioning (future)
- 🖥️ **IDE Support** - Trae IDE + VS Code

---

## Security & Privacy

**Data Storage**
- All data is stored **locally** on your machine
- Raw data in SQLite database (plain text for fast FTS5 search)
- **No data is ever sent to external servers**

**Backup**
- Encrypted backup feature is planned for future release
- Encryption algorithm: Fernet (symmetric encryption)
- Key management: User-provided passphrase

**Privacy**
- Zero network requests by default
- Your data stays on your machine
- You control when and how to share

---

## Current Status

| Feature | Status | Notes |
|:---|:---:|:---|
| CLI (init/add/search/list/status) | ✅ Done | Core commands working |
| Project/Global layers | ✅ Done | Like Poetry config |
| Full-text search (FTS5 + BM25) | ✅ Done | jieba for Chinese |
| Config inheritance | ✅ Done | extends global config |
| Template init | ✅ Done | minimal/standard/full |
| Python API | ✅ Done | from openmem import |
| Encrypted backup | 🔜 Planned | v0.2 |
| Git-like version control | 🔜 Planned | v0.2 |
| IDE rules auto-generation | 🔜 In Progress | Trae/VS Code support |
| LLM summarization | 🔜 Planned | v0.3 |

---

## Architecture

```mermaid
graph TD
    A[User Input] --> B{CLI or API}
    B -->|CLI| C[Memory Manager]
    B -->|API| C
    C --> D{Scope Check}
    D -->|Project| E[Project DB<br/>.memory/]
    D -->|Global| F[Global DB<br/>~/.memory/]
    E --> G[SQLite + FTS5]
    F --> G
    G --> H[BM25 Ranking]
    H --> I[Search Results]
```

**Data Flow:**
1. User input via CLI or Python API
2. Memory Manager routes to Project or Global layer
3. Data stored in local SQLite with FTS5 index
4. Search uses BM25 for relevance ranking

---

## Installation

```bash
pip install openmem
```

Or development mode:

```bash
pip install -e .
```

## Quick Start

### Initialize

```bash
# Project-level Memory
omem init

# Global Memory (shared across projects)
omem init --global

# Select template
omem init --template=standard
omem init --template=full

# Non-interactive mode
omem init -y
```

### Basic Usage

```bash
# Add memory
omem add "Use JWT for authentication" --type decision --tags auth,security

# Search
omem search auth
omem search auth --scope both

# List
omem list --type decision

# Status
omem status
omem status -v
```

### Python API

```python
from openmem import MemoryManager

# Auto-select (project first, fallback to global)
memory = MemoryManager()

# Explicit project path
memory = MemoryManager(project_path="/path/to/project")

# Global memory only
memory = MemoryManager(project_path=None)

# Add memory
memory_id = memory.add(
    content="Use JWT for authentication",
    type="decision",
    tags=["auth", "security"],
    priority=8
)

# Search with filters
results = memory.search(
    query="authentication",
    scope="project",      # "project" | "global" | "both"
    memory_type="decision",
    tags=["auth"],
    limit=10
)

# List memories
memories = memory.list(
    memory_type="decision",
    tags=["auth"],
    limit=50
)

# Update and delete
memory.update(memory_id, content="New content")
memory.delete(memory_id)

memory.close()
```

## Documentation

- [Quick Start Guide](QUICKSTART.md)
- [Usage Guide](USAGE.md)
- [Architecture](ARCHITECTURE.md)
- [Philosophy](PHILOSOPHY.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

---

## 中文简介

**OpenMem** - 面向 AI 开发的个人记忆系统

### 核心理念

现在的个人知识库就是一个**资料库**——你把文件塞进去，用的时候再搜。但真相是：

> 你不搜你就不知道。
> 搜到了，也不一定是你的。

**知识就是力量**——但这些系统存的是：
- 别人的知识
- 天下共识
- 外部信息

只有你**内化**了，才是你的知识。

OpenMem 存的是你的：
- 🎯 **你的决策**——不是别人做的决定
- 🔧 **你的经验**——不是别人的经历
- 💡 **你的领悟**——不是别人的想法
- ⚔️ **你的能力**——你的十八般兵器

这才是**你的能力**，不只是信息。

### 我们的目标

不是做一个"什么都能查"的知识库，而是帮助你建立**真正的个人能力系统**。

### 主要特性

- 🎯 项目级记忆（独立空间）
- 🔍 中英文全文搜索（jieba + FTS5 + BM25）
- 🌐 全局/项目双层结构
- 📦 模板初始化
- ⚙️ 配置继承
- 📝 IDE 规则自动生成
- 🔒 加密备份
- ⏮️ 版本控制
- 🖥️ 支持 Trae IDE + VS Code
- ⚡ 最小依赖（SQLite + jieba）

### 安装

```bash
pip install openmem
```

### 快速开始

```bash
# 初始化
openmem init

# 添加记忆
openmem add "使用 JWT 做认证" --type decision

# 搜索
openmem search JWT
```

### 作为 Python 库使用

```python
from openmem import MemoryManager

memory = MemoryManager()
memory.add("重要决策", type="decision")
results = memory.search("JWT")
```

**让我们一起成长，与 AI 共进化！**

---

## License

MIT
