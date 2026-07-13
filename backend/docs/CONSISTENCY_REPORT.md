# MaxKB 重构后端 vs 原 Django 后端 —— 功能一致性对比报告

> 对比方式：纯静态代码对比（未启动任何服务，未连接 PostgreSQL/Redis，未执行 `create_all`/`alembic`）。
> 对比日期：2026-07-13
> 重构侧根目录：`/Users/logenswolf/IdeaProjects/MaxKB/backend/app`（FastAPI + SQLModel + Agno）
> 原后端根目录：`/Users/logenswolf/IdeaProjects/MaxKB/apps`（Django 5.2 + DRF + LangChain）

---

## 0. 总体结论

**结论：重构后端已完成"骨架级"对齐，但尚不能视为与原后端功能一致。**

- **数据模型层**：表名 44/44 对齐，但存在 **1 张表完全缺失**（`knowledge_action`）与 **1 张表字段缺失**（`application_version` 缺 `workspace_id`/`application_name`）。这是上线阻塞级缺口。
- **API 接口层**：顶层模块（user/knowledge/model/application/chat/tool/trigger/system/oss/homepage）全部挂载，但 **大量二级端点缺失**（导入/导出、分页路径、标注改进、embed/mcp/share 等约 40+ 端点）。
- **行为/算法层**：核心链路（RAG 入库、工作流执行、Chat SSE）已有实现，但存在 **切分断句算法偏差、检索缺 keywords 模式、向量化缺 Termbase 词典注入、Agent 记忆策略不同、部分工作流节点为占位/透传、Provider 仅映射未写厂商专用实现** 等实质性差异。

建议：在补齐 P0/P1 缺口并完成真实 PG/Redis 端到端验证前，重构后端不可直接替代原 Django 后端。

---

## 1. 对比基线说明

### 1.1 路径归一化机制（影响 API 对照）
重构侧通过 `PathRewriteMiddleware`（`backend/app/middleware/path_rewrite.py`）在请求进入路由前做归一化：
- 将 `/admin/api/*` 与 `/chat/api/*` 统一重写为 `/api/*`；
- 剥离 `/api/workspace/<wid>/` 段（`workspace` 固定为 `"default"`，见各 router 的 `workspace_id="default"` 默认值）；
- 别名映射如 `/api/user_manage → /api/user/manage`。

因此下文的 API "路径对齐"判断，均以"剥离前缀与 workspace 段后语义对等"为准。

### 1.2 表结构约定
两端均**无真实外键**，沿用纯 `*_id` 列（`db_constraint=False`）；mptt 树表均保留 `tree_id/level/lft/rght` + `parent_id` 邻接。重构侧 44 张表的 `__tablename__` 与 Django 侧 `Meta.db_table` 为对照基准。

---

## 2. API 接口层面对比

### 2.1 顶层路由挂载对照

| 维度 | 重构侧 | 原 Django 侧 |
|---|---|---|
| 健康检查 | `GET /api/health` | 无专门 health |
| 用户/鉴权 | `/api/user` | `users.urls`（admin 前缀）|
| 应用 | `/api/application` | `application.urls`（admin 前缀）|
| 会话/聊天 | `/api/chat` | `chat.urls`（chat 前缀）+ admin 前缀 `chat_message` |
| 知识库 | `/api/knowledge` | `knowledge.urls`（admin 前缀）|
| 模型 | `/api/model` | `models_provider.urls`（admin 前缀）|
| 工具 | `/api/tool` | `tools.urls`（admin 前缀）|
| 触发器 | `/api/trigger` | `trigger.urls`（admin 前缀）|
| 系统 | `/api/system` | `system_manage.urls`（admin 前缀）|
| OSS | `/api/oss` | `oss.urls`（admin + chat 前缀）|
| 首页 | `/api/homepage` | `homepage.urls`（admin 前缀）|
| 国际化 | `/admin/locales`、`/chat/locales` | `apps/locales` 目录 |
| 本地模型 | `/api/local_model/v1` | `models_provider.urls`（local_model 模式）|

### 2.2 缺失端点清单（Django 有 / FastAPI 无）

