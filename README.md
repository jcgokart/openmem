# OpenMem

Project-level memory system for AI-powered development.

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

## Philosophy: Skills vs Knowledge

**The Difference Between Knowing and Doing**

Most AI memory systems focus on **knowledge** - storing documents, files, and information you can look up. They use RAG technology to build massive knowledge bases. But here's the truth:

> **Knowledge is not ability.**
> Knowing how to swim won't make you a swimmer.
> Knowing 1000 recipes won't make you a chef.

### A Personal Journey

I witnessed the AI revolution unfold:

- **2016**: AlphaGo defeated Lee Sedol. For the first time, AI found optimal solutions in an infinite space - it wasn't just brute-force search anymore. It had "intuition."

- **The Expert System Era**: We built knowledge bases to store what we already knew. Search, retrieve, repeat. No creation, no growth.

- **The LLM Era**: Now we ask AI everything. But here's the pain: **the more we search, the less we internalize.** Information overload without transformation.

> The more I look up, the less I actually know.

That's the core problem OpenMem solves.

**Our Vision**: Build a personal knowledge and capability system - a repository of your creativity, not just information.

**Our Journey**: This project isn't just about using AI - it's about **growing with AI**. As AI evolves, so does OpenMem. We:
- Embrace new technologies (LLM integration, multimodal, agents)
- Learn from the community (open source contributions)
- Evolve together with the AI landscape

The goal: Not just consuming AI, but **building with it**.

---

## Features

- 🎯 **Project-level Memory** - Independent memory space per project
- 🔍 **Full-text Search** - Chinese tokenization (jieba) + FTS5 + BM25 ranking
- 🌐 **Global/Project Layers** - Flexible like Poetry
- 📦 **Template Init** - minimal / standard / full
- ⚙️ **Config Inheritance** - extends global config
- 📝 **Rules Generation** - Auto-generate IDE-readable rules
- 🔒 **Encrypted Backup** - Local encrypted storage
- ⏮️ **Version Control** - Git-like versioning
- 🖥️ **Dual IDE Support** - Trae IDE + VS Code
- ⚡ **Zero Dependencies** - SQLite only, ready out of the box

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
memory init

# Global Memory (shared across projects)
memory init --global

# Select template
memory init --template=standard
memory init --template=full

# Non-interactive mode
memory init -y
```

### Basic Usage

```bash
# Add memory
memory add "Use JWT for authentication" --type decision --tags auth,security

# Search
memory search auth
memory search auth --scope both

# List
memory list --type decision

# Status
memory status
memory status -v
```

### Python API

```python
from memory import MemoryManager

# Auto-select (project first)
memory = MemoryManager()

# Add memory
memory_id = memory.add(
    content="Use JWT for authentication",
    type="decision",
    tags=["auth", "security"]
)

# Search
results = memory.search("auth", scope="both")

# List
memories = memory.list(type="decision")

memory.close()
```

## Documentation

- [Quick Start Guide](QUICKSTART.md)
- [Usage Guide](USAGE.md)
- [Architecture](ARCHITECTURE.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

---

## 中文简介

**OpenMem** - 面向 AI 开发的个人记忆系统

### 核心理念

我们相信：**知识不是能力**。

现有的 AI 记忆系统都在追求"大而全"——把天下知识都存进来。但真正有价值的是**你身上的本事**：
- 你踩过哪些坑？
- 你精通哪些工具？
- 你做过哪些决策？

这才是你的**十八般兵器**。

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
- ⚡ 零依赖（仅 SQLite）

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
