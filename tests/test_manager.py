"""
Tests for MemoryManager
"""

import os
import tempfile
import shutil
import pytest

from core.manager import MemoryManager
from core.config import MemoryConfig


class TestMemoryManager:
    """Test MemoryManager"""
    
    @pytest.fixture
    def temp_project(self):
        tmpdir = tempfile.mkdtemp()
        yield tmpdir
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    def test_init_global(self):
        """Test global init"""
        manager = MemoryManager()
        assert manager.global_config is not None
    
    def test_init_project(self, temp_project):
        """Test project init"""
        manager = MemoryManager(project_path=temp_project)
        assert manager.project_config is not None
        assert manager.project_store is not None
    
    def test_add_memory(self, temp_project):
        """Test add memory"""
        manager = MemoryManager(project_path=temp_project)
        
        memory_id = manager.add(
            content="Test decision",
            type="decision",
            tags=["test"]
        )
        
        assert memory_id is not None
        assert memory_id > 0
        
        manager.close()
    
    def test_get_memory(self, temp_project):
        """Test get memory"""
        manager = MemoryManager(project_path=temp_project)
        
        memory_id = manager.add(
            content="Test content",
            type="knowledge"
        )
        
        memory = manager.get(memory_id)
        assert memory is not None
        assert memory["content"] == "Test content"
        
        manager.close()
    
    def test_search_memory(self, temp_project):
        """Test search memory"""
        manager = MemoryManager(project_path=temp_project)
        
        manager.add(content="Python is great", type="knowledge")
        manager.add(content="JavaScript is also good", type="knowledge")
        
        results = manager.search("Python")
        assert len(results) >= 1
        assert "Python" in results[0]["content"]
        
        manager.close()
    
    def test_list_memories(self, temp_project):
        """Test list memories"""
        manager = MemoryManager(project_path=temp_project)
        
        manager.add(content="Memory 1", type="decision")
        manager.add(content="Memory 2", type="knowledge")
        
        memories = manager.list()
        assert len(memories) >= 2
        
        manager.close()
    
    def test_delete_memory(self, temp_project):
        """Test delete memory"""
        manager = MemoryManager(project_path=temp_project)
        
        memory_id = manager.add(content="To be deleted", type="temp")
        
        result = manager.delete(memory_id)
        assert result == True
        
        memory = manager.get(memory_id)
        assert memory is None
        
        manager.close()
    
    def test_get_stats(self, temp_project):
        """Test get stats"""
        manager = MemoryManager(project_path=temp_project)
        
        manager.add(content="Stat 1", type="decision")
        manager.add(content="Stat 2", type="knowledge")
        
        stats = manager.get_stats()
        assert stats["total"] >= 2
        
        manager.close()
    
    def test_count(self, temp_project):
        """Test count"""
        manager = MemoryManager(project_path=temp_project)
        
        initial_count = manager.count()
        
        manager.add(content="New memory", type="test")
        
        new_count = manager.count()
        assert new_count == initial_count + 1
        
        manager.close()
    
    def test_page(self, temp_project):
        """Test page"""
        manager = MemoryManager(project_path=temp_project)
        
        for i in range(25):
            manager.add(content=f"Memory {i}", type="test")
        
        page = manager.page(page=0, page_size=10)
        assert len(page["messages"]) == 10
        assert page["total"] >= 25
        
        manager.close()
