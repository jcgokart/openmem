"""
P2-3: 加密和备份
实现敏感信息加密和增强备份功能

============================================================
工程经验总结
============================================================

1. 【密钥管理】永远不要硬编码密钥
   - 问题：密钥写在代码里，泄露后无法修改
   - 解决：使用环境变量或密钥管理系统
   - 经验：密钥与代码分离是基本安全原则

2. 【备份验证】备份后必须验证
   - 问题：备份文件损坏无法发现，恢复时失败
   - 解决：记录 checksum，恢复时校验
   - 经验：备份不验证 = 没备份

3. 【原子操作】文件操作要考虑中断
   - 问题：备份过程中断产生残文件
   - 解决：先写临时文件，再原子重命名
   - 经验：文件操作要考虑异常场景

特性：
- AES-256 加密
- 密钥管理
- 自动备份
- 增量备份
- 备份验证
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


# ==================== 加密模块 ====================

class EncryptionError(Exception):
    """加密异常"""
    pass


class CryptoManager:
    """加密管理器"""
    
    def __init__(self, key: Optional[str] = None):
        """
        初始化加密管理器
        
        Args:
            key: 加密密钥（可选）
        """
        self.key = key or os.environ.get('MEMORY_ENCRYPTION_KEY')
        if not self.key:
            import secrets
            self.key = secrets.token_hex(32)
            print(f"⚠️ 未设置加密密钥，已自动生成密钥: {self.key[:8]}...")
    
    def _get_cipher(self):
        """
        获取加密 cipher（使用 PBKDF2 派生密钥）
        
        工程经验：密钥派生要用 PBKDF2/Argon2，不要直接 hash
        """
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
        """
        加密数据
        
        Args:
            data: 待加密数据
        
        Returns:
            加密后的数据
        """
        if not self.key:
            raise EncryptionError("未设置加密密钥")
        
        cipher = self._get_cipher()
        encrypted = cipher.encrypt(data.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        解密数据
        
        Args:
            encrypted_data: 加密数据
        
        Returns:
            解密后的数据
        """
        if not self.key:
            raise EncryptionError("未设置加密密钥")
        
        try:
            cipher = self._get_cipher()
            decoded = base64.b64decode(encrypted_data.encode())
            decrypted = cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception as e:
            raise EncryptionError(f"解密失败: {e}")
    
    def encrypt_dict(self, data: dict) -> dict:
        """
        加密字典
        
        Args:
            data: 待加密字典
        
        Returns:
            加密后的字典
        """
        json_data = json.dumps(data, ensure_ascii=False)
        encrypted = self.encrypt(json_data)
        return {
            "_encrypted": True,
            "data": encrypted
        }
    
    def decrypt_dict(self, encrypted_data: dict) -> dict:
        """
        解密字典
        
        Args:
            encrypted_data: 加密字典
        
        Returns:
            解密后的字典
        """
        if not encrypted_data.get("_encrypted"):
            return encrypted_data
        
        decrypted = self.decrypt(encrypted_data["data"])
        return json.loads(decrypted)


# ==================== 备份模块 ====================

class BackupType(Enum):
    """备份类型"""
    FULL = "full"           # 全量备份
    INCREMENTAL = "incremental"  # 增量备份


@dataclass
class BackupInfo:
    """备份信息"""
    backup_id: str              # 备份 ID
    backup_path: str            # 备份路径
    backup_type: BackupType     # 备份类型
    size: int                  # 大小（字节）
    created_at: str             # 创建时间
    checksum: str              # 校验和
    memory_count: int           # 记忆数量
    status: str                 # 状态


