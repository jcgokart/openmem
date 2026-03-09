"""
Memory 核心管理器
支持全局/项目分层，像 Poetry 一样灵活
"""

import os
from typing import List, Dict, Any, Optional

from memory.core.config import MemoryConfig
from memory.storage import SQLiteStorage


class MemoryManager:
    """
    Memory 核心管理器
    
    支持全局/项目分层：
    - 全局模式：所有项目共享 ~/.memory/
    - 项目模式：仅当前项目可用 .memory/
    - 混合模式：项目优先，没有则搜全局
    
    使用示例：
        # 自动选择（项目优先）
        memory = MemoryManager()
        
        # 明确指定项目
        memory = MemoryManager(project_path="/path/to/project")
        
        # 混合使用
        global_memory = MemoryManager()
    """
    
    def __init__(self, project_path: str = None, global_first: bool = False):
        """
        初始化 Memory 管理器
        
        Args:
            project_path: 项目路径，如果为 None 则使用全局
            global_first: 搜索时是否全局优先
        """
        self.project_path = project_path
        self.global_first = global_first
        
        if project_path:
            self.project_config = MemoryConfig(project_path=project_path)
            self.project_store = SQLiteStorage(self.project_config)
        else:
            self.project_config = None
            self.project_store = None
        
        self.global_config = MemoryConfig()
        self.global_store = SQLiteStorage(self.global_config)
    
    def add(self, content: str, type: str = "decision",
           tags: List[str] = None, metadata: dict = None,
           priority: int = 0, scope: str = "project") -> int:
        """添加记忆"""
        if scope == "global":
            return self.global_store.create(type, content, metadata, tags, priority)
        else:
            if self.project_store:
                return self.project_store.create(type, content, metadata, tags, priority)
            else:
                return self.global_store.create(type, content, metadata, tags, priority)
    
    def get(self, memory_id: int, scope: str = "project") -> Optional[Dict[str, Any]]:
        """获取记忆"""
        store = self._get_store(scope)
        return store.read(memory_id)
    
    def update(self, memory_id: int, content: str = None,
              metadata: dict = None, tags: List[str] = None,
              priority: int = None, scope: str = "project") -> bool:
        """更新记忆"""
        store = self._get_store(scope)
        return store.update(memory_id, content, metadata, tags, priority)
    
    def delete(self, memory_id: int, scope: str = "project") -> bool:
        """删除记忆"""
        store = self._get_store(scope)
        return store.delete(memory_id)
    
    def search(self, query: str, limit: int = 10, scope: str = "project") -> List[Dict[str, Any]]:
        """搜索记忆"""
        if scope == "both":
            return self._search_both(query, limit)
        
        store = self._get_store(scope)
        return store.search(query, limit)
    
    def _search_both(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """混合搜索（项目优先，没有则搜全局）"""
        if self.project_store:
            results = self.project_store.search(query, limit)
            if results:
                return results
        
        return self.global_store.search(query, limit)
    
    def search_by_tags(self, tags: List[str], limit: int = 10, 
                      scope: str = "project") -> List[Dict[str, Any]]:
        """按标签搜索"""
        store = self._get_store(scope)
        return store.search_by_tags(tags, limit)
    
    def list(self, type: str = None, limit: int = 100, 
            offset: int = 0, scope: str = "project") -> List[Dict[str, Any]]:
        """列出记忆"""
        store = self._get_store(scope)
        
        if type:
            return store.list_by_type(type, limit, offset)
        else:
            page_result = store.get_messages_page(
                page=offset // limit,
                page_size=limit
            )
            return page_result['messages']
    
    def page(self, page: int = 0, page_size: int = 20,
            memory_type: str = None, scope: str = "project") -> Dict[str, Any]:
        """分页获取"""
        store = self._get_store(scope)
        return store.get_messages_page(page, page_size, memory_type)
    
    def count(self, scope: str = "project") -> int:
        """获取记忆数量"""
        store = self._get_store(scope)
        return store.get_memory_count()
    
    def _get_store(self, scope: str):
        """获取存储后端"""
        if scope == "global":
            return self.global_store
        elif scope == "project":
            return self.project_store if self.project_store else self.global_store
        else:
            return self.global_store
    
    def close(self):
        """关闭连接"""
        if self.project_store:
            self.project_store.close()
        self.global_store.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
