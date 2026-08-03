#!/usr/bin/env bash
# Start MaxKB FastAPI backend services.
# Usage: ./start.sh [web|worker|local_model|all]   (default: all)
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT="$(pwd)"
RUN_DIR="$ROOT/run"
mkdir -p "$RUN_DIR"

# Load .env (if present) so port / prefix / log-level / secrets reach the services.
if [ -f "$ROOT/.env" ]; then
  set -a; . "$ROOT/.env"; set +a
fi
# Role selector: web | local_model. Workers do not branch on this.
export SERVER_NAME="${SERVER_NAME:-web}"

SERVICE="${1:-all}"

# Resolve the Python interpreter. Prefer the operator-prepared environment:
# local .venv, then the active `python` (venv/conda on PATH), lastly `uv run`.
if [ -x "./.venv/bin/python" ]; then
  PY=(./.venv/bin/python)
elif command -v python >/dev/null 2>&1; then
  PY=(python)
elif command -v uv >/dev/null 2>&1; then
  PY=(uv run python)
else
  PY=(python)
fi

start_one() {
  local name="$1"; shift
  local pidfile="$RUN_DIR/$name.pid"
  if [ -f "$pidfile" ] && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
    echo "[$name] already running (pid $(cat "$pidfile"))"
    return
  fi
  echo "[$name] starting: ${PY[*]} $*"
  nohup "${PY[@]}" "$@" > "$RUN_DIR/$name.log" 2>&1 &
  echo $! > "$pidfile"
  echo "[$name] started (pid $(cat "$pidfile")), log -> run/$name.log"
}

# Web is started directly via uvicorn (no `--reload`) so it matches the systemd unit
# and is safe for background/production use. `reload` stays only in the dev entrypoint main.py.
web_cmd() {
  start_one web -m uvicorn app.main:app \
    --host "${MAXKB_WEB_HOST:-0.0.0.0}" \
    --port "${MAXKB_WEB_PORT:-8080}" \
    --log-level "${MAXKB_LOG_LEVEL:-info}"
}

case "$SERVICE" in
  web)
    web_cmd
    ;;
  worker)
    start_one worker -c "from app.core.tasks import run_worker; run_worker()"
    ;;
  local_model)
    start_one local_model main_local_model.py
    ;;
  all)
    web_cmd
    start_one worker -c "from app.core.tasks import run_worker; run_worker()"
    ;;
  *)
    echo "Unknown service: $SERVICE (use web|worker|local_model|all)"
    exit 1
    ;;
esac
