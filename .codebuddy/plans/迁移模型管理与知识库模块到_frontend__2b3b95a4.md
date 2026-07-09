---
name: 迁移模型管理与知识库模块到 frontend/
overview: 在已有 frontend/（Next.js 14 + React 18 + AntD 5 + Zustand + next-intl）脚手架基础上，完整移植 Vue 侧的"模型管理"与"知识库"两个业务模块，以及它们依赖的全部共享基础设施：动态表单引擎（dynamics-form）、文件夹树/资源授权/映射抽屉/无限滚动/CardBox/AppIcon、API 层与类型、model/knowledge/folder 状态、权限桩（仅 workspace，按钮全显）、i18n 文案。新增 /frontend/model 与 /frontend/knowledge 路由并接入左侧菜单。后端与 ui/ 零改动。
design:
  architecture:
    framework: react
  styleKeywords:
    - Enterprise Admin
    - Card Grid
    - Split Panel
    - Clean
    - Responsive
  fontSystem:
    fontFamily: PingFang SC
    heading:
      size: 20px
      weight: 600
    subheading:
      size: 16px
      weight: 500
    body:
      size: 14px
      weight: 400
  colorSystem:
    primary:
      - "#1677FF"
      - "#4096FF"
    background:
      - "#f5f7fa"
      - "#ffffff"
      - "#141414"
    text:
      - "#1f1f1f"
      - "#646a73"
      - "#ffffff"
    functional:
      - "#52c41a"
      - "#ff4d4f"
      - "#faad14"
todos:
  - id: base-infra
    content: 移植基础工具与枚举：enums(model/common)、utils(common/time/array/permission桩)、constants、request 补 exportFile/exportExcel、type 定义
    status: completed
  - id: dynamic-form
    content: 完整移植动态表单引擎：DynamicsForm/FormItem/items(32)/constructor(18)/type/visibility，对齐 FormField 与 render/validate
    status: completed
    dependencies:
      - base-infra
  - id: shared-components
    content: 移植共享组件：AppIcon(+iconfont资源)、CardBox、CommonList、InfiniteScroll、DownloadLoading、KnowledgeIcon、folder-tree、授权/映射/生成问题抽屉
    status: completed
    dependencies:
      - base-infra
  - id: api-stores
    content: 落地 API 层与状态：model/knowledge API(workspace)、shared-api 包装、stores(model/knowledge/folder) 与 user store 补充
    status: completed
    dependencies:
      - base-infra
  - id: model-module
    content: 实现模型管理模块：(admin)/model 页面 + Provider/ModelCard/CreateModelDialog/SelectProviderDialog/EditModel/ParamSettingDialog/AddParamDrawer/data
    status: completed
    dependencies:
      - dynamic-form
      - shared-components
      - api-stores
  - id: knowledge-module
    content: 实现知识库模块：(admin)/knowledge 页面 + KnowledgeListContainer/ExportKnowledgeDialog/SyncWebDialog 与 create-component 四个创建对话框
    status: completed
    dependencies:
      - dynamic-form
      - shared-components
      - api-stores
  - id: i18n-menu
    content: 追加 i18n 命名空间(views.model/knowledge/dynamicsForm/common/shared/components)并接线菜单路由，验证 (admin)/layout 菜单入口
    status: completed
    dependencies:
      - model-module
      - knowledge-module
  - id: build-verify
    content: 执行 npm run build 类型检查与构建，npm run dev 联调 /frontend/model 与 /frontend/knowledge 主流程
    status: completed
    dependencies:
      - i18n-menu
---

## 用户需求概述

将 MaxKB 现有 Vue 前端中的「模型管理」与「知识库」两大业务模块，以"新建式"方式完整迁移到已落地的 Next.js（React）独立工程 `frontend/`。本次迁移追求**最高保真度**，需将后端驱动的动态表单引擎、共享业务组件一并移植，并打通真实 `/admin/api` 联调。

## 核心范围（已与用户确认）

