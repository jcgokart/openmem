# Quickstart - 5 minutes to get started

## Install

```bash
pip install trae-memory
```

## 1. Initialize

```bash
# Project-level Memory
memory init

# Global Memory (shared across projects)
memory init --global
```

## 2. Add Memory

```bash
# Auto-detect type (recommended)
memory add "We decided to use PostgreSQL database"

# Specify type
memory add "Completed user login feature" --type milestone

# Add tags
memory add "Use JWT for authentication" --tags auth,jwt
```

## 3. Search

```bash
# Keyword search
memory search PostgreSQL

# Tag search
memory search --tag auth
```

## 4. List

```bash
# List all memories
memory list

# Filter by type
memory list --type decision
```

## 5. Generate Rules

```bash
# Generate .memory/rules/project.md
memory rules
```

---

## Common Commands

| Command | Description |
|:---|:---|
| `memory init` | Initialize |
| `memory add "content"` | Add memory (auto-detect type) |
| `memory search keyword` | Search |
| `memory list` | List |
| `memory rules` | Generate rules |
| `memory backup` | Backup |
| `memory version` | Version history |

---

## Next Steps

- See [USAGE.md](USAGE.md) for detailed usage
- See [ARCHITECTURE.md](ARCHITECTURE.md) for architecture design
