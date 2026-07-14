# MaxKB 后端重构：接口与功能差异文档

> 版本：基于 `backend/`（FastAPI + SQLModel + Agno，新建式重构）与 `apps/`（Django 5.2 + DRF + LangChain）对比
> 统计时间：2026-07-13
> 配套进度文档：`backend/docs/REFACTOR_STATUS.md`

---

## 1. 概述

`backend/` 是 MaxKB 后端的**新建式重构**，与 `apps/` 并行运行，复用同一 PostgreSQL（pgvector）/ Redis 实例，**不迁移数据**，仅严格对齐表结构。本文档聚焦：

- 两侧**接口清单逐模块对照**
- **功能差异**与 **stub（桩）/ 缺失**能力清单
- 路径前缀、响应结构等**兼容性变化**
- 真实端到端验证的**风险点**
- 附：**分阶段补齐实现路线图**

### 1.1 端点规模（按路由定义计数）

| 侧 | 路由/URL 文件数 | 路由/URL 模式总数 | 说明 |
|----|----------------|------------------|------|
| Django `apps/` | 12 个 `urls.py` | **262** 条 | `oss` 在 admin 与 chat 前缀各挂载一次（去重后 262；含双挂载则 264） |
| FastAPI `backend/` | 12 个 router（含 `locales`/`health`/`local_model`） | **203** 条 | 按 `@router.{get,post,put,delete,patch}` 装饰器计数 |

> 注：Django 部分视图用 `http_method_names` 在单个 `path()` 内处理多方法，且普遍带 `workspace/<str:workspace_id>/` 路径作用域；FastAPI 去除了 workspace 路径作用域、统一前缀 `/api`。因此两数字并非 1:1 可比，仅作规模参考。

### 1.2 逐模块规模对照

| 模块 | Django 端点 | FastAPI 路由 | 差异 |
|------|:---:|:---:|:---:|
| users ↔ `auth` | 21 | 14 | FastAPI 偏少（缺邮件/验证码/workspace 用户接口） |
| knowledge ↔ `knowledge` | 94 | 73 | FastAPI 偏少（大量 stub + 真实入库缺失） |
| models_provider ↔ `models` | 15 | 25 | FastAPI 偏多（共享模型/文件夹/分页变体），但 `model_params_form` 为空 |
| application ↔ `application` | 38 | 18 | FastAPI 偏少（缺历史/导出/导入/workflow chat 等） |
| chat ↔ `chat` | 21 | 14 | FastAPI 偏少（缺 embed/mcp/share/clear，tts/stt 占位） |
| tools ↔ `tools` | 31 | 19 | FastAPI 偏少（import/debug/record/mcp 缺失） |
| trigger ↔ `trigger` | 11 | 7 | FastAPI 偏少（batch/activate/source/webhook 缺失） |
| system_manage ↔ `system` | 9 | 10 | 基本覆盖 |
| oss ↔ `oss` | 2 | 3 | 基本覆盖（缺签名 URL） |
| homepage ↔ `homepage` | 13 | 14 | 聚合真实、排行/导出为 stub |
| folders | 2 | — | FastAPI 拆散进 knowledge/application/tool，缺 user 文件夹 |
| local_model ↔ `local_model` | 5 | 3 | FastAPI 仅做代理转发（不含自建推理） |
| （无对应）`locales`/`health` | — | 2 / 1 | FastAPI 新增，Django 经静态资源提供 |

---

## 2. 总体架构与路径变化

### 2.1 前缀与路径重写

- Django 挂载：`/admin/api/...`（管理端）、`/chat/api/...`（用户端），且资源路径普遍带 `workspace/<str:workspace_id>/` 作用域。
- FastAPI 统一前缀：`/api/...`（`auth`→`/api/user`，`chat`→`/api/chat` 等）。
- 兼容手段：`app/middleware/path_rewrite.py` 的 `PathRewriteMiddleware` 将 `/admin/api`、`/chat/api` 重写为 `/api`；`app/middleware/response_format.py` 的 `LegacyResponseMiddleware` 把响应包成 `{code,data,message}` 信封，对齐 Django `Result`。
- **风险**：FastAPI 去除了 `workspace/<id>` 路径作用域，workspace 隔离完全依赖请求体/字段（默认 `"default"`）。若前端仍按 workspace 路径传参，需确认前端已适配。

### 2.2 鉴权

