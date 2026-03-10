---
name: openmem
description: OpenMem - Memory System for AI-powered Development. Provides persistent memory storage with full-text search, version control, and IDE integration. Use when user wants to record, search, or manage personal memories, decisions, and project knowledge.
version: 0.1.1
author: jcgokart
tags: [memory, knowledge-base, search, version-control]
---

# OpenMem Skill

OpenMem helps AI assistants manage persistent memories for users. It stores decisions, knowledge, and experiences that the user wants to remember.

## When to Use This Skill

Use OpenMem when the user wants to:
- Record important decisions made during development
- Save knowledge or information for future reference
- Search past conversations and context
- Maintain project-specific knowledge base
- Organize meeting notes automatically
- Track milestones and progress

## Installation

The user must install OpenMem first:

```bash
pip install openmem
```

Or for development:
```bash
pip install -e .
```

## Commands

### 1. init - Initialize Memory

Initialize a new memory storage. Can be project-level or global.

```bash
# Project-level memory (creates .memory/ in current directory)
openmem init

# Global memory (creates ~/.memory/)
openmem init --global

# With template
openmem init --template standard
```

**Templates:**
- `minimal` - Basic setup
- `standard` - Recommended (default)
- `full` - Includes all features

### 2. add - Add a Memory

Add a new memory entry with automatic type detection.

```bash
# Add with auto-detected type
openmem add "We decided to use PostgreSQL for the database"

# Specify type explicitly
openmem add "Use JWT for authentication" --type decision

# With tags
openmem add "Database connection pool config" --type knowledge --tags database,performance

# With priority (0-10)
openmem add "Critical fix for auth bug" --type issue --priority 10
```

**Memory Types:**
- `decision` - Important decisions (default)
- `milestone` - Project milestones
- `issue` - Problems and solutions
- `knowledge` - Technical knowledge
- `conversation` - Meeting notes
- `archive` - Archived memories

### 3. search - Search Memories

Full-text search across all memories.

```bash
# Basic search
openmem search JWT

# Search in specific scope
openmem search database --scope project   # only project memory
openmem search database --scope global    # only global memory
openmem search database --scope both      # both (default)

# With limit
openmem search "authentication" --limit 20
```

### 4. list - List Memories

List all memories with optional filters.

```bash
# List all
openmem list

# Filter by type
openmem list --type decision

# With limit
openmem list --type knowledge --limit 50
```

### 5. organize - AI Meeting Notes

Organize meeting notes using AI.

```bash
# Auto-organize recent conversations
openmem organize --auto --llm ollama

# Organize last N days
openmem organize --days 7

# Specify LLM provider
openmem organize --auto --llm deepseek
openmem organize --auto --llm openai
```

**LLM Providers:**
- `ollama` - Local models (free)
- `deepseek` - Cheap API
- `openai` - Standard API

## Examples for AI to Understand Context

**When user makes a decision:**
> "Let's use SQLite for now"
AI should: `openmem add "Decided to use SQLite for now" --type decision`

**When user explains something important:**
> "The max connections should be 100"
AI should: `openmem add "Database max connections = 100" --type knowledge --tags database,performance`

**When user completes a milestone:**
> "First version is done"
AI should: `openmem add "Released v1.0.0" --type milestone`

**When user mentions a problem:**
> "Found a memory leak in the auth module"
AI should: `openmem add "Memory leak in auth module - need to fix" --type issue`

## Storage Structure

- **Project memory**: `.memory/` in project directory
- **Global memory**: `~/.memory/` in user home
- **Database**: SQLite with FTS5 full-text search
- **Config**: `config.yaml` in memory directory

## Configuration

Default config location: `.memory/config.yaml`

```yaml
version: "0.1.1"
storage:
  path: "memory.db"
  enable_fts: true
  wal_mode: true

features:
  auto_backup: false
  encryption: false
```

## Tips for AI Assistants

1. **Proactive Recording**: When user explains important concepts, offer to save them
2. **Context Awareness**: Use `--scope project` for project-specific info, `--scope global` for personal knowledge
3. **Type Selection**: Help user choose appropriate memory type
4. **Search First**: Before answering, check if user has existing memories about the topic
5. **Version Control**: All memories are versioned, can be retrieved with history
