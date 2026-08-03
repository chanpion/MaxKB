#!/usr/bin/env bash
# MaxKB FastAPI backend — source installer (no Docker required).
#
# NOTE: dependencies are NOT installed by this script. The Python 3.11 runtime
# and its dependencies are expected to be prepared out-of-band on the target
# host (e.g. an activated venv / conda env, or a system Python with deps
# already installed). Pass --deps to let the script install them (uv or pip).
#
# What it does:
#   1. Verifies a usable Python 3.11 interpreter.
#   2. Creates .env from .env.example if missing.
#   3. Initializes PostgreSQL: creates the database (if absent) and applies schema.sql.
#   4. Optionally registers & starts systemd units (--systemd, needs root).
#
# Usage:
#   ./install.sh [--prefix DIR] [--deps] [--systemd] [--no-db] [-h]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

INSTALL_DIR="$ROOT"
DB_INIT=1
USE_SYSTEMD=0
INSTALL_DEPS=0

log()  { echo -e "\033[32m[install]\033[0m $*"; }
warn() { echo -e "\033[33m[warn]\033[0m $*"; }
err()  { echo -e "\033[31m[error]\033[0m $*" >&2; exit 1; }

usage() {
  cat <<EOF
Usage: ./install.sh [options]

Options:
  -p, --prefix DIR   Working/install directory (default: current dir)
  --deps             Install dependencies now (uv sync, or venv+pip). Off by
                     default — prepare the Python env out-of-band instead.
  --systemd         Register & start systemd units (requires root + systemd)
  --no-db           Skip database initialization (run schema.sql manually)
  -h, --help        Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--prefix) INSTALL_DIR="$2"; shift 2;;
    --deps)      INSTALL_DEPS=1; shift;;
    --systemd)   USE_SYSTEMD=1; shift;;
    --no-db)     DB_INIT=0; shift;;
    -h|--help)   usage; exit 0;;
    *) err "Unknown option: $1";;
  esac
done

# ---------------------------------------------------------------------------
# 1. Python check (runtime is prepared by the operator)
# ---------------------------------------------------------------------------
PY_BIN=""
if command -v python3.11 >/dev/null 2>&1; then
  PY_BIN="python3.11"
elif command -v python3 >/dev/null 2>&1; then
  ver="$(python3 -c 'import sys;print("%d.%d"%sys.version_info[:2])' 2>/dev/null || echo unknown)"
  if [[ "$ver" == "3.11" ]]; then
    PY_BIN="python3"
  else
    warn "System python3 is $ver; backend requires 3.11 — make sure the active env is 3.11."
  fi
else
  warn "No python3 / python3.11 found on PATH. Ensure the target env is 3.11 and on PATH."
fi

# ---------------------------------------------------------------------------
# 2. Dependencies (skipped by default)
# ---------------------------------------------------------------------------
if [[ "$INSTALL_DEPS" -eq 1 ]]; then
  if command -v uv >/dev/null 2>&1; then
    log "Installing dependencies with uv (into .venv) ..."
    uv sync --no-install-project 2>/dev/null || uv sync
  elif [[ -n "$PY_BIN" ]]; then
    log "Creating venv with $PY_BIN and installing via pip ..."
    "$PY_BIN" -m venv .venv
    ./.venv/bin/pip install -U pip >/dev/null
    ./.venv/bin/pip install -r requirements.txt
  else
    err "Cannot install dependencies: neither uv nor python3.11 available. Provide one, or install deps manually."
  fi
else
  log "Skipping dependency installation (--deps not set)."
  echo "  Ensure the active Python 3.11 environment has the dependencies installed, e.g.:"
  echo "    uv sync            # or"
  echo "    python -m venv .venv && .venv/bin/pip install -r requirements.txt"
fi

# ---------------------------------------------------------------------------
# 3. Environment file
# ---------------------------------------------------------------------------
if [[ ! -f .env ]]; then
  cp .env.example .env
  warn "Created .env from .env.example — review database/redis settings before starting."
fi

