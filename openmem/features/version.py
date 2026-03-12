"""
Version Control
Git-like version control for memory entries
"""

import sqlite3
import json
import hashlib
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class VersionType(Enum):
    """Version type enumeration"""
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"


@dataclass
class Version:
    """Version data structure"""
    version_id: int
    memory_id: int
    version_number: int
    version_type: VersionType
    content: str
    metadata: dict
    hash: str
    parent_hash: Optional[str]
    created_at: str
    message: Optional[str] = None


class VersionControl:
    """Git-like version control for memories"""
    
    def __init__(self, storage):
        self.storage = storage
        self._init_version_table()
    
    def _init_version_table(self):
        """Initialize version table"""
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_versions (
                version_id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id INTEGER NOT NULL,
                version_number INTEGER NOT NULL,
                version_type TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                hash TEXT NOT NULL,
                parent_hash TEXT,
                created_at TEXT NOT NULL,
                message TEXT,
                FOREIGN KEY (memory_id) REFERENCES memories(id)
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_versions_memory 
            ON memory_versions(memory_id)
        """)
        
        conn.commit()
    
    def commit(self, memory_id: int, version_type: VersionType = VersionType.PATCH,
              message: str = None) -> int:
        """Create a new version"""
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT content, metadata FROM memories WHERE id = ?", (memory_id,))
        row = cursor.fetchone()
        
        if not row:
            raise ValueError(f"Memory {memory_id} not found")
        
        content, metadata_json = row
        metadata = json.loads(metadata_json) if metadata_json else {}
        
        cursor.execute("""
            SELECT hash, version_number FROM memory_versions 
            WHERE memory_id = ? ORDER BY version_number DESC LIMIT 1
        """, (memory_id,))
        
        last_version = cursor.fetchone()
        parent_hash = last_version[0] if last_version else None
        version_number = last_version[1] + 1 if last_version else 1
        
        version_data = f"{content}{metadata_json}{version_number}"
        version_hash = hashlib.sha256(version_data.encode()).hexdigest()[:16]
        
        cursor.execute("""
            INSERT INTO memory_versions 
            (memory_id, version_number, version_type, content, metadata, 
             hash, parent_hash, created_at, message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (memory_id, version_number, version_type.value, content,
              metadata_json, version_hash, parent_hash, 
              datetime.now().isoformat(), message))
        
        cursor.execute("""
            UPDATE memories SET version = ?, updated_at = ? WHERE id = ?
        """, (version_number, datetime.now().isoformat(), memory_id))
        
        conn.commit()
        
        return cursor.lastrowid
    
    def get_versions(self, memory_id: int) -> List[Version]:
        """Get all versions of a memory"""
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT version_id, memory_id, version_number, version_type, 
                   content, metadata, hash, parent_hash, created_at, message
            FROM memory_versions
            WHERE memory_id = ?
            ORDER BY version_number DESC
        """, (memory_id,))
        
        rows = cursor.fetchall()
        
        versions = []
        for row in rows:
            versions.append(Version(
                version_id=row[0],
                memory_id=row[1],
                version_number=row[2],
                version_type=VersionType(row[3]),
                content=row[4],
                metadata=json.loads(row[5]) if row[5] else {},
                hash=row[6],
                parent_hash=row[7],
                created_at=row[8],
                message=row[9]
            ))
        
        return versions
    
    def diff(self, memory_id: int, v1: int, v2: int) -> Dict[str, Any]:
        """Compare two versions"""
        versions = self.get_versions(memory_id)
        
        v1_version = None
        v2_version = None
        
        for v in versions:
            if v.version_number == v1:
                v1_version = v
            if v.version_number == v2:
                v2_version = v
        
        if not v1_version or not v2_version:
            raise ValueError("Version not found")
        
        return {
            "v1": {
                "version": v1_version.version_number,
                "content": v1_version.content,
                "created_at": v1_version.created_at
            },
            "v2": {
                "version": v2_version.version_number,
                "content": v2_version.content,
                "created_at": v2_version.created_at
            },
            "diff": self._text_diff(v1_version.content, v2_version.content)
        }
    
    def _text_diff(self, text1: str, text2: str) -> str:
        """Simple text diff"""
        lines1 = text1.split('\n')
        lines2 = text2.split('\n')
        
        diff_lines = []
        
        for i, (l1, l2) in enumerate(zip(lines1, lines2)):
            if l1 != l2:
                diff_lines.append(f"Line {i+1}:")
                diff_lines.append(f"  - {l1}")
                diff_lines.append(f"  + {l2}")
        
        if len(lines1) > len(lines2):
            for i in range(len(lines2), len(lines1)):
                diff_lines.append(f"Line {i+1}: - {lines1[i]}")
        
        if len(lines2) > len(lines1):
            for i in range(len(lines1), len(lines2)):
                diff_lines.append(f"Line {i+1}: + {lines2[i]}")
        
        return '\n'.join(diff_lines) if diff_lines else "No changes"
    
    def rollback(self, memory_id: int, version_number: int) -> bool:
        """Rollback to a specific version"""
        versions = self.get_versions(memory_id)
        
        target_version = None
        for v in versions:
            if v.version_number == version_number:
                target_version = v
                break
        
        if not target_version:
            raise ValueError(f"Version {version_number} not found")
        
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE memories 
            SET content = ?, metadata = ?, updated_at = ?
            WHERE id = ?
        """, (target_version.content, json.dumps(target_version.metadata),
              datetime.now().isoformat(), memory_id))
        
        self.commit(memory_id, VersionType.PATCH, f"Rollback to v{version_number}")
        
        conn.commit()
        
        return True


if __name__ == "__main__":
    print("=" * 60)
    print("Version Control Test")
    print("=" * 60)
    print("Requires storage initialization")
    print("=" * 60)
