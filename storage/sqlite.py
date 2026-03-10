"""
Memory SQLite Storage Implementation
High-performance SQLite backend with FTS5 full-text search
"""

import sqlite3
import json
import os
import threading
from datetime import datetime
from typing import List, Dict, Any, Optional

from .base import MemoryBackend, MemoryType


class SQLiteConfig:
    """SQLite Config"""

    def __init__(self, db_path: str, enable_fts: bool = True,
                 wal_mode: bool = True, busy_timeout: int = 30000):
        self.db_path = db_path
        self.enable_fts = enable_fts
        self.wal_mode = wal_mode
        self.busy_timeout = busy_timeout


class SQLiteMemoryBackend(MemoryBackend):
    """
    SQLite Storage Backend Implementation

    Features:
    - SQLite + WAL mode (high performance, concurrent safe)
    - FTS5 full-text search (pre-tokenized storage)
    - Transaction support
    - Version control
    """

    def __init__(self, config: SQLiteConfig):
        self.config = config
        self._local = threading.local()
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local connection"""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            os.makedirs(os.path.dirname(self.config.db_path), exist_ok=True)
            conn = sqlite3.connect(
                self.config.db_path,
                check_same_thread=False,
                timeout=30
            )
            conn.row_factory = sqlite3.Row
            self._local.conn = conn
            self._configure_connection(conn)
        return self._local.conn

    def _configure_connection(self, conn: sqlite3.Connection):
        """Configure connection"""
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA busy_timeout={self.config.busy_timeout}")

        if self.config.wal_mode:
            cursor.execute("PRAGMA journal_mode=WAL")

        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.execute("PRAGMA foreign_keys=ON")

    def _init_database(self):
        """Initialize database"""
        conn = self._get_connection()
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
        import jieba
        tokens = list(jieba.cut(content))
        return ' '.join([t.strip().lower() for t in tokens if t.strip()])
    
    def create(self, type: str, content: str,
               metadata: dict = None, tags: List[str] = None,
               priority: int = 0, expires_at: str = None) -> int:
        """Create memory"""
        conn = self._get_connection()
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
        conn = self._get_connection()
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
        conn = self._get_connection()
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
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        conn.commit()
        
        return cursor.rowcount > 0
    
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Full-text search"""
        if not self.config.enable_fts:
            return self._search_like_fallback(query, limit)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            tokens = list(jieba.cut(query))
            tokens = [t.strip().lower() for t in tokens if t.strip()]
            fts_query = ' OR '.join(tokens)
            
            cursor.execute("""
                SELECT m.id, m.type, m.content, m.metadata, m.tags, m.priority, 
                       m.created_at, m.updated_at, m.expires_at, m.version
                FROM memories m
                JOIN memories_fts fts ON m.id = fts.rowid
                WHERE memories_fts MATCH ?
                ORDER BY bm25(memories_fts)
                LIMIT ?
            """, (fts_query, limit))
            
            return [self._row_to_dict(row) for row in cursor.fetchall()]
            
        except sqlite3.OperationalError as e:
            error_msg = str(e).lower()
            if 'fts' in error_msg or 'match' in error_msg or 'syntax' in error_msg:
                return self._search_like_fallback(query, limit)
            raise
    
    def _search_like_fallback(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """LIKE search fallback"""
        conn = self._get_connection()
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
        conn = self._get_connection()
        cursor = conn.cursor()
        
        conditions = ' OR '.join(['tags LIKE ?' for _ in tags])
        params = [f'%{tag}%' for tag in tags] + [limit]
        
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
        conn = self._get_connection()
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
        conn = self._get_connection()
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
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM memories")
        return cursor.fetchone()[0]
    
    def close(self):
        """Close connection"""
        if hasattr(self._local, 'conn') and self._local.conn:
            self._local.conn.close()
            self._local.conn = None


import jieba
