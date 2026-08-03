# MaxKB Backend (FastAPI)

MaxKB（Max Knowledge Brain）重构后端：企业级智能体平台的 RAG 检索增强、智能体工作流与 MCP 工具调用的服务端实现。技术栈 **FastAPI + SQLModel + Agno**，配合 **PostgreSQL(pgvector) + Redis**。

> 本目录是 MaxKB 后端的**新建式重构**，与 `apps/`（遗留 Django 后端）并行运行，共享同一 PostgreSQL / Redis 实例，仅对齐表结构、不迁移数据。

---

## 技术栈

- Web 框架：FastAPI（uvicorn 运行）
- ORM / 模型：SQLModel（44 张表，对齐 Django `db_table`，无真实外键）
- Agent / 工作流：Agno（`ChatAgent` + `WorkflowEngine` 图遍历 / SSE）
- 数据库：PostgreSQL 17 + pgvector（向量检索），asyncpg 连接池
- 缓存 / 异步队列：Redis + arq（替代 Celery）
- 依赖管理：uv（`pyproject.toml` / `uv.lock`）
- 迁移：Alembic（仅空基线 `0001_empty` 打标，不建表）

---

## 目录结构

```
backend/
├── app/                  # 应用源码（api / models / schemas / core / agents / rag / workflows / tools）
│   ├── main.py           # 开发入口（uvicorn + reload）
│   └── main_local_model.py
├── alembic.ini / alembic/  # Alembic 空基线迁移
├── config/               # systemd 单元模板、配置样例
├── scripts/              # package.sh / start.sh / stop.sh / restart.sh
├── schema.sql            # 完整 DDL（含 pgvector 扩展）
├── init.sql              # 仅启用 pgvector 扩展
├── init_tables.py        # 开发用：按 SQLModel metadata 补建缺失表
├── install.sh            # 目标机安装（建库 + 建表 + Alembic 基线）
├── .env.example          # 环境变量模板（MAXKB_*）
├── pyproject.toml        # 依赖清单（uv）
├── requirements.txt      # 依赖清单（pip 兜底）
├── uv.lock               # 锁定的依赖版本
├── SOURCE_INSTALL.md     # 离线源码包部署详细步骤
└── DEPLOY.md             # 非容器化部署总览（架构 / 变量 / Nginx / FAQ）
```

---

## 本地开发

需要 Python 3.11、可用的 PostgreSQL(pgvector) 与 Redis，以及 `uv`。

```bash
cd backend

# 1) 安装依赖（含 dev）
uv sync

# 2) 配置（参考 .env.example，至少设置 MAXKB_DB_* / MAXKB_REDIS_*）
cp .env.example .env
#   编辑 .env：数据库 / Redis / MAXKB_API_PREFIX=/admin/api / MAXKB_CHAT_API_PREFIX=/chat/api

# 3) 准备数据库（首次）
uv run alembic upgrade head        # 仅打 Alembic 基线
psql ... -d maxkb -f schema.sql    # 建表（若未复用遗留 Django 库）

# 4) 启动（开发模式，带 reload）
uv run python main.py              # 监听 http://0.0.0.0:8080
```

> 开发入口 `main.py` 使用 `reload=True`。生产 / 后台启动请直跑 `uvicorn app.main:app`（见下方部署）。

启停脚本（裸机 / 生产）：

```bash
./scripts/start.sh all     # web + worker
./scripts/stop.sh all
./scripts/restart.sh all
```

---

## 配置

两种配置来源（优先级：环境变量 / `.env` > `config.yaml` > 默认值）：

- **`.env` / `MAXKB_*` 环境变量**：兼容遗留 Django 命名，推荐用于部署。关键项：
  - `MAXKB_DB_*` / `MAXKB_REDIS_*`：数据库与缓存连接
  - `MAXKB_WEB_HOST` / `MAXKB_WEB_PORT`：Web 监听（默认 `0.0.0.0:8080`）
  - `MAXKB_API_PREFIX` / `MAXKB_CHAT_API_PREFIX`：API 前缀，默认 `/admin/api`、`/chat/api`（与前端代理一致；不设置时回退 `/api` 会导致前端 404）
  - `MAXKB_LOG_LEVEL`：日志级别（生产建议 `INFO`）
- **`config.yaml`**：YAML 配置（默认读取工程根或 `/opt/maxkb/conf`，可由 `MAXKB_CONFIG` 环境变量切换）。

---

## 部署

- **离线源码包（推荐，非容器）**：`scripts/package.sh` 打 tar 包 → 目标机 `install.sh` 建库建表 + 基线 → `start.sh` / `restart.sh` / `stop.sh` 启停，可选 `--systemd` 托管。详见 [SOURCE_INSTALL.md](./SOURCE_INSTALL.md)。
- **手动裸机部署 / 反向代理 / 环境变量详表 / 常见问题**：见 [DEPLOY.md](./DEPLOY.md)。

> 本交付**不含 Docker 部署**。原 `Dockerfile` / `docker-compose*` / `docker-entrypoint.sh` / `build.sh` 等容器文件保持原样、不在维护范围内。
