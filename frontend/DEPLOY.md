# MaxKB 前端打包与部署指南

重构后的前端位于 `frontend/`，是一个 **Next.js 14** 应用，使用 `output: 'standalone'` 生产部署模式。
本目录提供：

| 文件 | 作用 | 运行位置 |
| --- | --- | --- |
| `scripts/package.sh` | 构建并打包成可部署的 `tar.gz` | 构建机 |
| `deploy.sh` | 解包后配置并启动服务 | 目标机 |
| `config/systemd/maxkb-frontend.service` | systemd 单元模板 | 目标机（由 `deploy.sh --systemd` 渲染） |
| `.env.example` | 配置样例（后端地址 / 端口） | — |

> 关键特性：`API_TARGET` 在 `next.config.mjs` 的 `rewrites()` 中**运行时**读取，**无构建期变量**。
> 因此同一份部署包可在任意环境修改后端地址后「重启即可生效」，无需重新构建。

---

## 一、前置条件

### 构建机
- Node.js **>= 18.17**（Next.js 14.2 要求）
- npm（需支持 `npm ci`，故仓库须有 `package-lock.json`）
- 网络可访问 npm registry

### 目标机
- Node.js **>= 18.17**（**不包含**在部署包内，由运维另行准备）
- 部署包解压路径（建议 `/opt/maxkb/frontend`）
- 可选：systemd（用于进程托管）

---

## 二、在构建机打包

```bash
cd frontend
chmod +x scripts/package.sh deploy.sh

# 使用 package.json 中的 version（当前 0.1.0）
./scripts/package.sh

# 或显式指定版本 / 输出目录
./scripts/package.sh --version 1.2.3 --out-dir ./dist
```

脚本会依次执行：`npm ci` → `npm run build`，然后从以下来源组装部署包：

- `.next/standalone/`（standalone 运行时：`server.js` + 精简 `node_modules`）
- `.next/static` → 拷贝进 `standalone/.next/static`
- `public/` → 拷贝进 `standalone/public`
- `.env.example`、`deploy.sh`、`config/systemd/` 模板、`DEPLOY.md`、`VERSION`

产物：`frontend/dist/maxkb-frontend-<version>.tar.gz`。

> 说明：构建机上的开发依赖 `node_modules/`、`src/` 源码、`.next/cache`、`.git` 等**不会**进入包内，
> 包体仅包含运行所需的最小集。

---

## 三、在目标机部署

### 3.1 解包

```bash
mkdir -p /opt/maxkb/frontend
tar -xzf maxkb-frontend-<version>.tar.gz -C /opt/maxkb/frontend --strip-components=1
cd /opt/maxkb/frontend
```

解包后目录结构：

```
/opt/maxkb/frontend/
├── server.js              # standalone 入口
├── node_modules/          # standalone 精简依赖
├── .next/                 # static + required-server-files
├── public/
├── .env.example
├── deploy.sh
├── config/systemd/maxkb-frontend.service
├── DEPLOY.md
└── VERSION
```

### 3.2 配置后端地址与端口

```bash
./deploy.sh --env      # 从 .env.example 生成 .env（仅在缺失时生成）
```

编辑 `.env`：

```ini
# 后端地址：只填 host:port 根地址，/admin/api 等路径由 rewrite 自动拼接
API_TARGET=http://127.0.0.1:8080

# 前端监听端口（server.js 读取，默认 3000）
PORT=3000
```

> 修改 `.env` 后**重启**服务即可生效，无需重新构建。

### 3.3 启动（nohup 方式）

```bash
./deploy.sh            # 生成 .env（如缺失）并以后台 nohup 启动
```

- PID 写入 `logs/app.pid`，日志写入 `logs/app.log`
- 停止：`./deploy.sh --stop`

### 3.4 启动（systemd 方式，推荐生产）

```bash
# 以 root 运行；会创建 /etc/systemd/system/maxkb-frontend.service 并启用
RUN_USER=maxkb ./deploy.sh --systemd
```

模板中的占位符会被渲染为实际路径 / 端口 / 后端地址 / 运行用户：

| 占位符 | 来源 |
| --- | --- |
| `__DEPLOY_DIR__` | 当前解包目录（`pwd`） |
| `__PORT__` | `.env` 的 `PORT`（默认 3000） |
| `__API_TARGET__` | `.env` 的 `API_TARGET` |
| `__RUN_USER__` | 环境变量 `RUN_USER`（默认 `maxkb`） |

建议先创建运行用户（如 `useradd -r -s /usr/sbin/nologin maxkb` 并 `chown -R maxkb:maxkb /opt/maxkb/frontend`）。

常用命令：

```bash
systemctl status maxkb-frontend
journalctl -u maxkb-frontend -f
systemctl restart maxkb-frontend
```

卸载：`./deploy.sh --uninstall`（需 root）。

---

## 四、与后端的关系（反向代理）

前端本身不承担 API 逻辑，仅通过 `next.config.mjs` 的 `rewrites` 将以下路径**反向代理**到 `API_TARGET`（后端 8080）：

| 前端路径 | 代理目标 |
| --- | --- |
| `/admin/api/*` | `{API_TARGET}/admin/api/*` |
| `/chat/api/*` | `{API_TARGET}/chat/api/*` |
| `/oss/*` | `{API_TARGET}/oss/*` |
| `/doc/*` | `{API_TARGET}/doc/*` |
| `/schema/*` | `{API_TARGET}/schema/*` |
| `/static/*` | `{API_TARGET}/static/*` |

因此目标机只需保证前端能访问到后端的 `host:port` 即可，无需额外配置 Nginx 反代 API（若需在 80/443 统一入口，可再在 Nginx 将 `/` 指向前端、`/admin/api`、`/chat/api` 等指向后端）。

---

## 五、升级

1. 在构建机重新 `./scripts/package.sh --version <新版本>` 产出新包；
2. 目标机停止服务（`./deploy.sh --stop` 或 `systemctl stop maxkb-frontend`）；
3. 备份旧目录后解包新包到同一目录；
4. 保留原有 `.env`（不要覆盖），重启服务。

---

## 六、常见问题

- **启动后页面空白 / API 404**：检查 `.env` 中 `API_TARGET` 是否指向可达的后端地址与端口；改后需重启。
- **端口被占用**：修改 `.env` 的 `PORT` 并重启。
- **`node: command not found`**：目标机未安装 Node.js，请先安装 >= 18.17。
- **systemd 启动失败**：查看 `journalctl -u maxkb-frontend`，常见为 `User` 不存在或目录权限不足。