#### application 模块
| Django 端点 | 功能 | 状态 |
|---|---|---|
| `POST application/folder/<fid>/import` | 应用模板导入 | ❌ 缺失 |
| `GET application/<id>/application_token_usage` | Token 用量统计 | ❌ 缺失 |
| `GET application/<id>/top_questions` | 热门问题统计 | ❌ 缺失 |
| `GET application/<id>/application_version`（分页） | 版本分页 | ❌ 缺失（仅全量 list）|
| `GET application/<id>/application_key/<key_id>` | 单查 API Key | ❌ 缺失（仅 list/create/delete）|
| `GET application/<id>/export` | 应用导出 | ❌ 缺失 |
| `POST application/<id>/access_token` | 创建访问令牌 | ❌ 缺失（仅 GET/PUT）|
| `POST application/<id>/add_knowledge` | 对话记录加知识库 | ❌ 缺失 |
| `GET application/<id>/chat/export` | 对话导出 | ❌ 缺失 |
| `GET application/<id>/chat/<cid>/chat_record` 等分页 | 对话/记录分页、单条 | ❌ 缺失 |
| `POST .../chat_record/<rid>/improve`（含 2 个段落级路径）| 标注改进 | ❌ 缺失 |
| `GET application/<id>/open` | 开启应用 | ❌ 缺失 |
| `POST application/<id>/text_to_speech` / `speech_to_text` / `play_demo_text` | TTS/STT/演示播报 | ❌ 缺失 |
| `GET application/<id>/mcp_tools` | MCP 工具列表 | ❌ 缺失 |
| `POST application/<id>/model/<mid>/prompt_generate` | 提示词生成 | ❌ 缺失 |
| `POST application/store/application_template` | 应用模板库 | ❌ 缺失 |
| `POST application/batch_clean_time` / `batch_move` / `batch_delete` | 批量操作 | ❌ 缺失 |

FastAPI 已覆盖：list/create/get/update/delete、publish、application_key(list/create/delete)、access_token(get/put)、application_version(list/get)、stats、chat(POST SSE)、folder(list/create)。

#### chat 模块
| Django 端点 | 功能 | 状态 |
|---|---|---|
| `GET embed` | 嵌入式对话组件 | ❌ 缺失 |
| `POST mcp` | MCP 协议入口 | ❌ 缺失 |
| `GET historical_conversation/<p>/<s>` | 历史对话分页 | ❌ 缺失（仅 query 分页）|
| `POST historical_conversation/clear` | 清空历史对话 | ❌ 缺失 |
| `GET historical_conversation/<cid>`（operate）| 单对话操作 | ❌ 缺失 |
| `GET historical_conversation/<cid>/record/<rid>` | 单记录详情 | ❌ 缺失 |
| `GET share/<link>` / `<app_id>/chat/<cid>/share_chat` | 分享链接 | ❌ 缺失 |
| `GET vote/...` | 评分 GET 形式 | ❌ 缺失（仅 PUT）|

FastAPI 已覆盖：auth/anonymous、profile、application/profile、open、chat_message、historical_conversation(list/record list)、delete、vote(PUT)、edit_abstract、chat/completions、tts、stt、captcha。

#### knowledge 模块
FastAPI 已覆盖基础的文档/段落/问题 CRUD 与入库触发，但 Django 的 **批量导入、向量检索测试（hit_test）、文档迁移/同步** 等二级端点未全部对齐。

#### auth 模块
| Django 端点 | 功能 | 状态 |
|---|---|---|
| `user/send_email` | 邮件发送 | ❌ 缺失 |
| `user/check_*` 等校验端点 | 校验 | ❌ 部分缺失 |

FastAPI 已覆盖：login、profile/me、list、logout、re_password、captcha、manage(CRUD)、language、password。

### 2.3 新增端点（FastAPI 有 / Django 无）
- `GET /api/user/me`（Django 由 profile 覆盖，语义新增个人端点）
- `GET /api/health`（Django 无专门 health）

