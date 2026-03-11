# USAGE - Detailed Usage Guide

## CLI Commands

### init - Initialize

```bash
# Interactive mode
omem init

# Non-interactive mode
omem init -y

# Specify project path
omem init /path/to/project

# Global Memory (shared across projects)
omem init --global

# Select template
omem init --template=minimal   # Minimal config
omem init --template=standard  # Standard config
omem init --template=full      # Full config

# Specify project name
omem init --project-name myapp
```

### add - Add Memory

```bash
# Auto-detect type (recommended)
omem add "We decided to use PostgreSQL"

# Specify type
omem add "Completed login feature" --type milestone

# Add tags
omem add "Use JWT for authentication" --tags auth,jwt

# Specify priority (0-10)
omem add "Important decision" --priority 8

# Specify scope
omem add "Global knowledge" --scope global

# Full example
omem add "Use Redis for caching" --type knowledge --tags redis,cache --priority 5
```

**Type Reference:**
| Type | Description | Trigger Keywords |
|:---|:---|:---|
| `decision` | Decisions | decide, adopt, implement |
| `milestone` | Milestones | complete, release, launch |
| `issue` | Issues | fix, resolve, bug |
| `knowledge` | Knowledge | tech, doc, API |

### search - Search

```bash
# Keyword search
omem search PostgreSQL

# Limit results
omem search database --limit 5

# Tag search
omem search --tag auth

# Project path
omem search JWT --project /path/to/project
```

### list - List

```bash
# All memories
omem list

# Filter by type
omem list --type decision
omem list --type milestone

# Limit
omem list --limit 50
```

### page - Pagination

```bash
# First page, 20 items per page
omem page --page 0

# Specific page and size
omem page --page 2 --page-size 50
```

### status - Status

```bash
# Show Memory status
omem status
```

---

## Python API

### Basic Usage

```python
from openmem import MemoryManager

# Project-level
omem = MemoryManager(project_path="/path/to/project")

# Or global
omem = MemoryManager()
```

### Add Memory

```python
# Add
memory_id = memory.add(
    content="We decided to use PostgreSQL",
    type="decision",
    tags=["database", "backend"],
    priority=5
)
```

### Search

```python
# Keyword search
results = memory.search("PostgreSQL")

# Tag search
results = memory.search_by_tags(["auth"])
```

### List

```python
# All
results = memory.list()

# By type
results = memory.list(type="decision")

# Paginate
page = memory.page(page=0, page_size=20)
```

### Update/Delete

```python
# Update
memory.update(memory_id, content="New content", tags=["new"])

# Delete
memory.delete(memory_id)
```

### Close

```python
memory.close()
```

---

## Smart Trigger

When adding memory, the system automatically analyzes content and detects type:

```bash
omem add "We decided to use JWT for authentication"
# Output:
# 🔍 Auto-detected type: decision (confidence: 0.70)
#    Keywords: decide, decide to use
# ✅ Memory added: ID=1
```

Trigger mechanism analyzes:
- Keyword detection (decide, adopt, complete, etc.)
- Negation handling ("not important" won't be misdetected)
- Intensifiers ("very important" has higher confidence)
