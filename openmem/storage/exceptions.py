"""
Custom exceptions for OpenMem storage layer
"""


class MemoryError(Exception):
    """Base exception for all memory operations"""
    pass


class StorageError(MemoryError):
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
    def __init__(self, memory_id: int, message: str = None):
        self.memory_id = memory_id
        self.message = message or f"Memory with id {memory_id} not found"
        super().__init__(self.message)


class DatabaseIntegrityError(StorageError):
    """Database integrity constraint error"""
    def __init__(self, message: str, original_error: Exception = None):
        self.original_error = original_error
        super().__init__(message)


class DatabaseOperationalError(StorageError):
    """Database operational error (connection, lock, etc.)"""
    def __init__(self, message: str, original_error: Exception = None):
        self.original_error = original_error
        super().__init__(message)


class SessionError(StorageError):
    """Session related errors"""
    pass


class EventSourcingError(StorageError):
    """Event sourcing related errors"""
    pass
