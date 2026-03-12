"""
SQLAlchemy ORM models for OpenMem
"""

from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, JSON, ForeignKey, Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Memory(Base):
    """
    Memory model for storing memories.
    """
    __tablename__ = 'memories'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(50), nullable=False, index=True, default='knowledge')
    content = Column(Text, nullable=False)
    content_tokenized = Column(Text, nullable=True)
    meta_data = Column(JSON, nullable=True, default=dict)
    tags = Column(JSON, nullable=True, default=list)
    priority = Column(Integer, nullable=True, default=0)
    session_id = Column(String(100), nullable=True, index=True)
    source_event_id = Column(Integer, ForeignKey('events.id'), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_memories_type', 'type'),
        Index('idx_memories_session_id', 'session_id'),
        Index('idx_memories_created_at', 'created_at'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'type': self.type,
            'content': self.content,
            'metadata': self.meta_data or {},
            'tags': self.tags or [],
            'priority': self.priority or 0,
            'session_id': self.session_id,
            'source_event_id': self.source_event_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self) -> str:
        return f"<Memory(id={self.id}, type={self.type!r})>"


class Event(Base):
    """
    Event model for event sourcing.
    """
    __tablename__ = 'events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(100), nullable=False, index=True)
    payload = Column(JSON, nullable=True, default=dict)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    session_id = Column(String(100), nullable=True, index=True)
    
    memories = relationship("Memory", backref="source_event")
    
    __table_args__ = (
        Index('idx_events_type', 'type'),
        Index('idx_events_session_id', 'session_id'),
        Index('idx_events_timestamp', 'timestamp'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'type': self.type,
            'payload': self.payload or {},
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'session_id': self.session_id
        }
    
    def __repr__(self) -> str:
        return f"<Event(id={self.id}, type={self.type!r})>"