### 2.4 鉴权方式差异
- 重构侧：JWT(HS256) + RBAC `require_roles`（`backend/app/core/security.py`），无状态。
- Django 侧：`AnonymousAuthentication` + Session/Token 混合，集中在 `common/exception.handle_exception`。
- 登录态机制本质不同（JWT 无状态 vs Django 会话态），已通过 `LegacyResponseMiddleware` 兼容响应体结构，但 `logout` 在 JWT 下恒成功、无真正失效。

---

## 3. 数据模型层面对比

### 3.1 总体概览
| 维度 | 重构侧 | Django 侧 |
|---|---|---|
| 模型类声明数 | 44 个 `table=True` | 48 个类（3 组重复指向同表，去重后 44 张）|
| 去重后实际表数 | **44** | **44** |
| 表名对齐 | 43/44 一致 | 43/44 一致 |

### 3.2 致命缺口：表级缺失
**`knowledge_action` 表完全缺失**
- Django 定义：`apps/knowledge/models/knowledge_action.py:33-49`（`KnowledgeAction`，字段 `id`/`knowledge_id`/`state`(默认 STARTED)/`details`(JSON)/`run_time`/`meta`(JSON) + 2 mixin = 8 列）。
- 重构侧：`backend/app/models/` 下无任何对应类，全目录 `grep knowledge_action` 命中 0 次。
- **影响**：知识库异步动作的状态追踪无任何数据模型，迁移/读写将无对应表。

### 3.3 字段缺失
**`application_version` 字段差异**
- Django：`apps/application/models/application.py:142-197` 含 `workspace_id`、`application_name` 等字段（共 45 列）。
- 重构侧：`backend/app/models/application.py` 对应类为 43 列，**缺 `workspace_id`、`application_name`**。
- **影响**：Django 写入这些字段的迁移/同步会失败或字段丢失。

### 3.4 其余表字段级对照（均一致）
按 app 分组，字段数（含 `AppModelMixin`/`AppTableBase` 注入的 `create_time`/`update_time`）对齐：

| App | 表 | 状态 |
|---|---|---|
| application | application_folder / application / application_knowledge_mapping / application_chat / application_chat_record / application_chat_share_link / application_chat_user_stats / application_long_term_memory / application_access_token / application_api_key | ✅ 一致 |
| application | application_version | ⚠️ 缺 2 字段 |
| knowledge | knowledge_folder / knowledge / knowledge_workflow / knowledge_workflow_version / document / tag / document_tag / paragraph / problem / problem_paragraph_mapping / termbase / embedding / file | ✅ 一致 |
| knowledge | knowledge_action | ❌ 表缺失 |
| model/system/user/tools/trigger | model / system_setting / user / chat_user / user_group / user_group_relation / resource_chat_user_authorize / resource_chat_user_group_authorize / log / resource_mapping / workspace_user_resource_permission / tool_folder / tool / tool_record / tool_workflow / tool_workflow_version / event_trigger / event_trigger_task / event_trigger_task_record | ✅ 一致 |

---

## 4. 行为/算法层面对比

### 4.1 RAG 流水线
| 环节 | 重构实现 | Django 实现 | 结论 |
|---|---|---|---|
| 文档解析 | `rag/parsers.py`：txt/md/pdf(字号标题检测)/html(BeautifulSoup+markdownify)/docx(python-docx 表格转 md)/xlsx/csv/zip | `knowledge/serializers/document.py` + `common/handle/impl/text/*`：同上 + **网页实时抓取 + 数据库/API 数据源** | ⚠️ 缺失网页抓取/数据源解析；图片/音视频内嵌解析被显式跳过（`parsers.py:14-15,232`）|
| 切分 | `rag/splitter.py`：markdown 标题层级 + 空行切分；`smart_split_paragraph` 仅按 `\n` + 硬长度 `[\S\s]{1,limit}`（`splitter.py:119-132`）| `common/utils/split_model.py`：`smart_split_paragraph` 在 limit 内**优先按中英文句号/问号/感叹号断句**（`split_model.py:319-335`）| ⚠️ **算法不一致**：长段落落点选择不同，chunk 边界会偏离 |
| 默认 limit | 4096（`splitter.py:249,259`；`pipeline.py:65`）| 默认 100000，但文档上传实际传 4096（`document.py:1237`）| ✅ 默认值对齐 |
| 向量化 | `rag/embed.py`：normalize/256 字符分块/jieba/to_ts_vector/batch 10 落库 | `knowledge/vector/pg_vector.py`：同上 + **按 knowledge_id 查 Termbase 用户词典注入 jieba**（`pg_vector.py:58-64,94-101`）| ⚠️ **缺失 Termbase 用户词典注入**，专有名词分词会劣化 |
| 检索 | `agents/retriever.py`：embedding / blend 两种 | `knowledge/vector/pg_vector.py`：`EmbeddingSearch`/`KeywordsSearch`/`BlendSearch` 三种 | ⚠️ **缺失 keywords（关键词）检索模式** |

