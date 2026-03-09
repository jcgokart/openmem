"""
Memory 存储层抽象接口
定义统一的存储后端接口，支持多实现切换
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class MemoryType(Enum):
    """记忆类型"""
    DECISION = "decision"
    MILESTONE = "milestone"
    ISSUE = "issue"
    KNOWLEDGE = "knowledge"
    ARCHIVE = "archive"
    SESSION = "session"
    LONGTERM = "longterm"
    WORK = "work"


@dataclass
class Memory:
    """记忆数据结构"""
    id: int
    type: str
    content: str
    metadata: Dict[str, Any] = None
    tags: List[str] = None
    priority: int = 0
    created_at: str = None
    updated_at: str = None
    expires_at: str = None
    version: int = 1


class MemoryBackend(ABC):
    """
    记忆存储抽象接口
    
    使用示例：
        class SQLiteMemory(MemoryBackend):
            def create(self, type, content, **kwargs):
                ...
        
        backend = SQLiteMemory(config)
        memory_id = backend.create("decision", "使用 JWT 认证")
    """
    
    @abstractmethod
    def create(self, type: str, content: str, 
               metadata: dict = None, tags: List[str] = None,
               priority: int = 0, expires_at: str = None) -> int:
        """
        创建记忆
        
        Args:
            type: 记忆类型
            content: 记忆内容
            metadata: 元数据
            tags: 标签
            priority: 优先级
            expires_at: 过期时间
        
        Returns:
            记忆 ID
        """
        pass
    
    @abstractmethod
    def read(self, memory_id: int) -> Optional[Dict[str, Any]]:
        """
        读取记忆
        
        Args:
            memory_id: 记忆 ID
        
        Returns:
            记忆字典，不存在返回 None
        """
        pass
    
    @abstractmethod
    def update(self, memory_id: int, content: str = None,
               metadata: dict = None, tags: List[str] = None,
               priority: int = None) -> bool:
        """
        更新记忆
        
        Args:
            memory_id: 记忆 ID
            content: 新内容
            metadata: 新元数据
            tags: 新标签
            priority: 新优先级
        
        Returns:
            是否成功
        """
        pass
    
    @abstractmethod
    def delete(self, memory_id: int) -> bool:
        """
        删除记忆
        
        Args:
            memory_id: 记忆 ID
        
        Returns:
            是否成功
        """
        pass
    
    @abstractmethod
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        全文搜索
        
        Args:
            query: 搜索关键词
            limit: 限制数量
        
        Returns:
            搜索结果列表
        """
        pass
    
    @abstractmethod
    def search_by_tags(self, tags: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        """
        按标签搜索
        
        Args:
            tags: 标签列表
            limit: 限制数量
        
        Returns:
            搜索结果列表
        """
        pass
    
    @abstractmethod
    def list_by_type(self, type: str, limit: int = 100, 
                    offset: int = 0) -> List[Dict[str, Any]]:
        """
        按类型列出记忆
        
        Args:
            type: 记忆类型
            limit: 限制数量
            offset: 偏移量
        
        Returns:
            记忆列表
        """
        pass
    
    @abstractmethod
    def get_messages_page(self, page: int = 0, page_size: int = 100,
                         memory_type: str = None) -> Dict[str, Any]:
        """
        分页获取记忆
        
        Args:
            page: 页码（从 0 开始）
            page_size: 每页大小
            memory_type: 类型过滤
        
        Returns:
            分页结果
        """
        pass
    
    @abstractmethod
    def get_memory_count(self) -> int:
        """
        获取记忆总数
        
        Returns:
            记忆数量
        """
        pass
    
    @abstractmethod
    def close(self):
        """
        关闭连接
        """
        pass
