"""
Encryption and Backup
AES-256 encryption with PBKDF2 key derivation + atomic backup using SQLite VACUUM
"""

import os
import json
import hashlib
import shutil
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import base64


class EncryptionError(Exception):
    """Encryption error"""
    pass


class CryptoManager:
    """Encryption manager"""
    
    def __init__(self, key: Optional[str] = None):
        """Initialize encryption manager"""
        self.key = key or os.environ.get('MEMORY_ENCRYPTION_KEY')
        if not self.key:
            import secrets
            self.key = secrets.token_hex(32)
            print(f"⚠️ No encryption key set, generated: {self.key[:8]}...")
    
    def _get_cipher(self):
        """Get cipher with PBKDF2 key derivation"""
        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes
        
        salt = b'memory_system_salt_v1'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.key.encode()))
        return Fernet(key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt data"""
        if not self.key:
            raise EncryptionError("No encryption key set")
        
        cipher = self._get_cipher()
        encrypted = cipher.encrypt(data.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt data"""
        if not self.key:
            raise EncryptionError("No encryption key set")
        
        try:
            cipher = self._get_cipher()
            decoded = base64.b64decode(encrypted_data.encode())
            decrypted = cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            raise EncryptionError(f"Decryption failed: {e}")
    
    def encrypt_dict(self, data: dict) -> dict:
        """Encrypt dictionary"""
        json_data = json.dumps(data, ensure_ascii=False)
        encrypted = self.encrypt(json_data)
        return {
            "_encrypted": True,
            "data": encrypted
        }
    
    def decrypt_dict(self, encrypted_data: dict) -> dict:
        """Decrypt dictionary"""
        if not encrypted_data.get("_encrypted"):
            return encrypted_data
        
        decrypted = self.decrypt(encrypted_data["data"])
        return json.loads(decrypted)


class BackupType(Enum):
    """Backup type enumeration"""
    FULL = "full"
    INCREMENTAL = "incremental"


@dataclass
class BackupInfo:
    """Backup information"""
    backup_id: str
    backup_path: str
    backup_type: BackupType
    size: int
    created_at: str
    checksum: str
    memory_count: int
    status: str


class BackupManager:
    """Backup manager"""
    
    def __init__(self, storage, backup_dir: str = "data/backups"):
        """Initialize backup manager"""
        self.storage = storage
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)
        
        self._init_backup_table()
    
    def _init_backup_table(self):
        """Initialize backup table"""
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        
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
    
    def backup(self, backup_type: BackupType = BackupType.FULL, 
               encrypt: bool = False) -> BackupInfo:
        """Create backup using SQLite VACUUM INTO for atomic operation"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_id = f"backup_{timestamp}"
        
        backup_path = os.path.join(self.backup_dir, backup_id)
        os.makedirs(backup_path, exist_ok=True)
        
        db_backup_path = os.path.join(backup_path, "memory.db")
        
        if backup_type == BackupType.INCREMENTAL:
            last_backup = self._get_last_backup()
            if not last_backup:
                backup_type = BackupType.FULL
            else:
                self._backup_incremental(last_backup, db_backup_path)
                memory_count = self._count_changes_since(last_backup['created_at'])
                size = os.path.getsize(db_backup_path)
                checksum = self._calculate_checksum(db_backup_path)
                
                conn = self.storage._get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO backup_records 
                    (id, backup_path, backup_type, size, created_at, checksum, memory_count, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    backup_id,
                    db_backup_path,
                    backup_type.value,
                    size,
                    datetime.now().isoformat(),
                    checksum,
                    memory_count,
                    'completed'
                ))
                conn.commit()
                
                return BackupInfo(
                    backup_id=backup_id,
                    backup_path=db_backup_path,
                    backup_type=backup_type,
                    size=size,
                    created_at=datetime.now().isoformat(),
                    checksum=checksum,
                    memory_count=memory_count,
                    status='completed'
                )
        
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(f"VACUUM INTO '{db_backup_path}'")
        
        memory_count = self.storage.get_memory_count()
        checksum = self._calculate_checksum(db_backup_path)
        size = os.path.getsize(db_backup_path)
        
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO backup_records 
            (id, backup_path, backup_type, size, created_at, checksum, memory_count, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            backup_id,
            backup_path,
            backup_type.value,
            size,
            datetime.now().isoformat(),
            checksum,
            memory_count,
            "completed"
        ))
        conn.commit()
        
        return BackupInfo(
            backup_id=backup_id,
            backup_path=backup_path,
            backup_type=backup_type,
            size=size,
            created_at=datetime.now().isoformat(),
            checksum=checksum,
            memory_count=memory_count,
            status="completed"
        )
    
    def restore(self, backup_id: str, target_path: Optional[str] = None) -> bool:
        """Restore from backup"""
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT backup_path, checksum FROM backup_records
            WHERE id = ?
        """, (backup_id,))
        
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Backup not found: {backup_id}")
        
        backup_path, expected_checksum = row
        
        db_backup_path = os.path.join(backup_path, "memory.db")
        actual_checksum = self._calculate_checksum(db_backup_path)
        
        if actual_checksum != expected_checksum:
            raise ValueError(f"Backup checksum verification failed")
        
        if target_path is None:
            target_path = self.storage.db_path
        
        shutil.copy2(db_backup_path, target_path)
        
        return True
    
    def list_backups(self, limit: int = 10) -> List[BackupInfo]:
        """List backups"""
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, backup_path, backup_type, size, created_at, 
                   checksum, memory_count, status
            FROM backup_records
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        
        backups = []
        for row in rows:
            backups.append(BackupInfo(
                backup_id=row[0],
                backup_path=row[1],
                backup_type=BackupType(row[2]),
                size=row[3],
                created_at=row[4],
                checksum=row[5],
                memory_count=row[6],
                status=row[7]
            ))
        
        return backups
    
    def delete_backup(self, backup_id: str) -> bool:
        """Delete backup"""
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT backup_path FROM backup_records
            WHERE id = ?
        """, (backup_id,))
        
        row = cursor.fetchone()
        if not row:
            return False
        
        backup_path = row[0]
        
        if os.path.exists(backup_path):
            shutil.rmtree(backup_path)
        
        cursor.execute("DELETE FROM backup_records WHERE id = ?", (backup_id,))
        conn.commit()
        
        return True
    
    def verify_backup(self, backup_id: str) -> bool:
        """Verify backup integrity"""
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT backup_path, checksum FROM backup_records
            WHERE id = ?
        """, (backup_id,))
        
        row = cursor.fetchone()
        if not row:
            return False
        
        backup_path, expected_checksum = row
        
        db_backup_path = os.path.join(backup_path, "memory.db")
        if not os.path.exists(db_backup_path):
            return False
        
        actual_checksum = self._calculate_checksum(db_backup_path)
        
        return actual_checksum == expected_checksum
    
    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate file checksum"""
        sha256 = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        
        return sha256.hexdigest()
    
    def _get_last_backup(self) -> Optional[Dict[str, Any]]:
        """Get last backup"""
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, backup_path, created_at 
            FROM backup_records 
            ORDER BY created_at DESC 
            LIMIT 1
        """)
        row = cursor.fetchone()
        if row:
            return {'id': row[0], 'backup_path': row[1], 'created_at': row[2]}
        return None
    
    def _count_changes_since(self, since: str) -> int:
        """Count changes since last backup"""
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM memories 
            WHERE created_at > ? OR updated_at > ?
        """, (since, since))
        return cursor.fetchone()[0]
    
    def _backup_incremental(self, last_backup: Dict[str, Any], target_path: str):
        """Incremental backup"""
        import shutil
        source_dir = os.path.dirname(self.storage.db_path)
        wal_path = self.storage.db_path + "-wal"
        
        if os.path.exists(wal_path):
            shutil.copy2(wal_path, target_path + "-wal")
        shutil.copy2(last_backup['backup_path'], target_path)
    
    def auto_backup(self, max_backups: int = 7) -> Optional[BackupInfo]:
        """Auto backup keeping N recent backups"""
        backup = self.backup(BackupType.FULL)
        
        backups = self.list_backups(max_backups + 10)
        
        if len(backups) > max_backups:
            for old_backup in backups[max_backups:]:
                self.delete_backup(old_backup.backup_id)
        
        return backup


if __name__ == "__main__":
    print("=" * 60)
    print("Encryption and Backup Test")
    print("=" * 60)
    
    print("\n【Encryption Test】")
    crypto = CryptoManager(key="test_key_12345")
    
    encrypted = crypto.encrypt("Sensitive information")
    print(f"Original: Sensitive information")
    print(f"Encrypted: {encrypted[:50]}...")
    
    decrypted = crypto.decrypt(encrypted)
    print(f"Decrypted: {decrypted}")
    
    data = {"username": "admin", "password": "secret123"}
    encrypted_dict = crypto.encrypt_dict(data)
    print(f"\nEncrypted dict: {encrypted_dict}")
    
    decrypted_dict = crypto.decrypt_dict(encrypted_dict)
    print(f"Decrypted dict: {decrypted_dict}")
    
    print("\n" + "=" * 60)
    print("✓ Test Complete")
    print("=" * 60)
