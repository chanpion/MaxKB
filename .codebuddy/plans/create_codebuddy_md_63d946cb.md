---
name: create_codebuddy_md
overview: 为 MaxKB 仓库创建 CODEBUDDY.md，供后续 CodeBuddy 实例快速了解项目架构与常用命令。重点描述后端 Django 应用划分、工作流引擎、模型提供方抽象，以及前后端开发/构建/测试/启停命令。
todos:
  - id: create-codebuddy-md
    content: 在仓库根创建 CODEBUDDY.md，写入固定前缀、常用命令与各 ≤100 词描述、≤1600 词高层架构
    status: completed
  - id: verify-accuracy
    content: 核对命令与架构描述与代码事实一致，确认无泛泛规范、未重复造轮子
    status: completed
    dependencies:
      - create-codebuddy-md
---

## 用户需求

用户通过 `@command://init` 触发，要求分析 MaxKB 代码库并创建根目录的 `CODEBUDDY.md` 文件，供未来的 CodeBuddy（Coding IDE Agent）在本仓库中工作时参考。

## 交付内容

1. 文件头部固定前缀：`# CODEBUDDY.md This file provides guidance to CodeBuddy when working with code in this repository.`
2. **常用命令**章节：包含构建、lint、运行测试、运行单个测试、本地开发等命令。每条命令的描述不得超过 100 词。
3. **高层架构**章节：不超过 1600 词，聚焦需要跨多个文件才能理解的"大局"架构（Django 项目结构、服务启动与运行模式、API 路由、配置系统、RAG 流水线、工作流/Agent 引擎、模型提供方抽象、异步与调度、前端结构、国际化）。

## 约束

- 已检索确认仓库根不存在 AGENTS.md / CODEBUDDY.md / CLAUDE.md / .cursorrules / .github/copilot-instructions.md，因此新建 `CODEBUDDY.md`（不创建 AGENTS.md）。
- 不重复造轮子，不写"提供有用错误信息""为所有工具写单测"等泛泛规范；不罗列易发现的每个组件/文件。
- 包含 README.md 中的重要内容（技术栈、默认凭据、端口、Docker 启动）。
- 命令与架构描述必须基于已核证的代码事实，不得编造。

## 技术事实（用于撰写 CODEBUDDY.md 的准确内容）

### 项目结构（monorepo）

- 后端：Django 5.2 项目位于 `apps/`，`apps/maxkb/` 为项目配置（settings / urls / const / conf），其余为功能 app。
- 前端：`ui/`（Vue3 + Vite + TS + Element Plus + Pinia）。
- 部署：`installer/`（Dockerfile、start-maxkb.sh、init.sql）。
- 技术栈：Vue.js / Python+Django / LangChain / PostgreSQL+pgvector / Redis。

### 常用命令（每条描述 ≤100 词，写入文件时照此呈现）

**后端依赖安装**
使用 uv（pyproject.toml 声明）。在项目根执行 `uv sync` 安装全部依赖（Django、LangChain、Celery、sentence-transformers 等）。若仅本地开发可加 `--no-install-project`。无 requirements.txt，请勿用 pip 直接安装。

**后端本地开发（Web）**
`python main.py dev web` 在 0.0.0.0:8080 启动 Django runserver（会先 collect_static 与 migrate）。需先在根目录放 `config.yaml` 或设 `MAXKB_CONFIG=1`，并启动 PostgreSQL 与 Redis。

**后端本地开发（异步任务）**
`python main.py dev celery` 启动 Celery worker（celery_default / celery_model），用于处理向量化、模型推理等异步任务。Web 与 Celery 需分别启动。

**数据库迁移**
`python main.py upgrade_db` 执行 Django migrate（含数据库未就绪重试）。也可在 `apps/` 目录执行 `python manage.py migrate`，需 `DJANGO_SETTINGS_MODULE=maxkb.settings`（manage.py 已默认设置）。

**收集前端静态资源**
`python main.py collect_static` 将 `ui/dist` 静态文件收集到 `apps/static`，供 Django 托管 admin/chat 两个 SPA。

**生产启动服务**
`python main.py start all -d` 以守护进程启动全部服务（gunicorn web + celery）。可单独启动 `web` / `task`。服务管理命令：`start` / `stop` / `restart` / `status`（位于 apps/common/management/commands）。

**后端 Lint**
`ruff check apps`（ruff 0.15.12，line-length=120）。也可 `ruff format apps` 自动格式化。pyproject.toml 已配置 ruff，无需额外配置。

**后端运行全部测试**
在 `apps/` 目录执行 `python manage.py test <app>`，例如 `python manage.py test application`。仓库无 pytest 配置，统一使用 Django test runner。

**后端运行单个测试**
`python manage.py test application.tests.TestClass.test_method` 运行指定测试方法；或用 `application.tests.TestClass` 运行整个测试类。需在 `apps/` 目录、且依赖的 PostgreSQL/Redis 可用。

**前端安装依赖**
`cd ui && npm install` 安装 Vue3/Vite/Element Plus 等依赖。