- **动态表单引擎**：完整移植 `ui/src/components/dynamics-form/`（所有输入类型与构造器，约 50+ 文件），模型/知识库创建编辑表单由后端返回 `FormField[]` 动态渲染。
- **知识库范围**：首页列表 + 创建各类知识库对话框（通用/Web/飞书/工作流）+ 卡片操作（删除/向量化/同步/生成问题/导出/导入/移动/授权）。**不含** document/paragraph/setting 等子页面。
- **权限与模式**：仅实现 workspace 普通工作空间模式，忽略 shared/systemManage；权限桩恒为 true（按钮全部显示）。
- **共享组件**：一并移植 FolderVirtualizedTree、ResourceAuthorizationDrawer、ResourceMappingDrawer、InfiniteScroll、CardBox、AppIcon、common-list、generate-related-dialog、CreateFolderDialog、MoveToDialog、KnowledgeIcon、DownloadLoading 等。

## 约束

- `ui/`、`main.py`、后端代码**全部不改**；新代码仅写入 `frontend/`；`basePath: '/frontend'`；API 经 rewrites 代理到 Django `:8080` 的 `/admin/api`。
- 复用既有脚手架约定（Next 14 + React 18 + antd 5 + zustand + next-intl + axios）。

## 本次不实现

- 知识库 document / paragraph / setting / WorkflowTransform 子页面及对应组件。
- 系统共享/系统管理两种 apiType 的分支与权限数据源。
- 应用/工具/触发等其他模块页面。
- 飞书/工作流创建对话框的深度后端联调（先保证主流程可提交，工作流编辑器后续单列）。

## 技术栈

- 框架：Next.js 14 App Router + React 18（沿用 `frontend/` 脚手架，不升级到 React 19 以兼容 antd 5）
- UI 组件库：Ant Design 5 + `@ant-design/nextjs-registry`（SSR 样式）
- 状态：Zustand（新增 model/knowledge/folder store，扩展 user store）
- 国际化：next-intl（`messages/zh.json`、`en.json`，追加命名空间）
- 请求：axios（复用 `src/lib/request`，补充 `exportFile/exportExcel`）
- 图标：复制原 `ui/src/assets/iconfont` 资源到 `frontend/public`，实现 `AppIcon` 组件保真渲染

## 实现策略

采用**逐文件忠实移植 + Vue→React 范式映射**：

1. Vue `v-model` → React 受控组件 + `useState`/`zustand`。
2. Vue `loadSharedApi({type, systemType})` → React 直接 `import` 对应 API 模块（仅 workspace，prefix=`/workspace/${workspaceId}`）。
3. Vue `useStore()`(Pinia) → `useXxxStore()`(Zustand)。
4. Vue `$t('views.xxx')` → `useTranslations('views.xxx')` / `t('views.xxx')`。
5. 动态表单引擎 `DynamicsForm`：封装为受控 antd `Form` 组件，props `value`/`renderData`/`model`，通过 `ref` 暴露 `render(fields)` 与 `validate()`（返回 Promise）；内部按 `field.input_type` 分派到 `items/*` 组件，并执行必填/规则校验。

## 关键技术决策

- **动态表单引擎完整移植**：因模型凭证表单、知识库创建表单完全由后端 `FormField[]` 驱动，必须完整移植 `items/`（31 个 .vue 输入类型 + `index.ts`）与 `constructor/`（17 个 .vue + `data.ts` 的 `input_type_list` 等），否则无法适配不同供应商的新模型类型。
- **AppIcon 资产复制**：原 Vue 使用 iconfont 字体 + `innerHTML` 渲染 SVG，React 侧复制 `iconfont` 字体文件至 `frontend/public`，`AppIcon` 按 `iconName` 映射类名，保证图标与原版一致。
- **权限桩**：`permissionMap['model'|'knowledge']['workspace']` 各方法（create/delete/edit/...）恒返回 true；`hasPermission` 恒 true，后续阶段可替换为真实 RBAC。
- **仅 workspace 模式**：所有 API prefix 统一为 `/workspace/${workspaceId}`，去掉 `apiType` 中 shared/systemManage 分支，降低复杂度。

