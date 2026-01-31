#!/bin/bash
# Emdash Agent Benchmark Runner
# Usage: ./run_benchmark.sh [dataset] [options]
#
# Environment variables:
#   MODEL         - Model name (default: accounts/fireworks/models/minimax-m2p1)
#   PARALLEL      - Number of concurrent tasks (default: 4)
#   OPENAI_BASE_URL - Custom OpenAI-compatible API base URL
#   OPENAI_API_KEY  - API key for custom endpoint
#
# Examples:
#   ./run_benchmark.sh evoeval
#   MODEL="opus-4.5" OPENAI_BASE_URL="https://api.example.com/v1" OPENAI_API_KEY="sk-..." ./run_benchmark.sh evoeval

set -e

# Default settings
DATASET="${1:-evoeval}"
MODEL="${MODEL:-accounts/fireworks/models/minimax-m2p1}"
PARALLEL="${PARALLEL:-4}"
AGENT="agents.emdash_coding:EmdashCodingAgent"

# Export API key for Fireworks
export FIREWORKS_API_KEY="${FIREWORKS_API_KEY:-fw_QU1Ai92J2LRZfNjYfBCKAk}"

# Shift first arg if it's a dataset name
if [[ "$1" != -* ]] && [[ -n "$1" ]]; then
    shift
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Ensure dependencies are installed via uv
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Sync dependencies (creates venv if needed)
cd "$SCRIPT_DIR"
uv sync

echo "========================================"
echo "Emdash Benchmark Runner"
echo "========================================"
echo "Dataset:  $DATASET"
echo "Model:    $MODEL"
echo "Parallel: $PARALLEL"
if [[ -n "$OPENAI_BASE_URL" ]]; then
    echo "Base URL: $OPENAI_BASE_URL"
fi
echo "========================================"

# Run benchmark using uv run
uv run harbor run \
    -d "$DATASET" \
    --agent-import-path "$AGENT" \
    -m "$MODEL" \
    -n "$PARALLEL" \
    "$@"
