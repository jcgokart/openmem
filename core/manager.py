"""
Memory Core Manager
Supports Global/Project layers, flexible like Poetry
"""

import os
from typing import List, Dict, Any, Optional

from openmem.core.config import MemoryConfig
from openmem.storage import SQLiteStorage, SQLiteConfig


class MemoryManager:
    """
    Memory Core Manager
    
    Supports Global/Project layers:
    - Global mode: All projects share ~/.memory/
    - Project mode: Only current project available .memory/
    - Hybrid mode: Project first, fallback to global
    
    Usage:
        # Auto-select (project first)
        memory = MemoryManager()
        
        # Explicit project
        memory = MemoryManager(project_path="/path/to/project")
        
        # Hybrid
        global_memory = MemoryManager()
    """
    
    def _create_storage(self, config: MemoryConfig) -> SQLiteStorage:
        """Create SQLite storage from MemoryConfig"""
        storage_config = SQLiteConfig(
            db_path=config.get_db_path(),
            enable_fts=config.get_enable_fts(),
            wal_mode=config.get_wal_mode(),
            busy_timeout=config.get_busy_timeout()
        )
        return SQLiteStorage(storage_config)
    
    def __init__(self, project_path: str = None, global_first: bool = False):
        """
        Initialize Memory Manager
        
        Args:
            project_path: Project path, None for global
            global_first: Search global first
        """
        self.project_path = project_path
        self.global_first = global_first
        
        if project_path:
            self.project_config = MemoryConfig(project_path=project_path)
            self.project_store = self._create_storage(self.project_config)
        else:
            self.project_config = None
            self.project_store = None
        
        self.global_config = MemoryConfig()
        self.global_store = None
        if os.path.exists(self.global_config.memory_dir):
            self.global_store = self._create_storage(self.global_config)
    
    def add(self, content: str, type: str = "decision",
           tags: List[str] = None, metadata: dict = None,
           priority: int = 0, scope: str = "project") -> int:
        """Add memory"""
        if scope == "global":
            return self.global_store.create(type, content, metadata, tags, priority)
        else:
            if self.project_store:
                return self.project_store.create(type, content, metadata, tags, priority)
            else:
                return self.global_store.create(type, content, metadata, tags, priority)
    
    def get(self, memory_id: int, scope: str = "project") -> Optional[Dict[str, Any]]:
        """Get memory"""
        store = self._get_store(scope)
        return store.read(memory_id)
    
    def update(self, memory_id: int, content: str = None,
              metadata: dict = None, tags: List[str] = None,
              priority: int = None, scope: str = "project") -> bool:
        """Update memory"""
        store = self._get_store(scope)
        return store.update(memory_id, content, metadata, tags, priority)
    
    def delete(self, memory_id: int, scope: str = "project") -> bool:
        """Delete memory"""
        store = self._get_store(scope)
        return store.delete(memory_id)
    
    def list(self, type: str = None, scope: str = "project",
            tags: List[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """List memories"""
        store = self._get_store(scope)
        if tags:
            return store.search_by_tags(tags, limit)
        elif type:
            return store.list_by_type(type, limit)
        else:
            return store.list_by_type(None, limit)
    
    def search(self, query: str, scope: str = "both",
              tags: List[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search memories
        
        Args:
            query: Search keyword
            scope: project/global/both
            tags: Filter by tags
            limit: Result limit
        """
        results = []
        
        if scope in ("project", "both"):
            if self.project_store:
                if tags:
                    project_results = self.project_store.search_by_tags(tags, limit)
                else:
                    project_results = self.project_store.search(query, limit)
                for r in project_results:
                    r["scope"] = "project"
                results.extend(project_results)
        
        if scope in ("global", "both"):
            if self.global_store:
                if tags:
                    global_results = self.global_store.search_by_tags(tags, limit)
                else:
                    global_results = self.global_store.search(query, limit)
                for r in global_results:
                    r["scope"] = "global"
                results.extend(global_results)
        
        return results
    
    def search_by_tags(self, tags: List[str], scope: str = "both", limit: int = 10) -> List[Dict[str, Any]]:
        """Search by tags"""
        return self.search("", scope=scope, tags=tags, limit=limit)
    
    def page(self, page: int = 0, page_size: int = 20,
            scope: str = "project", type: str = None) -> Dict[str, Any]:
        """Paginate memories"""
        store = self._get_store(scope)
        return store.get_messages_page(page, page_size, type)
    
    def get_stats(self, scope: str = "both") -> Dict[str, Any]:
        """Get statistics"""
        stats = {"total": 0, "by_type": {}, "by_scope": {}}
        
        if scope in ("project", "both"):
            if self.project_store:
                project_stats = self.project_store.get_stats()
                stats["by_scope"]["project"] = project_stats
                stats["total"] += project_stats["total"]
                stats["by_type"].update(project_stats.get("by_type", {}))
        
        if scope in ("global", "both"):
            if self.global_store:
                global_stats = self.global_store.get_stats()
                stats["by_scope"]["global"] = global_stats
                stats["total"] += global_stats["total"]
                stats["by_type"].update(global_stats.get("by_type", {}))
        
        return stats
    
    def _get_store(self, scope: str):
        """Get storage by scope"""
        if scope == "global":
            if not self.global_store:
                raise ValueError("Global memory not initialized")
            return self.global_store
        else:
            if not self.project_store:
                if not self.global_store:
                    raise ValueError("No memory initialized")
                return self.global_store
            return self.project_store
    
    def close(self):
        """Close connections"""
        if self.project_store:
            self.project_store.close()
        if self.global_store:
            self.global_store.close()
