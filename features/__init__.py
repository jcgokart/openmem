"""
Memory 高级功能模块
"""

from memory.features.encryption import CryptoManager, BackupManager, BackupType, BackupInfo, EncryptionError
from memory.features.version import VersionController, Version, VersionType, Diff
from memory.features.trigger import SmartTrigger, TriggerType, TriggerResult
from memory.features.search import EnhancedSearch, ChineseTokenizer

__all__ = [
    "CryptoManager",
    "BackupManager", 
    "BackupType",
    "BackupInfo",
    "EncryptionError",
    "VersionController",
    "Version",
    "VersionType",
    "Diff",
    "SmartTrigger",
    "TriggerType",
    "TriggerResult",
    "EnhancedSearch",
    "ChineseTokenizer",
]
