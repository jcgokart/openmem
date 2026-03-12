"""
Tests for MemoryConfig
"""

import os
import tempfile
import shutil
import pytest

from openmem.core.config import MemoryConfig


class TestMemoryConfig:
    """Test MemoryConfig"""
    
    def test_default_config(self):
        """Test default config"""
        config = MemoryConfig()
        assert config.memory_dir is not None
    
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
