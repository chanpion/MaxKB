#!/usr/bin/env bash
# coding=utf-8
# Build (and optionally push) the MaxKB FastAPI backend Docker image.
#
# Usage:
#   ./scripts/build.sh [--push] [--no-cache]
#
# Environment overrides:
#   IMAGE_NAME   default: maxkb-backend
#   IMAGE_TAG    default: <git short sha>  (or "latest" outside a git repo)
#   DOCKERFILE   default: Dockerfile (in repo root)
set -euo pipefail

cd "$(dirname "$0")/.."
ROOT="$(pwd)"

IMAGE_NAME="${IMAGE_NAME:-maxkb-backend}"

# Derive a default tag from git, fall back to the date stamp.
if command -v git >/dev/null 2>&1 && git rev-parse --short HEAD >/dev/null 2>&1; then
  DEFAULT_TAG="$(git rev-parse --short HEAD)"
else
  DEFAULT_TAG="$(date +%Y%m%d)"
fi
IMAGE_TAG="${IMAGE_TAG:-$DEFAULT_TAG}"
DOCKERFILE="${DOCKERFILE:-Dockerfile}"

PUSH=0
EXTRA_ARGS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --push) PUSH=1; shift ;;
    --no-cache) EXTRA_ARGS+=(--no-cache); shift ;;
    -h|--help)
      grep '^#' "$0" | sed 's/^# \{0,1\}//'
      exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

FULL_TAG="${IMAGE_NAME}:${IMAGE_TAG}"

echo "==> Building ${FULL_TAG} from ${DOCKERFILE}"
docker build \
  -f "$DOCKERFILE" \
  -t "$FULL_TAG" \
  -t "${IMAGE_NAME}:latest" \
  "${EXTRA_ARGS[@]}" \
  "$ROOT"

echo "==> Built: ${FULL_TAG} (also tagged ${IMAGE_NAME}:latest)"

if [ "$PUSH" -eq 1 ]; then
  echo "==> Pushing ${FULL_TAG} and ${IMAGE_NAME}:latest"
  docker push "$FULL_TAG"
  docker push "${IMAGE_NAME}:latest"
  echo "==> Pushed."
else
  echo "==> Done. Use --push to also push to a registry (set IMAGE_NAME to your registry path)."
fi
