"""
Security tests for v0.1.7.1
- SQL injection protection
- Concurrent write safety
- Large content handling
"""

import pytest
import os
import tempfile
import shutil
import threading
import time

from openmem.storage import UnifiedStorage, StorageError, DatabaseIntegrityError


class TestSQLInjectionProtection:
    """测试 SQL 注入防护"""
    
    @pytest.fixture
    def temp_storage(self):
        tmpdir = tempfile.mkdtemp()
        db_path = os.path.join(tmpdir, "test.db")
        storage = UnifiedStorage(db_path=db_path)
        yield storage
        storage.close()
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    def test_sql_injection_in_content(self, temp_storage):
        """测试内容中的 SQL 注入被阻止"""
        malicious_content = "'; DROP TABLE memories; --"
        
        memory_id = temp_storage.add_memory(content=malicious_content)
        
        assert memory_id > 0
        
        memories = temp_storage.list_memories()
        assert len(memories) >= 1
        
        memory = temp_storage.get_memory(memory_id)
        assert memory["content"] == malicious_content
    
    def test_sql_injection_in_update(self, temp_storage):
        """测试更新中的 SQL 注入被阻止"""
        memory_id = temp_storage.add_memory(content="original")
        
        malicious_content = "'; DELETE FROM memories WHERE 1=1; --"
        result = temp_storage.update_memory(memory_id, content=malicious_content)
        
        assert result is True
        
        memory = temp_storage.get_memory(memory_id)
        assert memory["content"] == malicious_content
        
        memories = temp_storage.list_memories()
        assert len(memories) >= 1
    
    def test_sql_injection_in_tags(self, temp_storage):
        """测试标签中的 SQL 注入被阻止"""
        malicious_tags = ["'; DROP TABLE memories; --", "normal_tag"]
        
        memory_id = temp_storage.add_memory(content="test", tags=malicious_tags)
        
        memory = temp_storage.get_memory(memory_id)
        assert memory["tags"] == malicious_tags
    
    def test_sql_injection_in_metadata(self, temp_storage):
        """测试元数据中的 SQL 注入被阻止"""
        malicious_metadata = {
            "evil": "'; DROP TABLE memories; --",
            "normal": "value"
        }
        
        memory_id = temp_storage.add_memory(content="test", metadata=malicious_metadata)
        
        memory = temp_storage.get_memory(memory_id)
        assert memory["metadata"]["evil"] == "'; DROP TABLE memories; --"


class TestConcurrentWrite:
    """测试并发写入安全"""
    
    @pytest.fixture
    def temp_storage(self):
        tmpdir = tempfile.mkdtemp()
        db_path = os.path.join(tmpdir, "test.db")
        storage = UnifiedStorage(db_path=db_path)
        yield storage
        storage.close()
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    def test_concurrent_add_memory(self, temp_storage):
        """测试并发添加记忆"""
        errors = []
        
        def worker(worker_id):
            try:
                for i in range(10):
                    temp_storage.add_memory(
                        content=f"worker-{worker_id}-item-{i}",
                        tags=[f"worker-{worker_id}"]
                    )
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"并发错误: {errors}"
        
        memories = temp_storage.list_memories(limit=100)
        assert len(memories) == 50
    
    def test_concurrent_update_same_memory(self, temp_storage):
        """测试并发更新同一个记忆"""
        memory_id = temp_storage.add_memory(content="original", priority=0)
        
        errors = []
        
        def worker():
            try:
                for _ in range(5):
                    temp_storage.update_memory(memory_id, priority=1)
                    time.sleep(0.01)
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=worker) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"并发错误: {errors}"
        
        memory = temp_storage.get_memory(memory_id)
        assert memory is not None


class TestLargeContent:
    """测试大数据量处理"""
    
    @pytest.fixture
    def temp_storage(self):
        tmpdir = tempfile.mkdtemp()
        db_path = os.path.join(tmpdir, "test.db")
        storage = UnifiedStorage(db_path=db_path)
        yield storage
        storage.close()
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    def test_large_content_1mb(self, temp_storage):
        """测试 1MB 内容"""
        large_content = "x" * (1024 * 1024)
        
        memory_id = temp_storage.add_memory(content=large_content)
        
        memory = temp_storage.get_memory(memory_id)
        assert len(memory["content"]) == 1024 * 1024
    
    def test_many_memories(self, temp_storage):
        """测试大量记忆"""
        for i in range(100):
            temp_storage.add_memory(content=f"memory-{i}")
        
        count = temp_storage.get_memory_count()
        assert count == 100
        
        memories = temp_storage.list_memories(limit=50)
        assert len(memories) == 50
