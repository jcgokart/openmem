# Checklist

## Phase 1: 紧急修复（P0）

### 连接泄漏修复
- [x] ConnectionPool.connection() 上下文管理器实现正确
- [x] SQLiteMemoryBackend 所有方法都使用上下文管理器
- [x] UnifiedStorage 所有方法都使用上下文管理器
- [x] 异常情况下连接也能正确归还

### 架构统一
- [x] MemoryManager 使用 UnifiedStorage
- [x] CLI 和 Python API 操作同一数据库
- [x] SQLiteMemoryBackend 标记为废弃
- [x] storage/__init__.py 导出正确

### FTS5 触发器
- [x] UnifiedStorage 包含 INSERT 触发器 (memories_ai)
- [x] UnifiedStorage 包含 UPDATE 触发器 (memories_au)
- [x] UnifiedStorage 包含 DELETE 触发器 (memories_ad)
- [x] 更新记忆后 FTS5 索引同步更新

## Phase 2: 稳定性修复（P1）

### 线程安全
- [x] ConnectionPool.get_connection() 使用双重检查锁定
- [x] 并发测试通过

### 异常处理
- [x] 自定义异常类定义完整
- [x] search() 方法使用自定义异常
- [x] 调用方可针对性处理异常

### 测试覆盖
- [x] 连接池并发测试通过
- [x] 连接泄漏测试通过
- [x] FTS5 失败 fallback 测试通过
