"""
Memory Storage Layer Abstract Interface
Defines unified storage backend interface, supports multiple implementations
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class MemoryType(Enum):
    """Memory type"""
    DECISION = "decision"
    MILESTONE = "milestone"
    KNOWLEDGE = "knowledge"
    CONVERSATION = "conversation"
    ARCHIVE = "archive"


class MemoryData:
    """Memory data structure"""

    def __init__(self,
                 id: Optional[int] = None,
                 type: str = "",
                 content: str = "",
                 metadata: Dict[str, Any] = None,
                 tags: List[str] = None,
                 priority: int = 0,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None,
                 expires_at: Optional[datetime] = None,
                 version: int = 1):
        self.id = id
        self.type = type
        self.content = content
        self.metadata = metadata or {}
        self.tags = tags or []
        self.priority = priority
        self.created_at = created_at
        self.updated_at = updated_at
        self.expires_at = expires_at
        self.version = version


class MemoryBackend(ABC):
    """
    Memory storage abstract interface

    Usage example:
        backend = SQLiteMemoryBackend(config)
        memory_id = backend.create("decision", "Use JWT for authentication")
        memory = backend.read(memory_id)
        backend.update(memory_id, content="Updated content")
        backend.delete(memory_id)
    """

    @abstractmethod
    def create(self, type: str, content: str,
               metadata: dict = None, tags: List[str] = None,
               priority: int = 0, expires_at: str = None) -> int:
        """
        Create memory

        Args:
            type: Memory type
            content: Memory content
            metadata: Metadata
            tags: Tags
            priority: Priority
            expires_at: Expiration time

        Returns:
            Memory ID
        """
        pass

    @abstractmethod
    def read(self, memory_id: int) -> Optional[Dict[str, Any]]:
        """
        Read memory

        Args:
            memory_id: Memory ID

        Returns:
            Memory dict, returns None if not found
        """
        pass

    @abstractmethod
    def update(self, memory_id: int, content: str = None,
              metadata: dict = None, tags: List[str] = None,
              priority: int = None) -> bool:
        """
        Update memory

        Args:
            memory_id: Memory ID
            content: New content
            metadata: New metadata
            tags: New tags
            priority: New priority

        Returns:
            Whether successful
        """
        pass

    @abstractmethod
    def delete(self, memory_id: int) -> bool:
        """
        Delete memory

        Args:
            memory_id: Memory ID

        Returns:
            Whether successful
        """
        pass

    @abstractmethod
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Full-text search

        Args:
            query: Search keyword
            limit: Limit count

        Returns:
            Search result list
        """
        pass

    @abstractmethod
    def search_by_tags(self, tags: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search by tags

        Args:
            tags: Tag list
            limit: Limit count

        Returns:
            Search result list
        """
        pass

    @abstractmethod
    def list_by_type(self, type: str = None, limit: int = 100,
                    offset: int = 0) -> List[Dict[str, Any]]:
        """
        List memories by type

        Args:
            type: Memory type
            limit: Limit count
            offset: Offset

        Returns:
            Memory list
        """
        pass

    @abstractmethod
    def get_messages_page(self, page: int = 0, page_size: int = 100,
                         memory_type: str = None) -> Dict[str, Any]:
        """
        Get memories by page

        Args:
            page: Page number (starting from 0)
            page_size: Page size
            memory_type: Type filter

        Returns:
            Paginated result
        """
        pass

    @abstractmethod
    def get_memory_count(self) -> int:
        """
        Get total memory count

        Returns:
            Memory count
        """
        pass

    @abstractmethod
    def close(self):
        """
        Close connection
        """
        pass
