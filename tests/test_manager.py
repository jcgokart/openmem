import pytest
import os
import tempfile
import shutil
from openmem.core.manager import MemoryManager


class TestMemoryManager:
    @pytest.fixture
    def temp_project(self):
        tmpdir = tempfile.mkdtemp()
        yield tmpdir
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    def test_init_project(self, temp_project):
        memory = MemoryManager(project_path=temp_project)
        assert memory.project_store is not None
        memory.close()
    
    def test_add_memory(self, temp_project):
        memory = MemoryManager(project_path=temp_project)
        memory_id = memory.add("Test memory", "decision", tags=["test"])
        assert memory_id > 0
        memory.close()
    
    def test_list_memory(self, temp_project):
        memory = MemoryManager(project_path=temp_project)
        memory.add("Test 1", "decision", tags=["test"])
        memory.add("Test 2", "milestone", tags=["test"])
        
        results = memory.list(type="decision")
        assert len(results) >= 1
        
        results = memory.list(type="milestone")
        assert len(results) >= 1
        memory.close()
    
    def test_search_memory(self, temp_project):
        memory = MemoryManager(project_path=temp_project)
        memory.add("Use JWT for authentication", "decision", tags=["auth"])
        
        results = memory.search("JWT")
        assert len(results) >= 1
        memory.close()
    
    def test_search_chinese(self, temp_project):
        memory = MemoryManager(project_path=temp_project)
        memory.add("Database connection pool config", "knowledge", tags=["db"])
        
        results = memory.search("database")
        assert len(results) >= 1
        memory.close()
    
    def test_tags_search(self, temp_project):
        memory = MemoryManager(project_path=temp_project)
        memory.add("Test", "decision", tags=["python", "test"])
        
        results = memory.search_by_tags(["python"])
        assert len(results) >= 1
        memory.close()
    
    def test_update_memory(self, temp_project):
        memory = MemoryManager(project_path=temp_project)
        memory_id = memory.add("Original content", "decision")
        
        updated = memory.update(memory_id, content="Updated content")
        assert updated is True
        
        results = memory.list()
        assert any(r['content'] == "Updated content" for r in results)
        memory.close()
    
    def test_delete_memory(self, temp_project):
        memory = MemoryManager(project_path=temp_project)
        memory_id = memory.add("To be deleted", "decision")
        
        deleted = memory.delete(memory_id)
        assert deleted is True
        memory.close()
    
    def test_page_memory(self, temp_project):
        memory = MemoryManager(project_path=temp_project)
        for i in range(15):
            memory.add(f"Memory {i}", "decision")
        
        page1 = memory.page(page=0, page_size=10)
        assert len(page1['messages']) == 10
        assert page1['total'] >= 15
        memory.close()
