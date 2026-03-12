"""
Unified Storage Layer with Event Sourcing
All data goes to SQLite, jsonl is only for export
"""

import sqlite3
import json
import os
import uuid
import secrets
from datetime import datetime
from typing import List, Dict, Any, Optional, Generator
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from enum import Enum

from .sqlite import ConnectionPool
from .exceptions import StorageError, FTSSearchError


class EventType(str, Enum):
    """Event types for Event Sourcing"""
    SESSION_STARTED = "session_started"
    SESSION_ENDED = "session_ended"
    MESSAGE_RECORDED = "message_recorded"
    MEMORY_ADDED = "memory_added"
    MEMORY_UPDATED = "memory_updated"
    MEMORY_DELETED = "memory_deleted"
    ORGANIZE_COMPLETED = "organize_completed"


@dataclass
class Event:
    """Event for Event Sourcing"""
    id: Optional[int] = None
    type: str = ""
    payload: Dict[str, Any] = None
    timestamp: str = ""
    session_id: Optional[str] = None
    
    def __post_init__(self):
        if self.payload is None:
            self.payload = {}
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class Session:
    """Session for conversation context"""
    id: str = ""
    project_id: Optional[str] = None
    started_at: str = ""
    ended_at: Optional[str] = None
    summary: Optional[str] = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.started_at:
            self.started_at = datetime.now().isoformat()


