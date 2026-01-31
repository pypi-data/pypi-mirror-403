#!/bin/bash
set -e

# Terminal-bench runner for emdash coding agent
# Requires: Harbor installed, Docker running (Colima or Rancher Desktop)

cd "$(dirname "$0")/.."

# Load .env file if exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Check Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker not running."
    echo "Start Colima: colima start"
    echo "Or Rancher Desktop from Applications"
    exit 1
fi

# Check Harbor is installed
if ! command -v harbor &> /dev/null; then
    echo "Error: Harbor not installed."
    echo "Install with: pip install harbor"
    exit 1
fi

# Default values (can be overridden via environment)
DATASET="${DATASET:-terminal-bench@2.0}"
MODEL="${MODEL:-accounts/fireworks/models/glm-4p7}"
PARALLEL="${PARALLEL:-4}"

echo "Running terminal-bench with emdash-coding agent"
echo "Dataset: $DATASET"
echo "Model: $MODEL"
echo "Parallel: $PARALLEL"
echo ""

# Run benchmark
harbor run \
    -d "$DATASET" \
    --agent-import-path agents.emdash_coding:EmdashCodingAgent \
    -m "$MODEL" \
    -n "$PARALLEL" \
    "$@"