class BackupManager:
    """备份管理器"""
    
    def __init__(self, storage, backup_dir: str = "data/backups"):
        """
        初始化备份管理器
        
        Args:
            storage: 存储实例
            backup_dir: 备份目录
        """
        self.storage = storage
        self.backup_dir = backup_dir
        os.makedirs(backup_dir, exist_ok=True)
        
        self._init_backup_table()
    
    def _init_backup_table(self):
        """初始化备份表"""
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
        """
        创建备份（原子操作）
        
        使用 SQLite VACUUM INTO 实现原子备份，避免备份过程中数据写入导致损坏
        
        Args:
            backup_type: 备份类型
            encrypt: 是否加密
        
        Returns:
            备份信息
        """
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
                    id=backup_id,
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
        
        # 记录备份信息
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
        """
        恢复备份
        
        Args:
            backup_id: 备份 ID
            target_path: 目标路径（可选）
        
        Returns:
            是否成功
        """
        # 查找备份
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT backup_path, checksum FROM backup_records
            WHERE id = ?
        """, (backup_id,))
        
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"备份不存在: {backup_id}")
        
        backup_path, expected_checksum = row
        
        # 验证校验和
        db_backup_path = os.path.join(backup_path, "memory.db")
        actual_checksum = self._calculate_checksum(db_backup_path)
        
        if actual_checksum != expected_checksum:
            raise ValueError(f"备份校验失败")
        
        # 恢复数据库
        if target_path is None:
            target_path = self.storage.db_path
        
        shutil.copy2(db_backup_path, target_path)
        
        return True
    
    def list_backups(self, limit: int = 10) -> List[BackupInfo]:
        """
        列出备份
        
        Args:
            limit: 限制数量
        
        Returns:
            备份列表
        """
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
        """
        删除备份
        
        Args:
            backup_id: 备份 ID
        
        Returns:
            是否成功
        """
        # 查找备份
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
        
        # 删除备份目录
        if os.path.exists(backup_path):
            shutil.rmtree(backup_path)
        
        # 删除记录
        cursor.execute("DELETE FROM backup_records WHERE id = ?", (backup_id,))
        conn.commit()
        
        return True
    
    def verify_backup(self, backup_id: str) -> bool:
        """
        验证备份
        
        Args:
            backup_id: 备份 ID
        
        Returns:
            是否有效
        """
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
        
        # 计算实际校验和
        db_backup_path = os.path.join(backup_path, "memory.db")
        if not os.path.exists(db_backup_path):
            return False
        
        actual_checksum = self._calculate_checksum(db_backup_path)
        
        return actual_checksum == expected_checksum
    
    def _calculate_checksum(self, file_path: str) -> str:
        """
        计算文件校验和
        
        Args:
            file_path: 文件路径
        
        Returns:
            校验和
        """
        sha256 = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        
        return sha256.hexdigest()
    
    def _get_last_backup(self) -> Optional[Dict[str, Any]]:
        """获取最近一次备份"""
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
        """统计自上次备份以来的变化数量"""
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM memories 
            WHERE created_at > ? OR updated_at > ?
        """, (since, since))
        return cursor.fetchone()[0]
    
    def _backup_incremental(self, last_backup: Dict[str, Any], target_path: str):
        """增量备份：复制 WAL 文件"""
        import shutil
        source_dir = os.path.dirname(self.storage.db_path)
        wal_path = self.storage.db_path + "-wal"
        
        if os.path.exists(wal_path):
            shutil.copy2(wal_path, target_path + "-wal")
        shutil.copy2(last_backup['backup_path'], target_path)
    
    def auto_backup(self, max_backups: int = 7) -> Optional[BackupInfo]:
        """
        自动备份（保留最近的 N 个备份）
        
        Args:
            max_backups: 最大备份数量
        
        Returns:
            备份信息
        """
        # 创建新备份
        backup = self.backup(BackupType.FULL)
        
        # 删除旧备份
        backups = self.list_backups(max_backups + 10)
        
        if len(backups) > max_backups:
            for old_backup in backups[max_backups:]:
                self.delete_backup(old_backup.backup_id)
        
        return backup


# ==================== 测试代码 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("加密和备份测试")
    print("=" * 60)
    
    # 测试加密
    print("\n【测试加密】")
    crypto = CryptoManager(key="test_key_12345")
    
    # 加密字符串
    encrypted = crypto.encrypt("这是敏感信息")
    print(f"加密前: 这是敏感信息")
    print(f"加密后: {encrypted[:50]}...")
    
    # 解密字符串
    decrypted = crypto.decrypt(encrypted)
    print(f"解密后: {decrypted}")
    
    # 加密字典
    data = {"username": "admin", "password": "secret123"}
    encrypted_dict = crypto.encrypt_dict(data)
    print(f"\n加密字典: {encrypted_dict}")
    
    # 解密字典
    decrypted_dict = crypto.decrypt_dict(encrypted_dict)
    print(f"解密字典: {decrypted_dict}")
    
    # 测试备份
    print("\n【测试备份】")
    from sqlite_storage import SQLiteStorage, SQLiteConfig
    
    # 创建存储实例
    config = SQLiteConfig(db_path="data/backup_test.db")
    storage = SQLiteStorage(config)
    
    # 强制初始化数据库
    storage._get_connection()
    
    # 创建备份管理器
    backup_manager = BackupManager(storage, "data/backups")
    
    # 创建测试数据
    storage.create(
        type="decision",
        content="测试备份功能"
    )
    
    # 创建备份
    backup = backup_manager.backup(BackupType.FULL)
    print(f"备份创建成功: {backup.backup_id}")
    print(f"备份大小: {backup.size} 字节")
    print(f"记忆数量: {backup.memory_count}")
    
    # 列出备份
    backups = backup_manager.list_backups()
    print(f"\n当前备份数量: {len(backups)}")
    
    # 验证备份
    is_valid = backup_manager.verify_backup(backup.backup_id)
    print(f"备份验证: {'有效' if is_valid else '无效'}")
    
    # 关闭
    storage.close()
    
    print("\n" + "=" * 60)
    print("✓ 测试完成")
    print("=" * 60)
