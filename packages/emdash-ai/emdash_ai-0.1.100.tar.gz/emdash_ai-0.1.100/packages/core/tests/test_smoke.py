"""Smoke tests for emdash-core server.

These tests verify the server starts, accepts requests, and streams SSE events.
"""

import json
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest


# Server configuration
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 18765  # Use non-standard port to avoid conflicts
SERVER_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"
STARTUP_TIMEOUT = 30  # seconds
HEALTH_CHECK_INTERVAL = 0.5  # seconds


@pytest.fixture(scope="module")
def server_process():
    """Start the emdash-core server for testing."""
    # Find the emdash_core package
    core_dir = Path(__file__).parent.parent

    # Start server process
    process = subprocess.Popen(
        [
            sys.executable,
            "-m", "emdash_core.server",
            "--host", SERVER_HOST,
            "--port", str(SERVER_PORT),
        ],
        cwd=core_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    # Wait for server to be ready
    start_time = time.time()
    server_ready = False

    while time.time() - start_time < STARTUP_TIMEOUT:
        try:
            response = httpx.get(
                f"{SERVER_URL}/api/health",
                timeout=2.0,
            )
            if response.status_code == 200:
                server_ready = True
                break
        except (httpx.RequestError, httpx.TimeoutException):
            pass

        # Check if process died
        if process.poll() is not None:
            stdout = process.stdout.read() if process.stdout else ""
            pytest.fail(f"Server process died during startup:\n{stdout}")

        time.sleep(HEALTH_CHECK_INTERVAL)

    if not server_ready:
        process.terminate()
        stdout = process.stdout.read() if process.stdout else ""
        pytest.fail(f"Server failed to start within {STARTUP_TIMEOUT}s:\n{stdout}")

    yield process

    # Cleanup
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


class TestHealthEndpoint:
    """Tests for the health endpoint."""

    def test_health_returns_200(self, server_process):
        """Health endpoint should return 200 OK."""
        response = httpx.get(f"{SERVER_URL}/api/health")
        assert response.status_code == 200

    def test_health_returns_valid_json(self, server_process):
        """Health endpoint should return valid JSON with expected fields."""
        response = httpx.get(f"{SERVER_URL}/api/health")
        data = response.json()

        assert "status" in data
        assert "version" in data
        assert "uptime_seconds" in data
        assert "database" in data
        assert data["version"] == "0.1.0"

    def test_ready_endpoint(self, server_process):
        """Readiness probe should return ready status."""
        response = httpx.get(f"{SERVER_URL}/api/health/ready")
        assert response.status_code == 200
        assert response.json() == {"ready": True}

    def test_live_endpoint(self, server_process):
        """Liveness probe should return alive status."""
        response = httpx.get(f"{SERVER_URL}/api/health/live")
        assert response.status_code == 200
        assert response.json() == {"alive": True}


class TestAgentChatSSE:
    """Tests for the agent chat SSE streaming endpoint."""

    def test_chat_returns_sse_stream(self, server_process):
        """Chat endpoint should return SSE content type."""
        with httpx.stream(
            "POST",
            f"{SERVER_URL}/api/agent/chat",
            json={"message": "Hello"},
            timeout=30.0,
        ) as response:
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")

    def test_chat_streams_session_start_event(self, server_process):
        """Chat endpoint should stream session_start as first event."""
        events = []

        with httpx.stream(
            "POST",
            f"{SERVER_URL}/api/agent/chat",
            json={"message": "What is 2+2?"},
            timeout=30.0,
        ) as response:
            current_event = None

            for line in response.iter_lines():
                line = line.strip()

                if line.startswith("event: "):
                    current_event = line[7:]
                elif line.startswith("data: ") and current_event:
                    try:
                        data = json.loads(line[6:])
                        events.append({"type": current_event, "data": data})
                    except json.JSONDecodeError:
                        pass
                    current_event = None

                # Stop after getting a few events
                if len(events) >= 3:
                    break

        # Verify we got session_start
        assert len(events) > 0, "Should receive at least one event"
        assert events[0]["type"] == "session_start", "First event should be session_start"
        assert "agent_name" in events[0]["data"]
        assert "session_id" in events[0]["data"]

    def test_chat_streams_session_end_event(self, server_process):
        """Chat endpoint should stream session_end as final event."""
        events = []

        with httpx.stream(
            "POST",
            f"{SERVER_URL}/api/agent/chat",
            json={"message": "Test message"},
            timeout=60.0,
        ) as response:
            current_event = None

            for line in response.iter_lines():
                line = line.strip()

                if line.startswith("event: "):
                    current_event = line[7:]
                elif line.startswith("data: ") and current_event:
                    try:
                        data = json.loads(line[6:])
                        events.append({"type": current_event, "data": data})
                    except json.JSONDecodeError:
                        pass
                    current_event = None

        # Verify we got session_end
        assert len(events) > 0, "Should receive at least one event"

        event_types = [e["type"] for e in events]
        assert "session_end" in event_types, "Should receive session_end event"

        # session_end should be the last event
        assert events[-1]["type"] == "session_end"

    def test_chat_includes_session_id_header(self, server_process):
        """Chat endpoint should include X-Session-ID header."""
        with httpx.stream(
            "POST",
            f"{SERVER_URL}/api/agent/chat",
            json={"message": "Hello"},
            timeout=30.0,
        ) as response:
            session_id = response.headers.get("x-session-id")
            assert session_id is not None, "Should include X-Session-ID header"
            assert len(session_id) > 0


class TestAgentSessions:
    """Tests for agent session management."""

    def test_list_sessions_returns_list(self, server_process):
        """Sessions endpoint should return a list."""
        response = httpx.get(f"{SERVER_URL}/api/agent/sessions")
        assert response.status_code == 200

        data = response.json()
        assert "sessions" in data
        assert isinstance(data["sessions"], list)

    def test_delete_nonexistent_session_returns_404(self, server_process):
        """Deleting a non-existent session should return 404."""
        response = httpx.delete(
            f"{SERVER_URL}/api/agent/sessions/nonexistent-session-id"
        )
        assert response.status_code == 404


def parse_sse_events(lines):
    """Parse SSE lines into events.

    Args:
        lines: Iterator of SSE lines

    Returns:
        List of {"type": str, "data": dict} events
    """
    events = []
    current_event = None

    for line in lines:
        line = line.strip()

        if line.startswith("event: "):
            current_event = line[7:]
        elif line.startswith("data: ") and current_event:
            try:
                data = json.loads(line[6:])
                events.append({"type": current_event, "data": data})
            except json.JSONDecodeError:
                pass
            current_event = None

    return events


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
