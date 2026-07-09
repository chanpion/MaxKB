---
name: 新增Next.js+React+AntD前端模块（原ui保留）架构设计方案
overview: 基于 MaxKB 现有源码，在**不改动原有 ui/（admin 与 chat 均为 Vue）** 的前提下，新增一个独立的 Next.js + React + Ant Design 前端模块，作为管理后台的 React 版本。原 ui/ 代码与现有 Django 静态托管/collect_static 完全保留。方案重点：新模块独立工程结构、与现有 /admin(Vue)、/chat(Vue) 共存的路径与部署拓扑（避免路径冲突）、vue-router→App Router / Pinia→Zustand / vue-i18n→next-intl / Element Plus→Ant Design 的迁移映射、axios 请求层与代理、@logicflow 工作流 React 适配，以及未来可选切换策略。交付物为一份架构设计方案文档，不实际改业务代码。
todos:
  - id: doc-topology
    content: 编写新模块工程结构与部署拓扑（nginx 分流、basePath、零改动 ui//后端）章节
    status: pending
  - id: doc-core-map
    content: 编写路由/状态/请求层/i18n 的 Vue→React 映射方案章节
    status: pending
    dependencies:
      - doc-topology
  - id: doc-ui-map
    content: 编写 Element Plus→Ant Design 组件与主题、样式迁移章节
    status: pending
    dependencies:
      - doc-core-map
  - id: doc-workflow
    content: 编写 LogicFlow 工作流与第三方库 React 替代方案章节
    status: pending
    dependencies:
      - doc-core-map
  - id: doc-build-roadmap
    content: 编写新模块构建脚本/env 与"新建式"迁移阶段路线图章节
    status: pending
    dependencies:
      - doc-ui-map
      - doc-workflow
  - id: doc-review
    content: 使用 [skill:doc-coauthoring] 汇总评审并产出最终设计文档
    status: pending
    dependencies:
      - doc-build-roadmap
---

## 用户需求

在完全不改动现有 `ui/`（Vue admin + Vue chat）、`main.py`、以及 `apps/maxkb` 后端任何代码的前提下，于仓库新增一个**独立的前端模块**，用 Next.js + React + Ant Design 实现对标原 admin 管理后台的管理控制台。

## 产品概述

该新模块是一个独立部署（独立 Node 进程）的企业级管理控制台，功能对标原 Vue admin：登录、工作台、系统设置、模型提供方、知识库/文档/段落、智能体应用、工具库、触发器，以及基于 LogicFlow 的工作流编排。它通过反向代理以独立路径（如 `/admin-react`）对外提供服务，并复用 Django 现有的认证与 `/admin/api` 接口。

## 核心特性

- 新增独立 Next.js（App Router）工程，与原 Vue 工程零耦合，路径与 `/admin`、`/chat` 不冲突。
- 用 Zustand 替代 Pinia、next-intl 替代 vue-i18n、Ant Design 替代 Element Plus，组件与文案 key 一一映射。
- 复用现有 axios 请求层与拦截器逻辑，经 `next.config` rewrites 指向 Django 8080。
- 用 `dynamic(import, { ssr:false })` 客户端加载 LogicFlow 工作流编辑器。
- 登录态通过同域 cookie 复用 Django 认证；原 Vue admin / chat 完全不受影响。
- 本次仅产出《新增 Next.js 前端模块架构设计方案》文档，不实际写代码。

## 技术栈选型

- 框架：Next.js（App Router，`output:'standalone'`，`basePath:'/admin-react'`），React 18+，TypeScript。
- UI 组件库：Ant Design v5，配合 `@ant-design/nextjs-registry` 解决 SSR 样式注水。
- 状态管理：Zustand（轻量、贴合 React hooks，替代 Pinia）。
- 国际化：next-intl（替代 vue-i18n，保留现有 key 不变）。
- 请求：axios（平移现有封装）+ fetch（SSE/流式）+ 原生 WebSocket。
- 工作流：`@logicflow/core` + `@logicflow/extension`（框架无关，React 侧 `useRef`+`useEffect` 封装）。
- 样式：Sass Modules + AntD `theme.token` 主题注入。
- 第三方库替代：md-editor-v3→`@mdxeditor/react`（或 `md-editor-rt`）、vue-codemirror→`@uiw/react-codemirror`、sortablejs/vue-draggable-plus→`@dnd-kit`、echarts→`echarts-for-react`、cropperjs→`react-cropper`、jsencrypt/mermaid/highlight.js/katex 通用直用、vueuse→`ahooks`。

## 实现方案