- Django：`AnonymousAuthentication` + DRF，权限多在视图层。
- FastAPI：`security.py` JWT(HS256) + `require_roles` RBAC。口令兼容 Django `pbkdf2_sha256` / `bcrypt$` / `$2b$` / 明文。
- **差异**：`auth.py` 的 `role`/`permissions` 数组为**前端式构造**（在 `_to_user_out` 内按 ADMIN/USER 拼接），**未持久化到 DB 资源权限表**。真正的 `WorkspaceUserResourcePermission` 表在 `system.py` 中有读写接口，但登录态下并未反向校验。

### 2.3 响应结构

两侧均兼容 `{code,data,message}`。`LegacyResponseMiddleware` 在 FastAPI 侧统一包裹；部分端点直接返回 `{"result": True}`（Django 习惯），前端以 `res.data` 取数，需保证关键字段一致。

---

## 3. 逐模块接口对照与功能差异

### 3.1 users ↔ `auth`（21 → 14）

**真实实现**：login（含 RSA 密文解密）、me、profile（别名）、list、logout、re_password、captcha（占位图）、PUT /me、language 切换、password 重置、manage 增删改。

**纯 stub / 占位**：
- `captcha` 返回固定占位图（`b"captcha-placeholder"`），非真实验证码。

**缺失（Django 有、FastAPI 无）**：
- `user/send_email`、`user/check_code`（邮件验证码注册/找回）
- `user/current/send_email`、`user/current/reset_password`（当前用户自助）
- `workspace/<id>/user_list`、`user_member`、`user/profile`（workspace 用户管理）
- `user_manage/batch_delete`、`user_manage/password`、`user_manage/<id>/page`（批量/分页）
- `user/test`（权限自检，可忽略）

---

### 3.2 knowledge ↔ `knowledge`（94 → 73，差异最大）

**真实实现**：KB 增删改查、KB 文件夹、文档增删改查、段落列表/详情、标签增删改+扩展（文档标签映射、级联删除）、`hit_test`（真实向量检索，返回 `comprehensive_score`）、embedding 触发（置 PENDING）、文档软删/移动、批量建文档（按段落）、批量加标签、文档 refresh/cancel_task、QA/表格/网页文档建空记录、`split` 预览、`/model` 与 `/embedding_model` 列表、publish（写 meta 标志）、文档标签查询/增删。

**纯 stub（直接 `{"result": True}` 或返回空）**：
- `batch_refresh`、`batch_hit_handling`、`batch_cancel_task`（批量取消）
- `batch_export` / `get_batch_export` / `get_batch_export_zip`（导出）
- `document/sync`（PUT 与 POST 两变体）、`tokenize`、`export`、`export_zip`、`download_source_file`、`replace_source_file`
- `migrate/<target>`（文档迁移）
- `split_pattern`（返回空 patterns）
- `generate_related`（生成相关问题）
- `export` / `export_zip` / `export_knowledge` / `export_knowledge_data`（知识库导出）
- `import_knowledge`、`sync`（知识库同步）
- `mcp_tools`（返回空 `tools`）
- `knowledge_version` 列表/详情/分页（均返回空）
- `document/template/export`、`table_template/export`

**关键缺失（影响核心闭环）**：
- **文档真实上传→解析→切分→向量化入库**：当前 `create_document` 仅建 `WAIT` 空记录，`split` 仅按 `\n\n` 朴素切分预览；没有「上传文件并触发 `ingest_document_task`」的接口。`rag/pipeline.ingest_document` 已存在，但**未通过 API 暴露真实入库路径**。
- **问题库(QA)/表格真实内容**：仅建空记录，无真实问答对/表结构存储与检索。
- **段落 `problem` / `association` 字段**：未提供接口。
- **知识库工作流引擎**（`transform_workflow`、`workflow/export|import`）：FastAPI 无对应。
- 术语库、段落关联、导出 zip 生成。

---

### 3.3 models_provider ↔ `models`（15 → 25）

**真实实现**：provider 结构化目录（`catalog.py`）、model_type_list、model_list（静态名称表）、model_params_form / model_form（返回 `credential_form`，**`model_params_form` 为空**）、模型 CRUD、下拉列表、共享模型 CRUD、模型文件夹（返回空）、模型 params_form 读写、meta、pause_download、分页。

