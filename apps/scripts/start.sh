#!/usr/bin/env bash
# Start MaxKB original Django (apps) backend services.
# Usage: ./start.sh [web|celery|all]   (default: all)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$ROOT"

RUN_DIR="$ROOT/run"
mkdir -p "$RUN_DIR"

SERVICE="${1:-all}"

# Python resolution: prefer `uv run`, then repo .venv, then system python.
if command -v uv >/dev/null 2>&1; then
  PY=(uv run python)
else
  if [ -x "$ROOT/.venv/bin/python" ]; then
    PY=("$ROOT/.venv/bin/python")
  else
    PY=(python)
  fi
fi

# Ensure venv bin is on PATH so the `celery` CLI (spawned by the management
# command via subprocess) can be found.
if [ -d "$ROOT/.venv/bin" ]; then
  export PATH="$ROOT/.venv/bin:$PATH"
fi

# Launch in a new session (setsid) so the whole process group can be stopped
# later, including the celery child spawned under `dev celery`.
start_one() {
  local name="$1"; shift
  local pidfile="$RUN_DIR/$name.pid"
  if [ -f "$pidfile" ] && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
    echo "[$name] already running (pid $(cat "$pidfile"))"
    return
  fi
  echo "[$name] starting: ${PY[*]} $*"
  setsid "${PY[@]}" "$@" > "$RUN_DIR/$name.log" 2>&1 &
  echo $! > "$pidfile"
  echo "[$name] started (pid $(cat "$pidfile")), log -> run/$name.log"
}

case "$SERVICE" in
  web)
    start_one web main.py dev web
    ;;
  celery)
    start_one celery main.py dev celery
    ;;
  all)
    start_one web main.py dev web
    start_one celery main.py dev celery
    ;;
  *)
    echo "Unknown service: $SERVICE (use web|celery|all)"
    exit 1
    ;;
esac