### 4.2 工作流引擎
- **节点类型覆盖**：重构 `workflows/nodes/__init__.py` 注册 **36 个节点 type**，与 Django `step_node/__init__.py` 的 36 个 `type` 完全对齐（含 `reply-node` 别名）。✅ 类型级对齐。
- **实现深度差异**：多个节点是**占位/透传**实现（如 `document_split_node`、`data_source_local`、`data_source_web`、`tool_start_node` 等在 REFACTOR_STATUS 中自述为"占位/透传"），并未实现 Django 的完整业务逻辑。⚠️
- **结构差异**：Django `node_map = {type: {workflow_mode: node}}`（`step_node/__init__.py:59`）含 `workflow_mode` 维度（simple/advanced 等，由节点 `support` 列表声明）；重构侧为扁平 `{type: node}`（`workflows/nodes/__init__.py:54`）。⚠️ 工作流模式维度丢失。
- **引擎能力**：图遍历 + AND/OR 扇入 + SSE 流式 + 分支（`branch_id`）+ 表单中断恢复（`interrupt`）均有实现，与 Django `WorkflowManage` 大体对应。✅

### 4.3 Chat Agent
| 维度 | 重构 | Django | 结论 |
|---|---|---|---|
| 记忆策略 | Agno `PostgresMemory`（对话历史记忆）| Celery 异步 `extract_long_term_memory` 调 LLM 提炼用户画像写入 `application_long_term_memory` 表 | ⚠️ **机制本质不同**：重构无"LLM 提炼长期记忆"等价实现 |
| 检索增强 | `PgVectorRetriever` + `get_embedder` | 工作流检索节点 + 对话流水线 | 部分对齐（缺 keywords，见 4.1）|

### 4.4 Provider 抽象
- 重构 `providers/registry.get_llm/get_embedder/get_tts/get_stt/get_tti/get_ttv` + `catalog.py` 覆盖原生/OpenAI 兼容/讯飞自研，统一回退。
- Django `models_provider/impl/` 为每个厂商（openai/deepseek/qwen/anthropic/gemini/ollama/vllm/azure/aws_bedrock/xinference/tencent/zhipu 等）写专用 `IModelProvider` 子类。
- **差异**：重构 `ModelProvider` 子类仅作加密/校验基类，**未给每个厂商写专用 `get_model`**（REFACTOR_STATUS 已自述）。⚠️ 厂商级定制（特殊鉴权/参数/协议）未对齐。

### 4.5 异步任务
- 重构：`app/core/tasks.py` 用 **arq** 替代 Celery，提供 `ingest_document_task`/`enqueue_ingest`/日志清理 cron/按 `event_trigger` 动态注册 cron/`run_trigger`。
- Django：`celery_default`/`celery_model` + `django_celery_beat` + `django_apscheduler` + `trigger` app。
- **结论**：任务覆盖度大体对应，但**真实 PG/Redis 端到端验证未完成**，重试/调度时序等仅 mock 路径覆盖。⚠️

### 4.6 鉴权（口令兼容性）
- 重构 `security.py` 兼容 Django `pbkdf2_sha256` / `bcrypt$` / 原生 `$2b$` / 明文哈希（REFACTOR_STATUS 已修复 split 段数与 `$2b$` 支持）。✅ 口令兼容。
- 但 JWT 无状态与 Django 会话态的差异见 2.4。

---

## 5. REFACTOR_STATUS.md 声明 vs 实际代码

