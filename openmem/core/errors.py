"""
Error handling module for OpenMem
"""

from enum import Enum
from typing import Optional, Dict, Any


class ErrorCode(Enum):
    """Error codes for OpenMem"""
    INTEGRITY_ERROR = "DATA_CONFLICT"
    OPERATIONAL_ERROR = "DB_UNAVAILABLE"
    VALIDATION_ERROR = "INVALID_INPUT"
    NOT_FOUND = "RESOURCE_NOT_FOUND"
    UNKNOWN_ERROR = "UNKNOWN"


class OpenMemError(Exception):
    """
    Base exception for OpenMem with error code support.
    
    Attributes:
        code: Error code enum
        message: Human-readable error message
        details: Additional error details
    """
    
    def __init__(
        self, 
        code: ErrorCode, 
        message: str, 
        details: Optional[Dict[str, Any]] = None
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(f"[{code.value}] {message}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for API responses"""
        return {
            "code": self.code.value,
            "message": self.message,
            "details": self.details
        }
    
    def __str__(self) -> str:
        return f"[{self.code.value}] {self.message}"
    
    def __repr__(self) -> str:
        return f"OpenMemError(code={self.code}, message={self.message!r})"
