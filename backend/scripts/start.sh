#!/usr/bin/env bash
# Start MaxKB FastAPI backend services.
# Usage: ./start.sh [web|worker|local_model|all]   (default: all)
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT="$(pwd)"
RUN_DIR="$ROOT/run"
mkdir -p "$RUN_DIR"

SERVICE="${1:-all}"

# Prefer `uv run` when available, otherwise fall back to system python.
if command -v uv >/dev/null 2>&1; then
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

case "$SERVICE" in
  web)
    start_one web main.py
    ;;
  worker)
    start_one worker -c "from app.core.tasks import run_worker; run_worker()"
    ;;
  local_model)
    start_one local_model main_local_model.py
    ;;
  all)
    start_one web main.py
    start_one worker -c "from app.core.tasks import run_worker; run_worker()"
    ;;
  *)
    echo "Unknown service: $SERVICE (use web|worker|local_model|all)"
    exit 1
    ;;
esac