## 性能与可靠性

- 模型卡片对下载中状态按 `setInterval` 6s 轮询 `getModelMetaById`，卸载时 `clearInterval` 防止泄漏（对齐原 `ModelCard`）。
- 知识库列表使用 `InfiniteScroll` 分页（`page_size=30`），追加式 `setKnowledgeList`。
- `exportFile/exportExcel` 走 axios `responseType:'blob'`，创建 `Blob` + `<a download>` 触发下载，避免阻塞主线程。
- 复用既有 `utils/message.ts`（antd `message`/`Modal.confirm` 封装），统一错误提示与 401 跳登录。

## 架构设计

```mermaid
flowchart TD
  L[(admin)/layout.tsx 管理壳+客户端守卫] --> M[(admin)/model/page.tsx]
  L --> K[(admin)/knowledge/page.tsx]
  M --> MP[Provider 左栏 + ModelCard 网格]
  K --> KP[FolderVirtualizedTree 左栏 + KnowledgeListContainer 右栏]
  MP --> DYN[DynamicsForm 引擎]
  KP --> DYN
  DYN --> IT[items/* 输入组件 31个]
  DYN --> CT[constructor/* 构造器 + data.ts]
  MP --> MA[model API + model store]
  KP --> KA[knowledge API + knowledge/folder store]
  MA --> REQ[request 层 /admin/api]
  KA --> REQ
  KP --> SH[共享组件: CardBox/CommonList/InfiniteScroll/Drawer...]
```

## 目录结构（全部为新增文件）

