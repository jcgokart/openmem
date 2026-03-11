# Contributing to OpenMem

Contributions welcome! Please follow these guidelines.

## Development Setup

```bash
# Clone repository
git clone https://github.com/jcgokart/openmem.git
cd openmem

# Install dependencies
pip install -e .
```

## Code Standards

We follow these coding standards:

- **PEP 8** - Python official style guide
- **Google Style Docstrings** - For documentation
- **Type Hints** - Required for function signatures

### Naming Conventions

| Type | Convention | Example |
|:---|:---|:---|
| Classes | PascalCase | `MemoryManager` |
| Functions/Variables | snake_case | `add_memory` |
| Constants | UPPER_SNAKE_CASE | `DEFAULT_PATH` |
| Private methods | _leading_underscore | `_internal_method` |

### Code Style

- **4-space indentation** (no tabs)
- **Line length**: Max 100 characters
- **Docstrings**: Required for all public classes/functions
- **Type hints**: Required for function signatures

### Error Handling

- Never swallow exceptions silently
- Provide actionable error messages

---

# Welcome to Contribute!

## Coding Standards

- **PEP 8** - Python official style
- **Google Style** - Docstrings
- **Type Hints** - Required in function signatures
- **VNPY Style** - Data classes for readability
- **AlphaAlgo Practice** - Internal project best practices

## Code Review Principles

1. Can you understand it in 30 seconds?
2. Is the type clear?
3. Is error handling appropriate?
4. Any magic values?
