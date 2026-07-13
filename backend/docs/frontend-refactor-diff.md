# frontend（Next.js 重构）vs ui（Vue3 原版）差异分析 & 实现计划

> 文档目标：对比重构前端 `frontend/` 与原前端 `ui/`；并给出将 `frontend/` 对标 `ui/` 的分阶段实现路线图。
> 重要修订（2026-07-13）：本期 `frontend/` 的**目标后端为旧版 Django `apps/`**，而非 FastAPI `backend/`。详见下文「关键发现」。

---

## 1. 技术栈对比

| 维度 | `frontend/`（重构） | `ui/`（原版） |
|---|---|---|
| 框架 | Next.js 14（App Router, RSC） + React 18 | Vue 3 + Vite SPA（admin.html / chat.html 双入口） |
| UI 组件库 | antd v5 | Element Plus |
| 状态管理 | zustand（8 store） | Pinia（12 store） |
| 国际化 | next-intl（`messages/zh.json`+`en.json`） | vue-i18n（`locales/`，86 个 ts） |
| 样式 | CSS-in-JS（antd）+ 内联 + 1 全局 css | SCSS + `use-element-plus-theme` 运行时换肤 |
| 图表 | echarts 6 | echarts 5 |
| 工作流编辑器 | ❌ 无 | LogicFlow（`@logicflow/core` + `workflow/` 168 文件） |
| 目标后端 | **Django `apps/`**（本期） | 原 Django `apps/` |

---

## 2. 规模对比

| 指标 | `frontend/` | `ui/` |
|---|---|---|
| 页面/视图 | 29 个 `page.tsx` | 227 个 `.vue` 视图 + 168 个 workflow 文件 |
| API 文件 | 17 个 | 83 个（多租户/多角色拆分） |
| 组件 | 27 个 | 164 个 |

`frontend/` 目前是**半成品后台骨架**（登录 + 各模块列表/详情页），远未覆盖 `ui/` 全部功能。

---

## 3. 关键发现：frontend 已面向 Django `apps/` 后端

经逐文件核对，`frontend/` 的 API 层实际是按 **Django `apps/` 契约**编写的，与 FastAPI `backend/` 并不兼容：

1. **接口路径一致（Django 风格）**
   - `frontend/src/lib/api/knowledge/knowledge.ts`：`prefix = /workspace/${ws}/knowledge`，分页 `get(.../${page.current_page}/${page.page_size})`。
   - `apps/knowledge/urls.py`：`workspace/<str:workspace_id>/knowledge`、`<int:current_page>/<int:page_size>` —— 完全对应。
   - `frontend/src/lib/api/login.ts`：`/user/login`、`/user/profile`、`/profile`（取 rsa）、`/user/captcha` —— 对应 `apps/users/urls.py`。
2. **响应信封一致**：Django `apps/common/result/result.py` 返回 `{code, message, data}`；`frontend/src/lib/request/index.ts` 拦截器检查 `data.code !== 200`。
3. **分页字段一致**：Django `Page` 返回 `{total, records, current, size}`；frontend `pageRequest={current_page, page_size}` 走路径分页。
4. **RSA 登录一致**：`useUserStore.fetchRsa` 从 `/profile.rsa` 取公钥；登录页 RSA 加密 `{username,password,captcha}` 后发送 `{encryptedData, username}`，对应 `apps/users/serializers/login.py` 的 `LoginSerializer.login`。
5. **代理配置指向 Django**：`next.config.mjs` 把 `/admin/api/*`、`/chat/api/*`、`/oss/*` 代理到 `API_TARGET`；`.env.local` 的 `API_TARGET=http://10.58.12.61:8080`（Django 实例）。

**与 FastAPI `backend/` 不兼容的证据**：`backend/app/api/knowledge.py` 使用 `prefix="/api/knowledge"`（无 `/admin/api` 前缀、无 `workspace` 路径段、响应体为 `{records, total}` 等、用 HTTP 状态码而非 `{code:200}` 信封）。因此 `frontend/` 当前**不**对接 FastAPI。`CODEBUDDY.md` 中「frontend 对接 FastAPI」与代码实际不符。

> 结论：`frontend/` 在结构上已面向 Django `apps/`，但需**验证并修复与 Django 的剩余偏差**以达到端到端可用；FastAPI 对齐移出本期范围（`backend/` 仅作为并行重构存在，frontend 不依赖它）。

---

## 4. frontend↔Django `apps/` 契约对照

| 契约项 | Django `apps/` | `frontend/` 现状 | 是否就绪 |
|---|---|---|---|
| 基础路径 | `/admin/api`（挂载） | `baseURL=/admin/api` + rewrites 代理 | ✅ |
| 鉴权头 | `AUTHORIZATION: Bearer <token>` | 请求拦截器注入 | ✅ |
| 响应信封 | `{code,message,data}`，`code=200` 成功 | 拦截器检查 `code`，`unwrap` 返回信封 | ⚠️ 需确认调用方统一用 `.data` |
| 分页 | `{total, records, current, size}` | `pageRequest={current_page,page_size}` + 表组件 | ⚠️ 需逐页核对字段读取 |
| 登录 | `/user/login` 收 `{encryptedData,username}` | 已实现 RSA 加密 | ✅ |
| 公钥 | `/profile` 的 `data.rsa` | `useUserStore.fetchRsa` | ✅ |
| 验证码 | `/user/captcha?username=` → `{captcha}` | 已实现 | ✅ |
| workspace | 路径含 `<workspace_id>` | `getWorkspaceId()` 自动选首个 | ✅（需联调切换） |
| 文件上传 | `multipart/form-data`，特定字段名 | ❌ 未实现 | ❌ Phase 0 补齐 |
| 流式/SSE | chat 走 SSE（`/chat/api/...`） | ❌ 未实现（无对话页） | ❌ Phase 2 补齐 |

