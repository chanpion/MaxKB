# MaxKB 后端（FastAPI）源码安装部署包

本文档说明如何把 `backend/` 打包成一个**不依赖 Docker / 容器运行时**的离线源码安装包，并在目标机器上完成安装与启动。

包内仅包含应用源码 + 安装脚本 + 数据库 schema + 环境模板 + systemd 单元，**不引用**仓库根 `installer/` 目录。

> Docker 部署不在本文档范围内。如需容器化方案，请参考 `Dockerfile` / `docker-compose.yml` 等原有文件（不在本次交付维护范围）。

---

## 1. 打包（构建离线安装包）

在开发机（已装 `bash`、能访问仓库）上执行：

```bash
cd backend
bash scripts/package.sh            # 默认取 pyproject.toml 中的版本号
# 或显式指定版本与输出目录
bash scripts/package.sh --version 2.0.0 --output ./dist
```

生成的产物：`backend/dist/maxkb-backend-<version>.tar.gz`。

包内结构（解压到 `maxkb-backend/`）：

```
maxkb-backend/
├── install.sh              # 目标机安装脚本（默认不装依赖）
├── .env.example            # 环境变量模板
├── schema.sql              # 完整 DDL（含 CREATE EXTENSION vector）
├── init.sql                # 仅启用 pgvector 扩展（备用）
├── pyproject.toml          # 依赖清单（进包）
├── requirements.txt        # 依赖清单（进包，pip 兜底）
├── uv.lock                 # 锁定依赖版本（进包，目标机可 uv sync --frozen）
├── alembic.ini / alembic/  # Alembic 空基线（0001_empty）
├── app/  main.py  main_local_model.py  init_tables.py
├── config/systemd/         # web / worker 的 systemd 单元模板
├── scripts/                # start.sh / stop.sh / restart.sh / package.sh
└── README.md  SOURCE_INSTALL.md  DEPLOY.md
```

> **约定**：源码包**不含已安装的依赖**（`.venv` 被排除），但**包含依赖清单与锁文件**（`pyproject.toml` / `requirements.txt` / `uv.lock`）。安装脚本**默认不安装依赖**——Python 3.11 运行时及其依赖由运维在目标机另行准备（激活的 venv / conda 或已装好依赖的系统 Python），或安装时显式加 `--deps`。包内已排除 `__pycache__`、`.git`、`run/`、`uploads/`、`docs/`、`*.pyc` 及所有 Docker 相关文件。

---

## 2. 目标机前置条件

| 依赖 | 说明 |
|------|------|
| Linux（x86_64 / aarch64） | 建议在 Ubuntu 22.04+ / CentOS 8+ 上运行 |
| Python 3.11 环境（含依赖） | **默认由运维另行准备**。需为 3.11（pyproject 约束 `>=3.11,<3.12`）；在该环境内预先装好依赖（`uv sync` 或 `pip install -r requirements.txt`）。安装脚本默认不装，加 `--deps` 才装 |
| PostgreSQL 17 + pgvector | 含 `vector` 扩展；需提前建好实例 |
| Redis 7+ | 用作缓存与 arq broker |
| `psql` 客户端（可选） | 用于安装脚本自动建库建表；缺失则跳过，需手动执行 SQL |
| systemd（可选） | 仅 `--systemd` 模式需要，且需 root |

> **依赖与 Python 环境**：源码包不含已安装依赖，安装脚本默认也不装依赖。启动 `scripts/start.sh` 时会优先使用当前激活的 Python 环境（`.venv` → 激活的 `python` → `uv run`）。
>
> 数据库与 Redis 由用户自备（与遗留 Django 服务可共享同一实例）。表由 `schema.sql` 创建，Alembic 仅空基线打标，不建表。

---

## 3. 安装

把 tar 包传到目标机并解压：

```bash
tar -xzf maxkb-backend-<version>.tar.gz -C /opt
cd /opt/maxkb-backend
```

### 3.1 最简安装（手动启动）

```bash
sudo ./install.sh                 # 建库建表 + 打 Alembic 基线（默认不装依赖，无 systemd）
./scripts/start.sh all            # 启动 web + worker
```

`install.sh` 会：
1. 校验 Python 3.11 解释器是否可用（**默认不安装依赖**）；
2. 若 `.env` 不存在，从 `.env.example` 复制一份（**请按需修改**）；
3. 用 `psql` 创建数据库（若不存在）并执行 `schema.sql`；
4. 执行 `alembic upgrade head` 打 Alembic 空基线（幂等，不建表）；
5. 打印启动命令。

> 依赖安装默认**跳过**。两种准备依赖的方式：
> - 先自行装好依赖，再跑 `./install.sh`（不加 `--deps`）；
> - 或让脚本代装：`./install.sh --deps`（走 `uv sync`，无 uv 时退化为 `venv + pip`）。

