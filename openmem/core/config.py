"""
Memory Config Class
Supports config inheritance: extends: ~/.memory/config.yaml
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class MemoryConfig:
    """
    Memory Config Manager

    Supports config inheritance:
        # .memory/config.yaml
        extends: ~/.memory/config.yaml
    """
    
    DEFAULT_GLOBAL_PATH = os.path.expanduser("~/.memory")
    
    def __init__(self, project_path: str = None):
        self.project_path = project_path
        
        if project_path:
            self.memory_dir = os.path.join(project_path, ".memory")
        else:
            self.memory_dir = os.path.normpath(os.path.expanduser("~/.memory"))
        
        self.config_file = os.path.join(self.memory_dir, "config.yaml")
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load and merge config with inheritance"""
        base_config = self._load_default_config()
        user_config = self._load_single_config(self.config_file, visited=set())
        config = self._merge_config(base_config, user_config)
        self._validate_config(config)
        return config
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default config"""
        return {
            'version': '0.1.1',
            'project': {'name': ''},
            'memory_types': {
                'decision': {'sync_to_global': False},
                'milestone': {'sync_to_global': False},
                'issue': {'sync_to_global': False},
                'knowledge': {'sync_to_global': True},
                'archive': {'sync_to_global': False},
            },
            'storage': {
                'type': 'sqlite',
                'path': 'memory.db',
                'wal_mode': True,
                'busy_timeout': 30000,
                'enable_fts': True,
            },
            'search': {
                'highlight': True,
                'tokenizer': 'jieba',
            },
            'backup': {
                'auto': False,
                'max_backups': 7,
            }
        }
    
    def _load_single_config(self, path: str, visited: set = None) -> Dict[str, Any]:
        """Load single config file with circular dependency detection"""
        if visited is None:
            visited = set()
        
        abs_path = os.path.abspath(os.path.expanduser(path))
        if abs_path in visited:
            raise ValueError(f"Circular config inheritance detected: {path}")
        visited.add(abs_path)
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
        except Exception:
            return {}
        
        if 'extends' in config:
            extends_path = os.path.expanduser(config['extends'])
            if os.path.exists(extends_path):
                parent_config = self._load_single_config(extends_path, visited)
                config = self._merge_config(parent_config, config)
        
        return config
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """Validate config values"""
        storage = config.get('storage', {})
        
        busy_timeout = storage.get('busy_timeout')
        if busy_timeout is not None and busy_timeout <= 0:
            raise ValueError(f"busy_timeout must be positive, got: {busy_timeout}")
        
        wal_mode = storage.get('wal_mode')
        if wal_mode is not None and not isinstance(wal_mode, bool):
            raise ValueError(f"wal_mode must be boolean, got: {wal_mode}")
    
    def _merge_config(self, base: Dict, override: Dict) -> Dict:
        """Deep merge config"""
        result = base.copy()
        for key, value in override.items():
            if key == 'extends':
                continue
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        return result
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get config value"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value
    
    def get_db_path(self) -> str:
        """Get database path"""
        storage = self.config.get('storage', {})
        db_path = storage.get('path', 'memory.db')
        if not os.path.isabs(db_path):
            db_path = os.path.join(self.memory_dir, db_path)
        return db_path
    
    def get_wal_mode(self) -> bool:
        return self.config.get('storage', {}).get('wal_mode', True)
    
    def get_busy_timeout(self) -> int:
        return self.config.get('storage', {}).get('busy_timeout', 30000)
    
    def get_enable_fts(self) -> bool:
        return self.config.get('storage', {}).get('enable_fts', True)
