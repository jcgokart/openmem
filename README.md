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

**What Really Matters: Your Skills**

OpenMem is designed for **personal capability building**:

- 🎯 **What bugs have you fixed?** (Your debugging expertise)
- 🛠️ **What patterns do you use?** (Your coding style)  
- 📚 **What have you learned?** (Your accumulated wisdom)
- 💡 **What decisions have you made?** (Your technical judgment)
- ⚔️ **What tools do you master?** (Your十八般兵器 - your toolkit)

**The Value Proposition**

| Other Systems | OpenMem |
|:---|:---|
| "What can I look up?" | "What can I do?" |
| External knowledge base | Your inner capabilities |
| Information storage | Experience沉淀 |
| RAG - retrieve and generate | Reflection - learn and grow |
| "I know everything" | "I can do this" |

**Your Toolkit Matters More Than Your Database**

The best developers aren't those who have access to the most information. They're the ones who have **mastered their toolkit** - the patterns, the debugging skills, the decision-making frameworks.

OpenMem helps you build that.

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

## License

MIT
