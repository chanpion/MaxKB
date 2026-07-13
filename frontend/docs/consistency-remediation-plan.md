# MaxKB 前端重构一致性补齐实施计划

> 配套文档：`consistency-audit.md`（审计报告）
> 目标：使重构前端 `frontend/`（Next.js）在**页面、功能、布局**上与原前端 `ui/`（Vue）对齐
> 现状前提：30 个 `page.tsx` 骨架 + 布局外壳 + 知识库/模型/登录一条线 + 通用组件库已就绪；**工作流编辑器、用户对话页、五大模块的 API/store 缺失**
> 说明：本计划仅描述"做什么/涉及哪些文件/依赖什么后端接口"，不在此阶段改代码，待确认后执行

---

## 0. 优先级与里程碑

按"先通数据、后补重型模块、再补细节"的顺序分 5 个里程碑：

| 里程碑 | 目标 | 关键产物 | 依赖 |
|---|---|---|---|
| **M0 数据打通** | 让空壳页面能拉到数据 | application/tool/trigger/system/home 的 API + store | 后端对应接口（见 §2） |
| **M1 工作流编辑器** | 还原 LogicFlow 可视化编排 | `frontend/src/workflow/*` + 3 个 workflow 路由页 | 后端 workflow 图接口 + 节点 schema |
| **M2 用户对话页** | 还原终端用户对话窗口 | `frontend/src/app/(chat)/*` + chat API | 后端 chat/stream 接口 |
| **M3 系统子模块补齐** | 资源管理/共享/对话/授权 | system 各子路由 + 授权抽屉对接 | 后端 resource/auth/shared 接口 |
| **M4 细节与一致性收尾** | 登录辅助页、动态菜单、i18n、面包屑 | 多文件 | M0-M3 |

---

## 1. M0 — 数据打通（空壳页面接数据）

**目标**：为 `application / tool / trigger / system / home` 五大页面补齐 API 层与状态管理，使其从"空壳"变为可用。

### 1.1 新建 API 模块（参考已完成的 `lib/api/knowledge/knowledge.ts` 写法）
- `frontend/src/lib/api/application/application.ts`
  - 方法：列表/创建/编辑/删除/详情、概览统计、访问设置、对话用户、对话日志分页
  - 前缀建议：`/workspace/{wsId}/application`
- `frontend/src/lib/api/tool/tool.ts`
  - 方法：列表/创建/编辑/删除、导入、调试
  - 前缀：`/workspace/{wsId}/tool`
- `frontend/src/lib/api/trigger/trigger.ts`
  - 方法：列表/创建/编辑/删除、启停、cron 表达式校验
  - 前缀：`/workspace/{wsId}/trigger`
- `frontend/src/lib/api/system/system.ts`
  - 方法：user（增删改查/角色分配）、role（CRUD/权限分配）、workspace（CRUD/成员）、log（操作日志分页）、setting（theme/auth/email 读写）
  - 前缀：`/api/system`（系统级，非 workspace 前缀，需确认后端路由）
- `frontend/src/lib/api/home/homepage.ts`（即报告中的 `homepageApi`）
  - 方法：统计卡片、Token 排行、问答排行、监控图表数据
- 在 `frontend/src/lib/api/shared-api.ts` 的 `loadSharedApi` 注册上述模块（消除 `application/tool/trigger/system/home` 的 import 报错）。

### 1.2 新建状态管理 store（参考 `lib/store/login.ts` / `folder.ts`）
- `lib/store/application.ts`、`tool.ts`、`trigger.ts`、`system.ts`、`home.ts`
- 各自持有列表/分页/当前选中资源等状态，供页面调用。

### 1.3 页面接数据（仅接已有 page，不新建）
- `application/page.tsx`、`application/[id]/(overview|setting|access|chat-log)/page.tsx`
- `tool/page.tsx`、`trigger/page.tsx`
- `system/(user|role|workspace|log|setting/*)/page.tsx`
- `home/page.tsx`
- 验收：各页面能发起请求并渲染列表/表单；空数据与 Loading 态有处理。

**依赖后端**：对应 5 大领域的 REST 接口需在 `backend/`（FastAPI 重构后端）中已实现或同步开发。若后端未就绪，本里程碑可先做前端类型与调用骨架（Mock 或 `@ts-ignore` 占位），但无法端到端验证。