```
frontend/
├── public/
│   └── iconfont/                 # [NEW] 复制 ui/src/assets/iconfont 字体与 css，供 AppIcon 使用
├── messages/
│   ├── zh.json                   # [NEW] 追加命名空间 views.model.* / views.knowledge.* / dynamicsForm.* / common.* / components.* / views.shared.*
│   └── en.json                   # [NEW] 同上英文本
└── src/
    ├── lib/
    │   ├── request/
    │   │   ├── index.ts          # [MODIFY] 补充 exportFile / exportExcel（blob 下载）
    │   │   └── Result.ts         # [MODIFY] 增加 blob/文件下载结果类型（如需）
    │   └── api/
    │       ├── type/
    │       │   ├── model.ts      # [NEW] Provider / Model / BaseModel / ListModelRequest / CreateModelRequest / EditModelRequest
    │       │   ├── knowledge.ts  # [NEW] knowledgeData 等类型
    │       │   └── common.ts     # [NEW] Dict / KeyValue / pageRequest 等
    │       ├── model/
    │       │   ├── model.ts      # [NEW] getModelList/createModel/updateModel/deleteModel/getModelById/getModelMetaById/pauseDownload/getModelParamsForm/updateModelParamsForm/getSelectModelList
    │       │   └── provider.ts   # [NEW] getProvider/getModelCreateForm/listModelType/listBaseModel/listBaseModelParamsForm
    │       ├── knowledge/
    │       │   └── knowledge.ts  # [NEW] getKnowledgeListPage/putKnowledge/delKnowledge/putReEmbeddingKnowledge/export*/putGenerateRelated/putKnowledgeHitTest/putSyncWebKnowledge/postKnowledge/postWebKnowledge/postLarkKnowledge/createWorkflowKnowledge/getKnowledgeModel/importKnowledgeBundle/delMulKnowledge/putMulMoveKnowledge/getAllTags
    │       └── shared-api.ts     # [NEW] loadSharedApi({type}) 包装，仅 workspace，返回对应 api 模块
    ├── enums/
    │   ├── model.ts              # [NEW] modelType 映射
    │   └── common.ts             # [NEW] SourceTypeEnum（KNOWLEDGE/MODEL...）
    ├── utils/
    │   ├── common.ts             # [NEW] i18n_name / numberFormat
    │   ├── time.ts               # [NEW] dateFormat
    │   ├── array.ts              # [NEW] splitArray
    │   ├── message.ts            # [MODIFY] 对齐 MsgConfirm/MsgSuccess/MsgError/MsgWarning API（如缺）
    │   └── permission/
    │       ├── data.ts           # [NEW] EditionConst/RoleConst/PermissionConst 常量桩
    │       └── index.ts          # [NEW] hasPermission 桩（恒 true）
    ├── permission.ts             # [NEW] permissionMap['model'|'knowledge']['workspace'] 各方法桩（恒 true）
    ├── store/
    │   ├── user.ts               # [MODIFY] 补充 getWorkspaceId / profile / isPE / isEE
    │   ├── model.ts              # [NEW] asyncGetProvider / providerList
    │   ├── knowledge.ts          # [NEW] knowledgeList / setKnowledgeList
    │   └── folder.ts             # [NEW] asyncGetFolder / setCurrentFolder / currentFolder
    ├── components/
    │   ├── AppIcon.tsx           # [NEW] iconfont 图标组件（按 iconName 映射）
    │   ├── CardBox.tsx           # [NEW] 带 icon/title/subTitle/tag/footer/mouseEnter 的卡片
    │   ├── CommonList.tsx        # [NEW] 带 active 状态的列表（Provider/Folder 复用）
    │   ├── InfiniteScroll.tsx    # [NEW] 分页无限滚动
    │   ├── DownloadLoading.tsx   # [NEW] 模型下载进度动画
    │   ├── KnowledgeIcon.tsx     # [NEW] 按 item.type 渲染知识库图标
    │   ├── dynamics-form/        # [NEW] 完整移植动态表单引擎
    │   │   ├── type.ts           # [NEW] FormField 等类型定义
    │   │   ├── index.tsx         # [NEW] DynamicsForm 主组件（value/renderData/model + render/validate）
    │   │   ├── FormItem.tsx      # [NEW] 表单项容器
    │   │   ├── FormItemLabel.tsx # [NEW] 带 tooltip 的标签
    │   │   ├── visibility/       # [NEW] 字段可见性逻辑
    │   │   ├── constructor/      # [NEW] 18 文件：data.ts(input_type_list) + 各构造器
    │   │   └── items/            # [NEW] 32 文件：input/password/select/radio/switch/number/textarea/Slider... 全部输入类型
    │   ├── folder-virtualized-tree/
    │   │   ├── FolderVirtualizedTree.tsx # [NEW] 文件夹虚拟树
    │   │   ├── CreateFolderDialog.tsx    # [NEW] 新建文件夹
    │   │   └── MoveToDialog.tsx          # [NEW] 移动到
    │   ├── resource-authorization-drawer/
    │   │   └── index.tsx         # [NEW] ResourceAuthorizationDrawer（type=MODEL/KNOWLEDGE）
    │   ├── resource_mapping/
    │   │   └── index.tsx         # [NEW] ResourceMappingDrawer
    │   └── generate-related-dialog/
    │       └── index.tsx         # [NEW] GenerateRelatedDialog
    └── app/
        └── (admin)/
            ├── model/
            │   ├── page.tsx                  # [NEW] 模型管理首页（Provider 左栏 + ModelCard 网格 + 创建入口）
            │   └── component/
            │       ├── Provider.tsx          # [NEW] 左栏供应商树（public/private 分组）
            │       ├── ModelCard.tsx         # [NEW] 模型卡片（状态轮询/编辑/参数设置/授权/删除下拉）
            │       ├── CreateModelDialog.tsx # [NEW] 创建模型（选供应商→base_info 动态表单+advanced_info 参数表）
            │       ├── SelectProviderDialog.tsx # [NEW] 选择供应商
            │       ├── EditModel.tsx         # [NEW] 编辑模型
            │       ├── ParamSettingDialog.tsx# [NEW] 参数设置
            │       ├── AddParamDrawer.tsx    # [NEW] 新增自定义参数抽屉
            │       └── data.ts               # [NEW] modelTypeList / allObj
            └── knowledge/
                ├── page.tsx                  # [NEW] 知识库首页（FolderTree 左栏 + ListContainer 右栏）
                ├── component/
                │   ├── KnowledgeListContainer.tsx # [NEW] 搜索/批量/创建下拉/无限滚动卡片网格/卡片操作
                │   ├── ExportKnowledgeDialog.tsx  # [NEW] 导出（含/不含源文件）
                │   └── SyncWebDialog.tsx         # [NEW] Web 知识库同步
                └── create-component/
                    ├── CreateKnowledgeDialog.tsx       # [NEW] 通用知识库（name/desc/embedding）
                    ├── CreateWebKnowledgeDialog.tsx    # [NEW] Web 知识库（source_url/selector）
                    ├── CreateLarkKnowledgeDialog.tsx   # [NEW] 飞书知识库（占位可提交）
                    └── CreateWorkflowKnowledgeDialog.tsx # [NEW] 工作流知识库（占位可提交）
```

