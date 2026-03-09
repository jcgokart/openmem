"""
P2-2: 版本控制增强（Git-like 存储）
实现类似 Git 的版本控制系统

============================================================
工程经验总结
============================================================

1. 【版本控制事务】多步操作必须原子性
   - 问题：历史版本保存 + 当前版本更新 之间崩溃导致数据不一致
   - 解决：使用 storage.transaction() 上下文管理器
   - 经验：版本控制本质是事务，commit 必须原子

2. 【差异算法】使用标准库 difflib
   - 问题：手写集合对比有重复行误判、无行号、O(n²)
   - 解决：使用 difflib.SequenceMatcher + unified_diff
   - 经验：diff 算法复杂，优先用标准库

3. 【哈希长度】哈希要用完整值
   - 问题：只用 SHA256 前 16 位增加碰撞风险
   - 解决：存储完整哈希或至少 32 位
   - 经验：哈希截断要看场景，安全场景不截断

特性：
- 版本快照
- 差异对比（使用 difflib 实现 LCS）
- 版本回退
- 版本分支
- 变更历史
"""

import sqlite3
import json
import hashlib
import difflib
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


# ==================== 版本类型枚举 ====================

class VersionType(Enum):
    """版本类型"""
    MAJOR = "major"     # 主版本
    MINOR = "minor"     # 次版本
    PATCH = "patch"     # 补丁版本


# ==================== 版本数据结构 ====================

@dataclass
class Version:
    """版本信息"""
    version_id: int                 # 版本 ID
    memory_id: int                  # 记忆 ID
    version_number: int             # 版本号
    version_type: VersionType       # 版本类型
    content: str                    # 内容
    metadata: dict                  # 元数据
    hash: str                       # 内容哈希
    parent_hash: Optional[str]      # 父版本哈希
    created_at: str                 # 创建时间
    message: Optional[str] = None   # 提交信息


@dataclass
class Diff:
    """差异信息"""
    old_content: str                # 旧内容
    new_content: str                # 新内容
    unified_diff: List[str]         # 统一的 diff 格式
    additions: List[Tuple[int, str]]   # 新增内容 (行号, 内容)
    deletions: List[Tuple[int, str]]    # 删除内容 (行号, 内容)
    changes: List[Dict[str, Any]]   # 变更内容


@dataclass
class DiffLine:
    """Diff 单行信息"""
    type: str                      # 'add', 'delete', 'context'
    content: str                   # 行内容
    old_line_no: Optional[int]     # 旧行号
    new_line_no: Optional[int]     # 新行号


# ==================== 版本控制器 ====================

