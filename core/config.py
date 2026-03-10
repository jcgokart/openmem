"""
Memory Config Class
支持配置继承：extends: ~/.memory/config.yaml
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class MemoryConfig:
    """
    Memory Config Manager
    
    支持配置继承 / Supports config inheritance:
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
        """加载配置（支持继承） / Load config with inheritance"""
        base_config = {
            'version': '2.0.0',
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
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = yaml.safe_load(f)
                    if user_config:
                        if 'extends' in user_config:
                            extends_path = os.path.expanduser(user_config['extends'])
                            if os.path.exists(extends_path):
                                parent_config = self._load_single_config(extends_path)
                                base_config = self._merge_config(parent_config, user_config)
                            else:
                                base_config = self._merge_config(base_config, user_config)
                        else:
                            base_config = self._merge_config(base_config, user_config)
            except Exception as e:
                print(f"Warning: Failed to load config: {e}")
        
        return base_config
    
    def _load_single_config(self, path: str) -> Dict[str, Any]:
        """加载单个配置文件 / Load single config file"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except:
            return {}
    
    def _merge_config(self, base: Dict, override: Dict) -> Dict:
        """深度合并配置 / Deep merge config"""
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
        """获取配置值 / Get config value"""
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
        """获取数据库路径 / Get database path"""
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
