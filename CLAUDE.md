# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

MaxKB（Max Knowledge Brain）是一个开源的企业级智能体平台，集成 RAG 检索增强流水线、智能体工作流引擎与 MCP 工具调用，支持文本、图像、音频、视频的输入输出。

**当前 v3 分支正在进行大规模重构：** Django + Vue.js → FastAPI + Next.js。旧代码（`apps/`、`ui/`）仍在运行，新代码（`backend/`、`frontend/`）正在建设中。两者共享同一 PostgreSQL/pgvector/Redis。

## 项目结构

```
apps/          # 旧 Django 后端（生产运行中）
ui/            # 旧 Vue.js 前端（生产运行中）
backend/       # 新 FastAPI + SQLModel + Agno 后端（重构中）
frontend/      # 新 Next.js + React + Antd 前端（重构中）
main.py        # 旧 Django 服务编排入口
installer/     # Dockerfile + 启动脚本
```

## 旧栈命令（apps/ + ui/，生产环境）

### 后端
- 安装依赖：`uv sync`（根目录 pyproject.toml，不要用裸 pip）
- 启动 Web：`python main.py dev web`（Django runserver，端口 8080，自动 collect_static + migrate）
- 启动 Celery：`python main.py dev celery`（向量化、模型推理异步任务）
- 数据库迁移：`python main.py upgrade_db` 或 `cd apps && python manage.py migrate`
- 收集静态资源：`python main.py collect_static`（将 `ui/dist` 拷贝到 `apps/static`）
- 生产启动：`python main.py start all -d`
- 代码检查：`ruff check apps` / `ruff format apps`（行宽 120）
- 运行测试：`cd apps && python manage.py test <app>`
- 运行单个测试：`cd apps && python manage.py test application.tests.TestClass.test_method`

### 前端（ui/）
- 安装依赖：`cd ui && npm install`
- 管理后台开发：`npm run dev`（端口来自 `ui/env/.env` 的 `VITE_APP_PORT`）
- 对话页面开发：`npm run chat`
- 构建：`npm run build`（管理端）/ `npm run build-chat`（对话端），之后执行后端 `collect_static`
- 检查/格式化：`npm run lint` / `npm run format` / `npm run type-check`

## 新栈命令（backend/ + frontend/，重构目标）

### 后端（backend/）
- 安装依赖：`uv sync --extra dev`
- 启动 Web：`uv run python main.py`（FastAPI，端口 8080）
- 启动 arq worker：`uv run python -c "from app.core.tasks import run_worker; run_worker()"`
- 数据库迁移：`uv run alembic upgrade head`
- 代码检查：`uvx ruff check app` / `uvx ruff format --check app`
- 运行测试：`uv run pytest -q`（不需要 DB/Redis）

### 前端（frontend/）
- 安装依赖：`cd frontend && npm install`
- 开发：`npm run dev`（Next.js dev server，默认端口 3000，basePath `/frontend`）
- 构建：`npm run build`（standalone 输出）
- 检查：`npm run lint` / `npm run type-check`

## 环境依赖

- PostgreSQL（含 pgvector 扩展）+ Redis
- 默认管理员：`admin` / `MaxKB@123..`
- 旧栈配置：`config.yaml`（或 `MAXKB_CONFIG=1` 从根目录读 `.env`）
- 新栈配置：`backend/.env`（`MAXKB_*` 环境变量前缀）
- CI 仅跑 lint + 单测，无服务容器；端到端验证需完整的 PG/Redis 环境

## 旧栈架构要点（apps/）

- **配置系统**：`apps/maxkb/conf.py` 的 `ConfigManager` 从 YAML 或环境变量加载配置；`apps/maxkb/const.py` 暴露 `CONFIG`、`BASE_DIR`、`VERSION`
- **Django app 职责**：`common`（基础设施）、`application`（智能体+工作流引擎核心）、`knowledge`（RAG 子系统）、`models_provider`（模型提供方抽象）、`chat`（对话 API）、`tools`（函数/工具库）、`trigger`（定时触发）、`oss`（对象存储）
- **工作流引擎**（`application/flow`）：`WorkflowManage` 将有向图作为工作流执行，节点通过 `node_map` 注册，实现 `INode` 接口。新增节点类型需实现 `INode` 并追加到 `step_node/__init__.py` 的 `node_list`
- **模型提供方**：`IModelProvider`（`base_model_provider.py`），`impl/` 下每个厂商一个包，共享基类覆盖常见协议

## 新栈架构要点（backend/）

- `app/models/` — 44 张 SQLModel 表，对齐 Django `Meta.db_table`，无真实外键
- `app/core/db.py` **不得**调用 `create_all`；表由旧 Django 创建，迁移仅经 Alembic 增量进行
- `app/providers/` — `registry.get_llm/get_embedder` + `catalog.py` 结构化目录
- `app/agents/` — `ChatAgent`（Agno Agent + pgvector Retriever 适配）
- `app/workflows/` — `engine.WorkflowEngine` 图遍历 + SSE，节点注册表
- 详细进度与已知限制见 `backend/docs/REFACTOR_STATUS.md`

## 国际化

Django gettext（语言包 `apps/locales`）+ 前端 vue-i18n（旧）/ next-intl（新）。支持语言由 `conf.get_languages()` 解析。
