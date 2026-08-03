# MaxKB 前端（frontend）

MaxKB 企业级智能体平台的管理/对话前端，基于 **Next.js 14（App Router）** 构建，使用 Ant Design、zustand 状态管理、next-intl 国际化。生产部署采用 Next.js 官方的 `output: 'standalone'` 自包含模式。

## 技术栈

- 框架：Next.js `14.2.15`（App Router，`output: 'standalone'`）
- UI：Ant Design `5.x`、`@ant-design/icons`、`ahooks`
- 状态：zustand
- 国际化：next-intl（`zh` / `en`，`localePrefix: 'never'`）
- 请求：axios（直发 `/admin/api`、`/chat/api` 等，由 rewrites 反向代理到后端）
- 图表：echarts；进度条：nprogress；加密：jsencrypt

## 目录结构

```
frontend/
├── src/                  # 应用源码（App Router 页面、组件、store、i18n）
├── messages/             # next-intl 多语言文案
├── public/               # 静态资源
├── docs/ / e2e/          # 文档与端到端测试
├── scripts/package.sh    # [构建机] 打包 standalone 部署 tar 包
├── deploy.sh             # [目标机] 解包后部署/启动脚本（含 --systemd）
├── config/systemd/       # systemd 单元模板
├── DEPLOY.md             # 打包部署详细文档
└── next.config.mjs       # 构建配置 + 运行时 API 代理
```

## 前置条件

- Node.js ≥ 18.17（开发/构建需完整 Node 环境；生产 standalone 部署仅需 Node 运行时，无需在目标机 `npm install`）
- 包管理：npm（`npm ci` 用于干净安装 `package-lock.json`）

## 常用命令

```bash
npm install        # 安装依赖（开发）
npm run dev        # 本地开发，默认 http://localhost:3000
npm run build      # 生产构建（生成 .next/standalone 等产物）
npm run start      # 以 standalone 方式启动（依赖 npm run build）
npm run lint       # ESLint 检查
npm run type-check # tsc --noEmit 类型检查
```

## 与后端的代理关系

`next.config.mjs` 的 `rewrites()` 在**请求期**读取环境变量 `API_TARGET`（默认 `http://127.0.0.1:8080`），将以下路径反代到后端：

- `/admin/api/*` — 管理后台 API
- `/chat/api/*` — 用户侧对话 API
- `/oss/*`、`/doc/*`、`/schema/*`、`/static/*` — 文件/资源

该变量为**运行时**注入（无构建期 `NEXT_PUBLIC_*` 变量），因此部署包可在目标机修改后端地址后**重启即生效，无需重新构建**。

## 部署

本目录采用 standalone 打包 + 目标机解包部署模式，与仓库 `backend/` 的部署范式保持一致：

1. **构建机打包**：执行 `scripts/package.sh`，产出 `dist/maxkb-frontend-<version>.tar.gz`（含 `.next/standalone`、`.next/static`、`public`、`.env.example`、`deploy.sh`、systemd 模板、`DEPLOY.md`）。
2. **目标机部署**：解包后运行 `./deploy.sh` 生成 `.env`（`API_TARGET` / `PORT` 默认 `3000`）并 `node server.js` 启动；可加 `--systemd` 注册 systemd 单元。

详细步骤、反代（Nginx 80/443 → 3000）、升级与排错见 [DEPLOY.md](./DEPLOY.md)。
