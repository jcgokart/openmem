# Architecture

## Overview

trae-memory is a project-level memory system for AI-powered development. It provides persistent memory storage with full-text search, version control, and IDE integration.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Layer                            │
│              (cli/main.py - argparse)                      │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                     Core Layer                              │
│        (core/manager.py - MemoryManager)                   │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                   Storage Layer                             │
│      (storage/sqlite.py - SQLiteStorage)                   │
│              FTS5 + BM25 Search                             │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                  Feature Modules                            │
│  ┌────────────┐ ┌──────────┐ ┌─────────┐ ┌──────────────┐ │
│  │ trigger.py │ │search.py │ │version.py│ │ encryption.py │ │
│  │  (Smart    │ │  (BM25)  │ │ (Git-   │ │  (Fernet +   │ │
│  │  Trigger)  │ │          │ │  like)  │ │   PBKDF2)    │ │
│  └────────────┘ └──────────┘ └─────────┘ └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Module Description

### Core Layer

- **MemoryManager**: Main interface for all memory operations
  - Auto-detect project/global memory
  - CRUD operations
  - Search, list, pagination

### Storage Layer

- **SQLiteStorage**: Database operations
  - WAL mode for concurrent access
  - FTS5 full-text search
  - BM25 ranking algorithm

### Feature Modules

| Module | Function |
|:---|:---|
| `trigger.py` | Auto-detect memory type using NLP |
| `search.py` | BM25 ranking implementation |
| `version.py` | Git-like version control |
| `encryption.py` | Encrypted backup (Fernet + PBKDF2) |
| `organizer.py` | Meeting minutes organizer |
| `llm.py` | LLM client for auto-summarize |

## Data Model

### Memory Table

```sql
CREATE TABLE memories (
    id INTEGER PRIMARY KEY,
    content TEXT NOT NULL,
    type TEXT DEFAULT 'knowledge',
    tags TEXT,
    priority INTEGER DEFAULT 5,
    scope TEXT DEFAULT 'project',
    created_at TEXT,
    updated_at TEXT
);
```

### FTS5 Virtual Table

```sql
CREATE VIRTUAL TABLE memories_fts USING fts5(
    content,
    tags,
    content=memories,
    content_rowid=id
);
```

## Search Flow

1. User inputs query
2. BM25 calculates relevance score
3. Results ranked by score
4. Highlight matched terms

## Config Inheritance

```
~/.memory/config.yaml (global)
    │
    ├── extends: null
    │
    └── project/config.yaml
            │
            └── extends: ~/.memory/config.yaml
```

Features inherited:
- memory_types definitions
- storage settings
- search preferences

## IDE Integration

- **Trae IDE**: `.memory/rules/project.md`
- **VS Code**: `.vscode/trae-memory.md`

Rules are auto-generated from memory content.