**总体策略**：在仓库根新增独立工程 `admin-react/`（与 `ui/`、`apps/` 并列，零耦合、零改动现有代码）。新模块以 Next standalone 单实例提供 SSR，由反向代理（nginx 首选，零后端改动）按路径分流：`/admin`、`/chat` 仍由 Django(:8080) 托管 Vue；`/admin-react` 指向 Next(:3000)；所有 `/admin/api`、`/chat/api`、`/oss` 转发 Django(:8080)。登录态通过同域 cookie（token）复用现有认证。

**关键决策与权衡**：

1. **独立模块 + 独立路径，而非改写现有 admin**：用户明确要求 `ui/` 不变，且后端静态托管按 `/admin` 路由，故新模块必须用 `basePath:'/admin-react'`（或 `/console`，可配置）规避冲突，独立部署互不干扰。
2. **nginx 分流而非改 Django 路由**：现有 `apps/maxkb/urls/web.py` 的 `prefix`/`chatPrefix` 运行时 HTML 替换逻辑只作用于 `ui/` 的 Vue `index.html`，新模块用 Next `basePath` + 构建期注入，无需触碰后端。
3. **SSR 鉴权**：用 `middleware.ts` 平移原 `router.beforeEach`（无 token 跳 `/login`、401 跳登录）；客户端组件保留 axios 直连 `/admin/api` 并携带同域 cookie。
4. **LogicFlow 客户端隔离**：编辑器依赖 DOM/画布，必须 `dynamic(import, { ssr:false })` 客户端加载，避免 SSR 报错。
5. **API 层复用**：原 `request/index.ts` 拦截器（token、Accept-Language、401/403、流式、blob 导出、WebSocket）逻辑平移；`baseURL` 由 `prefix+'/api'` 改为 `/admin/api`，与 `next.config` rewrites 对齐。

**性能与可靠性**：AntD 经 `@ant-design/nextjs-registry` 避免样式闪烁；工作流仅在工作流页懒加载（`ssr:false`）控制包体与内存；保留 NProgress 等价 loading。复用现有 API 契约，不改动后端。

## 实现要点（防回归）

- 零改动 `ui/`、`main.py`、`apps/maxkb/urls/web.py`、`apps/maxkb/settings/*`；新模块独立 `build`/`start`，不进入 `collect_static` 流程。
- 语言包 key 严格不变；权限判定 `hasPermission`（OR/AND 语义）平移为 `usePermission` hook + `middleware` 双层校验。
- 主题：原 `use-element-plus-theme` 运行时改主题色改为 AntD `ConfigProvider` `theme.token.colorPrimary` 动态注入。
- 日志仅保留必要接口错误提示，沿用 `MsgError` 等价封装，避免敏感信息外泄。

## 架构设计

### 部署拓扑

```mermaid
flowchart LR
  U[浏览器] -->|/admin/* /chat/* /api /oss| Nginx[反向代理 nginx]
  Nginx -->|/admin & /chat -> :8080| Django[Django 8080 + static]
  Nginx -->|/admin-react -> :3000| Next[Next.js Standalone SSR]
  Nginx -->|/admin/api /chat/api /oss -> :8080| Django
  Next -->|内部调用 /admin/api| Django
  Django --> PG[(PostgreSQL+pgvector)]
  Django --> Redis[(Redis)]
```

### 新模块内部架构

- 启动链：`app/layout.tsx`（AntD Registry + NextIntlClientProvider + Zustand Provider）→ `app/(admin)/layout.tsx`（侧边栏/顶栏框架）。
- 鉴权链：`middleware.ts` 读取 cookie token，未登录重定向 `/login`。
- 接口链：`lib/request.ts`（rewrites 到 Django）。
- 工作流链：`components/workflow/Editor.tsx`（client-only，动态注册 React 节点）。

### 目录映射

- `ui/src/views/*` → `admin-react/app/(admin)/<module>/page.tsx`
- `ui/src/components/*` → `admin-react/components/*`
- `ui/src/layout/*` → `admin-react/app/(admin)/layout.tsx` + `admin-react/components/layout/*`
- `ui/src/workflow/*` → `admin-react/components/workflow/*`
- `ui/src/stores/modules/*` → `admin-react/store/*.ts`（Zustand slice）
- `ui/src/api/*` → `admin-react/lib/api/*`
- `ui/src/request/*` → `admin-react/lib/request.ts`
- `ui/src/locales/lang/*` → `admin-react/messages/<locale>.ts`
- `ui/src/permission/*` → `admin-react/lib/permission.ts` + `admin-react/middleware.ts`
- `ui/src/utils/*`、`directives/*`、`bus/*` → `admin-react/lib/*`、AntD `App` 上下文、`eventemitter`
- `ui/src/styles/*` → `admin-react/styles/*`

