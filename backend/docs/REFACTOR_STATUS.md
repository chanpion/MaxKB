# 后端重构进度（FastAPI + SQLModel + Agno）

> 状态更新：2026-07-09
> 目标：将 Django 5.2 + DRF + LangChain 后端，以"新建式"方式重构为 FastAPI + SQLModel + Agno，
> 复用同一 PostgreSQL（pgvector）/ Redis 实例，**不迁移数据**，仅严格对齐表结构。

> 说明：早期计划文件曾把 10 个阶段全部标记为 `completed`，但实际代码仅停留在脚手架 + 部分原型。
> 本文档记录**真实进度**。

## 已完成 ✅

- **数据层（SQLModel，44 张表）**：7 个模型模块（user/knowledge/application/tool/trigger/system/models_provider），
  全部 `__tablename__` / 列类型 / 可空 / 默认值 严格对齐 Django `Meta.db_table`。无 `ForeignKey`（沿用 Django
  `db_constraint=False` 的纯 `*_id` 列）。mptt 树表保留 `tree_id/level/lft/rght` + `parent_id` 邻接。
- **Schemas**：auth / knowledge / model / application / tool / trigger / common，分页用 `Any` 列表规避 pydantic 嵌套模型 eval 问题。
- **API 路由（7 个模块，22 个路径）**：auth(login/me/list)、knowledge(CRUD)、model(CRUD + /providers 结构化目录)、
  application(列表/详情/流式 chat SSE)、tool(CRUD + 文件夹)、system(log/setting)、trigger(CRUD + 任务 + 手动执行)。
- **鉴权**：`security.py` JWT(HS256) + RBAC `require_roles`，已接入所有受保护路由；口令兼容 Django
  `pbkdf2_sha256` / `bcrypt$` / 原生 `$2b$` / 明文。
- **异步任务（arq 替代 Celery）**：`ingest_document_task`（包装 `rag.pipeline.ingest_document`）、
  `enqueue_ingest` 入队助手、每日清理日志/会话 cron、按活跃 `event_trigger` 动态注册 cron；`run_trigger` 入口。
- **Provider 抽象**：`registry.get_llm/get_embedder` 覆盖原生 / OpenAI 兼容 / 讯飞自研；新增 `catalog.py` 结构化供应商目录（凭据表单元数据）。
- **工作流引擎**：`engine.WorkflowEngine` 图遍历 + AND/OR 扇入 + SSE 流式 + 分支；节点注册表含 8 个节点
  （start / question / ai-chat / search-knowledge / tool / condition / direct-reply / variable-assign）。
- **Chat Agent**：`agents/chat_agent.ChatAgent`（Agno `Agent` + pgvector Retriever 适配 + 可选长期记忆）。
- **RAG 流水线**：`rag/pipeline.ingest_document`（解析→切分→向量化→落 `document`/`paragraph`/`embedding`，与 Django 共用同一 pgvector SQL）。
- **测试**：`pytest` 26 个用例全绿，全部 **不依赖真实 Postgres/Redis**（用 `TestClient` + FakeSession/依赖覆盖）。含密码兼容性、API CRUD、路由注册、provider 目录、登录鉴权。
- **CI**：`.github/workflows/ci.yml`（uv sync --extra dev → ruff check/format → pytest）。
- **Alembic**：空基线 `0001_empty.py`（`upgrade()` 仅 `pass`），`db.py` 不调用 `create_all`，CI 迁移守卫禁止 drop/改类型。

## 已知问题（已修复）
- `pipeline.py` / `trigger/manager.py` 误用未安装的 `uuid_utils`（改用本地 `uuid7()`）。
- `password.verify_password` 对 `pbkdf2_sha256` 的 split 写成了 5 段（实为 4 段）→ 已修复；并支持原生 `$2b$` 哈希（`hash_password` 产物）。
- `/api/model/providers` 被 `/{model_id}` 路由遮蔽（定义顺序）→ 已调整顺序。
- JWT 密钥由 `db_password`(20B) 派生为 SHA-256 32B，消除弱密钥告警。

