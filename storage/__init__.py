"""
Memory Storage Module
"""

from openmem.storage.sqlite import SQLiteMemoryBackend, SQLiteConfig

SQLiteStorage = SQLiteMemoryBackend

__all__ = ["SQLiteMemoryBackend", "SQLiteStorage", "SQLiteConfig"]
