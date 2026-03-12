"""
Memory Storage Module
"""

from openmem.storage.sqlite import SQLiteMemoryBackend, SQLiteConfig, ConnectionPool
from openmem.storage.unified import UnifiedStorage, Event, Session, EventType
from openmem.storage.exceptions import (
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
