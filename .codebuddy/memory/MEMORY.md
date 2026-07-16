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
- **端口约定**：`8081` = 新 FastAPI 后端（`backend/main.py` 的 `port=8081`）；`8080` = 老 Django 后端（`apps/`）。二者可并存。
- **老 ui 连新后端**：需在 `backend/.env` 设 `MAXKB_API_PREFIX=/admin/api`、`MAXKB_CHAT_API_PREFIX=/chat/api`（PathRewriteMiddleware 据此把老前缀重写到 `/api`）；`ui/vite.config.ts` 代理目标指向 `127.0.0.1:8081`。
- **新后端运行环境缺依赖**（已修并写入 `backend/pyproject.toml`）：`greenlet`（异步 SQLAlchemy 必需）、`pycryptodome`（`rsa_util` 的 `Crypto`）。实际运行环境为 `miniforge3/envs/py311/bin/python`（`python main.py`，cwd=backend/），非 uv `.venv`。
- **已知代码缺陷**：`backend/app/core/rsa_util.py` 创建 `SystemSetting` 时未填 `create_time`/`update_time`，与 Django 表 NOT NULL 冲突（已修：填 `datetime.now()`）。
