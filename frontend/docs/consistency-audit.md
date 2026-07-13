# MaxKB 前端重构一致性审计报告

> 基准：原前端 `ui/`（Vue 3 + Vue Router，231 个视图文件 + 168 个工作流文件）
> 被审计对象：重构前端 `frontend/`（Next.js App Router + Ant Design）
> 审计范围：全部模块（页面/路由、功能、布局），以源码结构为准
> 审计日期：2026-07-13
> 交付物：本报告 + `consistency-remediation-plan.md`（实施计划）

---

## 0. 总体结论

重构前端已搭好**页面骨架与布局外壳**（30 个 `page.tsx` + 后台布局 + 登录/404/home + 顶部导航 + i18n + 路由守卫），并重用了高质量的 `dynamics-form`、`folder-virtualized-tree` 等通用组件，同时已完成 **knowledge / model / provider / folder / login** 五大领域的 API 迁移。

但与原前端相比仍处于**早期骨架阶段**，存在三类重大缺口：

1. **整模块缺失**：工作流可视化编辑器（`LogicFlow` 流程图）与用户对话页（`/chat/:accessToken`）完全不存在。
2. **空壳页面**：`application / tool / trigger / system / home` 五大页面已建路由，但其依赖的 API 模块与 store **尚未实现**，运行时拉取数据会失败。
3. **布局范式差异**：原前端为「左侧菜单栏 + Header」后台布局；新前端改为「顶部三栏 TopMenu + 内容区」，无独立左侧导航栏（资源文件夹树内嵌在内容区），菜单为静态配置，权限动态过滤与资源授权 UI 仍为桩实现。

**一致性评分（按模块）**

| 模块 | 状态 | 说明 |
|------|------|------|
| 登录与鉴权 | 🟡 部分 | 登录页完整；找回密码 / 用户登录 / 无权限页缺失 |
| 首页仪表盘 | 🟡 部分 | 页面+图表齐全，但 `homepageApi` 未实现，无数据 |
| 应用 Application | 🟡 部分 | 列表/概览/设置/访问/日志页存在，API+store 缺失 |
| 知识库 Knowledge | ✅ 较完整 | 列表/文档/问题/术语库/命中测试/设置齐全，API 最完整 |
| 模型 Model | 🟡 部分 | 列表+创建/编辑对话框存在，API 已迁移 |
| 工具 Tool | 🟡 部分 | 列表页存在，API 缺失 |
| 触发器 Trigger | 🟡 部分 | 列表页存在，API 缺失 |
| 系统管理 System | 🟡 部分 | user/role/workspace/log/setting 存在，授权/共享/资源/对话子模块缺失或桩 |
| 工作流编辑器 Workflow | ❌ 缺失 | 无 LogicFlow、无节点画布，仅"创建工作流知识库"入口 |
| 用户对话页 Chat | ❌ 缺失 | 仅聊天日志查看，无终端用户对话窗口 |

---

## 1. 审计方法

1. 枚举原 `ui/` 全部路由（`router/index.ts` + `router/modules/*.ts` 9 个）与视图（`views/` 231 文件）、工作流（`workflow/` 168 文件）、布局（`layout/` 21 文件）。
2. 枚举新 `frontend/` 全部 `page.tsx`（30 个）、布局、`components/`、`lib/api/`。
3. 构建「页面 / 功能 / 布局」三维对比矩阵，标注 一致 / 部分 / 缺失 / 差异，附证据路径。

---

## 2. 布局一致性

### 原前端 `ui/`（基准）
- 三层后台框架 `MainLayout.vue`：**顶部 Header**（Logo + 顶部主菜单 + 用户头像）+ **左侧 Sidebar 菜单**（递归 `SidebarItem`）+ **内容区 `AppMain`**（`router-view`）。
- 菜单**完全由静态路由配置生成**（`router/modules/*` 的 `meta.menu/title/icon/order`），通过 `v-hasPermission` 指令 + `top-menu` 过滤 `meta.permission` 做动态显隐。
- 另有 `SimpleLayout`、`SystemMainLayout` 变体，以及独立 `login-layout`。
- 面包屑、用户中心（API Key / 关于 / 改密）齐全。

