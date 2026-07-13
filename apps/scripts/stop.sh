#!/usr/bin/env bash
# Stop MaxKB original Django (apps) backend services.
# Usage: ./stop.sh [web|celery|all]   (default: all)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
RUN_DIR="$ROOT/run"
SERVICE="${1:-all}"

# Stop by signalling the whole process group (services are started with
# setsid), so the celery child spawned under `dev celery` is also killed.
stop_one() {
  local name="$1"
  local pidfile="$RUN_DIR/$name.pid"
  if [ -f "$pidfile" ]; then
    local pid
    pid="$(cat "$pidfile")"
    if kill -0 "$pid" 2>/dev/null; then
      echo "[$name] stopping process group $pid"
      kill -TERM -- -"$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null || true
      for _ in $(seq 1 10); do
        kill -0 "$pid" 2>/dev/null || break
        sleep 1
      done
      if kill -0 "$pid" 2>/dev/null; then
        echo "[$name] force killing process group $pid"
        kill -9 -- -"$pid" 2>/dev/null || kill -9 "$pid" 2>/dev/null || true
      fi
    else
      echo "[$name] not running (stale pid $pid)"
    fi
    rm -f "$pidfile"
  else
    echo "[$name] no pidfile, skipping"
  fi
}

case "$SERVICE" in
  web|celery)
    stop_one "$SERVICE"
    ;;
  all)
    stop_one web
    stop_one celery
    ;;
  *)
    echo "Unknown service: $SERVICE (use web|celery|all)"
    exit 1
    ;;
esac
