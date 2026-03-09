"""
Memory 系统入口
"""

__version__ = "2.0.0"

from memory.core.manager import MemoryManager
from memory.core.config import MemoryConfig

__all__ = ["MemoryManager", "MemoryConfig", "__version__"]
