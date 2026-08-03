#!/usr/bin/env bash
# Restart MaxKB FastAPI backend services: stop then start.
# Usage: ./restart.sh [web|worker|local_model|all]   (default: all)
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE="${1:-all}"

"$DIR/stop.sh" "$SERVICE"
# Give the OS a moment to release the port before rebinding.
sleep 2
"$DIR/start.sh" "$SERVICE"
