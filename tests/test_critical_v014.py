"""
Critical tests for v0.1.4 fixes
- Connection leak detection
- FTS5 failure fallback
"""

import pytest
import os
import tempfile
import shutil
import threading
import time
import queue

from storage import UnifiedStorage, ConnectionPool, FTSSearchError, StorageError


class TestConnectionLeak:
    """测试连接泄漏修复"""
    
    @pytest.fixture
    def temp_db(self):
        tmpdir = tempfile.mkdtemp()
        db_path = os.path.join(tmpdir, "test.db")
        yield db_path
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    def test_context_manager_returns_connection(self, temp_db):
        """测试上下文管理器正确归还连接"""
        pool = ConnectionPool(db_path=temp_db, pool_size=2)
        
        with pool.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
        
        pool_size_before = pool._pool.qsize()
        
        with pool.connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 2")
        
        pool_size_after = pool._pool.qsize()
        
        assert pool_size_before == pool_size_after == 2
        
        pool.close_all()
    
    def test_exception_does_not_leak_connection(self, temp_db):
        """测试异常情况下连接仍然归还"""
        pool = ConnectionPool(db_path=temp_db, pool_size=2)
        
        pool_size_before = pool._pool.qsize()
        
        try:
            with pool.connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                raise ValueError("Simulated error")
        except ValueError:
            pass
        
        pool_size_after = pool._pool.qsize()
        
        assert pool_size_before == pool_size_after, "Connection leaked after exception"
        
        pool.close_all()
    
    def test_unified_storage_no_leak(self, temp_db):
        """测试 UnifiedStorage 操作不泄漏连接"""
        storage = UnifiedStorage(db_path=temp_db, pool_size=2)
        
        pool_size_before = storage._pool._pool.qsize()
        
        storage.add_memory("Test 1", "knowledge")
        storage.add_memory("Test 2", "decision")
        storage.search("Test")
        storage.get_memory(1)
        storage.list_memories()
        storage.get_stats()
        
        pool_size_after = storage._pool._pool.qsize()
        
        assert pool_size_before == pool_size_after, "Connection leaked in UnifiedStorage"
        
        storage.close()


class TestFTS5Fallback:
    """测试 FTS5 失败时的 fallback"""
    
    @pytest.fixture
    def temp_db(self):
        tmpdir = tempfile.mkdtemp()
        db_path = os.path.join(tmpdir, "test.db")
        yield db_path
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    def test_search_fallback_on_invalid_query(self, temp_db):
        """测试无效 FTS5 查询时 fallback 到 LIKE"""
        storage = UnifiedStorage(db_path=temp_db)
        
        storage.add_memory("Test content with special chars", "knowledge")
        
        results = storage.search("Test content")
        
        assert len(results) >= 1
        assert "Test content" in results[0]["content"]
        
        storage.close()
    
    def test_search_returns_empty_on_no_match(self, temp_db):
        """测试无匹配时返回空列表"""
        storage = UnifiedStorage(db_path=temp_db)
        
        storage.add_memory("Apple banana orange", "knowledge")
        
        results = storage.search("xyz123notfound")
        
        assert results == []
        
        storage.close()


class TestUnifiedStorageIntegration:
    """测试统一存储层集成"""
    
    @pytest.fixture
    def temp_db(self):
        tmpdir = tempfile.mkdtemp()
        db_path = os.path.join(tmpdir, "test.db")
        yield db_path
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    def test_event_sourcing(self, temp_db):
        """测试事件溯源"""
        storage = UnifiedStorage(db_path=temp_db)
        
        memory_id = storage.add_memory("Test decision", "decision")
        
        events = storage.get_events(event_type="memory_added", limit=10)
        
        assert len(events) >= 1
        assert events[0].type == "memory_added"
        assert "Test decision" in events[0].payload.get("content", "")
        
        storage.close()
    
    def test_session_tracking(self, temp_db):
        """测试会话追踪"""
        storage = UnifiedStorage(db_path=temp_db)
        
        session_id = storage.start_session(project_id="test-project")
        
        storage.add_memory("Decision in session", "decision", session_id=session_id)
        storage.add_memory("Another decision", "decision", session_id=session_id)
        
        context = storage.get_session_context(session_id)
        
        assert len(context["memories"]) == 2
        assert len(context["events"]) >= 2
        
        storage.end_session(session_id, summary="Test session completed")
        
        session = storage.get_session(session_id)
        assert session.ended_at is not None
        assert session.summary == "Test session completed"
        
        storage.close()
    
    def test_fts5_update_trigger(self, temp_db):
        """测试 FTS5 UPDATE 触发器"""
        storage = UnifiedStorage(db_path=temp_db)
        
        memory_id = storage.add_memory("Original content", "knowledge")
        
        results = storage.search("Original")
        assert len(results) >= 1
        
        storage.update_memory(memory_id, content="Updated content completely")
        
        results = storage.search("Updated")
        assert len(results) >= 1
        
        results = storage.search("Original")
        assert all("Updated" in r["content"] for r in results)
        
        storage.close()


class TestThreadSafety:
    """测试线程安全"""
    
    @pytest.fixture
    def temp_db(self):
        tmpdir = tempfile.mkdtemp()
        db_path = os.path.join(tmpdir, "test.db")
        yield db_path
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    def test_double_checked_locking(self, temp_db):
        """测试双重检查锁定防止重复初始化"""
        pool = ConnectionPool(db_path=temp_db, pool_size=5)
        
        init_count = [0]
        original_init = pool.initialize
        
        def counted_init():
            init_count[0] += 1
            return original_init()
        
        pool.initialize = counted_init
        
        pool.get_connection()
        pool.return_connection(pool.get_connection())
        pool.get_connection()
        
        assert init_count[0] == 1, f"initialize() called {init_count[0]} times, expected 1"
        
        pool.close_all()
