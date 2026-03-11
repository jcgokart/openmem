import pytest
import os
import tempfile
import shutil
from openmem.core.config import MemoryConfig


class TestMemoryConfig:
    def test_default_global_path(self):
        config = MemoryConfig()
        assert '.memory' in config.memory_dir
    
    def test_project_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config = MemoryConfig(project_path=tmpdir)
            assert config.memory_dir == os.path.join(tmpdir, '.memory')
    
    def test_config_structure(self):
        config = MemoryConfig()
        assert 'version' in config.config
        assert 'memory_types' in config.config
        assert 'storage' in config.config
    
    def test_memory_types(self):
        config = MemoryConfig()
        types = config.config['memory_types']
        assert 'decision' in types
        assert 'milestone' in types
        assert 'knowledge' in types
    
    def test_get_db_path(self):
        config = MemoryConfig()
        db_path = config.get_db_path()
        assert db_path.endswith('.db')
    
    def test_wal_mode_default(self):
        config = MemoryConfig()
        assert config.get_wal_mode() is True
    
    def test_busy_timeout_default(self):
        config = MemoryConfig()
        assert config.get_busy_timeout() == 30000
    
    def test_enable_fts_default(self):
        config = MemoryConfig()
        assert config.get_enable_fts() is True
