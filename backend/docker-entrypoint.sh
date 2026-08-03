#!/usr/bin/env bash
# coding=utf-8
# Container entrypoint for the MaxKB FastAPI backend.
#
# Responsibilities:
#   1. Wait for PostgreSQL to accept connections (pg_isready).
#   2. Wait for Redis to respond to PING (arq broker / cache).
#   3. Stamp / apply Alembic migrations (`alembic upgrade head`).
#   4. Launch the service selected by SERVICE_MODE (web | worker).
#
# The same image serves both the API (web) and the async worker (worker); the
# SERVICE_MODE environment variable selects which process boots. Defaults to "web".
set -euo pipefail

cd /opt/maxkb-backend

DB_HOST="${MAXKB_DB_HOST:-127.0.0.1}"
DB_PORT="${MAXKB_DB_PORT:-5432}"
DB_USER="${MAXKB_DB_USER:-root}"
DB_NAME="${MAXKB_DB_NAME:-maxkb}"
REDIS_HOST="${MAXKB_REDIS_HOST:-127.0.0.1}"
REDIS_PORT="${MAXKB_REDIS_PORT:-6379}"
SERVICE_MODE="${SERVICE_MODE:-web}"

# --- Wait for PostgreSQL ---------------------------------------------------
echo "[entrypoint] waiting for PostgreSQL at ${DB_HOST}:${DB_PORT} ..."
for _ in $(seq 1 60); do
  if pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; then
    echo "[entrypoint] PostgreSQL is ready."
    break
  fi
  sleep 1
done
if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; then
  echo "[entrypoint] ERROR: PostgreSQL did not become ready in time." >&2
  exit 1
fi

# --- Wait for Redis -------------------------------------------------------
echo "[entrypoint] waiting for Redis at ${REDIS_HOST}:${REDIS_PORT} ..."
for _ in $(seq 1 30); do
  if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping >/dev/null 2>&1; then
    echo "[entrypoint] Redis is ready."
    break
  fi
  sleep 1
done
if ! redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping >/dev/null 2>&1; then
  echo "[entrypoint] ERROR: Redis did not become ready in time." >&2
  exit 1
fi

# --- Run Alembic migrations ----------------------------------------------
# The initial migration is an empty baseline that only stamps the version state.
# It is safe to re-run; it is a no-op when already stamped.
echo "[entrypoint] running database migrations (alembic upgrade head) ..."
uv run alembic upgrade head || echo "[entrypoint] WARNING: alembic upgrade head failed (non-fatal)."

# --- Launch service -------------------------------------------------------
case "$SERVICE_MODE" in
  web)
    echo "[entrypoint] starting web service (uvicorn) on 0.0.0.0:${MAXKB_WEB_PORT:-8080}"
    exec uv run uvicorn app.main:app \
      --host "${MAXKB_WEB_HOST:-0.0.0.0}" \
      --port "${MAXKB_WEB_PORT:-8080}" \
      --workers "${UVICORN_WORKERS:-1}" \
      --log-level "${MAXKB_LOG_LEVEL:-info}"
    ;;
  worker)
    echo "[entrypoint] starting arq worker"
    exec uv run python -c "from app.core.tasks import run_worker; run_worker()"
    ;;
  *)
    echo "[entrypoint] ERROR: unknown SERVICE_MODE='${SERVICE_MODE}' (use web|worker)." >&2
    exit 1
    ;;
esac