### 新前端 `frontend/`
- `(admin)/layout.tsx`：**固定顶栏（56px）三栏** —— 左 `Logo`(200px) / 中 `TopMenu`(居中) / 右 `UserAvatar`(200px) + 内容区（`maxWidth:1400` 居中）。
- **无独立左侧菜单栏**；知识库/应用/工具的资源文件夹树（`FolderVirtualizedTree`）内嵌在内容区左侧。
- `TopMenu` 为**静态数组**（`home / application / knowledge / tool / model` 五项），**不含 trigger**；用户区下拉含 个人资料 / 系统管理 / 修改密码(禁用) / API Key(禁用) / 语言 / 关于 / 登出。
- 菜单**不做权限动态过滤**（与 `ui/` 的指令级过滤不同）。

### 差异判定：🔄 范式差异
- 从「左栏导航 + 顶栏」变为「顶栏导航 + 内嵌树」，功能上可等价，但**导航心智模型与 `ui/` 不一致**；且 `trigger` 未进入顶栏，原 `ui/` 工作区菜单含 application/knowledge/tool/model/trigger 五项。
- 权限动态菜单、API Key / 改密 等用户中心能力在新前端为禁用桩。

---

## 3. 路由 / 页面覆盖矩阵

> 状态图例：✅ 一致 ｜ 🟡 部分（页面在但功能/API 不全）｜ ❌ 缺失 ｜ 🔄 差异

| 原 `ui/` 路由 | 功能 | 新 `frontend/` 对应 | 状态 |
|---|---|---|---|
| `/` → home（redirect） | 根重定向 | `app/page.tsx` | ✅ |
| `/login` | 登录 | `(auth)/login/page.tsx` | ✅ |
| `/forgot_password` | 找回密码 | — | ❌ 缺失 |
| `/reset_password/:code/:email` | 重置密码 | — | ❌ 缺失 |
| `/user-login/:accessToken` | 用户免登 | — | ❌ 缺失 |
| `/no-permission` | 无权限 | — | ❌ 缺失 |
| `/no-service` | 服务不可用 | — | ❌ 缺失 |
| `/permission` | 权限占位 | — | ❌ 缺失 |
| `/:pathMatch(.*)` → 404 | 404 | `(auth)/404/page.tsx` | ✅ |
| `/home` | 仪表盘 | `(admin)/home/page.tsx` | 🟡（无 homepageApi） |
| `/application` | 应用列表 | `(admin)/application/page.tsx` | 🟡（无 application API） |
| `/application/:from/:id/:type/overview` | 应用概览 | `application/[id]/overview` | 🟡 |
| `.../setting` | 应用设置 | `application/[id]/setting` | 🟡 |
| `.../access` | 访问设置 | `application/[id]/access` | 🟡 |
| `.../chat-user` | 应用对话用户 | —（知识库有，应用无） | ❌ 缺失 |
| `.../chat-log` | 对话日志 | `application/[id]/chat-log` | 🟡 |
| `/application/:from/:id/workflow` | **应用工作流编辑器** | — | ❌ 缺失 |
| `/knowledge` | 知识库列表 | `(admin)/knowledge/page.tsx` | ✅ |
| `/knowledge/document/upload/:folderId/:type` | 上传文档 | `knowledge/upload` | 🟡 |
| `/knowledge/import/lark/:folderId` | 飞书导入 | — | ❌ 缺失 |
| `/knowledge/import/workflow/:folderId` | 工作流导入 | — | ❌ 缺失 |
| `/knowledge/:id/:folderId/:type/document` | 文档列表 | `knowledge/[id]/document` | ✅ |
| `.../document` 段编辑 | 分段编辑 | `knowledge/[id]/document/[docId]` | 🟡 |
| `.../knowledge-workflow-setting` | 知识库工作流转换 | — | ❌ 缺失 |
| `.../problem` | 问题管理 | `knowledge/[id]/problem` | 🟡 |
| `.../termbase` | 术语库 | `knowledge/[id]/termbase` | 🟡 |
| `.../hit-test` | 命中测试 | `knowledge/[id]/hit-test` | 🟡 |
| `.../chat-user` | 知识库对话用户 | `knowledge/[id]/chat-user` | 🟡 |
| `.../setting` | 知识库设置 | `knowledge/[id]/setting` | 🟡 |
| `/paragraph/:id/:documentId` | 段落编辑 | 并入 document/[docId] | 🔄 差异 |
| `/model` | 模型列表 | `(admin)/model/page.tsx` | 🟡（API 已迁） |
| `/tool` | 工具列表 | `(admin)/tool/page.tsx` | 🟡（无 tool API） |
| `/trigger` | 触发器列表 | `(admin)/trigger/page.tsx` | 🟡（无 trigger API） |
| `/system/user` | 用户管理 | `system/user` | 🟡（无 system API） |
| `/system/workspace` | 工作区管理 | `system/workspace` | 🟡 |
| `/system/role` | 角色管理 | `system/role` | 🟡 |
| `/system/resource-management/*` | 资源管理（应用/知识/工具/模型） | — | ❌ 缺失 |
| `/system/authorization/*` | 资源授权（应用/知识/工具/模型） | `resource-authorization-drawer`（桩） | 🟡 桩 |
| `/system/shared/*` | 共享资源（知识/工具/模型） | — | ❌ 缺失 |
| `/system/chat/*` | 对话用户/用户组/认证 | — | ❌ 缺失 |
| `/system/setting/theme` | 主题设置 | `system/setting/theme` | 🟡 |
| `/system/setting/authentication` | 登录认证设置 | `system/setting/auth` | 🟡 |
| `/system/setting/email` | 邮件设置 | `system/setting/email` | 🟡 |
| `/operate` | 操作日志 | `system/log` | 🟡 |
| `/chat/:accessToken` | **用户对话页** | — | ❌ 缺失 |
| `/demo` | 演示页 | — | ❌ 缺失 |

