# OpenMem 升级方案 v0.1.3

**版本**：v0.1.3
**日期**：2026-03-11
**分支**：`feature/v0.1.3-refactor`
**执行者**：Solo Coder
**仓库**：github.com/jcgokart/openmem

---

## 一、背景：外部批判汇总

### 批判 #1：概念与架构

| 问题 | 详情 |
|------|------|
| 概念包装过度 | "存能力而不是知识"是伪命题，代码就是普通的 memory.add() |
| 缺 Session 层 | 只有 Global/Project 两层，无法解决对话上下文继承 |
| FTS5 不够 | BM25 是词袋模型，不懂语义 |
| 竞品对比不清 | 和 OpenClaw memory 的区别在哪？ |

### 批判 #2：代码层面

| 问题 | 详情 |
|------|------|
| 线程安全隐患 | threading.local() + check_same_thread=False，可能死锁 |
| 搜索实现错误 | OR 连接导致召回爆炸，没有 BM25 阈值过滤 |
| Manager 职责不清 | project 和 global 分别查，没有合并排序 |
| CLI 混乱 | add vs record vs organize，用户该用哪个？ |
| 类型系统太弱 | type: str 太宽泛，拼错静默失败 |

### 批判 #3：Features 模块

| 问题 | 详情 |
|------|------|
| Trigger 太简单 | 就是关键词匹配 + jieba 分词，不是"智能触发" |
| Organizer 孤立 | raw 存 jsonl，SQLite 独立，数据不互通 |
| LLM 集成敷衍 | Trae 模式是生成文本让用户手动复制，不是调用 |
| 提示词太 naive | 没有 few-shot，没有长度限制，错误数据静默存入 |

### 批判 #4：三个核心模块

| 问题 | 详情 |
|------|------|
| Search 排序错误 | bm25 值越小越相关，但代码用升序排列 |
| Version 伪 Git | 10 次修改 = 10 份完整数据，不是 diff |
| Encryption 假安全 | 盐值硬编码，只能全量加密 |
| Backup 假增量 | 复制完整 backup + WAL，不是真正增量 |

### 核心结论

> "代码能跑，架构散了，概念超前，实现保守。您做了一个'带搜索的笔记软件'，而不是'AI 能力系统'。"

---

## 二、核心问题诊断

| 层面 | 问题 | 根因 |
|------|------|------|
| 架构 | 六个模块六套数据 | 缺统一存储层 |
| 架构 | 缺 Session 层 | 只有 Global/Project 两层 |
| 架构 | 模块零通信 | 没有事件机制 |
| 技术 | FTS5 排序错误 | bm25 理解错误 |
| 技术 | 线程安全 | 连接池缺失 |
| 技术 | 搜索语义缺失 | 没有向量索引 |
| 功能 | 记忆不生效 | 存了不用，没有闭环 |
| 功能 | Trigger 太简单 | 只有关键词匹配 |
| 功能 | IDE Rules 不更新 | 没有自动生成机制 |
| 体验 | CLI 混乱 | add/record/organize 互斥 |

---

## 三、升级目标

```
从"带搜索的笔记软件" → "AI 能力系统"
```

**三个核心转变**：

| 维度 | 当前 | 升级后 |
|------|------|--------|
| 存 vs 用 | 存了就算 | 产生可消费的结果 |
| 散 vs 聚 | 六套数据 | 统一存储 |
| 被动 vs 主动 | 等着被搜 | 自动注入上下文 |

---

## 四、架构升级

### 4.1 新架构：三层 + Event Sourcing

```
┌─────────────────────────────────────┐
│           Session Layer             │  ← 新增：对话上下文
├─────────────────────────────────────┤
│           Project Layer             │
├─────────────────────────────────────┤
│           Global Layer              │
└─────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────┐
│        Event Store (SQLite)         │  ← 统一存储
│   - events 表：所有变更事件           │
│   - memories 表：物化视图            │
│   - sessions 表：对话上下文          │
│   - vectors 表：向量索引             │  ← 新增
└─────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────┐
│         IDE Rules (自动生成)         │  ← 新增
│   - .cursorrules                    │
│   - .trae/rules.md                  │
│   - PROJECT_RULES.md                │
└─────────────────────────────────────┘
```

### 4.2 Event Sourcing 设计

```
events 表:
  - id
  - type: "memory_added" | "memory_updated" | "session_started" | ...
  - payload: JSON
  - timestamp
  - session_id

# memories 表是物化视图，从 events 生成
# 天然支持：版本、回溯、分支
```

---

## 五、模块升级

### 5.1 统一存储层

**目标**：所有数据进 SQLite，jsonl 只作导出

**功能**：
- 初始化连接池
- 初始化表结构（events、sessions、vectors）
- 所有操作都是添加事件
- 从事件生成物化视图

### 5.2 Session 层

**目标**：解决对话上下文继承

**功能**：
- start()：开始新会话
- record()：记录对话，自动关联 session_id
- finalize()：结束会话，自动整理
- get_context()：获取上下文（知道"用JWT"和"改成OAuth"是替代关系）

### 5.3 Trigger → Action 闭环

**目标**：不是存了就算，要产生可消费的结果

**触发动作映射**：
| 触发类型 | 动作 |
|----------|------|
| decision | generate_decision_md, update_ide_rules, notify_team |
| tech_stack | update_ide_rules |
| todo | add_to_todo_md, set_reminder |
| issue | create_issue_md, link_to_milestone |