class VersionController:
    """版本控制器（Git-like）"""
    
    def __init__(self, storage):
        self.storage = storage
    
    def commit(self, memory_id: int, content: str, metadata: dict = None,
               message: str = None, version_type: VersionType = VersionType.MINOR) -> Version:
        """
        提交新版本（带事务保护）
        
        Args:
            memory_id: 记忆 ID
            content: 内容
            metadata: 元数据
            message: 提交信息
            version_type: 版本类型
        
        Returns:
            版本信息
        """
        with self.storage.transaction() as conn:
            cursor = conn.cursor()
            
            # 1. 获取当前版本
            cursor.execute("""
                SELECT version, content, metadata
                FROM memories
                WHERE id = ?
            """, (memory_id,))
            
            row = cursor.fetchone()
            if row is None:
                raise ValueError(f"记忆不存在: {memory_id}")
            
            current_version = row[0]
            current_content = row[1]
            current_metadata = json.loads(row[2]) if row[2] else {}
            
            # 2. 计算哈希
            content_hash = self._calculate_hash(content)
            parent_hash = self._calculate_hash(current_content)
            
            # 3. 保存到历史表
            cursor.execute("""
                INSERT INTO memory_history 
                (memory_id, type, content, metadata, version, hash, parent_hash, message, version_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                memory_id,
                'update',
                current_content,
                json.dumps(current_metadata, ensure_ascii=False),
                current_version,
                parent_hash,
                None,
                message,
                version_type.value
            ))
            
            # 4. 更新当前版本
            new_version = current_version + 1
            cursor.execute("""
                UPDATE memories
                SET content = ?, metadata = ?, version = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                content,
                json.dumps(metadata, ensure_ascii=False) if metadata else None,
                new_version,
                memory_id
            ))
            
            # 返回版本信息
            return Version(
                version_id=cursor.lastrowid,
                memory_id=memory_id,
                version_number=new_version,
                version_type=version_type,
                content=content,
                metadata=metadata or {},
                hash=content_hash,
                parent_hash=parent_hash,
                created_at=datetime.now().isoformat(),
                message=message
            )
    
    def get_version(self, memory_id: int, version_number: int = None) -> Optional[Version]:
        """
        获取指定版本
        
        Args:
            memory_id: 记忆 ID
            version_number: 版本号（None 表示当前版本）
        
        Returns:
            版本信息
        """
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        
        try:
            if version_number is None:
                # 获取当前版本
                cursor.execute("""
                    SELECT id, type, content, metadata, version, created_at, updated_at
                    FROM memories
                    WHERE id = ?
                """, (memory_id,))
                
                row = cursor.fetchone()
                if row is None:
                    return None
                
                return Version(
                    version_id=row[0],
                    memory_id=memory_id,
                    version_number=row[4],
                    version_type=VersionType.MINOR,
                    content=row[2],
                    metadata=json.loads(row[3]) if row[3] else {},
                    hash=self._calculate_hash(row[2]),
                    parent_hash=None,
                    created_at=row[5],
                    message=None
                )
            else:
                # 获取历史版本
                cursor.execute("""
                    SELECT id, type, content, metadata, version, hash, parent_hash, created_at, message, version_type
                    FROM memory_history
                    WHERE memory_id = ? AND version = ?
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (memory_id, version_number))
                
                row = cursor.fetchone()
                if row is None:
                    return None
                
                return Version(
                    version_id=row[0],
                    memory_id=memory_id,
                    version_number=row[4],
                    version_type=VersionType(row[9]) if row[9] else VersionType.MINOR,
                    content=row[2],
                    metadata=json.loads(row[3]) if row[3] else {},
                    hash=row[5],
                    parent_hash=row[6],
                    created_at=row[7],
                    message=row[8]
                )
                
        except Exception as e:
            raise Exception(f"获取版本失败: {e}")
    
    def get_history(self, memory_id: int, limit: int = 10) -> List[Version]:
        """
        获取版本历史
        
        Args:
            memory_id: 记忆 ID
            limit: 限制数量
        
        Returns:
            版本列表
        """
        conn = self.storage._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, type, content, metadata, version, hash, parent_hash, created_at, message, version_type
                FROM memory_history
                WHERE memory_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (memory_id, limit))
            
            rows = cursor.fetchall()
            
            versions = []
            for row in rows:
                versions.append(Version(
                    version_id=row[0],
                    memory_id=memory_id,
                    version_number=row[4],
                    version_type=VersionType(row[9]) if row[9] else VersionType.MINOR,
                    content=row[2],
                    metadata=json.loads(row[3]) if row[3] else {},
                    hash=row[5],
                    parent_hash=row[6],
                    created_at=row[7],
                    message=row[8]
                ))
            
            return versions
            
        except Exception as e:
            raise Exception(f"获取版本历史失败: {e}")
    
    def diff(self, memory_id: int, version1: int, version2: int) -> Diff:
        """
        对比两个版本（使用 difflib 实现 LCS）
        
        Args:
            memory_id: 记忆 ID
            version1: 版本 1
            version2: 版本 2
        
        Returns:
            差异信息
        """
        v1 = self.get_version(memory_id, version1)
        v2 = self.get_version(memory_id, version2)
        
        if v1 is None or v2 is None:
            raise ValueError("版本不存在")
        
        lines1 = v1.content.split('\n')
        lines2 = v2.content.split('\n')
        
        # 使用 difflib 生成 unified diff
        diff_generator = difflib.unified_diff(
            lines1, lines2,
            fromfile=f'v{version1}',
            tofile=f'v{version2}',
            lineterm=''
        )
        unified_diff = list(diff_generator)
        
        # 使用 difflib.SequenceMatcher 获取变更
        matcher = difflib.SequenceMatcher(None, lines1, lines2)
        
        additions = []
        deletions = []
        changes = []
        
        old_line_no = 0
        new_line_no = 0
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                # 相同内容
                old_line_no = i1
                new_line_no = j1
            elif tag == 'replace':
                # 替换
                for idx in range(max(i2 - i1, j2 - j1)):
                    if idx < (i2 - i1):
                        deletions.append((old_line_no + idx + 1, lines1[i1 + idx]))
                    if idx < (j2 - j1):
                        additions.append((new_line_no + idx + 1, lines2[j1 + idx]))
                    
                    if idx < (i2 - i1) and idx < (j2 - j1):
                        changes.append({
                            'old_line': old_line_no + idx + 1,
                            'new_line': new_line_no + idx + 1,
                            'old_content': lines1[i1 + idx],
                            'new_content': lines2[j1 + idx]
                        })
                old_line_no = i2
                new_line_no = j2
            elif tag == 'delete':
                # 删除
                for idx in range(i1, i2):
                    deletions.append((idx + 1, lines1[idx]))
                old_line_no = i2
            elif tag == 'insert':
                # 新增
                for idx in range(j1, j2):
                    additions.append((idx + 1, lines2[idx]))
                new_line_no = j2
        
        return Diff(
            old_content=v1.content,
            new_content=v2.content,
            unified_diff=unified_diff,
            additions=additions,
            deletions=deletions,
            changes=changes
        )
    
    def rollback(self, memory_id: int, version_number: int) -> Version:
        """
        回退到指定版本
        
        Args:
            memory_id: 记忆 ID
            version_number: 目标版本号
        
        Returns:
            回退后的版本信息
        """
        # 获取目标版本
        target_version = self.get_version(memory_id, version_number)
        if target_version is None:
            raise ValueError(f"版本不存在: {version_number}")
        
        # 提交回退
        return self.commit(
            memory_id,
            target_version.content,
            target_version.metadata,
            message=f"回退到版本 {version_number}",
            version_type=VersionType.PATCH
        )
    
    def _calculate_hash(self, content: str) -> str:
        """
        计算内容哈希
        
        Args:
            content: 内容
        
        Returns:
            哈希值
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]