## 目录结构

```
admin-react/                              # [NEW] 独立 Next.js 工程（与 ui/ 并列，零耦合，不改动现有文件）
├── app/
│   ├── layout.tsx                        # [NEW] 根布局：AntD Registry + Intl + Zustand Provider
│   ├── (admin)/
│   │   ├── layout.tsx                    # [NEW] 后台框架布局（侧边栏/顶栏，对等 layout/*）
│   │   ├── login/page.tsx                # [NEW] 登录页
│   │   ├── home/page.tsx                 # [NEW] 工作台
│   │   ├── application/...               # [NEW] 应用/工作流入口
│   │   ├── knowledge/...                 # [NEW] 知识库/文档/段落
│   │   ├── model/...                     # [NEW] 模型提供方
│   │   ├── system/...                    # [NEW] 系统设置
│   │   ├── tool/...                      # [NEW] 工具库
│   │   └── trigger/...                   # [NEW] 触发器
├── components/                           # [NEW] 通用组件（Table/Form/Modal/Message 封装，对等 components/*）
│   └── workflow/                         # [NEW] LogicFlow React 封装与节点 renderer
├── lib/
│   ├── request.ts                        # [NEW] axios 实例 + 拦截器（平移 request/index.ts）
│   ├── api/                              # [NEW] 业务接口（平移 api/*，83 文件）
│   ├── permission.ts                     # [NEW] usePermission + hasPermission（平移 permission/utils）
│   └── store/                            # [NEW] Zustand slices（平移 stores/modules/*）
├── messages/                             # [NEW] next-intl 语言包（平移 locales/lang/*）
├── middleware.ts                         # [NEW] 路由鉴权守卫（平移 router.beforeEach）
├── next.config.mjs                       # [NEW] basePath '/admin-react' + rewrites 到 Django 8080
├── styles/                               # [NEW] 全局样式 + AntD token（平移 styles/*）
├── package.json                          # [NEW] 独立依赖与脚本（dev/build/start）
└── tsconfig.json                         # [NEW] Next.js TypeScript 配置
```

## 关键代码结构

```typescript
// next.config.mjs 关键契约
const nextConfig = {
  basePath: '/admin-react',
  output: 'standalone',
  async rewrites() {
    const target = process.env.API_TARGET ?? 'http://127.0.0.1:8080'
    return [
      { source: '/admin/api/:path*', destination: `${target}/admin/api/:path*` },
      { source: '/chat/api/:path*', destination: `${target}/chat/api/:path*` },
      { source: '/oss/:path*', destination: `${target}/oss/:path*` },
    ]
  },
}
```

```typescript
// lib/request.ts 请求基址（平移现有 baseURL 逻辑）
const request = axios.create({
  baseURL: (process.env.NEXT_PUBLIC_BASE_PATH ?? '/admin-react') + '/api',
  timeout: 1800000,
})
// 拦截器注入 AUTHORIZATION(Bearer) 与 Accept-Language，错误态 401→login、403→提示
```

## 迁移路线图（建议阶段）

- 阶段 0：脚手架（Next 工程、basePath/rewrites、Provider、next-intl、Zustand、axios 封装）。
- 阶段 1：核心设施（请求层、store 映射、i18n、permission hook、布局/框架、路由壳+鉴权 middleware）。
- 阶段 2：共享组件与主题（Table/Form/Modal/Message 封装、AntD 主题 token、样式迁移）。
- 阶段 3：业务模块（登录、首页、system、model、knowledge、application、tool、trigger）。
- 阶段 4：工作流编辑器（LogicFlow React 封装 + 节点 renderer，按需懒加载 ssr:false）。
- 阶段 5：联调验证（nginx 分流、SSR 数据、权限、i18n、e2e），原 `/admin`、`/chat` 不受影响。

## 验证方式

- 本地 `next dev`（:3000）经 rewrites 访问 `127.0.0.1:8080` 的 `/admin/api`；`next build` + `next start` 验证 standalone SSR。
- 回归：原 `/admin`(Vue)、`/chat`(Vue) 独立可用；登录态、菜单权限、语言切换、主题色、工作流增删节点、导出/流式接口正常。

## Agent Extensions

### Skill

- **doc-coauthoring**
- 用途：按结构化写作流程（提案/技术规格）撰写本架构设计方案技术文档，组织章节、迭代与校验可读性、术语一致性。
- 预期结果：产出一份结构完整、术语一致、可直接评审的《MaxKB 新增 Next.js+React+AntD 前端模块架构设计方案》文档（不实际改代码）。