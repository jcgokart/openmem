# OpenMem v0.1.4 紧急修复规范

## Why
代码审查发现多个致命问题：连接泄漏会导致程序卡死，架构分裂导致 CLI 和 API 操作两个独立数据库世界。

## What Changes
- **BREAKING**: 统一存储层，废弃 `SQLiteMemoryBackend`，全面使用 `UnifiedStorage`
- 修复连接泄漏：所有方法使用上下文管理器确保连接归还
- 添加 FTS5 UPDATE 触发器
- 修复线程安全竞态条件
- 完善异常处理

## Impact
- Affected specs: 存储层架构
- Affected code: 
  - `storage/sqlite.py` - 修复连接泄漏、线程安全
  - `storage/unified.py` - 添加 UPDATE 触发器、修复连接泄漏
  - `core/manager.py` - 切换到 UnifiedStorage
  - `storage/__init__.py` - 更新导出

## ADDED Requirements

### Requirement: 连接池上下文管理
系统 SHALL 提供连接池的上下文管理器，确保连接自动归还。

#### Scenario: 正常操作
- **WHEN** 使用 `with pool.connection() as conn:` 获取连接
- **THEN** 操作完成后连接自动归还到池中

#### Scenario: 异常情况
- **WHEN** 操作过程中抛出异常
- **THEN** 连接仍然被正确归还到池中

### Requirement: 统一存储层
系统 SHALL 使用 `UnifiedStorage` 作为唯一存储实现。

#### Scenario: CLI 操作
- **WHEN** 用户通过 `omem add` 添加记忆
- **THEN** 数据存储在 UnifiedStorage 的表中

#### Scenario: Python API 操作
- **WHEN** 用户通过 `MemoryManager` 操作
- **THEN** 数据存储在 UnifiedStorage 的表中，与 CLI 数据互通

### Requirement: 自定义异常类
系统 SHALL 提供自定义异常类，不使用字符串匹配判断错误类型。

#### Scenario: FTS5 查询失败
- **WHEN** FTS5 查询语法错误
- **THEN** 抛出 `FTSSearchError` 异常，调用方可针对性处理

## MODIFIED Requirements

### Requirement: 连接池线程安全
连接池 SHALL 使用双重检查锁定或预初始化，避免竞态条件。

**修改前**:
```python
def get_connection(self):
    if not self._initialized:  # 无锁检查
        self.initialize()       # 可能重复初始化
    return self._pool.get()
```

**修改后**:
```python
def get_connection(self):
    if not self._initialized:
        with self._lock:
            if not self._initialized:  # 双重检查
                self.initialize()
    return self._pool.get()
```

### Requirement: FTS5 触发器完整
UnifiedStorage SHALL 包含完整的 FTS5 触发器（INSERT、UPDATE、DELETE）。

**修改**: 添加 `memories_au` UPDATE 触发器。

## REMOVED Requirements

### Requirement: SQLiteMemoryBackend 直接使用
**Reason**: 架构分裂，导致 CLI 和 API 操作不同数据库
**Migration**: MemoryManager 改用 UnifiedStorage