## 关键代码结构（核心契约）

```ts
// src/components/dynamics-form/type.ts
export interface FormField {
  field: string
  input_type: string          // 对应 items/* 的组件名
  label: string | { input_type: string; label: string }
  required?: boolean
  default_value?: any
  props?: Record<string, any>
  show?: boolean
  // ...其他渲染元数据
}

// src/components/dynamics-form/index.tsx
export interface DynamicsFormRef {
  render(fields: FormField[]): void
  validate(): Promise<void>
}
// props: { value: Record<string, any>; renderData: FormField[]; model: Record<string, any> }

// src/lib/api/shared-api.ts
export function loadSharedApi(opts: { type: 'model' | 'knowledge' | 'workspace'; systemType?: 'workspace' }): any
// 返回对应 api 模块（仅 workspace 实现）
```

## 设计风格

忠实移植 MaxKB 管理后台的既有视觉语言（企业级后台，清晰卡片网格 + 左右分栏布局），组件库由 Element Plus 替换为 Ant Design 5，沿用脚手架既有的主题与暗色模式（primary `#1677FF`，ConfigProvider 注入）。

## 模型管理页

- 左右分栏（复用 `(admin)/layout.tsx` 外壳）：左侧为供应商列表（public/private 折叠分组 + 全部/共享入口），右侧为模型卡片网格（响应式 2~3 列）。
- 卡片展示名称、供应商图标、模型类型、基础模型、创建时间、共享标签；下载中显示 `DownloadLoading` 进度遮罩。
- 卡片悬浮展开下拉菜单：编辑 / 参数设置 / 授权 / 删除；创建按钮打开两步对话框（选供应商 → 动态表单填凭证 + 自定义参数表）。

## 知识库页

- 左右分栏：左侧 `FolderVirtualizedTree` 文件夹树，右侧 `KnowledgeListContainer`。
- 右栏顶部为搜索 + 创建下拉（通用/Web/飞书/工作流/导入/新建文件夹）+ 批量操作栏；下方为无限滚动卡片网格，卡片显示名称、图标、创建人、文档数、字符数，悬浮下拉含同步/向量化/生成问题/移动/设置/导出(Excel/ZIP/知识库)/删除。
- 创建对话框使用 `DynamicsForm` 动态渲染后端返回的表单字段。

## 交互与响应式

- 沿用脚手架的 Sider 折叠、LocaleSwitch、ThemeToggle、暗色模式。
- 网格列数响应式（xs=1, sm=2, lg=3~4）；对话框/抽屉使用 antd `Modal`/`Drawer`，`destroyOnClose`。
- 图标使用复制的 iconfont 资产经 `AppIcon` 渲染，保持与 Vue 版一致。