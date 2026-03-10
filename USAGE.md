# USAGE - Detailed Usage Guide

## CLI Commands

### init - Initialize

```bash
# Interactive mode
memory init

# Non-interactive mode
memory init -y

# Specify project path
memory init /path/to/project

# Global Memory (shared across projects)
memory init --global

# Select template
memory init --template=minimal   # Minimal config
memory init --template=standard  # Standard config
memory init --template=full      # Full config

# Specify project name
memory init --project-name myapp
```

### add - Add Memory

```bash
# Auto-detect type (recommended)
memory add "We decided to use PostgreSQL"

# Specify type
memory add "Completed login feature" --type milestone

# Add tags
memory add "Use JWT for authentication" --tags auth,jwt

# Specify priority (0-10)
memory add "Important decision" --priority 8

# Specify scope
memory add "Global knowledge" --scope global

# Full example
memory add "Use Redis for caching" --type knowledge --tags redis,cache --priority 5
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
memory search PostgreSQL

# Limit results
memory search database --limit 5

# Tag search
memory search --tag auth

# Project path
memory search JWT --project /path/to/project
```

### list - List

```bash
# All memories
memory list

# Filter by type
memory list --type decision
memory list --type milestone

# Limit
memory list --limit 50
```

### page - Pagination

```bash
# First page, 20 items per page
memory page --page 0

# Specific page and size
memory page --page 2 --page-size 50
```

### status - Status

```bash
# Show Memory status
memory status
```

---

## Python API

### Basic Usage

```python
from memory import MemoryManager

# Project-level
memory = MemoryManager(project_path="/path/to/project")

# Or global
memory = MemoryManager()
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
memory add "We decided to use JWT for authentication"
# Output:
# 🔍 Auto-detected type: decision (confidence: 0.70)
#    Keywords: 决定
# ✅ Memory added: ID=1
```

Trigger mechanism analyzes:
- Keyword detection (decide, adopt, complete, etc.)
- Negation handling ("not important" won't be misdetected)
- Intensifiers ("very important" has higher confidence)