随后：
- 启动：`scripts/start.sh [web|worker|local_model|all]`
- 停止：`scripts/stop.sh  [web|worker|local_model|all]`
- 重启：`scripts/restart.sh [web|worker|local_model|all]`
- 健康检查：`curl http://127.0.0.1:8080/api/health`
- 日志：`run/web.log`、`run/worker.log`

### 3.2 系统服务安装（systemd，推荐生产）

以 root 执行，由 systemd 托管 web 与 worker：

```bash
sudo ./install.sh --systemd       # 建库建表 + 打基线 + 注册并启动 unit（默认不装依赖）
# 需要脚本代装依赖时：
sudo ./install.sh --deps --systemd
```

安装脚本会把 `config/systemd/maxkb-backend-{web,worker}.service` 渲染到
`/etc/systemd/system/`（替换 `__INSTALL_DIR__` 与 `__RUN_USER__`），并 `enable` + `start`。

常用操作：
```bash
systemctl status  maxkb-backend-web maxkb-backend-worker
systemctl restart maxkb-backend-web
journalctl -u maxkb-backend-web -f
```

> 如果数据库已就绪、不需要脚本自动建表，可加 `--no-db`；若只想换安装目录用 `-p /srv/maxkb-backend`。

---

## 4. 配置

编辑 `.env`（与 `apps/maxkb/conf.py` 兼容的 `MAXKB_*` 变量），关键项：

| 变量 | 默认 | 说明 |
|------|------|------|
| `SERVER_NAME` | `web` | 服务角色：`web` / `local_model` |
| `MAXKB_DB_HOST/PORT/NAME/USER/PASSWORD` | `127.0.0.1:5432` / `maxkb` / `root` / `Password123@postgres` | PostgreSQL 连接 |
| `MAXKB_REDIS_HOST/PORT/PASSWORD/DB` | `127.0.0.1:6379` / `Password123@redis` / `0` | Redis 连接 |
| `MAXKB_WEB_HOST/PORT` | `0.0.0.0:8080` | Web 监听地址 |
| `MAXKB_API_PREFIX` | `/admin/api` | 管理端 API 前缀（`.env.example` 已设；不设置时 config.py 回退为 `/api`，会导致前端 404） |
| `MAXKB_CHAT_API_PREFIX` | `/chat/api` | 用户端 API 前缀 |
| `MAXKB_LOG_LEVEL` | `DEBUG` | 生产建议 `INFO` |
| `MAXKB_LANGUAGE_CODE` / `MAXKB_TIME_ZONE` | `zh-CN` / `Asia/Shanghai` | 区域设置 |

修改 `.env` 后：手动模式 `scripts/restart.sh`（或 stop+start）；systemd 模式 `systemctl restart maxkb-backend-*`。

---

## 5. 数据库手动初始化（无 psql 或跳过自动建表时）

```bash
# 建库
psql -h $MAXKB_DB_HOST -p $MAXKB_DB_PORT -U $MAXKB_DB_USER \
     -c 'CREATE DATABASE "maxkb";'
# 建表（已含 CREATE EXTENSION vector）
psql -h $MAXKB_DB_HOST -p $MAXKB_DB_PORT -U $MAXKB_DB_USER \
     -d maxkb -f schema.sql
```

若表由 `schema.sql` 创建，仍需打 Alembic 空基线（幂等，不建表）：

```bash
uv run alembic upgrade head      # 或 ./.venv/bin/alembic upgrade head
```

---

## 6. 与前端 / 反向代理

- Web 监听 `0.0.0.0:8080`，管理端 API 前缀 `/admin/api`，用户端 API 前缀 `/chat/api`（由 `MAXKB_API_PREFIX` / `MAXKB_CHAT_API_PREFIX` 驱动）。
- 前端（Vue）代理 `/admin/api`、`/chat/api` 到后端 `8080`；生产部署可用 Nginx 反向代理，将 `/admin/api`、`/chat/api`（以及前端静态资源 `/admin`、`/chat`）转发到 `127.0.0.1:8080`。Nginx 示例见 `DEPLOY.md`。
- 若与遗留 Django 服务同机，注意端口（Django 8080 / 本服务 8080）冲突时，改 `MAXKB_WEB_PORT` 并同步前端代理。

---

## 7. 卸载

- 手动模式：`./scripts/stop.sh all`，删除目录即可。
- systemd 模式：
  ```bash
  sudo systemctl disable --now maxkb-backend-web maxkb-backend-worker
  sudo rm -f /etc/systemd/system/maxkb-backend-*.service
  sudo systemctl daemon-reload
  ```
