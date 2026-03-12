"""
Memory Core Manager
Supports Global/Project layers, flexible like Poetry
"""

import os
import warnings
from typing import List, Dict, Any, Optional

from openmem.core.config import MemoryConfig
from openmem.storage import UnifiedStorage


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
            self.project_store = UnifiedStorage(
                db_path=self.project_config.get_db_path()
            )
        else:
            self.project_config = None
            self.project_store = None
        
        self.global_config = MemoryConfig()
        self.global_store = None
        if os.path.exists(self.global_config.memory_dir):
            self.global_store = UnifiedStorage(
                db_path=self.global_config.get_db_path()
            )
    
    def add(self, content: str, type: str = "decision",
           tags: List[str] = None, metadata: dict = None,
           priority: int = 0, scope: str = "project") -> int:
        """Add memory"""
        store = self._get_store(scope)
        return store.add_memory(
            content=content,
            memory_type=type,
            metadata=metadata,
            tags=tags,
            priority=priority
        )
    
    def get(self, memory_id: int, scope: str = "project") -> Optional[Dict[str, Any]]:
        """Get memory"""
        store = self._get_store(scope)
        return store.get_memory(memory_id)
    
    def update(self, memory_id: int, content: str = None,
              metadata: dict = None, tags: List[str] = None,
              priority: int = None, scope: str = "project") -> bool:
        """Update memory (returns True/False based on actual result)"""
        store = self._get_store(scope)
        update_kwargs = {}
        if content is not None:
            update_kwargs["content"] = content
        if metadata is not None:
            update_kwargs["metadata"] = metadata
        if tags is not None:
            update_kwargs["tags"] = tags
        if priority is not None:
            update_kwargs["priority"] = priority
        
        if update_kwargs:
            return store.update_memory(memory_id, **update_kwargs)
        return False
    
    def delete(self, memory_id: int, scope: str = "project") -> bool:
        """Delete memory (returns True/False based on actual result)"""
        store = self._get_store(scope)
        return store.delete_memory(memory_id)
    
    def list(self, type: str = None, scope: str = "project",
            tags: List[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """List memories"""
        store = self._get_store(scope)
        memories = store.list_memories(memory_type=type, limit=limit)
        
        if tags:
            memories = [m for m in memories if any(tag in m.get("tags", []) for tag in tags)]
        
        return memories
    
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
                project_results = self.project_store.search(query, limit)
                for r in project_results:
                    r["scope"] = "project"
                results.extend(project_results)
        
        if scope in ("global", "both"):
            if self.global_store:
                global_results = self.global_store.search(query, limit)
                for r in global_results:
                    r["scope"] = "global"
                results.extend(global_results)
        
        if tags:
            results = [r for r in results if any(tag in r.get("tags", []) for tag in tags)]
        
        return results[:limit]
    
    def search_by_tags(self, tags: List[str], scope: str = "both", limit: int = 10) -> List[Dict[str, Any]]:
        """Search by tags"""
        return self.search("", scope=scope, tags=tags, limit=limit)
    
    def page(self, page: int = 0, page_size: int = 20,
            scope: str = "project", type: str = None) -> Dict[str, Any]:
        """Paginate memories"""
        store = self._get_store(scope)
        offset = page * page_size
        memories = store.list_memories(
            memory_type=type, 
            limit=page_size, 
            offset=offset
        )
        total = store.get_memory_count()
        
        return {
            "messages": memories,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": (total + page_size - 1) // page_size if total > 0 else 0
        }
    
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
    
    def count(self, scope: str = "both") -> int:
        """Get total count of memories"""
        total = 0
        if scope in ("project", "both"):
            if self.project_store:
                total += self.project_store.get_memory_count()
        if scope in ("global", "both"):
            if self.global_store:
                total += self.global_store.get_memory_count()
        return total
    
    def _get_store(self, scope: str) -> UnifiedStorage:
        """Get storage by scope"""
        if scope == "global":
            if not self.global_store:
                raise ValueError("Global memory not initialized. Run 'omem init --global' first.")
            return self.global_store
        elif scope == "project":
            if not self.project_store:
                raise ValueError(
                    "Project memory not initialized. Run 'omem init' in your project directory first."
                )
            return self.project_store
        else:
            raise ValueError(f"Invalid scope: {scope}. Use 'project' or 'global'.")
    
    def close(self):
        """Close connections"""
        if self.project_store:
            self.project_store.close()
        if self.global_store:
            self.global_store.close()