---

## 2. M1 — 工作流可视化编辑器（重型模块）

**目标**：还原原 `ui/src/workflow/` 的 LogicFlow 编排能力。原实现规模：222 文件、40+ 节点类型、节点配置面板、画布工具栏、Dagre 自动布局、快捷键、校验。

### 2.1 依赖引入
- `frontend/package.json` 增加 `@logicflow/core`、`@logicflow/extension`（对齐原 `ui` 技术栈）。
- 评估是否用 React 封装 LogicFlow 实例（原 `ui` 为 Vue 组件，需重写为 `.tsx` + 自定义 React 节点）。

### 2.2 目录与文件（新建 `frontend/src/workflow/`）
- `workflow/index.tsx` —— 编辑器入口（挂载 LogicFlow、注册节点/边、画布事件）
- `workflow/common/` —— `app-node.ts`（节点基类）、`edge.ts`/`loopEdge.ts`（连线/循环边）、`node.ts`/`template.ts`（节点注册表与模板）、`validate.ts`（校验）、`shortcut.ts`（快捷键）、`NodeContainer.tsx`（节点配置面板容器）、`NodeControl.tsx`（画布工具栏：缩放/适配/拖拽光标）、`NodeSearch.tsx`（节点搜索）
- `workflow/icons/` —— 各节点 SVG 图标组件（40+，可脚本化生成或分批）
- `workflow/plugins/dagre.ts` —— 自动布局
- `workflow/nodes/` —— 40 个节点类型（每个 `index.tsx` + 配置），如：开始、对话、知识库检索、文档检索、问题、条件、回复、工具、工具库、MCP、表单、意图、重排序、循环（开始/跳出/继续）、变量赋值/拆分/聚合、图像/视频/音频理解与生成、数据源（本地/网页）、知识库写入、文档切分、应用、工具开始。

### 2.3 路由页（新建，对齐原三条 workflow 路由）
- `frontend/src/app/(admin)/application/[id]/workflow/page.tsx` —— 应用工作流编辑器
- `frontend/src/app/(admin)/knowledge/[id]/workflow/page.tsx` —— 知识库工作流编辑器
- `frontend/src/app/(admin)/tool/[id]/workflow/page.tsx` —— 工具工作流编辑器
- （原 `ui` 路由为 `/application/:from/:id/workflow`、`/knowledge/:id/:folderId/workflow`、`/tool/:id/:folderId/workflow`，新前端统一用 `[id]/workflow` 动态段，属范式收敛）

### 2.4 后端依赖
- `backend/app/workflows/` 的图保存/读取/校验/SSE 执行接口；节点 schema 与参数定义（供前端 `template.ts` 生成配置面板）。
- 知识库"工作流转换侧栏"（`knowledge-workflow-setting` → `WorkflowTransform.vue`）可作为知识库详情内的子入口，复用同一编辑器。

**工作量**：本里程碑为全项目最大，建议拆为「基础设施（画布+节点基类+工具栏）→ 节点类型分批（核心 10 个 → 其余 30 个）→ 三条路由接入 → 与后端联调」。

---

## 3. M2 — 用户对话页 Chat（重型模块）

**目标**：还原原 `ui/views/chat/index.vue`（`/chat/:accessToken`，免登录白名单）的终端用户对话窗口。

### 3.1 路由与布局
- 新建独立路由组 `frontend/src/app/(chat)/` 或 `(share)/chat/[accessToken]/page.tsx`（免登录，不套用 `(admin)` 布局）。
- 页面能力：消息气泡（用户/助手）、**流式回复**（SSE/流式读取）、引用来源（知识片段高亮）、多轮上下文、输入区（含发送/清空/历史）、可能含"用户登录"（`user-login` 入口）。

### 3.2 组件
- `frontend/src/components/chat/` —— `ChatWindow.tsx`、`MessageBubble.tsx`、`SourceCitation.tsx`、`ChatInput.tsx`、`StreamReader.tsx`（流式消费）。
- 复用 `dynamics-form` 渲染应用表单节点（若应用含表单/变量收集）。

