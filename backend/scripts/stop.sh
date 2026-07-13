#!/usr/bin/env bash
# Stop MaxKB FastAPI backend services.
# Usage: ./stop.sh [web|worker|local_model|all]   (default: all)
set -euo pipefail

cd "$(dirname "$0")/.."
RUN_DIR="$(pwd)/run"
SERVICE="${1:-all}"

stop_one() {
  local name="$1"
  local pidfile="$RUN_DIR/$name.pid"
  if [ -f "$pidfile" ]; then
    local pid
    pid="$(cat "$pidfile")"
    if kill -0 "$pid" 2>/dev/null; then
      echo "[$name] stopping pid $pid"
      kill "$pid" 2>/dev/null || true
      for _ in $(seq 1 10); do
        kill -0 "$pid" 2>/dev/null || break
        sleep 1
      done
      if kill -0 "$pid" 2>/dev/null; then
        echo "[$name] force killing pid $pid"
        kill -9 "$pid" 2>/dev/null || true
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
  web|worker|local_model)
    stop_one "$SERVICE"
    ;;
  all)
    stop_one web
    stop_one worker
    stop_one local_model
    ;;
  *)
    echo "Unknown service: $SERVICE (use web|worker|local_model|all)"
    exit 1
    ;;
esac
