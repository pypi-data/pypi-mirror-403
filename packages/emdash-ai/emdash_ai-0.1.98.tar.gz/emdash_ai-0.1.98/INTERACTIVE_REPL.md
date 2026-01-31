# Multiuser Message Sync Implementation Plan

## Overview

This document outlines the implementation plan for adding real-time message synchronization to the multiuser shared sessions feature. Currently, `/share` and `/join` commands work, but messages don't sync between participants.

## Current State

### What Works
- `/share` - Creates a shared session in Firebase, returns invite code
- `/join <code>` - Joins a session, adds participant to Firebase
- `/who` - Lists participants
- `/leave` - Leaves session
- Firebase sync provider stores session state
- SSE streaming endpoint exists (`/session/{id}/stream`)
- Event broadcaster fans out events to all participants

### What's Missing
- Messages sent by one participant don't appear for others
- CLI doesn't use the multiuser message API
- No background listener for incoming events
- No real-time rendering of other participants' activity

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLI Instance A (Owner)                       │
├─────────────────────────────────────────────────────────────────────┤
│  /share → shared_session_id = "abc123"                              │
│  User types: "help me fix this bug"                                 │
│       ↓                                                              │
│  POST /api/multiuser/session/abc123/message                         │
│       ↓                                                              │
│  SSE Listener receives: RESPONSE, TOOL_START, etc.                  │
│       ↓                                                              │
│  Render to terminal                                                  │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              │ Firebase Realtime DB
                              │ Event Sync
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       CLI Instance B (Joined)                        │
├─────────────────────────────────────────────────────────────────────┤
│  /join ABC123 → shared_session_id = "abc123"                        │
│       ↓                                                              │
│  SSE Listener starts → receives events from Instance A              │
│       ↓                                                              │
│  Sees: "User A asked: help me fix this bug"                         │
│  Sees: Agent response streaming in real-time                         │
│                                                                      │
│  User B types: "also check the tests"                               │
│       ↓                                                              │
│  POST /api/multiuser/session/abc123/message                         │
│  (queued if agent busy with A's message)                            │
└─────────────────────────────────────────────────────────────────────┘
```

## Implementation Phases

---

## Phase 1: Shared Session State Tracking

**Goal**: CLI knows when it's in a shared session and tracks the necessary state.

### Files to Modify
- `packages/cli/emdash_cli/commands/agent/interactive.py`

### Changes

#### 1.1 Add shared session state variables (near line 209)

```python
# Current
session_id = None
current_spec = None

# Add
shared_session_id: str | None = None  # The multiuser session ID
shared_user_id: str | None = None     # Our user ID in the shared session
shared_invite_code: str | None = None # For display purposes
is_shared_session: bool = False       # Quick check flag
```

#### 1.2 Update `/share` handler (lines 781-786)

```python
elif command == "/share":
    plan_mode = current_mode == AgentMode.PLAN
    result = handle_share(args, client, session_id, model, plan_mode)
    if result.get("session_id"):
        shared_session_id = result["session_id"]
        shared_invite_code = result.get("invite_code")
        shared_user_id = result.get("user_id") or _get_user_id()
        is_shared_session = True
        # TODO Phase 2: Start SSE listener
    return True
```

#### 1.3 Update `/join` handler (lines 789-795)

```python
elif command == "/join":
    result = handle_join(args, client)
    if result.get("session_id"):
        shared_session_id = result["session_id"]
        shared_user_id = result.get("user_id") or _get_user_id()
        is_shared_session = True
        # Load existing messages from session
        # TODO Phase 2: Start SSE listener, fetch history
    return True
```

#### 1.4 Update `/leave` handler (lines 797-805)

```python
elif command == "/leave":
    if shared_session_id:
        handle_leave(args, client, shared_session_id, shared_user_id)
        # TODO Phase 2: Stop SSE listener
        shared_session_id = None
        shared_user_id = None
        shared_invite_code = None
        is_shared_session = False
    else:
        console.print("[yellow]Not in a shared session.[/yellow]")
    return True
```

#### 1.5 Add user ID helper function

```python
def _get_user_id() -> str:
    """Generate consistent user ID for this machine."""
    import hashlib
    import socket
    import os
    hostname = socket.gethostname()
    username = os.environ.get("USER", os.environ.get("USERNAME", "user"))
    return hashlib.sha256(f"{username}@{hostname}".encode()).hexdigest()[:16]
```

### Deliverables
- [ ] Shared session state variables added
- [ ] `/share` updates state on success
- [ ] `/join` updates state on success
- [ ] `/leave` clears state
- [ ] User ID generation helper

---

## Phase 2: Message Routing via Multiuser API

**Goal**: When in a shared session, send messages through the multiuser API instead of direct agent calls.

### Files to Modify
- `packages/cli/emdash_cli/commands/agent/interactive.py`
- `packages/cli/emdash_cli/commands/agent/handlers/multiuser.py`

### Changes

#### 2.1 Add multiuser message sender function

```python
# In multiuser.py handlers

def send_shared_message(
    client,
    session_id: str,
    user_id: str,
    content: str,
    images: list[dict] | None = None,
) -> dict:
    """Send a message to a shared session.

    Returns:
        Dict with message_id, queued_at, queue_position, agent_busy
    """
    import httpx

    response = httpx.post(
        f"{client.base_url}/api/multiuser/session/{session_id}/message",
        json={
            "user_id": user_id,
            "content": content,
            "images": images,
            "priority": 0,
        },
        timeout=30.0,
    )

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to send message: {response.text}")
```

#### 2.2 Modify chat dispatch in interactive.py (lines 938-953)

```python
# Current flow
if session_id:
    stream = client.agent_continue_stream(session_id, expanded_input, ...)
else:
    stream = client.agent_chat_stream(expanded_input, model, options)

# New flow
if is_shared_session and shared_session_id:
    # Use multiuser API - message will be queued and processed
    result = send_shared_message(
        client,
        shared_session_id,
        shared_user_id,
        expanded_input,
        images=images_to_send,
    )

    if result.get("agent_busy"):
        console.print(f"[dim]Message queued (position {result.get('queue_position', 0) + 1})[/dim]")

    # Response comes via SSE stream (Phase 3)
    # For now, wait and poll or show placeholder

elif session_id:
    stream = client.agent_continue_stream(session_id, expanded_input, ...)
else:
    stream = client.agent_chat_stream(expanded_input, model, options)
```

#### 2.3 Update handle_join to return user_id

```python
# In multiuser.py handle_join()

def handle_join(args: str, client) -> dict:
    # ... existing code ...

    # Get/generate user_id
    user_id = _get_user_id()  # Add to request

    response = httpx.post(
        f"{client.base_url}/api/multiuser/session/join",
        json={
            "invite_code": invite_code,
            "display_name": display_name,
            "user_id": user_id,  # Include user_id
        },
        timeout=30.0,
    )

    if response.status_code == 200:
        data = response.json()
        return {
            "session_id": data.get("session_id"),
            "user_id": user_id,
            "participants": data.get("participants", []),
            "message_count": data.get("message_count", 0),
        }
```

### Deliverables
- [ ] `send_shared_message()` function
- [ ] Chat dispatch checks `is_shared_session`
- [ ] Messages routed to multiuser API when shared
- [ ] Queue position feedback shown to user

---

## Phase 3: SSE Event Listener

**Goal**: Background task listens for events and renders them in real-time.

### Files to Create/Modify
- `packages/cli/emdash_cli/commands/agent/sse_listener.py` (NEW)
- `packages/cli/emdash_cli/commands/agent/interactive.py`

### Changes

#### 3.1 Create SSE listener module

```python
# sse_listener.py

import asyncio
import httpx
from rich.console import Console
from typing import Callable, Optional

console = Console()


class SharedSessionListener:
    """Listens to SSE events from a shared session."""

    def __init__(
        self,
        base_url: str,
        session_id: str,
        user_id: str,
        on_event: Optional[Callable] = None,
    ):
        self.base_url = base_url
        self.session_id = session_id
        self.user_id = user_id
        self.on_event = on_event or self._default_handler
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        """Start listening for events."""
        self._running = True
        self._task = asyncio.create_task(self._listen())

    async def stop(self):
        """Stop listening."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _listen(self):
        """Main listen loop."""
        url = f"{self.base_url}/api/multiuser/session/{self.session_id}/stream"
        params = {"user_id": self.user_id}

        async with httpx.AsyncClient(timeout=None) as client:
            while self._running:
                try:
                    async with client.stream("GET", url, params=params) as response:
                        async for line in response.aiter_lines():
                            if not self._running:
                                break
                            if line.startswith("data:"):
                                data = line[5:].strip()
                                if data and data != "[DONE]":
                                    await self._handle_event(data)
                except httpx.ReadTimeout:
                    continue  # Reconnect
                except Exception as e:
                    console.print(f"[dim]SSE connection error: {e}[/dim]")
                    await asyncio.sleep(2)  # Backoff before reconnect

    async def _handle_event(self, data: str):
        """Parse and handle SSE event."""
        import json
        try:
            event = json.loads(data)
            await self.on_event(event)
        except json.JSONDecodeError:
            pass

    def _default_handler(self, event: dict):
        """Default event handler - prints events."""
        event_type = event.get("type", "unknown")

        if event_type == "participant_joined":
            name = event.get("data", {}).get("display_name", "Someone")
            console.print(f"[green]+ {name} joined the session[/green]")

        elif event_type == "participant_left":
            name = event.get("data", {}).get("display_name", "Someone")
            console.print(f"[yellow]- {name} left the session[/yellow]")

        elif event_type == "response":
            # Agent response text
            text = event.get("data", {}).get("text", "")
            source = event.get("source_user_id", "")
            if source != self.user_id:
                # Response to someone else's message
                console.print(f"[cyan]{text}[/cyan]")

        elif event_type == "tool_start":
            tool = event.get("data", {}).get("tool", "")
            console.print(f"[dim]Using tool: {tool}[/dim]")

        elif event_type == "queue_updated":
            length = event.get("data", {}).get("length", 0)
            if length > 0:
                console.print(f"[dim]Queue: {length} message(s) waiting[/dim]")
```

#### 3.2 Integrate listener in interactive.py

```python
# At top of run_interactive()
from .sse_listener import SharedSessionListener

# In state variables
sse_listener: Optional[SharedSessionListener] = None

# After /share success
if result.get("session_id"):
    shared_session_id = result["session_id"]
    # ... other state ...

    # Start SSE listener
    sse_listener = SharedSessionListener(
        base_url=client.base_url,
        session_id=shared_session_id,
        user_id=shared_user_id,
        on_event=handle_shared_event,
    )
    asyncio.create_task(sse_listener.start())

# After /join success - same pattern

# After /leave
if sse_listener:
    asyncio.create_task(sse_listener.stop())
    sse_listener = None

# Event handler function
async def handle_shared_event(event: dict):
    """Handle incoming shared session events."""
    event_type = event.get("type", "")
    data = event.get("data", {})
    source_user = event.get("source_user_id", "")

    # Skip our own events (we see them locally)
    if source_user == shared_user_id:
        return

    if event_type == "participant_joined":
        console.print(f"\n[green]+ {data.get('display_name')} joined[/green]")

    elif event_type == "participant_left":
        console.print(f"\n[yellow]- {data.get('display_name')} left[/yellow]")

    elif event_type == "user_message":
        # Another user sent a message
        console.print(f"\n[bold]{data.get('display_name')}:[/bold] {data.get('content')}")

    elif event_type in ("response", "partial_response", "assistant_text"):
        # Agent response - render it
        text = data.get("text", "")
        if text:
            console.print(text, end="")

    elif event_type == "tool_start":
        tool = data.get("tool", "unknown")
        console.print(f"\n[dim]Tool: {tool}[/dim]")

    elif event_type == "tool_result":
        pass  # Often verbose, maybe summarize

    elif event_type == "error":
        console.print(f"\n[red]Error: {data.get('message')}[/red]")
```

### Deliverables
- [ ] `SharedSessionListener` class created
- [ ] Listener starts on `/share` and `/join`
- [ ] Listener stops on `/leave`
- [ ] Events rendered to terminal
- [ ] Reconnection on disconnect

---

## Phase 4: History Sync on Join

**Goal**: When joining a session, fetch and display existing conversation history.

### Files to Modify
- `packages/cli/emdash_cli/commands/agent/handlers/multiuser.py`

### Changes

#### 4.1 Fetch messages on join

```python
def handle_join(args: str, client) -> dict:
    # ... existing join logic ...

    if response.status_code == 200:
        data = response.json()
        session_id = data.get("session_id")

        # Fetch conversation history
        messages = fetch_session_messages(client, session_id)

        if messages:
            console.print()
            console.print(Panel(
                f"[dim]Showing last {len(messages)} messages...[/dim]",
                title="Session History",
                border_style="dim",
            ))

            for msg in messages:
                role = msg.get("role", "")
                content = msg.get("content", "")

                if role == "user":
                    console.print(f"[bold]User:[/bold] {content[:200]}...")
                elif role == "assistant":
                    console.print(f"[cyan]Assistant:[/cyan] {content[:200]}...")

            console.print()

        return {
            "session_id": session_id,
            "user_id": user_id,
            "messages": messages,
            ...
        }


def fetch_session_messages(client, session_id: str, limit: int = 10) -> list:
    """Fetch recent messages from a session."""
    import httpx

    response = httpx.get(
        f"{client.base_url}/api/multiuser/session/{session_id}/messages",
        params={"limit": limit},
        timeout=30.0,
    )

    if response.status_code == 200:
        return response.json().get("messages", [])
    return []
```

### Deliverables
- [ ] `fetch_session_messages()` function
- [ ] History displayed on join
- [ ] Truncation for long messages

---

## Phase 5: UX Polish

**Goal**: Improve the multiuser experience with status indicators and better feedback.

### Changes

#### 5.1 Prompt indicator for shared mode

```python
# In get_prompt() function, add shared session indicator

def get_prompt():
    mode_str = "plan" if current_mode == AgentMode.PLAN else "code"

    if is_shared_session:
        # Show shared indicator with participant count
        participant_count = len(get_participants())  # Cache this
        shared_str = f" [shared:{participant_count}]"
    else:
        shared_str = ""

    return f"[{mode_str}]{shared_str} > "
```

#### 5.2 Status bar with queue info

```python
# Bottom toolbar showing shared session status

def get_bottom_toolbar():
    if is_shared_session:
        return f" Session: {shared_invite_code} | Participants: {participant_count} | Queue: {queue_length}"
    return ""
```

#### 5.3 `/status` command enhancement

```python
elif command == "/status":
    # ... existing status ...

    if is_shared_session:
        console.print()
        console.print(Panel(
            f"[bold]Shared Session[/bold]\n"
            f"Invite: [cyan]{shared_invite_code}[/cyan]\n"
            f"Participants: {participant_count}\n"
            f"Queue: {queue_length} messages",
            title="Multiuser Status",
            border_style="green",
        ))
```

#### 5.4 Typing indicators (stretch goal)

When a user starts typing, broadcast a "typing" event so others see "[User is typing...]"

### Deliverables
- [ ] Prompt shows shared mode indicator
- [ ] Bottom toolbar shows session info
- [ ] `/status` includes multiuser info
- [ ] (Optional) Typing indicators

---

## Testing Plan

### Manual Testing Scenarios

1. **Basic Flow**
   - User A: `/share` → get invite code
   - User B: `/join <code>` → see history (if any)
   - User A: Send message → both see response
   - User B: Send message → both see response
   - User B: `/leave` → User A sees notification

2. **Queue Testing**
   - User A sends long-running message
   - User B sends message while A's is processing
   - Verify B's message is queued
   - Verify B sees queue position
   - Verify B's message processed after A's completes

3. **Reconnection**
   - User B's network drops
   - SSE stream disconnects
   - Verify automatic reconnection
   - Verify no duplicate messages

4. **Edge Cases**
   - Join with invalid code
   - Leave while message is processing
   - Multiple rapid messages
   - Very long messages

### Automated Tests

```python
# tests/test_multiuser_sync.py

async def test_message_sync():
    """Test that messages sync between participants."""
    # Create session as User A
    # Join as User B
    # User A sends message
    # Assert User B receives via SSE
    # Assert message appears in session history

async def test_queue_ordering():
    """Test message queue processes in order."""
    # Send message A
    # Send message B while A processing
    # Assert B queued
    # Assert A completes first
    # Assert B processes second

async def test_sse_reconnection():
    """Test SSE listener reconnects on disconnect."""
    # Start listener
    # Simulate disconnect
    # Assert reconnection
    # Assert no message loss
```

---

## File Summary

| File | Changes |
|------|---------|
| `interactive.py` | Add shared state, modify chat dispatch, integrate SSE listener |
| `handlers/multiuser.py` | Add `send_shared_message()`, update `handle_join()` for history |
| `sse_listener.py` (NEW) | SSE event listener class |
| `constants.py` | Already updated with slash commands |
| `profiles.py` | Already updated with slash commands |

---

## Timeline Estimate

| Phase | Description | Complexity |
|-------|-------------|------------|
| Phase 1 | State tracking | Low |
| Phase 2 | Message routing | Medium |
| Phase 3 | SSE listener | Medium-High |
| Phase 4 | History sync | Low |
| Phase 5 | UX polish | Low |

---

## Open Questions

1. **Message persistence**: Should CLI maintain local copy of messages for offline viewing?
2. **Conflict resolution**: What if two users send messages at exact same time?
3. **Permissions**: Should viewers be able to send messages or just observe?
4. **Session timeout**: Auto-close session after inactivity?
5. **Max participants**: Limit on concurrent participants?

---

## References

- `packages/core/emdash_core/api/multiuser.py` - API endpoints
- `packages/core/emdash_core/multiuser/manager.py` - Session manager
- `packages/core/emdash_core/multiuser/broadcaster.py` - Event broadcasting
- `packages/core/emdash_core/sse/stream.py` - SSE handler