---

## 4. 按模块功能对比

### 4.1 登录与鉴权
- ✅ 新前端登录页：RSA 加密、图形验证码、中英文切换、双栏品牌布局，完整。
- ❌ 缺失：`forgot_password` / `reset_password` / `user-login`（用户免登对话入口）/ `no-permission` / `no-service` / `permission` 等辅助页。
- 🟡 `UserAvatar` 下拉中「修改密码」「API Key」为禁用桩。

### 4.2 首页 / 仪表盘 Home
- 🟡 页面 `home/page.tsx`（~12KB，含 ECharts 统计卡片、Token/问答排行、监控图表）结构完整，但依赖的 `homepageApi`（`@/lib/api/home`）**未实现**，页面无数据。

### 4.3 应用 Application
- 🟡 列表页 `application/page.tsx`（文件夹虚拟树 + 应用卡片）结构在，引用 `@/lib/api/application`（**未实现**）。
- 🟡 概览/设置/访问/日志四个 `[id]/*` 页存在；**缺少 `chat-user`（应用对话用户）页**。
- ❌ 应用工作流编辑器 `/application/:from/:id/workflow` 缺失（见 4.9）。

### 4.4 知识库 Knowledge（最完整）
- ✅ 列表、文档列表、文档/分段详情、问题、术语库、命中测试、对话用户、设置页**均已建路由**，且 `lib/api/knowledge/knowledge.ts` 是迁移最完整的模块（48 个方法，含 Web/Lark/Workflow 知识库、命中测试、同步、导出导入、MCP 工具等）。
- 🟡 缺少：飞书导入 / 工作流导入 独立页、`knowledge-workflow-setting`（工作流转换侧栏）。
- 🟡 段落编辑：原 `ui/` 有独立 `/paragraph` 路由，新前端并入 `document/[docId]`，属范式差异但功能可覆盖。

### 4.5 模型 Model
- 🟡 列表页 `model/page.tsx` 含 Provider 选择 + 模型卡片 + 创建/编辑对话框；`lib/api/model/*` 与 `provider` 已迁移，是该模块相对可用的基础。

### 4.6 工具 Tool
- 🟡 列表页 `tool/page.tsx` 存在，引用 `@/lib/api/tool/tool`（**未实现**）。

### 4.7 触发器 Trigger
- 🟡 列表页 `trigger/page.tsx` 存在，引用 `@/lib/api/trigger`（**未实现**）。

### 4.8 系统管理 System
- 🟡 已建：`user` / `role` / `workspace` / `log`（操作日志）/ `setting/{theme,auth,email}`。
- ❌ 缺失：`resource-management`（资源管理）、`shared`（共享资源）、`chat`（对话用户/用户组/认证）三个子系统。
- 🟡 资源授权 UI 三件套（`resource_mapping` / `resource-authorization-drawer` / `workspace-authorization-drawer`）均为**桩实现**，注释明确"未对接后端"。

### 4.9 工作流可视化编辑器 Workflow（关键缺失）
- ❌ 原 `ui/src/workflow/` 是基于 `@logicflow/core` 的 222 文件大型可视化编辑器（40+ 节点类型、节点配置面板 `NodeContainer`、画布工具栏 `NodeControl`、Dagre 自动布局、快捷键、校验 `validate.ts`）。
- ❌ 新前端**无 LogicFlow 依赖、无任何流程图/节点画布组件**。仅在 `knowledge` 中有「创建工作流知识库」的弹窗入口（`CreateWorkflowKnowledgeDialog`），无编辑/可视化。
- ❌ 涉及路由：`/application/:from/:id/workflow`、`/knowledge/:id/:folderId/workflow`、`/tool/:id/:folderId/workflow`（应用/知识/工具三类工作流编辑器）全部缺失。