**差异 / 缺失**：
- `model_params_form` 的 `model_params_form` 字段固定返回 `{}`；Django 由各厂商 `impl` 动态生成参数表单。
- 模型文件夹 `/folder` 返回 `[]` / `{"result": True}`（占位）。
- Provider 仅作映射 + 目录元数据，`registry.get_llm/get_embedder` 已覆盖主流接入，但未给每个厂商写专用 `get_model`（已声明为已知限制，可接受）。
- 多媒体注册表 `get_tts/get_stt/get_tti/get_ttv` 已加，但需 SDK 接入才真实可用（见路线图阶段 3）。

---

### 3.4 application ↔ `application`（38 → 18）

**真实实现**：列表、文件夹、详情、增删改、publish（含版本快照 + 自动建 access_token）、api_key 增删、`access_token` 读写、版本列表/详情、`stats`（对话数/点赞/点踩真实聚合）、`chat`（SSE 流式，SIMPLE 类型）。

**纯 stub / 占位**：
- `chat` 端点：当 `application.type == "WORK_FLOW"` 时**仍走 SIMPLE 流式**（代码 `else: return await _chat_simple_stream(...)`），**未走 WorkflowEngine**。

**缺失（Django 有、FastAPI 无）**：
- `chat_record` 对话历史查询、improve（用户纠错优化）、导出、open（对外打开）、批量/导入/移动、`add_knowledge`、prompt_generate、mcp 配置生效、tts/stt 设置落库校验。
- 路径分页 `/<page>/<page_size>` 仅覆盖列表，未覆盖全部查询维度。

---

### 3.5 chat ↔ `chat`（21 → 14，用户端）

**真实实现**：anonymous 认证、profile、application/profile、open（建对话）、chat_message（SSE 流式，SIMPLE）、historical_conversation、historical_conversation_record、删除对话、vote、edit_abstract、`/<id>/chat/completions`（OpenAI 兼容流式）、captcha。

**纯 stub / 占位**：
- `text_to_speech` / `speech_to_text`：仅返回 `{"result": True, "message": "..."}`，未接入真实模型。
- `chat_message` 同样忽略 `work_flow`（仅 SIMPLE）。

**缺失（Django 有、FastAPI 无）**：
- `embed`（匿名端向量化）、`mcp`、`share`（分享）、`clear`（清空历史）。
- workflow 类型应用的对话（同上，仅 SIMPLE）。

---

### 3.6 tools ↔ `tools`（31 → 19）

**真实实现**：文件夹增删、列表、tool_list（shared/tools 分桶）、增删改、workflow 获取/创建/发布/版本、batch_delete、batch_move、路径分页。

**纯 stub / 占位**：
- `upload_skill_file`：仅读字节并返回大小，**未解析/校验 skill 文件**。
- `test_connection`、`pylint`、`generate_code`：均返回 `{"result": True}` / 空。

**缺失（Django 有、FastAPI 无）**：
- `import`（导入工具）、`debug`（调试执行）、`tool_record`（调用记录）、`mcp_tools`（MCP 工具列表）、`store` / `add_internal`（内置工具市场）。

---

### 3.7 trigger ↔ `trigger`（11 → 7）

**真实实现**：CRUD、tasks 列表、`run`（手动经 `execute_trigger` 触发，admin）。

**缺失（Django 有、FastAPI 无）**：
- `batch_delete`、`batch_activate`（批量启用/停用）
- source 触发器（如 webhook 来源）、`task_record`（执行记录）、`webhook` 回调端点。
- 调度由 arq cron 驱动（`register_trigger_handlers` + `core/tasks`），但 webhook/source 触发未实现。

---

### 3.8 system_manage ↔ `system`（9 → 10）

**真实实现**：profile（含 RSA 公钥）、log 列表、setting 列表/详情、权限授予/撤销/列表（`WorkspaceUserResourcePermission`）、email_setting 读写、resource_mapping。

**差异 / 缺失**：
- 反向权限 `resource_user_permission`（按资源查用户）在 FastAPI 中以 `permission/user/<id>/resource/<type>` 提供，基本对齐。
- `valid`（配置校验）端点未实现。
- 权限未与登录态 RBAC 反查联动（见 2.2）。

---

### 3.9 oss ↔ `oss`（2 → 3）

**真实实现**：file 上传（落盘 + sha256 去重）、get（`FileResponse` 下载）、delete（删盘 + 记录）。

**缺失**：`get_url` 签名 URL（Django 有；FastAPI 无）。

---

### 3.10 homepage ↔ `homepage`（13 → 14）

**真实实现**：dashboard（应用/知识库/工具/模型/对话/记录/文档计数）、各 aggregation（application/knowledge/tool/model/chat_record/tokens 真实求和）、monitoring_aggregation。

