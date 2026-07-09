# CODEBUDDY.md 本文件为 CodeBuddy 在处理本仓库代码时提供指引。

MaxKB（Max Knowledge Brain）是一个开源的企业级智能体平台，集成了 RAG 检索增强流水线、智能体工作流引擎与 MCP 工具调用，支持文本、图像、音频、视频的输入输出。技术栈：Vue.js（前端）、Python/Django（后端）、LangChain（大模型编排）、PostgreSQL + pgvector（数据与向量库）、Redis（缓存 + 任务队列）。

## 常用命令

### 后端依赖安装
使用 `uv`（在 `pyproject.toml` 中声明）。在仓库根目录运行 `uv sync` 安装全部依赖（Django、LangChain、Celery、sentence-transformers 等）。仓库不存在 `requirements.txt`，请勿直接用裸 `pip` 安装。本地轻量安装可加 `--no-install-project`。

### 后端开发（web 服务）
`python main.py dev web` 启动 Django runserver，监听 `0.0.0.0:8080`（启动前会先执行 `collect_static` 与 `migrate`）。需要仓库根目录的 `config.yaml`（或设置 `MAXKB_CONFIG=1`），以及运行中的 PostgreSQL（pgvector）与 Redis。

### 后端开发（异步任务）
`python main.py dev celery` 启动 Celery worker（`celery_default`/`celery_model`），处理向量化、模型推理等异步任务。Web 与 Celery 是两个独立进程，需同时运行。

### 数据库迁移
`python main.py upgrade_db` 执行 Django `migrate`（含数据库未就绪的重试）。等价命令：在 `apps/` 下运行 `python manage.py migrate`。`manage.py` 已设置 `DJANGO_SETTINGS_MODULE=maxkb.settings`。

### 收集前端静态资源
`python main.py collect_static` 将 `ui/dist` 拷贝到 `apps/static`，供 Django 托管 admin 与 chat 两个 SPA。每次前端构建后执行。

### 启动服务（生产）
`python main.py start all -d` 以守护进程方式启动全部服务（gunicorn web + celery）。可用 `web` 或 `task` 启动部分服务。生命周期命令 `start`/`stop`/`restart`/`status` 位于 `apps/common/management/commands`。

### 后端代码检查
`ruff check apps`（ruff 0.15.12，行宽 120）。格式化用 `ruff format apps`。配置在 `pyproject.toml`，无需额外设置。

### 后端运行全部测试
在 `apps/` 下运行 `python manage.py test <app>`，例如 `python manage.py test application`。仓库无 pytest 配置，统一使用 Django 测试运行器。

### 后端运行单个测试
`python manage.py test application.tests.TestClass.test_method` 运行单个方法；`application.tests.TestClass` 运行整个类。须在 `apps/` 下运行，且 PostgreSQL 与 Redis 可用。

### 前端安装依赖
`cd ui && npm install` 安装 Vue3/Vite/Element Plus 等依赖。

### 前端开发（管理后台）
`cd ui && npm run dev` 启动管理端 SPA（端口来自 `ui/env/.env` 的 `VITE_APP_PORT`，默认 3001）。Vite 将 `/admin/api` 与 `/chat/api` 代理到 `127.0.0.1:8080`。

### 前端开发（对话页面）
`cd ui && npm run chat` 以对话模式启动面向用户的 SPA（`chat.html` 入口）。API 同样代理到后端 8080 端口。

### 前端构建
`cd ui && npm run build` 构建管理端；`npm run build-chat` 构建对话端。输出到 `ui/dist/<base>`，之后执行后端 `collect_static`。

### 前端检查 / 格式化 / 类型检查
`npm run lint`（eslint --fix）、`npm run format`（prettier）、`npm run type-check`（vue-tsc）。提交前建议执行。

## 高层架构

### 仓库布局
这是一个 monorepo：`apps/`（Django 后端）、`ui/`（Vue 前端）、`installer/`（Dockerfile + 启动脚本 + init.sql），`main.py` 作为入口。后端为 Django 5.2 工程；`apps/maxkb/` 仅存放工程配置（settings/urls/const/conf），各业务功能各自独立成 Django app。

