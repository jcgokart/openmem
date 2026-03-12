"""
Memory Storage Module
"""

from storage.sqlite import SQLiteMemoryBackend, SQLiteConfig, ConnectionPool
from storage.unified import UnifiedStorage, Event, Session, EventType
from storage.exceptions import (
    StorageError, 
    FTSSearchError, 
    ConnectionPoolError,
    MemoryNotFoundError
)

SQLiteStorage = SQLiteMemoryBackend

__all__ = [
    "SQLiteMemoryBackend",
    "SQLiteStorage",
    "SQLiteConfig",
    "ConnectionPool",
    "UnifiedStorage",
    "Event",
    "Session",
    "EventType",
    "StorageError",
    "FTSSearchError",
    "ConnectionPoolError",
    "MemoryNotFoundError"
]
