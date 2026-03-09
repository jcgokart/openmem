# trae-memory

Memory System for Trae IDE - 项目级记忆管理系统

## 特性

- 🎯 **项目级记忆** - 每个项目独立的记忆空间
- 🔍 **全文搜索** - 支持中文分词 (jieba) + FTS5 + BM25 排序
- 🌐 **全局/项目分层** - 像 Poetry 一样灵活
- 📦 **模板化初始化** - minimal / standard / full
- ⚙️ **配置继承** - 支持 extends 全局配置
- 📝 **规则文件** - 自动生成 IDE 可读规则
- 🔒 **加密备份** - 本地加密存储
- ⏮️ **版本控制** - Git-like 版本管理
- 🖥️ **双 IDE 支持** - 适配 Trae IDE + VS Code
- ⚡ **零依赖** - 只需 SQLite，开箱即用

## 对比 OpenClaw

| 特性 | trae-memory | OpenClaw |
|:---|:---|:---|
| 额外依赖 | **无** (零依赖) | 需要 sqlite-vec |
| 安装 | `pip install trae-memory` | 需配置向量引擎 |
| 搜索 | FTS5 + BM25 | vector + BM25 + MMR |
| 向量搜索 | 后续版本支持 | ✅ |

**trae-memory 优势**：开箱即用，无需安装额外数据库引擎！

## 安装

```bash
pip install trae-memory
```

或开发模式：

```bash
pip install -e .
```

## 快速开始

### 初始化

```bash
# 项目级 Memory
memory init

# 全局 Memory（所有项目共享）
memory init --global

# 选择模板
memory init --template=standard
memory init --template=full

# 非交互模式
memory init -y
```

### 基本使用

```bash
# 添加记忆
memory add "使用 JWT 认证" --type decision --tags auth,security

# 搜索记忆
memory search 认证
memory search 认证 --scope both

# 列出记忆
memory list --type decision

# 查看状态
memory status
memory status -v
```

### Python API

```python
from memory import MemoryManager

# 自动选择（项目优先）
memory = MemoryManager()

# 添加记忆
memory_id = memory.add(
    content="使用 JWT 认证",
    type="decision",
    tags=["auth", "security"]
)

# 搜索
results = memory.search("认证", scope="both")

# 列出
memories = memory.list(type="decision")

memory.close()
```

## 目录结构

```
.memory/                    # 项目 Memory
├── config.yaml            # 配置文件
├── memory.db              # SQLite 数据库
├── rules/
│   └── project.md        # IDE 规则
├── sessions/             # 会话导出
├── knowledge/            # 知识导出
└── backups/              # 备份

~/.memory/                 # 全局 Memory
├── config.yaml
├── memory.db
└── ...
```

## 配置

```yaml
# .memory/config.yaml
extends: ~/.memory/config.yaml  # 继承全局配置

project:
  name: "my-project"

memory_types:
  decision:
    sync_to_global: true   # 同步到全局
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

## 命令

| 命令 | 说明 |
|:---|:---|
| `memory init` | 初始化项目 Memory |
| `memory init --global` | 初始化全局 Memory |
| `memory init --template=standard` | 选择模板 |
| `memory status` | 查看状态 |
| `memory status -v` | 详细信息 |
| `memory add "内容"` | 添加记忆 |
| `memory search 关键词` | 搜索 |
| `memory list` | 列出 |
| `memory page` | 分页 |

## 记忆类型

| 类型 | 说明 | 同步到全局 |
|:---|:---|:---|
| decision | 重要决策 | 可选 |
| milestone | 里程碑 | 可选 |
| issue | 问题记录 | 否 |
| knowledge | 知识文档 | 是 |
| session | 会话记录 | 否 |
| archive | 归档内容 | 否 |

## License

MIT