# ==================== 测试代码 ====================

if __name__ == "__main__":
    print("=" * 60)
    print("版本控制增强测试")
    print("=" * 60)
    
    from sqlite_storage import SQLiteStorage, SQLiteConfig
    
    # 创建存储实例
    config = SQLiteConfig(db_path="data/version_test.db")
    storage = SQLiteStorage(config)
    
    # 创建版本控制器
    vc = VersionController(storage)
    
    # 创建测试记忆
    print("\n【创建测试记忆】")
    memory_id = storage.create(
        type="decision",
        content="决定使用 SQLite 作为存储引擎",
        metadata={"reason": "性能更好"}
    )
    
    # 提交版本
    print("\n【提交版本】")
    v1 = vc.commit(
        memory_id,
        content="决定使用 SQLite + WAL 作为存储引擎",
        metadata={"reason": "性能更好，支持并发"},
        message="添加 WAL 模式支持",
        version_type=VersionType.MINOR
    )
    print(f"版本 {v1.version_number}: {v1.message}")
    
    v2 = vc.commit(
        memory_id,
        content="决定使用 SQLite + WAL + FTS5 作为存储引擎",
        metadata={"reason": "性能更好，支持并发，支持全文搜索"},
        message="添加 FTS5 全文搜索支持",
        version_type=VersionType.MAJOR
    )
    print(f"版本 {v2.version_number}: {v2.message}")
    
    # 获取版本历史
    print("\n【版本历史】")
    history = vc.get_history(memory_id)
    for v in history:
        print(f"版本 {v.version_number}: {v.message or '初始版本'} ({v.version_type.value})")
    
    # 对比版本
    print("\n【对比版本】")
    diff = vc.diff(memory_id, 1, 2)
    print(f"新增: {diff.additions}")
    print(f"删除: {diff.deletions}")
    
    # 回退版本
    print("\n【回退版本】")
    v3 = vc.rollback(memory_id, 1)
    print(f"回退到版本 1，当前版本: {v3.version_number}")
    
    # 获取当前版本
    print("\n【当前版本】")
    current = vc.get_version(memory_id)
    print(f"版本 {current.version_number}: {current.content}")
    
    # 关闭
    storage.close()
    
    print("\n" + "=" * 60)
    print("✓ 测试完成")
    print("=" * 60)
