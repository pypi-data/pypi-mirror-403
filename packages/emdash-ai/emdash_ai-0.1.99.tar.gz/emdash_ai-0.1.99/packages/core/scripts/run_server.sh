#!/bin/bash
# Start the emdash-core server

SCRIPT_DIR="$(dirname "$0")"
CORE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

cd "$CORE_DIR"

echo "Starting emdash-core server on http://localhost:8765"
echo "Repo root: $REPO_ROOT"
echo "Press Ctrl+C to stop"
echo ""

uv run python -m emdash_core.server --port 8765 --repo-root "$REPO_ROOT"
