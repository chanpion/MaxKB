#!/usr/bin/env bash
# Package the MaxKB FastAPI backend source into an offline install tarball.
#
# The resulting tarball (maxkb-backend-<version>.tar.gz) is fully self-contained
# and requires NO Docker / container runtime on the target host. It contains the
# application source plus the installer (install.sh), DB schema, env template and
# systemd units.
#
# Usage:
#   ./package.sh [--version X.Y.Z] [--output DIR]
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT="$(pwd)"

# --- parse args ---
VERSION="$(grep -m1 '^version' "$ROOT/pyproject.toml" 2>/dev/null | sed -E 's/.*"([^"]+)".*/\1/')"
VERSION="${VERSION:-0.0.0}"
OUT_DIR="$ROOT/dist"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --version) VERSION="$2"; shift 2;;
    --output)  OUT_DIR="$2"; shift 2;;
    -h|--help) echo "Usage: $0 [--version X.Y.Z] [--output DIR]"; exit 0;;
    *) echo "Unknown arg: $1" >&2; exit 1;;
  esac
done

PKG_NAME="maxkb-backend-${VERSION}.tar.gz"
PKG_PATH="$OUT_DIR/$PKG_NAME"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
DEST="$TMP/maxkb-backend"

mkdir -p "$DEST" "$OUT_DIR"

# --- copy the source tree, excluding dev/runtime artifacts ---
tar -C "$ROOT" -cf - \
  --exclude='./.venv' \
  --exclude='./__pycache__' \
  --exclude='*/__pycache__' \
  --exclude='./.git' \
  --exclude='./run' \
  --exclude='./uploads' \
  --exclude='./docs' \
  --exclude='./dist' \
  --exclude='./.pytest_cache' \
  --exclude='./.ruff_cache' \
  --exclude='./.env' \
  --exclude='*.pyc' \
  --exclude='./Dockerfile' \
  --exclude='./docker-compose.yml' \
  --exclude='./docker-compose.dev.yml' \
  --exclude='./docker-entrypoint.sh' \
  --exclude='./.dockerignore' \
  --exclude='./scripts/build.sh' \
  --exclude='./.DS_Store' \
  --exclude='*/.DS_Store' \
  --exclude='./maxkb-backend-*.tar.gz' \
  . | tar -C "$DEST" -xf -

chmod +x "$DEST/install.sh" "$DEST/scripts/"*.sh 2>/dev/null || true

# --- build the tarball ---
tar -C "$TMP" -czf "$PKG_PATH" maxkb-backend

echo "Built offline source install package:"
echo "  $PKG_PATH  ($(du -h "$PKG_PATH" | cut -f1))"
echo
echo "Deploy on the target host with:"
echo "  tar -xzf $PKG_NAME -C /opt"
echo "  cd /opt/maxkb-backend && sudo ./install.sh"