# ---------------------------------------------------------------------------
# 4. Database initialization
# ---------------------------------------------------------------------------
init_db() {
  set -a
  # shellcheck disable=SC1091
  [[ -f .env ]] && . ./.env
  set +a

  local DB_HOST="${MAXKB_DB_HOST:-127.0.0.1}"
  local DB_PORT="${MAXKB_DB_PORT:-5432}"
  local DB_USER="${MAXKB_DB_USER:-root}"
  local DB_NAME="${MAXKB_DB_NAME:-maxkb}"
  local DB_PASS="${MAXKB_DB_PASSWORD:-}"

  if ! command -v psql >/dev/null 2>&1; then
    warn "psql client not found — skipping automatic DB init. Run manually:"
    echo "  psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c 'CREATE DATABASE \"$DB_NAME\";'"
    echo "  psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f $ROOT/schema.sql"
    return
  fi

  export PGPASSWORD="$DB_PASS"
  if ! psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -tc \
       "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" 2>/dev/null | grep -q 1; then
    log "Creating database '$DB_NAME' ..."
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "CREATE DATABASE \"$DB_NAME\";"
  else
    log "Database '$DB_NAME' already exists, skipping creation."
  fi

  log "Applying schema.sql (tables + pgvector extension) ..."
  psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$ROOT/schema.sql"
  unset PGPASSWORD
  log "Database schema ready."

  # Stamp the Alembic baseline so future incremental migrations can be applied.
  # Tables already exist (schema.sql); `alembic upgrade head` only records the
  # current revision (the empty baseline `0001_empty`) and is idempotent.
  log "Stamping Alembic baseline (alembic upgrade head) ..."
  if command -v uv >/dev/null 2>&1; then
    uv run alembic upgrade head
  elif [[ -x ./.venv/bin/alembic ]]; then
    ./.venv/bin/alembic upgrade head
  elif [[ -n "$PY_BIN" ]]; then
    "$PY_BIN" -m alembic upgrade head
  else
    warn "alembic not available — skip baseline stamp. After the deps are installed, run:"
    echo "  alembic upgrade head"
  fi
}

if [[ "$DB_INIT" -eq 1 ]]; then
  init_db
else
  warn "Skipped database initialization (--no-db). Apply schema.sql manually."
fi

# ---------------------------------------------------------------------------
# 5. systemd (optional)
# ---------------------------------------------------------------------------
if [[ "$USE_SYSTEMD" -eq 1 ]]; then
  if [[ "$(id -u)" -ne 0 ]]; then
    err "--systemd requires root privileges."
  fi
  if ! command -v systemctl >/dev/null 2>&1 || [[ ! -d /run/systemd/system ]]; then
    err "systemd is not available on this host."
  fi
  RUN_USER="$(id -un)"
  UNIT_DIR="/etc/systemd/system"
  for svc in web worker; do
    src="$ROOT/config/systemd/maxkb-backend-$svc.service"
    [[ -f "$src" ]] || { warn "Missing unit template $src, skipping."; continue; }
    sed -e "s#__INSTALL_DIR__#$INSTALL_DIR#g" -e "s#__RUN_USER__#$RUN_USER#g" "$src" \
      > "$UNIT_DIR/maxkb-backend-$svc.service"
    systemctl daemon-reload
    systemctl enable "maxkb-backend-$svc"
    systemctl restart "maxkb-backend-$svc"
    log "Registered & started systemd unit: maxkb-backend-$svc"
  done
  echo
  echo "Services are managed by systemd:"
  echo "  systemctl status maxkb-backend-web maxkb-backend-worker"
  echo "  journalctl -u maxkb-backend-web -f"
  exit 0
fi

# ---------------------------------------------------------------------------
# 6. Done
# ---------------------------------------------------------------------------
echo
log "Installation complete."
echo
echo "Precondition: an active Python 3.11 environment with dependencies installed."
echo
echo "Start services (foreground-free, nohup):"
echo "  $ROOT/scripts/start.sh all      # web + worker"
echo "  $ROOT/scripts/start.sh web      # web only"
echo "  $ROOT/scripts/start.sh worker   # arq worker only"
echo
echo "Stop services:"
echo "  $ROOT/scripts/stop.sh all"
echo
echo "Restart services:"
echo "  $ROOT/scripts/restart.sh all"
echo
echo "Web API health check:"
echo "  curl http://127.0.0.1:${MAXKB_WEB_PORT:-8080}/api/health"
echo
echo "Logs: $ROOT/run/*.log"
