# Tasks

## Phase 1: 紧急修复（P0）

- [x] Task 1: 修复连接泄漏 - 添加上下文管理器
  - [x] SubTask 1.1: 在 ConnectionPool 中添加 `connection()` 上下文管理器方法
  - [x] SubTask 1.2: 修改 SQLiteMemoryBackend 所有方法使用上下文管理器
  - [x] SubTask 1.3: 修改 UnifiedStorage 所有方法使用上下文管理器

- [x] Task 2: 统一存储层架构
  - [x] SubTask 2.1: 创建 UnifiedStorage 适配器，兼容 MemoryBackend 接口
  - [x] SubTask 2.2: 修改 MemoryManager 使用 UnifiedStorage
  - [x] SubTask 2.3: 更新 storage/__init__.py 导出
  - [x] SubTask 2.4: 添加废弃警告到 SQLiteMemoryBackend

- [x] Task 3: 添加 FTS5 UPDATE 触发器
  - [x] SubTask 3.1: 在 UnifiedStorage._init_tables() 中添加 memories_au 触发器

## Phase 2: 稳定性修复（P1）

- [x] Task 4: 修复线程安全竞态
  - [x] SubTask 4.1: 在 ConnectionPool.get_connection() 中使用双重检查锁定

- [x] Task 5: 完善异常处理
  - [x] SubTask 5.1: 创建自定义异常类 (StorageError, FTSSearchError, ConnectionPoolError, MemoryNotFoundError)
  - [x] SubTask 5.2: 修改 search() 方法使用自定义异常
  - [x] SubTask 5.3: 添加异常处理测试

- [x] Task 6: 补齐关键测试
  - [x] SubTask 6.1: 连接池并发测试
  - [x] SubTask 6.2: 连接泄漏测试
  - [x] SubTask 6.3: FTS5 失败 fallback 测试

# Task Dependencies
- [Task 2] depends on [Task 1] (统一存储前先修复连接泄漏) ✅
- [Task 3] 可以与 [Task 1] 并行 ✅
- [Task 4] 可以与 [Task 2] 并行 ✅
- [Task 5] depends on [Task 2] (异常处理需要在统一架构后) ✅
- [Task 6] depends on [Task 1, Task 2, Task 3, Task 4, Task 5] ✅
