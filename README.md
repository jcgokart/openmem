# trae-memory

Project-level memory system for AI-powered development.

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

## Why trae-memory?

| Feature | trae-memory | OpenClaw |
|:---|:---|:---|
| Extra Dependencies | **None** | Requires sqlite-vec |
| Installation | `pip install trae-memory` | Requires vector engine |
| Search | FTS5 + BM25 | vector + BM25 + MMR |
| Vector Search | Future support | ✅ |

**trae-memory advantage**: Works out of the box, no extra database engine needed!

## Installation

```bash
pip install trae-memory
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

## Directory Structure

```
.memory/                    # Project Memory
├── config.yaml            # Config
├── memory.db              # SQLite database
├── rules/
│   └── project.md        # IDE rules
├── sessions/             # Session exports
├── knowledge/            # Knowledge exports
└── backups/              # Backups

~/.memory/                 # Global Memory
├── config.yaml
├── memory.yaml
└── ...
```

## Config

```yaml
# .memory/config.yaml
extends: ~/.memory/config.yaml

project:
  name: "my-project"

memory_types:
  decision:
    sync_to_global: true
  milestone:
    sync_to_global: false

storage:
  type: sqlite
  wal_mode: true
  enable_fts: true

search:
  highlight: true
  tokenizer: jieba
```

## Commands

| Command | Description |
|:---|:---|
| `memory init` | Initialize project Memory |
| `memory init --global` | Initialize global Memory |
| `memory init --template=standard` | Select template |
| `memory status` | Show status |
| `memory status -v` | Verbose |
| `memory add "content"` | Add memory |
| `memory search query` | Search |
| `memory list` | List memories |
| `memory page` | Paginate |

## Memory Types

| Type | Description | Sync to Global |
|:---|:---|:---|
| decision | Important decisions | Optional |
| milestone | Milestones | Optional |
| issue | Issue records | No |
| knowledge | Knowledge docs | Yes |
| session | Session records | No |
| archive | Archived content | No |

## Related Docs

- [QUICKSTART.md](QUICKSTART.md) - 5-minute quick start
- [USAGE.md](USAGE.md) - Detailed usage
- [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture design

## License

MIT

---

# 中文简介

trae-memory 是专为 AI 开发设计的项目级记忆系统。

**核心特点：**
- 零依赖，开箱即用
- 支持中文分词搜索
- 项目级 + 全局分层
- 自动生成 IDE 规则
- 支持 Trae IDE 和 VS Code

**适用场景：**
- 记录技术决策和约束
- 知识沉淀和复用
- 项目规范统一