class UnifiedStorage:
    """
    Unified Storage Layer
    
    Features:
    - All data in SQLite
    - Event Sourcing for all operations
    - Session support for conversation context
    - Connection pool for thread safety
    - Context manager for connection handling (no leaks)
    """
    
    def __init__(self, db_path: str, pool_size: int = 5):
        self.db_path = db_path
        self._pool = ConnectionPool(
            db_path=db_path,
            pool_size=pool_size,
            wal_mode=True,
            busy_timeout=30000
        )
        self._init_tables()
    
    def _init_tables(self):
        """Initialize all tables"""
        with self._pool.connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    payload JSON NOT NULL,
                    timestamp TEXT NOT NULL,
                    session_id TEXT
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    project_id TEXT,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    summary TEXT
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    content_tokenized TEXT,
                    metadata JSON,
                    tags JSON,
                    priority INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    expires_at TEXT,
                    version INTEGER DEFAULT 1,
                    session_id TEXT,
                    source_event_id INTEGER,
                    FOREIGN KEY (source_event_id) REFERENCES events(id)
                )
            """)
            
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_memories_session ON memories(session_id)")
            
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts 
                USING fts5(content, content='memories', content_rowid='id')
            """)
            
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
                    INSERT INTO memories_fts(rowid, content) 
                    VALUES (new.id, new.content_tokenized);
                END
            """)
            
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
                    INSERT INTO memories_fts(memories_fts, rowid, content) 
                    VALUES('delete', old.id, old.content_tokenized);
                    INSERT INTO memories_fts(rowid, content) 
                    VALUES (new.id, new.content_tokenized);
                END
            """)
            
            cursor.execute("""
                CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
                    INSERT INTO memories_fts(memories_fts, rowid, content) 
                    VALUES('delete', old.id, old.content_tokenized);
                END
            """)
            
            conn.commit()
    
    def add_event(self, event_type: str, payload: Dict[str, Any], 
                  session_id: str = None) -> int:
        """Add an event (all operations are adding events)"""
        with self._pool.connection() as conn:
            cursor = conn.cursor()
            
            timestamp = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO events (type, payload, timestamp, session_id)
                VALUES (?, ?, ?, ?)
            """, (event_type, json.dumps(payload), timestamp, session_id))
            
            event_id = cursor.lastrowid
            conn.commit()
        
        self._update_materialized_view(event_id, event_type, payload, session_id)
        
        return event_id
    
    def _update_materialized_view(self, event_id: int, event_type: str, 
                                   payload: Dict[str, Any], session_id: str = None):
        """Update materialized view from event"""
        with self._pool.connection() as conn:
            cursor = conn.cursor()
            
            if event_type == EventType.MEMORY_ADDED:
                content = payload.get("content", "")
                content_tokenized = " ".join(self._tokenize(content))
                
                cursor.execute("""
                    INSERT INTO memories (type, content, content_tokenized, metadata, 
                                          tags, priority, session_id, source_event_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    payload.get("type", "knowledge"),
                    content,
                    content_tokenized,
                    json.dumps(payload.get("metadata", {})),
                    json.dumps(payload.get("tags", [])),
                    payload.get("priority", 0),
                    session_id,
                    event_id
                ))
                
            elif event_type == EventType.MEMORY_DELETED:
                memory_id = payload.get("memory_id")
                if memory_id:
                    cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
                    
            elif event_type == EventType.MEMORY_UPDATED:
                memory_id = payload.get("memory_id")
                if memory_id:
                    updates = []
                    values = []
                    
                    if "content" in payload:
                        content = payload["content"]
                        updates.append("content = ?")
                        values.append(content)
                        updates.append("content_tokenized = ?")
                        values.append(" ".join(self._tokenize(content)))
                        
                    if "metadata" in payload:
                        updates.append("metadata = ?")
                        values.append(json.dumps(payload["metadata"]))
                        
                    if "tags" in payload:
                        updates.append("tags = ?")
                        values.append(json.dumps(payload["tags"]))
                    
                    if updates:
                        updates.append("updated_at = ?")
                        values.append(datetime.now().isoformat())
                        values.append(memory_id)
                        
                        cursor.execute(
                            f"UPDATE memories SET {', '.join(updates)} WHERE id = ?",
                            values
                        )
            
            conn.commit()
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text for FTS5"""
        import jieba
        tokens = list(jieba.cut(text))
        return [t.strip().lower() for t in tokens if t.strip()]
    
    def get_events(self, session_id: str = None, event_type: str = None,
                   limit: int = 100) -> List[Event]:
        """Get events"""
        with self._pool.connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT id, type, payload, timestamp, session_id FROM events"
            conditions = []
            params = []
            
            if session_id:
                conditions.append("session_id = ?")
                params.append(session_id)
            if event_type:
                conditions.append("type = ?")
                params.append(event_type)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [Event(
                id=row[0],
                type=row[1],
                payload=json.loads(row[2]),
                timestamp=row[3],
                session_id=row[4]
            ) for row in rows]
    
    def start_session(self, project_id: str = None) -> str:
        """Start a new session"""
        session = Session(project_id=project_id)
        
        with self._pool.connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO sessions (id, project_id, started_at)
                VALUES (?, ?, ?)
            """, (session.id, session.project_id, session.started_at))
            
            conn.commit()
        
        self.add_event(EventType.SESSION_STARTED, {
            "session_id": session.id,
            "project_id": project_id
        }, session.id)
        
        return session.id
    
    def end_session(self, session_id: str, summary: str = None):
        """End a session"""
        with self._pool.connection() as conn:
            cursor = conn.cursor()
            
            ended_at = datetime.now().isoformat()
            
            cursor.execute("""
                UPDATE sessions SET ended_at = ?, summary = ?
                WHERE id = ?
            """, (ended_at, summary, session_id))
            
            conn.commit()
        
        self.add_event(EventType.SESSION_ENDED, {
            "session_id": session_id,
            "summary": summary
        }, session_id)
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session"""
        with self._pool.connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, project_id, started_at, ended_at, summary
                FROM sessions WHERE id = ?
            """, (session_id,))
            
            row = cursor.fetchone()
            
            if row:
                return Session(
                    id=row[0],
                    project_id=row[1],
                    started_at=row[2],
                    ended_at=row[3],
                    summary=row[4]
                )
            return None
    
    def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Get session context (all events and memories in this session)"""
        events = self.get_events(session_id=session_id, limit=1000)
        
        with self._pool.connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, type, content, metadata, tags, priority, created_at
                FROM memories WHERE session_id = ?
                ORDER BY created_at DESC
            """, (session_id,))
            
            rows = cursor.fetchall()
            
            memories = [{
                "id": row[0],
                "type": row[1],
                "content": row[2],
                "metadata": json.loads(row[3]) if row[3] else {},
                "tags": json.loads(row[4]) if row[4] else [],
                "priority": row[5],
                "created_at": row[6]
            } for row in rows]
            
            return {
                "session_id": session_id,
                "events": [asdict(e) for e in events],
                "memories": memories
            }
    
    def add_memory(self, content: str, memory_type: str = "knowledge",
                   metadata: Dict = None, tags: List[str] = None,
                   priority: int = 0, session_id: str = None) -> int:
        """Add a memory"""
        event_id = self.add_event(EventType.MEMORY_ADDED, {
            "content": content,
            "type": memory_type,
            "metadata": metadata or {},
            "tags": tags or [],
            "priority": priority
        }, session_id)
        
        with self._pool.connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT id FROM memories WHERE source_event_id = ?",
                (event_id,)
            )
            
            row = cursor.fetchone()
            return row[0] if row else event_id
    
    def update_memory(self, memory_id: int, **kwargs):
        """Update a memory"""
        self.add_event(EventType.MEMORY_UPDATED, {
            "memory_id": memory_id,
            **kwargs
        })
    
    def delete_memory(self, memory_id: int):
        """Delete a memory"""
        self.add_event(EventType.MEMORY_DELETED, {
            "memory_id": memory_id
        })
    
    def search(self, query: str, limit: int = 10, session_id: str = None) -> List[Dict]:
        """Search memories"""
        try:
            with self._pool.connection() as conn:
                cursor = conn.cursor()
                
                tokens = self._tokenize(query)
                fts_query = ' AND '.join(tokens)
                
                sql = """
                    SELECT m.id, m.type, m.content, m.metadata, m.tags, m.priority, 
                           m.created_at, m.session_id, bm25(memories_fts) as score
                    FROM memories m
                    JOIN memories_fts fts ON m.id = fts.rowid
                    WHERE memories_fts MATCH ? AND bm25(memories_fts) < 0
                """
                params = [fts_query]
                
                if session_id:
                    sql += " AND m.session_id = ?"
                    params.append(session_id)
                
                sql += " ORDER BY score ASC LIMIT ?"
                params.append(limit)
                
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                
                return [{
                    "id": row[0],
                    "type": row[1],
                    "content": row[2],
                    "metadata": json.loads(row[3]) if row[3] else {},
                    "tags": json.loads(row[4]) if row[4] else [],
                    "priority": row[5],
                    "created_at": row[6],
                    "session_id": row[7],
                    "score": row[8]
                } for row in rows]
        except sqlite3.OperationalError as e:
            if 'fts' in str(e).lower() or 'match' in str(e).lower():
                return self._search_like_fallback(query, limit, session_id)
            raise FTSSearchError(f"FTS5 search failed: {e}") from e
        except sqlite3.DatabaseError as e:
            raise StorageError(f"Database error during search: {e}") from e
    
    def _search_like_fallback(self, query: str, limit: int, session_id: str = None) -> List[Dict]:
        """LIKE search fallback"""
        with self._pool.connection() as conn:
            cursor = conn.cursor()
            
            sql = """
                SELECT id, type, content, metadata, tags, priority, created_at, session_id
                FROM memories
                WHERE content LIKE ?
            """
            params = [f'%{query}%']
            
            if session_id:
                sql += " AND session_id = ?"
                params.append(session_id)
            
            sql += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            return [{
                "id": row[0],
                "type": row[1],
                "content": row[2],
                "metadata": json.loads(row[3]) if row[3] else {},
                "tags": json.loads(row[4]) if row[4] else [],
                "priority": row[5],
                "created_at": row[6],
                "session_id": row[7],
                "score": None
            } for row in rows]
    
    def get_memory(self, memory_id: int) -> Optional[Dict]:
        """Get a single memory by ID"""
        with self._pool.connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, type, content, metadata, tags, priority, created_at, session_id
                FROM memories WHERE id = ?
            """, (memory_id,))
            
            row = cursor.fetchone()
            
            if row:
                return {
                    "id": row[0],
                    "type": row[1],
                    "content": row[2],
                    "metadata": json.loads(row[3]) if row[3] else {},
                    "tags": json.loads(row[4]) if row[4] else [],
                    "priority": row[5],
                    "created_at": row[6],
                    "session_id": row[7]
                }
            return None
    
    def list_memories(self, memory_type: str = None, limit: int = 100,
                      offset: int = 0, session_id: str = None) -> List[Dict]:
        """List memories with optional filters"""
        with self._pool.connection() as conn:
            cursor = conn.cursor()
            
            conditions = []
            params = []
            
            if memory_type:
                conditions.append("type = ?")
                params.append(memory_type)
            if session_id:
                conditions.append("session_id = ?")
                params.append(session_id)
            
            where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
            
            sql = f"""
                SELECT id, type, content, metadata, tags, priority, created_at, session_id
                FROM memories
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])
            
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            
            return [{
                "id": row[0],
                "type": row[1],
                "content": row[2],
                "metadata": json.loads(row[3]) if row[3] else {},
                "tags": json.loads(row[4]) if row[4] else [],
                "priority": row[5],
                "created_at": row[6],
                "session_id": row[7]
            } for row in rows]
    
    def get_memory_count(self) -> int:
        """Get total memory count"""
        with self._pool.connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM memories")
            return cursor.fetchone()[0]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics"""
        with self._pool.connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM memories")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT type, COUNT(*) as count FROM memories GROUP BY type")
            by_type = {row[0]: row[1] for row in cursor.fetchall()}
            
            cursor.execute("SELECT COUNT(*) FROM sessions")
            session_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM events")
            event_count = cursor.fetchone()[0]
            
            return {
                "total": total, 
                "by_type": by_type,
                "session_count": session_count,
                "event_count": event_count
            }
    
    def close(self):
        """Close all connections"""
        self._pool.close_all()