**纯 stub（返回空）**：
- `monitoring_aggregation`（返回 `[]`）
- `tokens_ranking` / `question_ranking` / `user_tokens_ranking`（均返回空页）
- `tokens_ranking/export` / `question_ranking/export` / `user_tokens_ranking/export`（均返回空）

---

### 3.11 folders / local_model / 其他

- **folders**：Django 统一 `/<source>/folder`（4 类：user/knowledge/application/tool）；FastAPI 拆散进 knowledge/application/tool 三个 router，**缺 user 文件夹**接口。
- **local_model**：Django `local_model/urls.py` 5 条（模型列表/chat/embeddings 等）；FastAPI `local_model/router.py` 仅 3 条代理转发（`/v1/models`、`/v1/chat/completions`、`/v1/embeddings`），**不自实现推理**，符合重构策略。
- **locales / health**：FastAPI 新增（前端 locale 由 Django 静态提供，健康检查 Django 无独立端点）。

---

## 4. 功能差异与 stub 清单汇总

### 4.1 高优先级（阻塞核心数据闭环）
| 能力 | 状态 | 影响 |
|------|------|------|
| 文档真实上传→解析→切分→向量化入库 | **缺失**（仅空记录 + 朴素 split 预览） | 知识库无法真正问答 |
| 应用 WORK_FLOW 类型走 WorkflowEngine | **stub**（chat 端点忽略 work_flow） | 工作流应用无法运行 |
| QA / 表格 / 网页文档真实内容 | **缺失**（仅空记录） | 三类文档不可用 |
| 段落 problem / association | **缺失** | 检索增强受限 |

### 4.2 中优先级（管理功能闭环）
| 能力 | 状态 |
|------|------|
| 文档 sync / tokenize / export / export_zip / cancel_task | stub |
| 知识库版本快照 + 导出（knowledge_version） | stub（返回空） |
| 应用 chat_record 历史 / improve / 导出 / open / 批量 / 导入 / 移动 / add_knowledge / prompt_generate | 缺失 |
| chat embed / mcp / share / clear | 缺失 |
| chat / application 的 tts / stt | 占位 |
| 工具 import / debug / tool_record / mcp_tools / store | 缺失 |
| 触发器 batch_delete / activate / source / task_record / webhook | 缺失 |
| 模型 model_params_form 动态生成 | 空（Django 各 impl 动态生成） |

### 4.3 低优先级（统计 / 运维 / 兼容）
| 能力 | 状态 |
|------|------|
| homepage rankings（tokens/question/user_tokens） | stub（空） |
| homepage monitoring_aggregation / exports | stub（空） |
| oss get_url 签名 URL | 缺失 |
| 权限持久化反查（登录态 RBAC 联动 DB） | 前端式构造，未持久化校验 |
| 邮件/验证码（send_email / check_code / 真实 captcha） | 缺失 / 占位 |
| folders 的 user 文件夹 | 缺失 |
| workspace 路径作用域对齐 | FastAPI 已去除，需前端确认兼容 |

---

## 5. 真实端到端验证风险

1. **PG + Redis 依赖**：`rag/pipeline.ingest_document`、`ChatAgent` 流式、arq worker 均需真实 PostgreSQL（pgvector）+ Redis。CI 仅跑 mock 路径（`pytest` 全绿但不触真实服务）。`backend/docker-compose.dev.yml` 提供 PG17+pgvector + Redis，需实测 `alembic upgrade head` 与 worker。
2. **流式 chat 真实凭证 + 网络**：`ChatAgent` 已 mock 测试 SSE 帧结构，真实 LLM 调用需凭证与网络。
3. **多媒体节点可选 SDK**：`pyproject.toml` 的 `multimedia` 可选依赖组未默认安装；节点已 lazy import + 友好报错，缺失时仅 CI mock 路径覆盖。
4. **表单中断恢复**：`form-node` 的 `interrupt` 挂起/恢复（带补齐值重跑引擎）已联调测试，但需真实场景验证。
5. **数据不迁移**：重构后端只读 Django 已建表，表结构须严格对齐；若 Django 侧迁移导致表结构变化，FastAPI 侧 SQLModel 需同步。

---

## 6. 分阶段实现路线图（整体）

> 目标：按优先级补齐 stub / 缺失能力，使 `backend/` 在功能上对齐 `apps/`。路线图为模块级粒度，不展开代码实现。

