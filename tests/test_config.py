"""
Tests for MemoryConfig
"""

import os
import tempfile
import shutil
import pytest

from core.config import MemoryConfig


class TestMemoryConfig:
    """Test MemoryConfig"""
    
    def test_default_config(self):
        """Test default config"""
        config = MemoryConfig()
        assert config.memory_dir is not None
        assert config.db_name == "memory.db"
    
    def test_project_config(self):
        """Test project config"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = MemoryConfig(project_path=tmpdir)
            assert config.memory_dir == os.path.join(tmpdir, ".memory")
    
    def test_get_db_path(self):
        """Test get_db_path"""
        config = MemoryConfig()
        db_path = config.get_db_path()
        assert db_path.endswith("memory.db")
    
    def test_config_file(self):
        """Test config file loading"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "memory.yaml")
            with open(config_path, 'w') as f:
                f.write("memory_dir: custom_memory\n")
            
            config = MemoryConfig(config_path=config_path)
            assert config.memory_dir == "custom_memory"
