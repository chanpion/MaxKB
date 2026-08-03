# MaxKB FastAPI Backend — 部署指南

MaxKB 重构后端（FastAPI + SQLModel + Agno）。本文档是**非容器化（裸机 / 虚机）部署**的总览，涵盖架构、环境变量配置、手动部署、反向代理与常见问题。

> 本文档**不含 Docker 部署**。离线源码包（tar.gz）的一站式安装、启停、systemd 托管步骤见 [`SOURCE_INSTALL.md`](./SOURCE_INSTALL.md)。
>
> 重要约束：重构后端与遗留 Django 后端**共享同一 PostgreSQL（pgvector）/ Redis 实例**，表结构由 Django 创建（或通过 `schema.sql` 建表），Alembic 仅做增量迁移打标。请勿用 `create_all` 或破坏性迁移改动既有表。

---

## 1. 架构概览

```
┌─────────────── 单节点（裸机 / 虚机）────────────────┐
│  web   (uvicorn app.main:app :8080)                  │
│  worker(arq: run_worker)                             │
│        │                       │                     │
│        ├────────► PostgreSQL 17 + pgvector            │
│        └────────► Redis 7 (缓存 + arq broker)         │
└─────────────────────────────────────────────────────┘
```

- **web**：FastAPI API 服务（`SERVER_NAME=web`）。
- **worker**：arq 异步任务（`app.core.tasks.run_worker`），处理文档向量化、定时触发。
- **postgres**：`pgvector` 扩展需提前启用（`CREATE EXTENSION vector`）。
- **redis**：作为缓存与 arq 消息代理。

`web` 与 `worker` 各自是独立进程，由 `scripts/start.sh` 或 systemd 单元分别拉起。

---

## 2. 部署方式选择

| 方式 | 适用场景 | 说明 |
|------|----------|------|
| **离线源码包**（推荐） | 目标机无公网 / 标准化交付 | 见 [`SOURCE_INSTALL.md`](./SOURCE_INSTALL.md)：`package.sh` 打 tar 包 → 目标机 `install.sh` 建库建表 → `start.sh`/`restart.sh`/`stop.sh` 启停，可选 `--systemd` 托管 |
| **手动裸机部署** | 开发 / 临时验证 | 见第 5 节，直接 `uv sync` + `uv run alembic upgrade head` + `uv run uvicorn app.main:app` |

---

## 3. 环境变量参考

所有变量均兼容遗留 `MAXKB_*` 命名（大小写不敏感），均有安全默认值。`.env.example` 已内置常用默认值，拷贝为 `.env` 后即可用。

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `SERVER_NAME` | 服务角色：`web` \| `local_model` | `web` |
| `MAXKB_DB_HOST` | PostgreSQL 主机 | `127.0.0.1` |
| `MAXKB_DB_PORT` | PostgreSQL 端口 | `5432` |
| `MAXKB_DB_NAME` | 数据库名 | `maxkb` |
| `MAXKB_DB_USER` | 数据库用户 | `root` |
| `MAXKB_DB_PASSWORD` | 数据库密码 | `Password123@postgres` |
| `MAXKB_DB_MAX_OVERFLOW` | 连接池溢出上限 | `80` |
| `MAXKB_REDIS_HOST` | Redis 主机 | `127.0.0.1` |
| `MAXKB_REDIS_PORT` | Redis 端口 | `6379` |
| `MAXKB_REDIS_PASSWORD` | Redis 密码（空字符串表示无密码） | `Password123@redis` |
| `MAXKB_REDIS_DB` | Redis DB 序号 | `0` |
| `MAXKB_REDIS_SENTINEL_SENTINELS` | Redis Sentinel 列表（可选，如 `h1:26379,h2:26379`） | 无 |
| `MAXKB_REDIS_SENTINEL_MASTER` | Sentinel master 名 | 无 |
| `MAXKB_WEB_HOST` | uvicorn 监听地址 | `0.0.0.0` |
| `MAXKB_WEB_PORT` | uvicorn 监听端口 | `8080` |
| `MAXKB_LOG_LEVEL` | 日志级别 | `DEBUG` |
| `MAXKB_API_PREFIX` | 管理端 API 前缀 | `/admin/api` |
| `MAXKB_CHAT_API_PREFIX` | 用户端 API 前缀 | `/chat/api` |
| `MAXKB_LOCAL_MODEL_HOST/PORT/PROTOCOL` | 本地模型服务地址 | `127.0.0.1:11636` |
| `MAXKB_LANGUAGE_CODE` | 语言 | `zh-CN` |
| `MAXKB_TIME_ZONE` | 时区 | `Asia/Shanghai` |