**前端本地开发（管理台）**
`cd ui && npm run dev` 启动 admin SPA（端口见 `ui/env/.env` 的 VITE_APP_PORT，默认 3001）。Vite 将 `/admin/api`、`/chat/api` 代理到 127.0.0.1:8080。

**前端本地开发（用户对话页）**
`cd ui && npm run chat` 以 chat 模式启动用户端 SPA（chat.html 入口）。同样代理 API 到后端 8080。

**前端构建**
`cd ui && npm run build` 构建 admin；`npm run build-chat` 构建 chat；产物输出到 `ui/dist/<base>`。构建后需后端 collect_static。

**前端 Lint / Format / 类型检查**
`npm run lint`（eslint --fix）、`npm run format`（prettier）、`npm run type-check`（vue-tsc 类型检查）。建议在提交前运行。

### 高层架构要点（写入文件，≤1600 词，聚焦跨文件"大局"）

1. **运行入口与服务模式**：`main.py` 为统一入口，`DJANGO_SETTINGS_MODULE=maxkb.settings`，将 `apps/` 注入 path。action 有 start/dev/upgrade_db/collect_static。服务分 web（gunicorn/runserver）、celery（celery_default、celery_model 异步 worker）、local_model（vLLM 模型服务）。`maxkb/urls/__init__.py` 按 `SERVER_NAME` 选择 web 或 model 路由配置。

2. **Django 项目与功能 App**：`apps/maxkb/` 仅放配置；功能 app 包括 common（共享基础设施）、application（Agent + 工作流引擎）、knowledge（RAG）、models_provider（模型提供方）、chat（对话 API + MCP）、tools（函数库）、trigger（定时触发）、oss（对象存储）、system_manage、users、folders、homepage、local_model。`INSTALLED_APPS` 见 `maxkb/settings/base/web.py`。

3. **API 路由**：`maxkb/urls/web.py` 把各 app 的 `urls.py` 挂载到 `/admin/api/`（管理台）与 `/chat/api/`（用户端），静态 SPA 由 `apps/static/{admin,chat}` 提供。DRF 自定义 `AnonymousAuthentication` 与统一异常处理（`common.exception.handle_exception`）。

4. **配置系统**：`maxkb/conf.py` 的 `ConfigManager` 从 `config.yaml`（默认 `/opt/maxkb/conf`，设 `MAXKB_CONFIG` 后从项目根）或环境变量（`MAXKB_CONFIG_TYPE=ENV`，前缀 `MAXKB_`）加载。`Config` 默认值含 DB（pgvector，dj_db_conn_pool）、Redis（缓存 + Celery broker）、本地模型绑定地址、路径、语言。

5. **RAG 流水线（knowledge）**：文档上传/爬取 → `common/chunk` 切分 → 向量化 → pgvector 存储（`knowledge/vector`）。工作流中的检索节点从向量库取上下文。

6. **工作流 / Agent 引擎（application/flow）**：系统核心。`WorkflowManage`（workflow_manage.py）按图执行节点：通过 `step_node.get_node(type, workflow_mode)` 从 `node_map` 注册表构造节点实例（`step_node/__init__.py` 的 `node_list`），用 `ThreadPoolExecutor`（200 worker）跑 DAG，支持流式（SSE 分块）与阻塞两种模式，处理分支（`branch_id`）、异常、循环、全局/对话/步骤变量与提示词变量替换。节点实现 `INode`（`i_step_node.py`）：`valid_args`/`run`/`write_context`/`get_details`。新增节点类型 = 实现 `BaseXxxNode` 并加入 `node_list` 注册。节点 `support` 列表区分工作流模式（简单/高级）。

7. **模型提供方抽象（models_provider）**：`IModelProvider`（`base_model_provider.py`）定义获取模型信息/凭据的接口；`impl/` 下每个厂商（openai/deepseek/qwen/anthropic/gemini/ollama/vllm/local_model…）实现各自凭据与客户端；`base_chat_open_ai`/`base_tti`/`base_tts`/`base_stt` 为通用基类。模型按类型（LLM/TTI/TTS/STT/reranker/embedding）引用。

8. **异步与调度**：Celery（celery_default、celery_model）处理嵌入与模型任务；`django_celery_beat` + `django_apscheduler` 与 trigger app 做定时触发。

9. **前端**：Vue3 + TS + Vite + Element Plus + Pinia + vue-router + vue-i18n。双入口 admin.html/chat.html；工作流编辑器基于 `@logicflow/core`。Vite 将 API 代理到 8080；构建产物经 collectstatic 进入 `apps/static`。

10. **国际化**：Django gettext（locales/）+ vue-i18n；支持语言由 `conf.get_languages()` 决定。

### 关键约束（写入文件）

- 默认管理员 `admin` / `MaxKB@123..`，Web 端口 8080。
- 开发需 PostgreSQL（pgvector）+ Redis。
- 后端 `manage.py` 位于 `apps/`；根 `main.py` 用于服务编排。
- 新增工作流节点、模型提供方、API 端点均应遵循上述注册/挂载约定，复用 common 基础设施。