| 文档声明 | 实际代码 | 是否相符 |
|---|---|---|
| "44 张表 `__tablename`/类型/可空/默认值 严格对齐 Django" | 表名对齐，但 **`knowledge_action` 表缺失**、`application_version` 缺 2 字段 | ❌ 不符（有关键缺口）|
| "工作流节点注册表 8 个节点"（已完成段）| 同一文档"已修复"段称 36 个；**代码实际 36 个** | ⚠️ 文档内部矛盾，代码与"36"段一致 |
| "36 个节点类型覆盖 legacy Django 全部节点类型" | 类型 36/36 对齐 ✅，但**部分节点为占位/透传**、**缺 workflow_mode 维度** | ⚠️ 类型对齐但实现深度不符 |
| "Provider 为映射+目录，未给每个厂商写专用 get_model" | 代码确为映射+目录 | ✅ 相符（自述一致）|
| "真实 PG/Redis 端到端验证未完成" | 节点可选 SDK、CI 仅 mock 路径 | ✅ 相符 |

---

## 6. 差距清单与修复优先级

### P0 —— 上线阻塞（必须修复）
1. **`knowledge_action` 表缺失**：在 `backend/app/models/` 补齐 `KnowledgeAction`（对齐 `apps/knowledge/models/knowledge_action.py`）。
2. **`application_version` 字段缺失**：补齐 `workspace_id`、`application_name` 等字段。
3. **核心二级端点缺失**：`application/<id>/open`、`chat/embed`、`chat/mcp`、`chat/share*`、`chat/historical_conversation/clear` 等为前端强依赖，需至少补齐可访问子集。

### P1 —— 高（行为正确性）
4. **切分算法偏差**：`splitter.smart_split_paragraph` 需对齐 Django 的"按中英文句号/问号/感叹号断句"逻辑，否则 chunk 边界与检索效果偏离。
5. **检索缺 keywords 模式**：`PgVectorRetriever` 补充 `KeywordsSearch`（tsvector 关键词检索）。
6. **向量化缺 Termbase 词典注入**：`embed.py`/入库流程按 `knowledge_id` 注入 jieba 用户词典。
7. **工作流节点占位实现**：将 `document_split`/`data_source_*`/`tool_start` 等占位节点补全真实逻辑。
8. **workflow_mode 维度**：重构 `node_map` 恢复 `{type: {workflow_mode: node}}` 维度（`support` 列表）。

### P2 —— 中（功能完整性）
9. **网页实时抓取/数据源解析**：`parsers.py` 补齐 web/数据库/API 数据源解析。
10. **图片/音视频内嵌解析**：补齐 DOCX/文档内嵌媒体的解析（当前显式跳过）。
11. **Agent 长期记忆对齐**：实现 Django 式"LLM 提炼用户画像写入 `application_long_term_memory`"或明确记录行为差异。
12. **Provider 厂商专用实现**：为各厂商补 `get_model` 专用逻辑（特殊鉴权/协议）。

### P3 —— 低（增强）
13. 邮件发送（`user/send_email`）、真实验证码、批量操作端点、应用导入导出/统计端点等。
14. JWT `logout` 真正失效机制（可选，视前端需求）。

---

## 7. 一致性评分（定性）

| 层面 | 覆盖度 | 说明 |
|---|---|---|
| 数据模型（表名）| ~95% | 43/44 表名对齐，1 张表缺失 + 1 张表字段缺失 |
| 数据模型（字段精度）| ~90% | 除上述缺口外，类型/可空/默认值对齐 |
| API（顶层模块）| 100% | 全部挂载 |
| API（端点功能）| ~55% | 核心 CRUD + chat SSE 已覆盖，约 40+ 二级端点缺失 |
| 行为/算法（核心链路）| ~60% | 入库/工作流/对话有实现，但算法细节与节点深度有差距 |
| 行为/算法（检索/记忆/Provider）| ~50% | keywords 检索、长期记忆、厂商专用实现缺失 |

**综合判断**：重构后端处于"可运行骨架 + 核心链路原型"阶段，距"功能一致、可上线替代"仍有 P0/P1 级缺口需补齐，并完成真实 PG/Redis 端到端验证。
