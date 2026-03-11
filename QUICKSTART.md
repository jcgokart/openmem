# Quickstart - 5 minutes to get started

## Install

```bash
pip install openmem
```

Or use the short alias:

```bash
pip install openmem
```

## 1. Initialize

```bash
# Project-level Memory
openmem init

# Or use the alias
mem init

# Global Memory (shared across projects)
openmem init --global
mem init --global
```

## 2. Add Memory

```bash
# Auto-detect type (recommended)
openmem add "We decided to use PostgreSQL database"
mem add "We decided to use PostgreSQL database"

# Specify type
openmem add "Completed user login feature" --type milestone

# Add tags
openmem add "Use JWT for authentication" --tags auth,jwt
```

## 3. Search

```bash
# Keyword search
openmem search PostgreSQL

# Tag search
openmem search --tag auth
```

## 4. List

```bash
# List all memories
openmem list

# Filter by type
openmem list --type decision
```

## As Python Library

```python
from openmem import MemoryManager

memory = MemoryManager()
memory.add("Important decision here", type="decision")
results = memory.search("PostgreSQL")
for r in results:
    print(r['content'])
```