### 阶段 1 — 核心数据闭环（最高优先级，阻塞用户验收）
- **知识库文档真实入库**：新增「上传文件 → 触发 `ingest_document_task`（arq）→ 解析/切分/向量化落库」的 API，复用 `rag/parsers` 与 `rag/pipeline.ingest_document`。
- **应用 WORK_FLOW 类型**：`application/chat` 与 `chat/chat_message` 在 `type == "WORK_FLOW"` 时改走已迁移的 `WorkflowEngine`（36 节点注册表），替换当前的 SIMPLE 兜底。
- **验收**：`docker-compose.dev.yml` 起 PG+Redis，上传文档→命中测试→工作流应用对话，端到端跑通。

### 阶段 2 — 管理功能闭环
- QA / 表格 / 网页文档真实内容 + 段落 `problem`/`association` 接口。
- 文档 `sync`/`tokenize`/`export`/`export_zip`/`cancel_task` 真实实现。
- 知识库版本 `knowledge_version` 真实快照 + 导出 zip。
- 应用：`chat_record` 历史、improve、导出、open、批量/导入/移动、`add_knowledge`、`prompt_generate`、mcp 配置生效。
- chat：`embed`、`mcp`、`share`、`clear`，workflow 对话。
- 工具：`import`、`debug`、`tool_record`、`mcp_tools`、`store`/`add_internal`。
- 触发器：`batch_delete`/`batch_activate`、source 触发器、`task_record`、`webhook`。
- **验收**：管理端各页面操作可落库并回访。

### 阶段 3 — 模型与 Provider 完善
- `model_params_form` 按 provider impl 动态生成参数表单（替代空 `{}`）。
- Provider 目录补全 + 关键厂商专用 `get_model` 实现。
- 多媒体节点真实 SDK 接入（tts/stt/tti/ttv）经 `get_tts/get_stt/get_tti/get_ttv` 注册表；`uv sync --extra multimedia` 后可用。
- application / tools 的 mcp 节点真实调用外部 MCP server。

### 阶段 4 — 统计 / 仪表盘与运维
- homepage `tokens_ranking` / `question_ranking` / `user_tokens_ranking` 真实聚合查询。
- `monitoring_aggregation` 与三个 export 真实数据生成（导出 zip）。
- 权限持久化：登录态 `role`/`permissions` 改为反查 `WorkspaceUserResourcePermission`，而非前端式构造。
- 邮件/验证码：`send_email` / `check_code` / 真实 `captcha`（RSA 已就绪）。
- oss `get_url` 签名 URL。

### 阶段 5 — 兼容性与验证收尾
- 多 workspace 路径作用域：确认前端已适配 FastAPI 去除 `workspace/<id>` 前缀的设计（或补充兼容层）。
- 全量接口契约测试：对比 Django 与 FastAPI 关键响应结构（`res.data` 字段）。
- CI 增加 PG+Redis 集成测试（或 mock 上游服务），覆盖阶段 1–4 的真实路径。
- 同步更新 `backend/docs/REFACTOR_STATUS.md`，将本路线图进展回写。

---

## 附录 A：端点统计明细（grep `path(|re_path(` / `@router.{method}(`）

| 文件 | 路由/URL 数 |
|------|:---:|
| `apps/users/urls.py` | 21 |
| `apps/knowledge/urls.py` | 94 |
| `apps/application/urls.py` | 38 |
| `apps/tools/urls.py` | 31 |
| `apps/models_provider/urls.py` | 15 |
| `apps/chat/urls.py` | 21 |
| `apps/trigger/urls.py` | 11 |
| `apps/system_manage/urls.py` | 9 |
| `apps/oss/urls.py` | 2 |
| `apps/homepage/urls.py` | 13 |
| `apps/folders/urls.py` | 2 |
| `apps/local_model/urls.py` | 5 |
| **Django 合计** | **262** |
| `backend/app/api/auth.py` | 14 |
| `backend/app/api/knowledge.py` | 73 |
| `backend/app/api/models.py` | 25 |
| `backend/app/api/application.py` | 18 |
| `backend/app/api/chat.py` | 14 |
| `backend/app/api/tools.py` | 19 |
| `backend/app/api/trigger.py` | 7 |
| `backend/app/api/system.py` | 10 |
| `backend/app/api/oss.py` | 3 |
| `backend/app/api/homepage.py` | 14 |
| `backend/app/api/locales.py` | 2 |
| `backend/app/api/health.py` | 1 |
| `backend/app/local_model/router.py` | 3 |
| **FastAPI 合计** | **203** |