---

## 5. frontend 相对 ui 的功能缺口

1. **工作流编排 UI**：`ui/` 有完整 LogicFlow 画布（67 节点、44 图标、插件体系）；`frontend/` 仅 list/overview/setting/chat-log/access，**无画布**。
2. **用户对话界面**：`ui/` 有 `chat/`（index/mobile/embed/share/auth）；`frontend/` 无独立对话页。
3. **文档片段（paragraph）管理**：`frontend/` 有 `paragraph.ts` 类型/API 但**无页面**。
4. **文档标签管理**：`ui/` 有 `document/tag/*`；`frontend/` 缺失。
5. **模板市场**：`ui/` 有 `application/template-store/*`；`frontend/` 缺失。
6. **多工作台/资源授权**：`ui/` 有 `system-resource-management/*` + `system-shared/*`；`frontend/` 仅有精简版 `resource-authorization-drawer`。
7. **登录增强**：`ui/` 有 ForgotPassword/ResetPassword；`frontend/` 仅基础登录。
8. **文档导入渠道**：`ui/` 支持 Lark/Workflow 导入；`frontend/` 仅基础上传占位。
9. **应用参数深度**：`ui/` 的 `ApplicationSetting.vue` ~59KB（MCP/记忆/TTS/STT/推理参数多抽屉）；`frontend/` setting 仅 2.6KB。

### frontend 独有、建议保留的抽象
`dynamics-form`（动态表单）、`folder-virtualized-tree`（虚拟树）、`resource_mapping`、`resource-authorization-drawer`、`LocaleSwitch`、`ThemeToggle`（暗色，antd `theme.darkAlgorithm`）。

---

## 6. 实现计划（目标后端：Django `apps/`）

### Phase 0：适配旧版 apps 后端（契约对齐 + 端到端跑通）—— 本期最高优先级
1. **契约审计**：逐一比对 `frontend/src/lib/api/*`（17 文件）与 Django 各 app `urls.py` + view（method / path / query-vs-body / 响应结构），产出偏差表并修正（路径拼写、参数位置等）。
2. **响应解包统一**：确认信封 `.data` 访问一致；分页读取 `data.records` / `data.total`（Django `Page` 返回 `{total,records,current,size}`），修正按 `list`/`data` 误读处。
3. **登录 / RSA / 验证码**：确认 `fetchRsa`→`/profile.rsa`、`/user/login`、`token` 写 localStorage + `MAXKB-TOKEN` cookie、中间件路由保护；联调验证码流。
4. **workspace 上下文**：确认 `getWorkspaceId()` 来源与切换逻辑正确驱动所有 `/workspace/{ws}/...` 请求。
5. **文件上传（multipart）**：实现通用 upload 封装（字段名对齐 Django），接入文档/知识库导入页。
6. **SSE/流式消费**：实现 fetch-stream 解析，对齐 Django chat SSE 事件格式（Phase 2 复用）。
7. **本地联调**：`python main.py dev web`（Django 8080，需 PG+Redis）+ `next dev`，逐页验证列表/详情/增删改/导入/导出。

### Phase 1：工作流编辑器（最大功能缺口）
React 封装 `@logicflow/core` + 节点注册表，对齐 Django `application` workflow 接口（图 JSON 存取、节点执行）。

### Phase 2：用户对话界面
独立对话页（SSE 对接 Django chat）；mobile/embed/share 路由（参考 `ui/src/views/chat/`）。

### Phase 3：知识库二级功能
片段管理页、文档标签管理、模板市场、Lark/Workflow 导入（对齐 `apps/knowledge/urls.py` 既有端点）。

### Phase 4：多工作台资源授权体系
复用 `resource-authorization-drawer`；对接 Django `system_manage` 跨应用/知识库/模型/工具/触发器的资源授权。

### Phase 5：应用深度参数 + 登录增强
应用设置抽屉（MCP/长期记忆/TTS/STT/推理参数，对齐 Django `application` 接口）；忘记/重置密码页。

---

## 7. 约束 / 注意
- 本期 `frontend/` **只对接 Django `apps/`**，不依赖 FastAPI `backend/`；表结构以 Django 为准（`backend/` 仅 `db.py` 不 `create_all`，表由 Django 创建）。
- 联调需 PostgreSQL(pgvector)+Redis 真实环境（本仓库 CI 仅 lint + 单测，无服务容器）。
- 保持 `frontend/` 现有技术栈一致（Next.js + antd + zustand + next-intl + 暗色主题），复用 `dynamics-form`、`folder-virtualized-tree` 等抽象。
- 实施时严格对照 `ui/src`（Vue 端）的接口调用与交互，逐接口映射。

## 8. 参考代码位置
- 差异文档：`backend/docs/frontend-refactor-diff.md`（本文件）
- frontend：`frontend/src/app/(admin)/{home,knowledge,application,tool,model,trigger,system}`、`frontend/src/lib/api/`、`frontend/src/store/`、`frontend/next.config.mjs`
- 原前端对照：`ui/src/views/`、`ui/src/workflow/`（LogicFlow）、`ui/src/router/modules/`、`ui/src/layout/`、`ui/src/api/`、`ui/src/request/index.ts`
- Django 后端：`apps/maxkb/urls/web.py`、`apps/knowledge/urls.py`、`apps/users/urls.py`、`apps/users/serializers/login.py`、`apps/common/result/result.py`
- FastAPI（本期不对接）：`backend/app/api/knowledge.py`