---

## 4. 数据库准备

重构后端**不自建表**。请按以下任一方式准备库表：

1. **复用遗留 Django 库**：直接连同一 PostgreSQL / 数据库名即可（推荐，表已存在）。
2. **全新部署（无 Django）**：手动执行 `schema.sql` 建表（已对齐全部 44 张表）：

   ```bash
   psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f schema.sql
   ```

无论哪种方式，都必须先启用 `vector` 扩展（仅有 `pgvector` 包还不够）：

```bash
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f init.sql
# 或：CREATE EXTENSION IF NOT EXISTS vector;
```

> 注意：Alembic 的 `alembic upgrade head` 仅执行空基线 `0001_empty`（打标），不会创建或修改任何表。离线源码包安装脚本会自动执行它，可重复运行、幂等。

---

## 5. 手动部署（裸机 / 虚机）

前提：Python 3.11、PostgreSQL 17 + pgvector、Redis 7，且已安装 `uv`。

```bash
cd backend

# 1) 安装依赖（不含 dev）
uv sync --no-dev

# 2) 准备数据库（见第 4 节）

# 3) 执行迁移打标
uv run alembic upgrade head

# 4) 启动服务（或使用 scripts/start.sh）
#    API：
uv run uvicorn app.main:app --host 0.0.0.0 --port 8080
#    Worker（另开终端）：
uv run python -c "from app.core.tasks import run_worker; run_worker()"
```

或使用项目自带脚本：

```bash
./scripts/start.sh all      # 启动 web + worker
./scripts/stop.sh all       # 停止
./scripts/restart.sh all    # 重启
```

---

## 6. 反向代理（Nginx 示例）

前端（Vue SPA）与 API 同域部署时，建议用 Nginx 统一转发：

```nginx
server {
    listen 80;
    server_name maxkb.example.com;

    # 前端静态资源（由 Django/构建产物托管，或单独部署）
    location /admin/ { proxy_pass http://127.0.0.1:8080/admin/; }
    location /chat/  { proxy_pass http://127.0.0.1:8080/chat/; }

    # 后端 API
    location /admin/api/ {
        proxy_pass http://127.0.0.1:8080/admin/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    location /chat/api/ {
        proxy_pass http://127.0.0.1:8080/chat/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

WebSocket / SSE（流式对话）走普通 HTTP，无需升级协议；如启用 gzip 或长超时，按需调整。

---

## 7. 常见问题

**Q: 启动报 `relation "xxx" does not exist`**
A: 表未创建。请先执行 `schema.sql` 或连到已有 Django 库（见第 4 节）。

**Q: 报 `extension "vector" is not installed` / 向量列创建失败**
A: 未启用 pgvector 扩展。执行 `init.sql` 或 `CREATE EXTENSION IF NOT EXISTS vector;`。

**Q: worker 不消费任务 / 任务卡住**
A: 确认 `MAXKB_REDIS_*` 与 app 一致，且 `redis-cli ping` 正常；worker 与 app 必须连同一个 Redis。

**Q: 前端连不上后端（422 / 404）**
A: 确认后端监听 `8080`，且 API 前缀与 `MAXKB_API_PREFIX` / `MAXKB_CHAT_API_PREFIX` 一致（默认 `/admin/api`、`/chat/api`，由 `.env` 透传）。前端 `vite.config.ts` 代理目标需指向该端口与对应前缀。

---

## 8. 文件清单（非 Docker 部署相关）

| 文件 | 用途 |
|------|------|
| `install.sh` | 目标机安装：建库 + 建表 + Alembic 基线（+ 可选 `--deps` / `--systemd`） |
| `schema.sql` | 完整 DDL（44 张表，全新部署时建表用，含 `vector` 扩展） |
| `init.sql` | 仅启用 `vector` 扩展（手动备用） |
| `init_tables.py` | 开发用：按 SQLModel metadata 补建缺失表 |
| `.env.example` | 环境变量模板 |
| `scripts/package.sh` | 打包离线源码 tar 包 |
| `scripts/start.sh` / `stop.sh` / `restart.sh` | 裸机启停 / 重启（web/worker/local_model/all） |
| `config/systemd/*.service` | web / worker 的 systemd 单元模板 |
| `README.md` | 项目概览 |
| `SOURCE_INSTALL.md` | 离线源码包部署详细步骤 |
