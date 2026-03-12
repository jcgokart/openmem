"""
Custom exceptions for OpenMem storage layer
"""


class StorageError(Exception):
    """Base exception for storage operations"""
    pass


class ConnectionPoolError(StorageError):
    """Connection pool related errors"""
    pass


class FTSSearchError(StorageError):
    """FTS5 full-text search related errors"""
    pass


class MemoryNotFoundError(StorageError):
    """Memory not found error"""
    pass


class SessionError(StorageError):
    """Session related errors"""
    pass


class EventSourcingError(StorageError):
    """Event sourcing related errors"""
    pass