### 3.3 后端依赖
- `backend` 的 `/chat/{accessToken}` 对话接口 + SSE 流式输出 + 引用来源结构。

---

## 4. M3 — 系统子模块补齐

### 4.1 资源管理 `system/resource-management/*`
- 原 `ui`：`ApplicationResourceIndex / KnowledgeResourceIndex / ToolResourceIndex / ModelResourceIndex`（admin 视角跨工作区查看资源）。
- 新前端：在 `system/` 下新建对应 page，调用 `system.ts` 的 resource 接口。

### 4.2 共享资源 `system/shared/*`
- `KnowLedgeSharedIndex / ToolSharedIndex / ModelSharedIndex`（EE 特性）。
- 新建 page + 对应 API（共享知识/工具/模型的读接口）。

### 4.3 对话管理 `system/chat/*`
- `chat-user`（对话用户）、`group`（用户组）、`authentication`（认证）。
- 新建 page + API（对话用户/用户组/认证 CRUD）。

### 4.4 资源授权抽屉（去桩）
- 改造现有桩组件：`resource_mapping/`、`resource-authorization-drawer/`、`workspace-authorization-drawer/`。
- 对接后端 `application/tool/knowledge/model` 的 workspace 用户资源权限接口（`*_WORKSPACE_USER_RESOURCE_PERMISSION_*`）。
- 实现成员/角色/权限勾选与保存。

---

## 5. M4 — 细节与一致性收尾

### 5.1 登录辅助页（补齐 ❌ 项）
- `forgot_password`、`reset_password/:code/:email`、`user-login/:accessToken`、`no-permission`、`no-service`、`permission`、`demo`。
- 在 `(auth)/` 下新建对应 page；`user-login` 与 M2 的 chat 用户登录入口关联。

### 5.2 布局与导航一致性
- **顶栏补充 `trigger` 入口**（原 `ui` 工作区菜单含 application/knowledge/tool/model/trigger 五项）。
- 评估是否恢复「左侧 Sidebar 菜单」或直接依赖顶栏 + 内嵌树；与产品确认导航范式。
- 实现**菜单权限动态过滤**（对照 `ui` 的 `v-hasPermission` + `top-menu` 过滤逻辑），基于 `userInfo.permissions/role`。

### 5.3 用户中心能力（去桩）
- `UserAvatar` 下拉中「修改密码」「API Key」由禁用改为可用，对接 `user` API。

### 5.4 i18n / 文案
- 核对 `next-intl` 消息目录是否覆盖原 `ui/locales/` 86 语言包中的关键 key（菜单、按钮、表单、提示）。
- 补齐缺失译文，确保中英双语。

### 5.5 面包屑与交互细节
- 详情页（`application/[id]/*`、`knowledge/[id]/*`）补充面包屑（对照 `ui` `breadcrumb`）。
- 上传/解析进度轮询（对照 `UploadDocument` + 进度组件）。
- 飞书导入 / 工作流导入独立页（若后端支持）。

---

## 6. 工作量与风险

| 里程碑 | 相对工作量 | 主要风险 |
|---|---|---|
| M0 数据打通 | 中（5 API + 5 store + 接数据） | 后端 5 大领域接口是否就绪 |
| M1 工作流编辑器 | **极大**（222→等价重写，40+ 节点） | 技术栈迁移（Vue→React LogicFlow）、后端 workflow 接口 |
| M2 用户对话页 | 大（流式/SSE/引用） | 流式协议、引用结构一致性 |
| M3 系统子模块 | 中 | 后端 resource/shared/auth 接口 |
| M4 细节收尾 | 中 | 文案量、导航范式决策 |

**关键前置决策（需产品/架构确认）**
1. 导航范式：维持"顶栏 + 内嵌树"还是恢复左侧菜单？（影响 M4.2 与整体一致性判定）
2. 工作流编辑器：完全重写 React LogicFlow，还是评估复用/桥接原 Vue 组件？（影响 M1 成本）
3. 后端进度：上述里程碑依赖 `backend/` 对应接口，需与后端重构计划对齐排期。

**建议执行顺序**：M0（先让已有页面可用）→ M4 中"顶栏 trigger + 动态菜单"小项 → M1/M2（并行启动重型模块）→ M3 → M4 其余。
