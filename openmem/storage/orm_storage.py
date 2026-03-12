"""
ORM-based Unified Storage Layer with Event Sourcing
Uses SQLAlchemy for safe, parameterized queries
"""

import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

from sqlalchemy import create_engine, select, delete, update, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError, OperationalError

from .orm import Base, Memory, Event
from .exceptions import (
    StorageError, MemoryNotFoundError,
    DatabaseIntegrityError, DatabaseOperationalError
)
from ..core.errors import ErrorCode, OpenMemError
from ..core.metrics import timed_query, metrics

logger = logging.getLogger("openmem")


class EventType:
    """Event types for Event Sourcing"""
    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"
    MESSAGE_RECORDED = "message_recorded"
    MEMORY_ADDED = "memory_added"
    MEMORY_UPDATED = "memory_updated"
    MEMORY_DELETED = "memory_deleted"
    ORGANIZE_COMPLETED = "organize_completed"


class ORMStorage:
    """
    ORM-based Unified Storage Layer.
    
    Uses SQLAlchemy for safe, parameterized queries.
    No SQL injection risk - all queries are parameterized.
    """
    
    ALLOWED_FIELDS = frozenset({'content', 'metadata', 'tags', 'priority'})
    
    def __init__(self, db_path: str = None, echo: bool = False):
        """
        Initialize ORM storage.
        
        Args:
            db_path: Path to SQLite database file
            echo: Whether to echo SQL statements
        """
        if db_path is None:
            db_path = os.path.expanduser("~/.memory/memory.db")
        
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.engine = create_engine(
            f"sqlite:///{db_path}",
            echo=echo,
            json_serializer=json.dumps,
            json_deserializer=json.loads
        )
        
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        Base.metadata.create_all(self.engine)
        
        self._init_fts()
        
        logger.info(f"ORMStorage initialized with db_path={db_path}")
    
    def _init_fts(self):
        """Initialize FTS5 virtual table for full-text search"""
        with self.engine.connect() as conn:
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                    content_tokenized,
                    content='memories',
                    content_rowid='id'
                )
            """)
            conn.commit()
    
    @contextmanager
    def get_session(self) -> Session:
        """Get a database session with automatic commit/rollback"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text for FTS5"""
        import jieba
        tokens = list(jieba.cut(text))
        return [t.strip().lower() for t in tokens if t.strip()]
    
    @timed_query
    def add_memory(
        self,
        content: str,
        memory_type: str = "knowledge",
        metadata: Dict = None,
        tags: List[str] = None,
        priority: int = 0,
        session_id: str = None
    ) -> int:
        """
        Add a memory using ORM.
        
        Args:
            content: Memory content
            memory_type: Type of memory
            metadata: Optional metadata dict
            tags: Optional list of tags
            priority: Priority level
            session_id: Optional session ID
            
        Returns:
            int: The ID of the created memory
            
        Raises:
            DatabaseIntegrityError: If database constraint violated
            DatabaseOperationalError: If database operation fails
        """
        try:
            with self.get_session() as session:
                event = Event(
                    type=EventType.MEMORY_ADDED,
                    payload={
                        "content": content,
                        "type": memory_type,
                        "metadata": metadata or {},
                        "tags": tags or [],
                        "priority": priority
                    },
                    session_id=session_id
                )
                session.add(event)
                session.flush()
                
                content_tokenized = " ".join(self._tokenize(content))
                
                memory = Memory(
                    type=memory_type,
                    content=content,
                    content_tokenized=content_tokenized,
                    meta_data=metadata or {},
                    tags=tags or [],
                    priority=priority,
                    session_id=session_id,
                    source_event_id=event.id
                )
                session.add(memory)
                session.flush()
                
                logger.info(f"Added memory id={memory.id}")
                return memory.id
                
        except IntegrityError as e:
            logger.error(f"Integrity error adding memory: {e}", exc_info=True)
            raise DatabaseIntegrityError(f"Data integrity error: {e}", e) from e
        except OperationalError as e:
            logger.error(f"Operational error adding memory: {e}", exc_info=True)
            raise DatabaseOperationalError(f"Database operational error: {e}", e) from e
        except Exception as e:
            logger.exception(f"Unexpected error adding memory")
            raise StorageError(f"Unexpected error: {e}") from e
    
    @timed_query
    def get_memory(self, memory_id: int) -> Dict[str, Any]:
        """
        Get a memory by ID.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            dict: Memory data
            
        Raises:
            MemoryNotFoundError: If memory not found
        """
        with self.get_session() as session:
            memory = session.get(Memory, memory_id)
            if not memory:
                raise MemoryNotFoundError(memory_id)
            return memory.to_dict()
    
    @timed_query
    def update_memory(self, memory_id: int, **kwargs) -> bool:
        """
        Update a memory using ORM.
        
        Args:
            memory_id: Memory ID
            **kwargs: Fields to update
            
        Returns:
            bool: True if updated
            
        Raises:
            ValueError: If no valid fields
            MemoryNotFoundError: If memory not found
        """
        updates = {k: v for k, v in kwargs.items() if k in self.ALLOWED_FIELDS}
        
        if not updates:
            raise ValueError(f"No valid fields to update. Allowed: {self.ALLOWED_FIELDS}")
        
        try:
            with self.get_session() as session:
                memory = session.get(Memory, memory_id)
                if not memory:
                    raise MemoryNotFoundError(memory_id)
                
                if 'metadata' in updates:
                    updates['meta_data'] = updates.pop('metadata')
                if 'content' in updates:
                    updates['content_tokenized'] = " ".join(self._tokenize(updates['content']))
                
                for key, value in updates.items():
                    setattr(memory, key, value)
                
                memory.updated_at = datetime.utcnow()
                
                event = Event(
                    type=EventType.MEMORY_UPDATED,
                    payload={"memory_id": memory_id, "updates": updates},
                    session_id=memory.session_id
                )
                session.add(event)
                
                logger.info(f"Updated memory id={memory_id}")
                return True
                
        except MemoryNotFoundError:
            raise
        except IntegrityError as e:
            logger.error(f"Integrity error updating memory {memory_id}: {e}", exc_info=True)
            raise DatabaseIntegrityError(f"Data integrity error: {e}", e) from e
        except OperationalError as e:
            logger.error(f"Operational error updating memory {memory_id}: {e}", exc_info=True)
            raise DatabaseOperationalError(f"Database operational error: {e}", e) from e
        except Exception as e:
            logger.exception(f"Unexpected error updating memory {memory_id}")
            raise StorageError(f"Unexpected error: {e}") from e
    
    @timed_query
    def delete_memory(self, memory_id: int) -> bool:
        """
        Delete a memory using ORM.
        
        Args:
            memory_id: Memory ID
            
        Returns:
            bool: True if deleted
            
        Raises:
            MemoryNotFoundError: If memory not found
        """
        try:
            with self.get_session() as session:
                memory = session.get(Memory, memory_id)
                if not memory:
                    raise MemoryNotFoundError(memory_id)
                
                event = Event(
                    type=EventType.MEMORY_DELETED,
                    payload={"memory_id": memory_id},
                    session_id=memory.session_id
                )
                session.add(event)
                
                session.delete(memory)
                
                logger.info(f"Deleted memory id={memory_id}")
                return True
                
        except MemoryNotFoundError:
            raise
        except IntegrityError as e:
            logger.error(f"Integrity error deleting memory {memory_id}: {e}", exc_info=True)
            raise DatabaseIntegrityError(f"Data integrity error: {e}", e) from e
        except OperationalError as e:
            logger.error(f"Operational error deleting memory {memory_id}: {e}", exc_info=True)
            raise DatabaseOperationalError(f"Database operational error: {e}", e) from e
        except Exception as e:
            logger.exception(f"Unexpected error deleting memory {memory_id}")
            raise StorageError(f"Unexpected error: {e}") from e
    
    @timed_query
    def list_memories(
        self,
        memory_type: str = None,
        session_id: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List memories with optional filters.
        
        Args:
            memory_type: Filter by type
            session_id: Filter by session
            limit: Max results
            offset: Offset for pagination
            
        Returns:
            list: List of memory dicts
        """
        with self.get_session() as session:
            query = select(Memory)
            
            if memory_type:
                query = query.where(Memory.type == memory_type)
            if session_id:
                query = query.where(Memory.session_id == session_id)
            
            query = query.order_by(Memory.created_at.desc()).limit(limit).offset(offset)
            
            memories = session.execute(query).scalars().all()
            return [m.to_dict() for m in memories]
    
    @timed_query
    def get_memory_count(self, memory_type: str = None, session_id: str = None) -> int:
        """Get count of memories"""
        with self.get_session() as session:
            query = select(func.count(Memory.id))
            
            if memory_type:
                query = query.where(Memory.type == memory_type)
            if session_id:
                query = query.where(Memory.session_id == session_id)
            
            return session.execute(query).scalar() or 0
    
    def close(self):
        """Close database connections"""
        self.engine.dispose()
        logger.info("ORMStorage closed")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        return metrics.to_dict()