- **Stage 9 — 工作流节点全量迁移（24 个新增节点，共 36 个）**：节点注册表从 12 个扩展到 **36 个类型**
  （+`reply-node` 别名），覆盖 legacy Django 全部节点类型。迁移严格遵循"Agno 已有能力直接复用"原则：
  - **批次 1（引擎核心）**：`loop-node` / `loop-start-node` / `loop-break-node` / `loop-continue-node`
    （子工作流逐轮 `WorkflowEngine` 执行 + BREAK/CONTINUE 信号 + 表单中断 `interrupt` 透传）、`application-node`
    （查库加载子应用 `work_flow` 并嵌套 `WorkflowEngine` 执行）。
  - **批次 2（简易/配置）**：`variable-splitting-node`（纯 Python 路径遍历替代 jsonpath_ng）、
    `variable-aggregation-node`（first_non_null/array/dict）、`data-source-web-node` / `data-source-local-node` /
    `tool-start-node` / `document-split-node`（占位/透传）。
  - **批次 3（Agno 简化）**：`mcp-node`（原生 `agno.tools.mcp.MCPTools`）、`parameter-extraction-node`
    （Agno `response_model` 结构化输出）、`tool-lib-node` / `tool-workflow-lib-node`（Agno Function tools）、
    `knowledge-write-node`（复用 `rag.pipeline.ingest_document`）、`document-extract-node`（复用 `rag.parsers.parse_file`）。
  - **批次 4（多媒体）**：`search-document-node`（复用 `PgVectorRetriever` + `get_embedder`）、
    `image-generate-node` / `text-to-video-node` / `image-to-video-node`（agno `DalleTools`/`FalTools`/`ReplicateTools`/`LumaLabTools`，
    经新增 `get_tti`/`get_ttv` 注册表）、`video-understand-node`（Agno `Agent` + `agno.media.Video`）、
    `text-to-speech-node` / `speech-to-text-node`（agno `ElevenLabsTools`/`OpenAITools`/`MLXTranscribeTools`，经新增 `get_tts`/`get_stt` 注册表）。
  - **测试**：新增 `test_batch1/2/3/4_nodes.py`，全部不依赖真实 PG/Redis/LLM/MCP（`monkeypatch` 隔离）；
    全量 `pytest` 64 passed / 1 skipped（mcp 测试因 `mcp` 可选包未装在 CI 环境 skip，节点在运行时友好报错）。
- **Provider 多媒体注册表**：`registry.get_tts/get_stt/get_tti/get_ttv` + `TTS_MAP/STT_MAP/TTI_MAP/TTV_MAP`
  对齐 `NATIVE_LLM_MAP` 模式，统一 OpenAI 兼容回退。

## 待完成 / 限制 ⏳
- **真实 PG/Redis 端到端验证**：arq worker、真实入库（`ingest_document_task`）、流式对话对真实 LLM 的调用仍需在具备
  PG(pgvector)+Redis 的环境验证。本仓库已提供 `backend/docker-compose.dev.yml`（PostgreSQL 17+pgvector + Redis），
  启动后执行 `alembic upgrade head` 确认空基线打标、`uv run python -c "from app.core.tasks import run_worker; run_worker()"`
  启动 worker。CI 仅覆盖 mock 路径。
- **节点运行时依赖可选 SDK（已声明）**：`pyproject.toml` 新增 `multimedia` 可选依赖组（mcp/elevenlabs/fal-client/
  replicate/luma/moviepy/opencv），`uv sync --extra multimedia` 安装后多媒体节点即可真实调用；节点已做 lazy import +
  友好报错，CI 仅覆盖 mock 路径。
- **Provider 为映射+目录**：`ModelProvider` 子类仅作加密/校验基类，未给每个厂商写专用 `get_model`（registry 已覆盖主流接入）。
- **流式 chat 真实模型凭证 + 网络**：`ChatAgent` 已加 `app/tests/test_chat_agent_stream.py`（mock Agno Agent，验证 SSE 帧
  结构 + 末尾 `done`），真实 LLM 调用仍需凭证/网络。
- **表单中断恢复（已联调）**：`form-node` 支持 `need_user_input` 中断（`NodeResult(interrupt=True)`），`WorkflowEngine.run()`
  在检测到中断时返回 `status=423 / interrupted=True / form` 挂起结果；恢复通过「带补齐值重跑引擎」实现（参数暴露为
  `global.<key>`）。端到端测试见 `app/tests/test_form_interrupt_resume.py`（3 passed）。
- **本地模型服务（已移植）**：`app/local_model/router.py` 提供 OpenAI 兼容代理（`/api/local_model/v1/{models,chat/completions,
  embeddings}`），转发到 `local_model_protocol://local_model_host:local_model_port` 的 vLLM/llama.cpp；已挂载进 `app`
  并在 `main_local_model.py` 进程可用。测试见 `app/tests/test_local_model.py`（3 passed，mock httpx）。
- **触发器执行处理器（已接线）**：见上节。

## 常用命令（backend/ 下）
- 安装：`uv sync --extra dev`
- 静态检查：`uvx ruff check app` / `uvx ruff format --check app`
- 测试：`uv run pytest -q`
- 启动 web：`uv run python main.py`（0.0.0.0:8080）
- 启动 worker：`uv run python -c "from app.core.tasks import run_worker; run_worker()"`
- 迁移（需 PG）：`uv run alembic upgrade head`
