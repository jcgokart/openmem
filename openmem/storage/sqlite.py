"""
Memory SQLite Storage Implementation
High-performance SQLite backend with FTS5 full-text search
"""

import sqlite3
import json
import os
import threading
import queue
from datetime import datetime
from typing import List, Dict, Any, Optional, Generator
from contextlib import contextmanager
import warnings

import jieba

from .base import MemoryBackend, MemoryType
from .exceptions import (
    StorageError, 
    FTSSearchError, 
    ConnectionPoolError,
    MemoryNotFoundError
)


class ConnectionPool:
    """Thread-safe SQLite connection pool with context manager support"""
    
    def __init__(self, db_path: str, pool_size: int = 5, 
                 wal_mode: bool = True, busy_timeout: int = 30000):
        self.db_path = db_path
        self.pool_size = pool_size
        self.wal_mode = wal_mode
        self.busy_timeout = busy_timeout
        self._pool = queue.Queue(maxsize=pool_size)
        self._lock = threading.Lock()
        self._initialized = False
        
    def _create_connection(self) -> sqlite3.Connection:
        """Create a new connection"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=30
        )
        conn.row_factory = sqlite3.Row
        
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA busy_timeout={self.busy_timeout}")
        if self.wal_mode:
            cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.execute("PRAGMA foreign_keys=ON")
        
        return conn
    
    def _do_initialize(self):
        """Internal initialize without lock (caller must hold lock)"""
        if self._initialized:
            return
        for _ in range(self.pool_size):
            conn = self._create_connection()
            self._pool.put(conn)
        self._initialized = True
    
    def initialize(self):
        """Initialize the pool (public method with lock)"""
        with self._lock:
            self._do_initialize()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get a connection from the pool with double-checked locking"""
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    self._do_initialize()
        return self._pool.get()
    
    def return_connection(self, conn: sqlite3.Connection):
        """Return a connection to the pool"""
        self._pool.put(conn)
    
    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Context manager for connection handling.
        Ensures connection is always returned to pool, even on exception.
        Auto-commits on success, auto-rollbacks on exception.
        
        Usage:
            with pool.connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO ...")
            # Auto-commit here
        """
        conn = None
        try:
            conn = self.get_connection()
            yield conn
            conn.commit()
        except Exception:
            if conn is not None:
                conn.rollback()
            raise
        finally:
            if conn is not None:
                self.return_connection(conn)
    
    def close_all(self):
        """Close all connections"""
        with self._lock:
            while not self._pool.empty():
                try:
                    conn = self._pool.get_nowait()
                    conn.close()
                except queue.Empty:
                    break
            self._initialized = False


class SQLiteConfig:
    """SQLite Config"""

    def __init__(self, db_path: str, enable_fts: bool = True,
                 wal_mode: bool = True, busy_timeout: int = 30000,
                 pool_size: int = 5):
        self.db_path = db_path
        self.enable_fts = enable_fts
        self.wal_mode = wal_mode
        self.busy_timeout = busy_timeout
        self.pool_size = pool_size


class SQLiteMemoryBackend(MemoryBackend):
    """
    SQLite Storage Backend Implementation

    Features:
    - SQLite + WAL mode (high performance, concurrent safe)
    - FTS5 full-text search (pre-tokenized storage)
    - Transaction support
    - Version control
    - Connection pool for thread safety

    .. deprecated:: 0.1.4
        Use UnifiedStorage instead for Event Sourcing support.
    """

    def __init__(self, config: SQLiteConfig):
        warnings.warn(
            "SQLiteMemoryBackend is deprecated. Use UnifiedStorage instead.",
            DeprecationWarning,
            stacklevel=2
        )
        self.config = config
        self._pool = ConnectionPool(
            db_path=config.db_path,
            pool_size=config.pool_size,
            wal_mode=config.wal_mode,
            busy_timeout=config.busy_timeout
        )
        self._init_database()

    def _init_database(self):
        """Initialize database"""
        with self._pool.connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    content_tokenized TEXT,
                    metadata TEXT,
                    tags TEXT,
                    priority INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    version INTEGER DEFAULT 1
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_type 
                ON memories(type)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_created 
                ON memories(created_at DESC)
            """)
            
            if self.config.enable_fts:
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
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    memory_id INTEGER NOT NULL,
                    type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    version INTEGER NOT NULL,
                    hash TEXT NOT NULL,
                    parent_hash TEXT,
                    message TEXT,
                    version_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (memory_id) REFERENCES memories(id)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS backup_records (
                    id TEXT PRIMARY KEY,
                    backup_path TEXT NOT NULL,
                    backup_type TEXT NOT NULL,
                    size INTEGER,
                    created_at TEXT,
                    checksum TEXT,
                    memory_count INTEGER,
                    status TEXT
                )
            """)
            
            conn.commit()
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convert row to dict"""
        return {
            'id': row[0],
            'type': row[1],
            'content': row[2],
            'metadata': json.loads(row[3]) if row[3] else {},
            'tags': json.loads(row[4]) if row[4] else [],
            'priority': row[5],
            'created_at': row[6],
            'updated_at': row[7],
            'expires_at': row[8],
            'version': row[9]
        }
    
    def _tokenize(self, content: str) -> str:
        """Tokenize text"""
        tokens = list(jieba.cut(content))
        return ' '.join([t.strip().lower() for t in tokens if t.strip()])
    
    def create(self, type: str, content: str,
               metadata: dict = None, tags: List[str] = None,
               priority: int = 0, expires_at: str = None) -> int:
        """Create memory"""
        with self._pool.connection() as conn:
            cursor = conn.cursor()
            
            content_tokenized = self._tokenize(content)
            
            cursor.execute("""
                INSERT INTO memories (type, content, content_tokenized, metadata, tags, priority, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                type,
                content,
                content_tokenized,
                json.dumps(metadata, ensure_ascii=False) if metadata else None,
                json.dumps(tags, ensure_ascii=False) if tags else None,
                priority,
                expires_at
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def read(self, memory_id: int) -> Optional[Dict[str, Any]]:
        """Read memory"""
        with self._pool.connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, type, content, metadata, tags, priority, 
                       created_at, updated_at, expires_at, version
                FROM memories WHERE id = ?
            """, (memory_id,))
            
            row = cursor.fetchone()
            return self._row_to_dict(row) if row else None
    
    def update(self, memory_id: int, content: str = None,
              metadata: dict = None, tags: List[str] = None,
              priority: int = None) -> bool:
        """Update memory"""
        with self._pool.connection() as conn:
            cursor = conn.cursor()
            
            updates = []
            params = []
            
            if content is not None:
                updates.append("content = ?")
                params.append(content)
                updates.append("content_tokenized = ?")
                params.append(self._tokenize(content))
            
            if metadata is not None:
                updates.append("metadata = ?")
                params.append(json.dumps(metadata, ensure_ascii=False))
            
            if tags is not None:
                updates.append("tags = ?")
                params.append(json.dumps(tags, ensure_ascii=False))
            
            if priority is not None:
                updates.append("priority = ?")
                params.append(priority)
            
            if not updates:
                return False
            
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(memory_id)
            
            cursor.execute(f"""
                UPDATE memories SET {', '.join(updates)} WHERE id = ?
            """, params)
            
            conn.commit()
            return cursor.rowcount > 0
    
    def delete(self, memory_id: int) -> bool:
        """Delete memory"""
        with self._pool.connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            conn.commit()
            
            return cursor.rowcount > 0
    
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Full-text search"""
        if not self.config.enable_fts:
            return self._search_like_fallback(query, limit)
        
        try:
            with self._pool.connection() as conn:
                cursor = conn.cursor()
                
                tokens = list(jieba.cut(query))
                tokens = [t.strip().lower() for t in tokens if t.strip()]
                fts_query = ' AND '.join(tokens)
                
                cursor.execute("""
                    SELECT m.id, m.type, m.content, m.metadata, m.tags, m.priority, 
                           m.created_at, m.updated_at, m.expires_at, m.version,
                           bm25(memories_fts) as score
                    FROM memories m
                    JOIN memories_fts fts ON m.id = fts.rowid
                    WHERE memories_fts MATCH ? AND bm25(memories_fts) < 0
                    ORDER BY score ASC
                    LIMIT ?
                """, (fts_query, limit))
                
                return [self._row_to_dict(row[:10]) for row in cursor.fetchall()]
                
        except sqlite3.OperationalError as e:
            if 'fts' in str(e).lower() or 'match' in str(e).lower():
                return self._search_like_fallback(query, limit)
            raise FTSSearchError(f"FTS5 search failed: {e}") from e
        except sqlite3.DatabaseError as e:
            raise StorageError(f"Database error during search: {e}") from e
    
    def _search_like_fallback(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """LIKE search fallback"""
        with self._pool.connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, type, content, metadata, tags, priority, 
                       created_at, updated_at, expires_at, version
                FROM memories
                WHERE content LIKE ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (f'%{query}%', limit))
            
            return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    def search_by_tags(self, tags: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """Search by tags"""
        with self._pool.connection() as conn:
            cursor = conn.cursor()
            
            conditions = ' OR '.join(['tags LIKE ?' for _ in tags])
            params = [f'%"{tag}"%' for tag in tags] + [limit]
            
            cursor.execute(f"""
                SELECT DISTINCT id, type, content, metadata, tags, priority, 
                       created_at, updated_at, expires_at, version
                FROM memories
                WHERE {conditions}
                ORDER BY created_at DESC
                LIMIT ?
            """, params)
            
            return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    def list_by_type(self, type: str = None, limit: int = 100,
                    offset: int = 0) -> List[Dict[str, Any]]:
        """List by type"""
        with self._pool.connection() as conn:
            cursor = conn.cursor()
            
            if type is None:
                cursor.execute("""
                    SELECT id, type, content, metadata, tags, priority, 
                           created_at, updated_at, expires_at, version
                    FROM memories
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset))
            else:
                cursor.execute("""
                    SELECT id, type, content, metadata, tags, priority, 
                           created_at, updated_at, expires_at, version
                    FROM memories
                    WHERE type = ?
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """, (type, limit, offset))
            
            return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    def get_messages_page(self, page: int = 0, page_size: int = 100,
                         memory_type: str = None) -> Dict[str, Any]:
        """Get messages by page"""
        with self._pool.connection() as conn:
            cursor = conn.cursor()
            
            offset = page * page_size
            
            if memory_type:
                where_clause = "WHERE type = ?"
                query_params = (memory_type, page_size, offset)
                count_params = (memory_type,)
            else:
                where_clause = ""
                query_params = (page_size, offset)
                count_params = ()
            
            cursor.execute(f"""
                SELECT id, type, content, metadata, tags, priority, 
                       created_at, updated_at, expires_at, version
                FROM memories
                {where_clause}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, query_params)
            
            messages = [self._row_to_dict(row) for row in cursor.fetchall()]
            
            if memory_type:
                cursor.execute("SELECT COUNT(*) FROM memories WHERE type = ?", count_params)
            else:
                cursor.execute("SELECT COUNT(*) FROM memories")
            
            total = cursor.fetchone()[0]
            
            return {
                'messages': messages,
                'page': page,
                'page_size': page_size,
                'total': total,
                'total_pages': (total + page_size - 1) // page_size
            }
    
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
            
            return {"total": total, "by_type": by_type}
    
    def close(self):
        """Close all connections"""
        self._pool.close_all()
