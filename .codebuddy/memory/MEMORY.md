# MaxKB 项目长期记忆（MEMORY.md）

## 项目背景
- MaxKB 企业级智能体平台。存在**两条并行的新建式重构线**，均以原 Django/Vue 为基准：
  - 前端：`frontend/`（Next.js）—— 基准原 `ui/`（Vue3 + Element Plus + LogicFlow）。
  - 后端：`backend/`（FastAPI + SQLModel + Agno）—— 基准原 `apps/`（Django5.2 + DRF + LangChain）。
- 两条重构线均**不迁移数据**，复用同一 PostgreSQL(pgvector)/Redis，仅严格对齐表结构。
- 原后端是事实标准；任何"功能一致"核查都应以此为准。

## 用户协作偏好（一致性检查类任务）
- 偏好**全面对比**（API 接口 + 数据模型 + 行为/算法三层），而非单点。
- 偏好**静态代码对比**（不起服务、不连 PG/Redis、不跑端到端），与 CI 仅跑 mock 路径一致。
- 产出形式偏好：**对比报告文档（Markdown）+ 差距清单 + 修复优先级建议**（P0/P1/P2/P3）。
- 报告落盘到对应重构目录的 `docs/` 下。

## 重要事实 / 已知约束
- `backend/app/core/db.py` 不得调用 `create_all`；表由 legacy Django 创建，迁移仅经 Alembic 增量。
- `REFACTOR_STATUS.md` 文档内部存在矛盾（"8 节点" vs "36 节点"），实际代码为 36 节点；且"44 张表严格对齐"声明与代码不符（缺 `knowledge_action` 表）。读该文档时需以实际代码为准。