### 5.4 语义搜索（sqlite-vec）

**目标**：支持"类似这样的决策"

**功能**：
- add_embedding()：添加向量
- search_similar()：语义搜索
- hybrid_search()：混合搜索（FTS5 + 向量）

### 5.5 IDE Rules 自动生成

**目标**：记忆变化时，自动更新 IDE 配置

**支持的文件**：
| IDE | 文件路径 |
|-----|----------|
| Cursor | .cursorrules |
| Trae | .trae/rules.md |
| Copilot | .github/copilot-instructions.md |
| Project | PROJECT_RULES.md |

---

## 六、技术修复

### 6.1 FTS5 修复

| 错误 | 正确 |
|------|------|
| ORDER BY score（升序） | ORDER BY score ASC（bm25 值越小越相关） |
| OR 连接 | AND 连接 + 阈值过滤 |

### 6.2 线程安全

- 添加连接池（pool_size=5）
- 每个连接设置 WAL 模式

### 6.3 加密修复

| 错误 | 正确 |
|------|------|
| 硬编码盐值 | 随机盐值（secrets.token_bytes(16)） |
| 全量加密 | 字段级加密（保持搜索能力） |

---

## 七、CLI 升级

**目标**：Git-like 命令，清晰的用户心智模型

```
omem init              # 初始化项目
omem start             # 开始会话
omem record "..."      # 记录对话
omem commit            # 整理 + 写回
omem search "..."      # 搜索
omem log               # 查看历史
omem status            # 状态
omem rules             # 手动更新 IDE Rules
```

---

## 八、数据流

```
用户对话
    ↓
Session.record()
    ↓
Event Store (events 表)
    ↓
Session.finalize()
    ↓
┌─────────────────────────────────────┐
│           并行处理                   │
├─────────────────────────────────────┤
│ 1. 物化视图 → memories 表            │
│ 2. 向量索引 → memory_vectors 表      │
│ 3. IDE Rules → .cursorrules 等       │
│ 4. 文档生成 → decisions.md 等        │
└─────────────────────────────────────┘
```

---

## 九、分支策略

```
main (master)
    │
    └── feature/v0.1.3-refactor
            │
            ├── Phase 1: 基础修复
            ├── Phase 2: 架构重构
            ├── Phase 3: 功能增强
            └── Phase 4: 体验优化
                    │
                    └── 测试通过后合并回 main
```

---

## 十、实施路线

### Phase 1：基础修复（1-2周）
- [ ] 修复 FTS5 排序错误
- [ ] 添加连接池
- [ ] 修复加密盐值
- [ ] 集成 sqlite-vec

### Phase 2：架构重构（2-3周）
- [ ] 统一存储层
- [ ] 添加 Session 层
- [ ] Event Sourcing

### Phase 3：功能增强（2-3周）
- [ ] Trigger → Action 闭环
- [ ] 语义搜索（sqlite-vec）
- [ ] IDE Rules 自动生成
- [ ] CLI 重构

### Phase 4：体验优化（1-2周）
- [ ] 自动上下文注入
- [ ] 决策效果追踪
- [ ] 文档完善

---

## 十一、总结

| 问题 | 解决方案 |
|------|----------|
| 六套数据 | 统一存储层 |
| 缺 Session | 三层架构 |
| 模块零通信 | Event Sourcing |
| FTS5 错误 | 技术修复 |
| 记忆不生效 | Trigger → Action |
| 搜索语义缺失 | sqlite-vec |
| IDE Rules 不更新 | 自动生成 |
| CLI 混乱 | Git-like 命令 |

---

## 十二、执行方式

1. 在 `github.com/jcgokart/openmem` 创建分支 `feature/v0.1.3-refactor`
2. 按 Phase 顺序逐步实施
3. 每个 Phase 完成后测试确认
4. **合并前需要人工确认程序，切记**
5. 全部测试通过并人工确认后合并回 main

---

## 十三、重要提醒

### ⚠️ 合并前必须人工确认

每个 Phase 完成后，必须经过以下确认流程：

1. **自动化测试通过**：所有单元测试、集成测试通过
2. **功能验证**：核心功能手动验证通过
3. **代码审查**：代码质量审查通过
4. **人工确认**：用户明确确认可以合并

**禁止自动合并，必须人工确认！**

---

## 十四、产品描述（中文）

```
OpenMem 是开发环境的基础设施。始终在后台默默运行，全程记录你与 AI 的每一次对话、交流和工作，生成系统化的工作记忆，形成系统化的开发文档。把查到的、学到的、做到的，以及你的决策过程，积累成你的经验和能力——提升技术力、决策力、执行力。知识就是力量，但知识库不是。知识库里的知识变成你的能力，才是真正的力量。OpenMem 帮你实现。
```

## 十五、产品描述（English）

```
OpenMem is the infrastructure for development environments. It runs silently in the background, recording every conversation, exchange, and work with AI, generating systematic work memories and forming systematic development documents. What you search, learn, and do, along with your decision-making process, accumulates into your experience and capabilities—boosting technical skills, decision-making, and execution. Knowledge is power, but a knowledge base is not. The knowledge in your knowledge base becomes your capability—that's true power. OpenMem helps you achieve it.
```
