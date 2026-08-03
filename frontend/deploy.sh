#!/usr/bin/env bash
#
# MaxKB 前端部署脚本（在「目标机」上执行）
#
# 解包部署包后，在本目录（含 server.js）内运行：
#   ./deploy.sh              # 生成 .env（若缺失）并以 nohup 方式启动
#   ./deploy.sh --env        # 仅生成/刷新 .env 配置，不启动
#   ./deploy.sh --stop       # 停止运行中的服务
#   ./deploy.sh --systemd    # 注册并启用 systemd 服务（需 root）
#   ./deploy.sh --uninstall  # 卸载 systemd 服务（需 root）
#
# 运行环境说明：
#   - 目标机需自行准备 Node.js >= 18.17，本包不含 node_modules（除 standalone 精简依赖）。
#   - API_TARGET / PORT 通过 .env 注入：
#       * PORT 由 standalone server.js 在启动时读取；
#       * API_TARGET 由 next.config.mjs 的 rewrites() 在 server.js 启动时读取。
#     => 修改 .env 后「重启」即可切换后端地址，无需重新构建。

set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

APP_NAME="maxkb-frontend"
ENV_FILE=".env"
LOG_FILE="logs/app.log"
PID_FILE="logs/app.pid"

mkdir -p logs

# -------- 解析参数 --------
ACTION="start"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --env)       ACTION="env" ;;
    --stop)      ACTION="stop" ;;
    --systemd)   ACTION="systemd" ;;
    --uninstall) ACTION="uninstall" ;;
    -h|--help)   sed -n '8,18p' "$0"; exit 0 ;;
    *) echo "未知参数: $1" >&2; exit 1 ;;
  esac
  shift
done

# -------- 生成 .env --------
generate_env() {
  if [[ -f "${ENV_FILE}" ]]; then
    echo "==> [deploy] 已存在 ${ENV_FILE}，保留现有配置（如需重置请手动删除该文件）。"
  else
    cp ".env.example" "${ENV_FILE}"
    echo "==> [deploy] 已根据 .env.example 生成 ${ENV_FILE}，请按需修改 API_TARGET / PORT。"
  fi
}

# -------- 停止 --------
stop_service() {
  if [[ -f "${PID_FILE}" ]]; then
    PID="$(cat "${PID_FILE}")"
    if kill -0 "${PID}" 2>/dev/null; then
      echo "==> [deploy] 停止进程 ${PID} ..."
      kill "${PID}" 2>/dev/null || true
      sleep 2
      kill -9 "${PID}" 2>/dev/null || true
    fi
    rm -f "${PID_FILE}"
  fi
  # 兜底：精确匹配 server.js 进程
  pkill -f "node .*server\.js" 2>/dev/null || true
  echo "==> [deploy] 已停止。"
}

# -------- 启动（nohup） --------
start_service() {
  generate_env
  # 加载 .env 到当前 shell（供 server.js / rewrites 读取）
  set -a; [[ -f "${ENV_FILE}" ]] && . "${ENV_FILE}"; set +a
  PORT="${PORT:-3000}"
  echo "==> [deploy] 启动 ${APP_NAME} (PORT=${PORT}, API_TARGET=${API_TARGET:-http://127.0.0.1:8080})"
  nohup node server.js > "${LOG_FILE}" 2>&1 &
  echo $! > "${PID_FILE}"
  sleep 2
  PID="$(cat "${PID_FILE}")"
  if kill -0 "${PID}" 2>/dev/null; then
    echo "==> [deploy] 已启动，PID=${PID}，日志见 ${LOG_FILE}"
  else
    echo "ERROR: 启动失败，请查看 ${LOG_FILE}" >&2
    exit 1
  fi
}

# -------- systemd 注册 --------
install_systemd() {
  generate_env
  set -a; [[ -f "${ENV_FILE}" ]] && . "${ENV_FILE}"; set +a
  PORT="${PORT:-3000}"
  API_TARGET="${API_TARGET:-http://127.0.0.1:8080}"
  RUN_USER="${RUN_USER:-maxkb}"

  UNIT_SRC="config/systemd/${APP_NAME}.service"
  [[ -f "${UNIT_SRC}" ]] || { echo "ERROR: 缺少 ${UNIT_SRC}" >&2; exit 1; }
  if [[ $(id -u) -ne 0 ]]; then
    echo "ERROR: 注册 systemd 服务需以 root 运行" >&2; exit 1
  fi

  DEPLOY_DIR="$(pwd)"
  TMP_UNIT="$(mktemp)"
  sed -e "s|__DEPLOY_DIR__|${DEPLOY_DIR}|g" \
      -e "s|__PORT__|${PORT}|g" \
      -e "s|__API_TARGET__|${API_TARGET}|g" \
      -e "s|__RUN_USER__|${RUN_USER}|g" \
      "${UNIT_SRC}" > "${TMP_UNIT}"
  install -m 0644 "${TMP_UNIT}" "/etc/systemd/system/${APP_NAME}.service"
  rm -f "${TMP_UNIT}"

  systemctl daemon-reload
  systemctl enable "${APP_NAME}"
  systemctl restart "${APP_NAME}"
  echo "==> [deploy] systemd 服务已注册并启动: ${APP_NAME}（运行用户 ${RUN_USER}）"
}

# -------- systemd 卸载 --------
uninstall_systemd() {
  if [[ $(id -u) -ne 0 ]]; then
    echo "ERROR: 卸载 systemd 服务需以 root 运行" >&2; exit 1
  fi
  systemctl stop "${APP_NAME}" 2>/dev/null || true
  systemctl disable "${APP_NAME}" 2>/dev/null || true
  rm -f "/etc/systemd/system/${APP_NAME}.service"
  systemctl daemon-reload
  echo "==> [deploy] systemd 服务已卸载。"
}

# -------- 分发 --------
case "${ACTION}" in
  env)       generate_env ;;
  stop)      stop_service ;;
  start)     start_service ;;
  systemd)   install_systemd ;;
  uninstall) uninstall_systemd ;;
esac