### 4.10 用户对话页 Chat（关键缺失）
- ❌ 原 `ui/views/chat/index.vue`（`/chat/:accessToken`，免登录白名单）是面向终端用户的对话窗口（流式回复、引用来源、历史记录）。
- ❌ 新前端仅有 `application/[id]/chat-log`（只读日志 Table）与 `knowledge/[id]/chat-user`（权限/使用人），**无任何对话交互界面**。

---

## 5. 功能 / 交互差异

| 维度 | 原 `ui/` | 新 `frontend/` | 状态 |
|---|---|---|---|
| 权限 / RBAC | `utils/permission/*`（17 文件）、`v-hasPermission` 指令、菜单动态过滤、`ComplexPermission` 组合 | `lib/utils/permission/`（data+index）、`folder` store 权限映射；菜单**静态无动态过滤** | 🟡 部分 |
| 动态表单 | 各业务页内联表单 | `dynamics-form`（按字段数组 + 联动 `relation_show_field_dict` 渲染）✅ 已抽象 | ✅ |
| 上传 / 解析进度 | UploadDocument 页 + 进度轮询 | `knowledge/upload` 页存在，但进度/解析交互待补 | 🟡 |
| i18n / 多语言 | `locales/` 86 个语言包 | `next-intl`（`i18n/navigation|request|routing`）；文案覆盖度待核 | 🟡 部分 |
| 主题（亮/暗） | 主题切换 + 登录主题背景 | `ThemeToggle` + Antd `ConfigProvider` 暗色封装 ✅ | ✅ |
| 面包屑 | `breadcrumb` 组件 | 需确认是否在详情页实现 | 🟡 |
| 文件夹树 | 各模块独立侧栏 | `FolderVirtualizedTree` 复用 ✅（虚拟滚动/搜索/排序/右键） | ✅ |

---

## 6. API 层覆盖

| 领域 | 原 `ui/api/`（83 文件） | 新 `frontend/lib/api/`（8 文件） | 状态 |
|---|---|---|---|
| user / login | ✅ | `api/login.ts` ✅ | ✅ 迁移 |
| knowledge | ✅ | `api/knowledge/knowledge.ts`（48 方法）✅ | ✅ 最完整 |
| model / provider | ✅ | `api/model/model.ts` + `provider.ts` ✅ | ✅ 迁移 |
| workspace folder | — | `api/workspace/folder.ts` ✅ | ✅ 新增 |
| application | ✅ | ❌ 未实现 | ❌ |
| tool | ✅ | ❌ 未实现 | ❌ |
| trigger | ✅ | ❌ 未实现 | ❌ |
| system | ✅ | ❌ 未实现 | ❌ |
| home | ✅ | ❌ 未实现 | ❌ |
| chat | ✅ | ❌ 未实现 | ❌ |
| workflow | ✅ | ❌ 未实现（仅 knowledge 内有 workflow 知识库 API） | ❌ |

> 缺失 API 同时意味着 `lib/store/` 中缺少 `application / tool / trigger / system / home` 对应的状态管理。

---

## 7. 一致性评级汇总

- **布局范式**：🔄 差异（顶栏替代左栏，trigger 缺顶栏入口，权限动态菜单缺失）
- **页面路由覆盖**：约 30/60+ 路由存在（含 5 个缺失辅助页 + 2 个核心编辑器 + 1 个对话页 + 多个系统子模块），覆盖度 ~50%（按功能点计更低）
- **功能完整度**：知识库/模型/登录/布局外壳较为可用；应用/工具/触发器/系统为**空壳**；工作流编辑器与对话页为**硬缺口**
- **API 迁移度**：5/11 领域完成（knowledge/model/provider/folder/login）
- **组件复用度**：✅ 高（`dynamics-form`、`folder-virtualized-tree`、各类 Drawer/Dialog 已抽象，可降低后续补齐成本）

**结论**：重构前端完成了"骨架 + 知识库/模型一条线 + 通用组件库"的奠基工作，但距与原前端**功能与布局一致**仍有显著差距，最大风险是**工作流编辑器**与**用户对话页**两大重型模块从零开始，以及五大模块的后端接口与状态管理尚未对接。详细补齐步骤见 `consistency-remediation-plan.md`。