### 入口与服务模式
`main.py` 是唯一编排器。它设置 `DJANGO_SETTINGS_MODULE=maxkb.settings`，将 `apps/` 注入 `sys.path`，并暴露 `start`、`dev`、`upgrade_db`、`collect_static` 四个动作。服务拆分为 `web`（gunicorn/runserver）、`celery`（`celery_default`、`celery_model` 异步 worker）与 `local_model`（vLLM 托管模型）。`apps/maxkb/urls/__init__.py` 根据 `SERVER_NAME` 环境变量选择 web 或 model 路由配置。`apps/common/management/commands/` 通过 `Services` 枚举（gunicorn、celery_default、local_model、web、celery、celery_model、task、all）提供 `start`/`stop`/`restart`/`status`。

### Django app 职责划分
`INSTALLED_APPS`（位于 `apps/maxkb/settings/base/web.py`）包含：`users`、`tools`、`knowledge`、`common`、`system_manage`、`models_provider`、`application`、`chat`、`oss`、`trigger`、`folders`、`homepage`，以及 `django_celery_beat`、`django_apscheduler`。
- `common`：共享基础设施——中间件、统一异常处理、鉴权（`AnonymousAuthentication`）、数据库、文档切分、处理器、管理命令、国际化、缓存。
- `application`：智能体 + 工作流引擎（见下）、对话流水线、长期记忆、模型、API。
- `knowledge`：RAG 子系统——文档解析/上传、切分、向量化、检索。
- `models_provider`：模型提供方抽象（见下）。
- `chat`：对话 API 端点与 MCP 集成。
- `tools`：函数/工具库。`trigger`：定时触发。`oss`：对象存储。`system_manage`/`users`：系统配置与鉴权。`local_model`：本地推理模型服务。

### API 路由
`apps/maxkb/urls/web.py` 将各 app 的 `urls.py` 挂载到 `admin_api_prefix`（`/admin/api/`，管理后台）与 `chat_api_prefix`（`/chat/api/`，用户侧）之下。静态 SPA 由 `apps/static/{admin,chat}` 提供。DRF 使用自定义 `AnonymousAuthentication` 与集中式异常处理器（`common.exception.handle_exception`）。admin/chat 基础路径可通过 `CONFIG` 配置。

### 配置系统
`apps/maxkb/conf.py` 的 `ConfigManager` 从 YAML 文件（`config.yaml`/`config.yml`，默认 `/opt/maxkb/conf`；设置 `MAXKB_CONFIG` 环境变量时从工程根读取）或环境变量（`MAXKB_CONFIG_TYPE=ENV`，键名前缀 `MAXKB_`）加载配置。`Config` 默认值覆盖数据库（PostgreSQL，经 `dj_db_conn_pool`，含 pgvector）、Redis（缓存 + Celery broker）、本地模型绑定地址、路径与语言。`apps/maxkb/const.py` 暴露 `CONFIG`、`BASE_DIR`、`PROJECT_DIR`、`VERSION`。

### RAG 流水线（knowledge）
上传或爬取的文档经 `common/chunk` 切分、向量化后存入 pgvector（`knowledge/vector`）。工作流中的检索节点从该向量库拉取上下文。SQL 迁移文件位于各 app 的 `sql/` 与 `migrations/` 下。

### 工作流 / 智能体引擎（application/flow）——核心
`WorkflowManage`（`workflow_manage.py`）将工作流作为有向图执行。`get_node(type, workflow_mode)` 查询 `node_map`（由 `step_node/__init__.py` 基于 `node_list` 构建）来实例化节点。节点运行于 `ThreadPoolExecutor`（200 个 worker），支持流式（SSE 分块）与阻塞响应、经 `branch_id` 的分支选择、异常处理、循环，以及 step/global/chat 三级变量作用域与提示词模板（`reset_prompt`/`generate_prompt`）。每个节点实现 `INode` 接口（`i_step_node.py`）：`valid_args`、`run`、`write_context`、`get_details`。`Workflow` 图（节点 + 边）以 JSON 序列化。

新增节点类型：实现 `INode` 的 `BaseXxxNode` 子类，并追加到 `step_node/__init__.py` 的 `node_list` 中。其 `support` 列表声明适用的多种工作流模式。已有节点类型：开始、对话、知识库检索、文档检索、问题、条件、回复、工具、工具库、MCP、表单、意图、重排序、循环（开始/跳出/继续）、变量赋值/拆分/聚合、图像/视频/音频理解与生成、数据源（本地/网页）、知识库写入、文档切分、应用、工具开始。

