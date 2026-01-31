#!/bin/bash
# Example curl commands for interacting with emdash-core server
# Run ./run_server.sh first in another terminal

BASE_URL="http://localhost:8765"

echo "=== Health Check ==="
curl -s "$BASE_URL/api/health" | python3 -m json.tool
echo ""

echo "=== Readiness Probe ==="
curl -s "$BASE_URL/api/health/ready"
echo ""
echo ""

echo "=== Liveness Probe ==="
curl -s "$BASE_URL/api/health/live"
echo ""
echo ""

echo "=== Agent Chat (SSE Stream) ==="
echo "Streaming events from agent..."
curl --no-buffer -X POST "$BASE_URL/api/agent/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "What files are in this project?"}'
echo ""

echo "=== List Sessions ==="
curl -s "$BASE_URL/api/agent/sessions" | python3 -m json.tool
echo ""
