"""Async SSE listener for multiuser shared sessions in the TUI.

This module provides a background listener that receives real-time
events from a shared session via Server-Sent Events (SSE).
"""

import asyncio
import json
from typing import Callable, Optional

import httpx


class TUISessionListener:
    """Async SSE listener for TUI shared sessions.

    This listener runs as an asyncio task and calls back with events
    to be rendered in the TUI.
    """

    def __init__(
        self,
        base_url: str,
        session_id: str,
        user_id: str,
        on_event: Optional[Callable[[dict], None]] = None,
        is_owner: bool = False,
    ):
        """Initialize the SSE listener.

        Args:
            base_url: API base URL (e.g., http://localhost:8000)
            session_id: The shared session ID to listen to
            user_id: This user's ID (to filter out own events)
            on_event: Callback for event handling (receives event dict)
            is_owner: Whether this user is the session owner
        """
        self.base_url = base_url
        self.session_id = session_id
        self.user_id = user_id
        self.on_event = on_event
        self.is_owner = is_owner
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start listening for events as an async task."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._listen())

    async def stop(self) -> None:
        """Stop listening for events."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _listen(self) -> None:
        """Async listen loop for SSE events."""
        url = f"{self.base_url}/api/multiuser/session/{self.session_id}/stream"
        params = {"user_id": self.user_id}

        while self._running:
            try:
                async with httpx.AsyncClient(timeout=None) as client:
                    async with client.stream("GET", url, params=params) as response:
                        if response.status_code != 200:
                            await asyncio.sleep(5.0)  # Backoff on error
                            continue

                        current_event_type = None
                        async for line in response.aiter_lines():
                            if not self._running:
                                break

                            # Parse SSE format
                            if line.startswith("event:"):
                                current_event_type = line[6:].strip()
                            elif line.startswith("data:"):
                                data = line[5:].strip()
                                if data and data != "[DONE]":
                                    self._handle_event(data, current_event_type)
                                current_event_type = None

            except asyncio.CancelledError:
                break
            except httpx.ReadTimeout:
                continue  # Normal timeout, reconnect
            except httpx.ConnectError:
                await asyncio.sleep(2.0)  # Backoff before reconnect
            except Exception:
                if self._running:
                    await asyncio.sleep(2.0)

    def _handle_event(self, data: str, event_type: str | None = None) -> None:
        """Parse and handle an SSE event."""
        try:
            payload = json.loads(data)
            # Check both user_id and _source_user_id since server may use either
            source_user_id = payload.get("user_id", "") or payload.get("_source_user_id", "")
            event = {
                "type": event_type or payload.get("type", "unknown"),
                "data": payload,
                "source_user_id": source_user_id,
            }

            # Skip events from ourselves (user_message, typing indicators)
            if source_user_id == self.user_id and event["type"] in (
                "user_message", "user_typing", "user_stopped_typing"
            ):
                return

            # Skip response/tool events for owners (they get these directly from streaming)
            # Joiners need to receive these via broadcast
            if self.is_owner and event["type"] in (
                "assistant_text", "response", "partial_response",
                "tool_start", "tool_result", "thinking", "chat_chunk"
            ):
                return

            if self.on_event:
                self.on_event(event)
        except json.JSONDecodeError:
            pass  # Ignore malformed events