### 模型提供方抽象（models_provider）
`IModelProvider`（`base_model_provider.py`）定义如何获取模型信息与凭据。`impl/` 下每个厂商一个包（openai、deepseek、qwen、anthropic、gemini、ollama、vllm、local_model、azure、aws_bedrock、xinference、tencent、zhipu 等）。共享基类 `base_chat_open_ai`、`base_tti`、`base_tts`、`base_stt` 覆盖常见协议。模型按类型引用：LLM、embedding、reranker、TTI、TTS、STT。

### 异步与调度
Celery worker（`celery_default`、`celery_model`）执行向量化与模型任务。`django_celery_beat` 与 `django_apscheduler` 配合 `trigger` app 驱动定时任务。

### 前端
Vue 3 + TypeScript + Vite + Element Plus + Pinia + vue-router + vue-i18n。两个 HTML 入口：`admin.html`（控制台）与 `chat.html`（用户对话组件）。工作流编辑器基于 `@logicflow/core`。`vite.config.ts` 将 `/admin/api`、`/chat/api`、`/doc`、`/schema`、`/static` 以及 OSS 文件路由代理到 `127.0.0.1:8080`。构建产物经 `collect_static` 注入 Django。

### 国际化
Django gettext（语言包位于 `apps/locales`）配合前端 vue-i18n。支持的语言由 `conf.get_languages()` 解析。

### 运维要点
默认管理员凭据：`admin` / `MaxKB@123..`。Web 端口：`8080`。本地开发需要 PostgreSQL（含 pgvector）与 Redis。后端 `manage.py` 位于 `apps/`；根目录 `main.py` 仅用于服务编排。新增工作流节点、模型提供方与 API 端点应遵循既有的注册/挂载约定，并复用 `common` 基础设施。

## 后端重构（FastAPI + SQLModel + Agno）— 进行中

`backend/` 目录是 MaxKB 后端的**新建式重构**（与 `apps/` 的 Django 后端并行，共享同一 PostgreSQL/pgvector/Redis，
不迁移数据，仅严格对齐表结构）。技术栈：FastAPI + SQLModel + Agno，Python 3.11，arq 替代 Celery。

### 目录（backend/）
- `app/models/` — 44 张 SQLModel 表（对齐 Django `Meta.db_table`，无真实外键）。
- `app/schemas/` — 请求/响应模型（auth / knowledge / model / application / tool / trigger / common）。
- `app/api/` — 路由：auth、knowledge、model、application、tool、system、trigger（共 22 个路径）。
- `app/core/` — config、db（asyncpg + 连接池）、security（JWT+RBAC）、password（兼容 Django 哈希）、
  tasks（arq 任务与 cron）、redis、i18n。
- `app/providers/` — `registry.get_llm/get_embedder`（原生 / OpenAI 兼容 / 讯飞自研）+ `catalog.py` 结构化目录。
- `app/agents/` — `ChatAgent`（Agno `Agent` + pgvector Retriever 适配）。
- `app/rag/` — 解析/切分/向量化 + `pipeline.ingest_document`。
- `app/workflows/` — `engine.WorkflowEngine` 图遍历 + SSE，节点注册表（8 个节点）。
- `app/tools/`、`app/trigger/` — 工具与定时触发（arq cron 驱动）。

### 常用命令（backend/ 下）
- 安装依赖：`uv sync --extra dev`（含 ruff / pytest）。
- 静态检查：`uvx ruff check app`、`uvx ruff format --check app`。
- 测试（全部 DB/Redis-free）：`uv run pytest -q`。
- 启动 web 服务：`uv run python main.py`（监听 0.0.0.0:8080）。
- 启动 arq worker：`uv run python -c "from app.core.tasks import run_worker; run_worker()"`。
- 数据库迁移（需 PostgreSQL+pgvector）：`uv run alembic upgrade head`（空基线 `0001_empty` 仅打标，不建表）。

### 约束 / 注意
- `app/core/db.py` **不得**调用 `create_all`；表由 legacy Django 创建，迁移仅经 Alembic 增量进行。
- 需在具备 PostgreSQL（pgvector）与 Redis 的环境做端到端验证（本仓库 CI 仅跑 lint + 单测，无服务容器）。
- 详细进度与已知限制见 `backend/docs/REFACTOR_STATUS.md`。
