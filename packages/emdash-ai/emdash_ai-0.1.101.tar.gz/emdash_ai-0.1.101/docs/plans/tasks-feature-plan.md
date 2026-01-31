# Tasks Feature Implementation Plan for emdash

## Executive Summary

This document outlines a strategy for upgrading emdash's existing Todo system to a more sophisticated **Tasks** system, inspired by Claude Code's recent Tasks feature announcement. The new system will support:

- **Task Dependencies** - Tasks can depend on other tasks
- **File System Persistence** - Tasks stored in `.emdash/tasks/` for cross-session collaboration
- **Multi-Session/Agent Collaboration** - Multiple subagents or sessions can work on the same task list
- **Real-Time Broadcasting** - Task updates are broadcast to all sessions working on the same Task List
- **Environment Variable Configuration** - Task lists can be set via environment variable

### Current vs. New System Comparison

| Feature | Current Todo System | New Tasks System |
|---------|---------------------|------------------|
| **Storage** | In-memory (`TaskState` singleton) | File system (`.emdash/tasks/`) |
| **Scope** | Single session only | Cross-session, cross-agent |
| **Dependencies** | None | Task-to-task dependencies |
| **Collaboration** | Not supported | Multiple sessions can share a task list |
| **Persistence** | Lost on session end | Persists across sessions |
| **Broadcasting** | None | Real-time updates to all sessions |
| **Configuration** | None | Environment variable support |

---

## 1. Current Architecture Analysis

### Existing Todo Components

```
┌─────────────────────────────────────────────────────────────┐
│                     CLI Layer                                │
│  /todos, /todo-add commands                                  │
│  packages/cli/emdash_cli/commands/agent/handlers/todos.py   │
├─────────────────────────────────────────────────────────────┤
│                     API Layer                                │
│  GET/POST /api/agent/chat/{session_id}/todos                │
│  packages/core/emdash_core/api/agent.py                     │
├─────────────────────────────────────────────────────────────┤
│                     Tools Layer                              │
│  WriteTodoTool, UpdateTodoListTool                          │
│  packages/core/emdash_core/agent/tools/tasks.py             │
├─────────────────────────────────────────────────────────────┤
│                     State Layer                              │
│  TaskState singleton (in-memory)                            │
│  packages/core/emdash_core/agent/tools/tasks.py             │
└─────────────────────────────────────────────────────────────┘
```

### Key Files to Modify

| File | Purpose | Changes Needed |
|------|---------|----------------|
| `packages/core/emdash_core/agent/tools/tasks.py` | Tool definitions & state | Add persistence, dependencies, file watchers |
| `packages/cli/emdash_cli/commands/agent/handlers/todos.py` | CLI handlers | Update for new task features |
| `packages/core/emdash_core/api/agent.py` | API endpoints | Add task list endpoints, SSE updates |
| `packages/cli/emdash_cli/commands/agent/interactive.py` | REPL mode | Integrate task list selection |

### Data Models (Current)

```python
# Current Task model
@dataclass
class Task:
    id: str
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
```

---

## 2. New Tasks Architecture

### Enhanced Data Models

```python
# New Task model with dependencies and labels
@dataclass
class Task:
    id: str
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING

    # Dependencies
    depends_on: list[str] = field(default_factory=list)  # Task IDs that must complete first

    # Labels for clustering/filtering (NOT assignment)
    labels: list[str] = field(default_factory=list)  # ["backend", "api", "auth"]

    # Claiming (who IS working on it - assigned at runtime)
    claimed_by: str | None = None
    claimed_at: str | None = None

    # Metadata
    created_at: str = ""
    updated_at: str = ""
    created_by: str = ""      # Session ID that created

    # Ordering
    priority: int = 0         # Higher = more important
    order: int = 0            # Display order

    # Conflict detection
    version: int = 1          # Increments on each update

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"       # Computed: has incomplete dependencies


@dataclass
class TaskList:
    """A named collection of tasks that can be shared across sessions."""
    id: str                          # Unique identifier
    name: str                        # Human-readable name
    description: str = ""
    tasks: list[Task] = field(default_factory=list)

    # Metadata
    created_at: str = ""
    updated_at: str = ""

    # Collaboration
    active_sessions: list[dict] = field(default_factory=list)  # [{id, joined_at, last_heartbeat}]

    def to_dict(self) -> dict: ...

    @classmethod
    def from_dict(cls, data: dict) -> "TaskList": ...
```

### Labels System

Labels are the key to task clustering. They allow:
- **Categorization**: Group tasks by type (backend, frontend, testing)
- **Filtering**: Agents filter to only see relevant tasks
- **Runtime assignment**: User tells agent "work on backend tasks" when starting

```python
# Common label patterns
LABEL_PATTERNS = {
    # By layer
    "backend": ["api", "database", "server", "auth"],
    "frontend": ["ui", "react", "css", "components"],
    "infra": ["deploy", "ci", "docker", "kubernetes"],

    # By type
    "feature": ["new", "enhancement"],
    "bugfix": ["fix", "patch", "hotfix"],
    "refactor": ["cleanup", "optimization"],
    "testing": ["test", "e2e", "unit", "integration"],
    "docs": ["documentation", "readme", "comments"],
}
```

### File System Structure

```
.emdash/
└── tasks/
    ├── index.json              # List of all task lists
    ├── {task-list-id}.json     # Individual task list data
    └── .lock                   # File locking for concurrent access
```

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     CLI Layer                                │
│  /tasks, /task-add, /task-list commands                     │
│  packages/cli/emdash_cli/commands/agent/handlers/tasks.py   │
├─────────────────────────────────────────────────────────────┤
│                     API Layer                                │
│  TaskList CRUD endpoints                                     │
│  Task updates with SSE broadcasting                          │
│  packages/core/emdash_core/api/tasks.py (new)               │
├─────────────────────────────────────────────────────────────┤
│                     Tools Layer                              │
│  WriteTaskTool, UpdateTaskTool, SetDependencyTool           │
│  packages/core/emdash_core/agent/tools/tasks.py             │
├─────────────────────────────────────────────────────────────┤
│                     Task Store Layer                         │
│  TaskStore (file-based, with file watchers)                 │
│  packages/core/emdash_core/tasks/store.py (new)             │
├─────────────────────────────────────────────────────────────┤
│                     Broadcasting Layer                       │
│  File watchers + SSE notifications                          │
│  packages/core/emdash_core/tasks/broadcaster.py (new)       │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Implementation Phases

### Phase 1: Core Task Store (Foundation)

**Goal:** Create the file-based task storage system.

**New Files:**
- `packages/core/emdash_core/tasks/__init__.py`
- `packages/core/emdash_core/tasks/store.py`
- `packages/core/emdash_core/tasks/models.py`

**Key Components:**

```python
# packages/core/emdash_core/tasks/store.py

from pathlib import Path
from filelock import FileLock
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import json
import uuid


class TaskStore:
    """File-based task storage with labels and cross-session support."""

    def __init__(self, repo_root: Path | None = None):
        self.repo_root = repo_root or Path.cwd()
        self.tasks_dir = self.repo_root / ".emdash" / "tasks"

    def _ensure_dir(self) -> None:
        self.tasks_dir.mkdir(parents=True, exist_ok=True)

    def _get_lock(self, task_list_id: str) -> FileLock:
        return FileLock(self.tasks_dir / f"{task_list_id}.lock", timeout=5)

    def _task_list_path(self, task_list_id: str) -> Path:
        return self.tasks_dir / f"{task_list_id}.json"

    # ─────────────────────────────────────────────────────────────
    # Task List CRUD
    # ─────────────────────────────────────────────────────────────

    def create_task_list(self, name: str, description: str = "") -> TaskList:
        self._ensure_dir()
        task_list = TaskList(
            id=name,  # Use name as ID for simplicity
            name=name,
            description=description,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
        )
        self._save_task_list(task_list)
        return task_list

    def get_task_list(self, task_list_id: str) -> TaskList | None:
        path = self._task_list_path(task_list_id)
        if not path.exists():
            return None
        data = json.loads(path.read_text())
        return TaskList.from_dict(data)

    def get_or_create_task_list(self, task_list_id: str) -> TaskList:
        task_list = self.get_task_list(task_list_id)
        if not task_list:
            task_list = self.create_task_list(task_list_id)
        return task_list

    def _save_task_list(self, task_list: TaskList) -> None:
        self._ensure_dir()
        task_list.updated_at = datetime.utcnow().isoformat()
        path = self._task_list_path(task_list.id)
        path.write_text(json.dumps(task_list.to_dict(), indent=2))

    # ─────────────────────────────────────────────────────────────
    # Task CRUD with Labels
    # ─────────────────────────────────────────────────────────────

    def add_task(
        self,
        task_list_id: str,
        title: str,
        description: str = "",
        labels: list[str] | None = None,
        depends_on: list[str] | None = None,
        priority: int = 0,
    ) -> Task:
        """Add a task with labels."""
        with self._get_lock(task_list_id):
            task_list = self.get_or_create_task_list(task_list_id)

            task = Task(
                id=f"task-{uuid.uuid4().hex[:8]}",
                title=title,
                description=description,
                labels=labels or [],
                depends_on=depends_on or [],
                priority=priority,
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat(),
                order=len(task_list.tasks),
            )

            # Validate dependencies exist
            existing_ids = {t.id for t in task_list.tasks}
            for dep_id in task.depends_on:
                if dep_id not in existing_ids:
                    raise ValueError(f"Dependency {dep_id} does not exist")

            task_list.tasks.append(task)
            self._save_task_list(task_list)
            return task

    def get_task(self, task_list_id: str, task_id: str) -> Task | None:
        task_list = self.get_task_list(task_list_id)
        if not task_list:
            return None
        for task in task_list.tasks:
            if task.id == task_id:
                return task
        return None

    def update_task(
        self,
        task_list_id: str,
        task_id: str,
        updates: dict,
        expected_version: int | None = None,
    ) -> Task:
        """Update task with optional optimistic locking."""
        with self._get_lock(task_list_id):
            task_list = self.get_task_list(task_list_id)
            if not task_list:
                raise ValueError(f"Task list {task_list_id} not found")

            for task in task_list.tasks:
                if task.id == task_id:
                    # Optimistic locking check
                    if expected_version and task.version != expected_version:
                        raise ConflictError(
                            f"Task modified (v{task.version} != expected v{expected_version})"
                        )

                    # Apply updates
                    for key, value in updates.items():
                        if hasattr(task, key):
                            setattr(task, key, value)

                    task.version += 1
                    task.updated_at = datetime.utcnow().isoformat()
                    self._save_task_list(task_list)
                    return task

            raise ValueError(f"Task {task_id} not found")

    # ─────────────────────────────────────────────────────────────
    # Labels-Based Filtering (Core Logic)
    # ─────────────────────────────────────────────────────────────

    def get_tasks_by_labels(
        self,
        task_list_id: str,
        labels: list[str],
        match_all: bool = False,
    ) -> list[Task]:
        """
        Get tasks matching the given labels.

        Args:
            labels: Labels to filter by
            match_all: If True, task must have ALL labels. If False, ANY label matches.
        """
        task_list = self.get_task_list(task_list_id)
        if not task_list:
            return []

        matching = []
        for task in task_list.tasks:
            task_labels = set(task.labels)
            filter_labels = set(labels)

            if match_all:
                # Task must have ALL requested labels
                if filter_labels.issubset(task_labels):
                    matching.append(task)
            else:
                # Task must have ANY requested label
                if task_labels & filter_labels:
                    matching.append(task)

        return matching

    def get_claimable_tasks(
        self,
        task_list_id: str,
        labels: list[str] | None = None,
    ) -> list[Task]:
        """
        Get tasks that can be claimed (not claimed, dependencies met).
        Optionally filter by labels.
        """
        task_list = self.get_task_list(task_list_id)
        if not task_list:
            return []

        claimable = []
        for task in task_list.tasks:
            # Skip if already claimed or completed
            if task.claimed_by or task.status == TaskStatus.COMPLETED:
                continue

            # Check dependencies are all completed
            if not self._are_dependencies_met(task, task_list):
                continue

            # Filter by labels if specified
            if labels:
                if not (set(labels) & set(task.labels)):
                    continue

            claimable.append(task)

        return claimable

    def _are_dependencies_met(self, task: Task, task_list: TaskList) -> bool:
        """Check if all dependencies are completed."""
        for dep_id in task.depends_on:
            dep_task = next((t for t in task_list.tasks if t.id == dep_id), None)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        return True

    def get_blocking_tasks(self, task_list_id: str, task_id: str) -> list[Task]:
        """Get tasks that are blocking a given task."""
        task_list = self.get_task_list(task_list_id)
        if not task_list:
            return []

        task = next((t for t in task_list.tasks if t.id == task_id), None)
        if not task:
            return []

        blocking = []
        for dep_id in task.depends_on:
            dep_task = next((t for t in task_list.tasks if t.id == dep_id), None)
            if dep_task and dep_task.status != TaskStatus.COMPLETED:
                blocking.append(dep_task)

        return blocking

    # ─────────────────────────────────────────────────────────────
    # Claiming Logic
    # ─────────────────────────────────────────────────────────────

    def claim_task(
        self,
        task_list_id: str,
        task_id: str,
        session_id: str,
    ) -> tuple[bool, str]:
        """
        Attempt to claim a task.
        Returns (success, message).
        """
        with self._get_lock(task_list_id):
            task_list = self.get_task_list(task_list_id)
            if not task_list:
                return False, f"Task list {task_list_id} not found"

            task = next((t for t in task_list.tasks if t.id == task_id), None)
            if not task:
                return False, f"Task {task_id} not found"

            # Check if already claimed
            if task.claimed_by:
                if task.claimed_by == session_id:
                    return True, "Already claimed by you"
                return False, f"Already claimed by {task.claimed_by}"

            # Check if already completed
            if task.status == TaskStatus.COMPLETED:
                return False, "Task already completed"

            # Check dependencies
            if not self._are_dependencies_met(task, task_list):
                blocking = self.get_blocking_tasks(task_list_id, task_id)
                blocking_names = [f"'{t.title}'" for t in blocking]
                return False, f"Blocked by: {', '.join(blocking_names)}"

            # Claim it!
            task.claimed_by = session_id
            task.claimed_at = datetime.utcnow().isoformat()
            task.status = TaskStatus.IN_PROGRESS
            task.version += 1
            self._save_task_list(task_list)

            return True, "Claimed successfully"

    def complete_task(
        self,
        task_list_id: str,
        task_id: str,
        session_id: str,
    ) -> tuple[bool, str]:
        """Mark a task as completed. Must be claimed by this session."""
        with self._get_lock(task_list_id):
            task_list = self.get_task_list(task_list_id)
            if not task_list:
                return False, f"Task list {task_list_id} not found"

            task = next((t for t in task_list.tasks if t.id == task_id), None)
            if not task:
                return False, f"Task {task_id} not found"

            # Verify ownership
            if task.claimed_by != session_id:
                return False, f"Task claimed by {task.claimed_by}, not you"

            # Complete it
            task.status = TaskStatus.COMPLETED
            task.version += 1
            task.updated_at = datetime.utcnow().isoformat()
            self._save_task_list(task_list)

            return True, "Completed successfully"

    def release_task(
        self,
        task_list_id: str,
        task_id: str,
        session_id: str,
    ) -> tuple[bool, str]:
        """Release a claimed task back to pending."""
        with self._get_lock(task_list_id):
            task_list = self.get_task_list(task_list_id)
            if not task_list:
                return False, f"Task list {task_list_id} not found"

            task = next((t for t in task_list.tasks if t.id == task_id), None)
            if not task:
                return False, f"Task {task_id} not found"

            if task.claimed_by != session_id:
                return False, f"Task claimed by {task.claimed_by}, not you"

            task.claimed_by = None
            task.claimed_at = None
            task.status = TaskStatus.PENDING
            task.version += 1
            self._save_task_list(task_list)

            return True, "Released"


class ConflictError(Exception):
    """Raised when optimistic locking detects a conflict."""
    pass
```

**Tasks:**
- [ ] Create `Task` and `TaskList` models with labels support
- [ ] Implement `TaskStore` class with file persistence
- [ ] Implement labels-based filtering (`get_tasks_by_labels`, `get_claimable_tasks`)
- [ ] Implement claiming logic with dependency checks
- [ ] Add file locking for concurrent access (using `filelock`)
- [ ] Add dependency cycle detection
- [ ] Write unit tests for store operations

---

### Phase 2: Broadcasting System

**Goal:** Enable real-time updates across sessions.

**New Files:**
- `packages/core/emdash_core/tasks/broadcaster.py`
- `packages/core/emdash_core/tasks/watcher.py`

**Key Components:**

```python
# packages/core/emdash_core/tasks/broadcaster.py

class TaskBroadcaster:
    """Broadcasts task updates to all connected sessions.

    Uses file system watching to detect changes made by other sessions
    and SSE to push updates to connected clients.
    """

    _instances: dict[str, "TaskBroadcaster"] = {}

    def __init__(self, task_list_id: str, store: TaskStore):
        self.task_list_id = task_list_id
        self.store = store
        self.subscribers: dict[str, asyncio.Queue] = {}
        self._watcher: FileWatcher | None = None

    @classmethod
    def get_broadcaster(cls, task_list_id: str, store: TaskStore) -> "TaskBroadcaster":
        """Get or create broadcaster for a task list."""
        if task_list_id not in cls._instances:
            cls._instances[task_list_id] = cls(task_list_id, store)
        return cls._instances[task_list_id]

    async def subscribe(self, session_id: str) -> AsyncGenerator[TaskEvent, None]:
        """Subscribe to task updates for this list."""
        queue = asyncio.Queue()
        self.subscribers[session_id] = queue
        try:
            while True:
                event = await queue.get()
                yield event
        finally:
            del self.subscribers[session_id]

    async def broadcast(self, event: TaskEvent) -> None:
        """Send event to all subscribers."""
        for queue in self.subscribers.values():
            await queue.put(event)

    def start_watching(self) -> None:
        """Start watching file for external changes."""
        self._watcher = FileWatcher(
            self.store.task_list_path(self.task_list_id),
            on_change=self._on_file_change
        )
        self._watcher.start()

    async def _on_file_change(self) -> None:
        """Called when task list file is modified externally."""
        task_list = self.store.get_task_list(self.task_list_id)
        await self.broadcast(TaskEvent(
            type="task_list_updated",
            task_list_id=self.task_list_id,
            data=task_list.to_dict()
        ))


@dataclass
class TaskEvent:
    """Event for task updates."""
    type: str  # task_added, task_updated, task_deleted, task_list_updated
    task_list_id: str
    task_id: str | None = None
    data: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
```

**Tasks:**
- [ ] Implement `FileWatcher` using `watchdog` library
- [ ] Create `TaskBroadcaster` with subscription system
- [ ] Add `TaskEvent` model for typed events
- [ ] Integrate with SSE endpoints
- [ ] Handle file watcher cleanup on session end

---

### Phase 2b: Async Task Waiter

**Goal:** Allow agents to physically wait for blocked tasks.

**New Files:**
- `packages/core/emdash_core/tasks/waiter.py`

**Key Components:**

```python
# packages/core/emdash_core/tasks/waiter.py

import asyncio
from typing import Optional

class TaskWaiter:
    """
    Allows agents to physically block until a task completes.
    Uses asyncio Futures to suspend execution without CPU usage.
    """

    # Shared completion futures: task_id -> Future
    _completion_futures: dict[str, asyncio.Future] = {}
    _lock = asyncio.Lock()

    @classmethod
    async def wait_for_task(
        cls,
        task_id: str,
        timeout: Optional[float] = None,
    ) -> bool:
        """
        Block until task completes.

        Args:
            task_id: Task to wait for
            timeout: Max seconds to wait (None = forever)

        Returns:
            True if task completed, False if timeout
        """
        async with cls._lock:
            if task_id not in cls._completion_futures:
                cls._completion_futures[task_id] = asyncio.Future()

        future = cls._completion_futures[task_id]

        try:
            if timeout:
                await asyncio.wait_for(future, timeout=timeout)
            else:
                await future
            return True
        except asyncio.TimeoutError:
            return False

    @classmethod
    async def notify_completion(cls, task_id: str):
        """
        Called when a task completes - wakes up all waiting agents.
        """
        async with cls._lock:
            if task_id in cls._completion_futures:
                future = cls._completion_futures[task_id]
                if not future.done():
                    future.set_result(True)
                # Create new future for any future waiters
                cls._completion_futures[task_id] = asyncio.Future()

    @classmethod
    async def wait_for_any(
        cls,
        task_ids: list[str],
        timeout: Optional[float] = None,
    ) -> str | None:
        """
        Wait for ANY of the given tasks to complete.
        Returns the task_id that completed, or None if timeout.
        """
        async with cls._lock:
            for task_id in task_ids:
                if task_id not in cls._completion_futures:
                    cls._completion_futures[task_id] = asyncio.Future()

        futures = [cls._completion_futures[tid] for tid in task_ids]

        try:
            done, pending = await asyncio.wait(
                futures,
                timeout=timeout,
                return_when=asyncio.FIRST_COMPLETED
            )

            if done:
                # Find which task completed
                for task_id in task_ids:
                    if cls._completion_futures[task_id] in done:
                        return task_id
            return None
        except asyncio.TimeoutError:
            return None
```

**Integration with Broadcaster:**

```python
# packages/core/emdash_core/tasks/broadcaster.py

class TaskBroadcaster:
    async def _on_file_change(self, events: list[TaskEvent]):
        for event in events:
            await self._broadcast(event)

            # Wake up waiters on completion
            if event.type == "task_completed":
                await TaskWaiter.notify_completion(event.task_id)
```

**Agent Tool for Waiting:**

```python
# packages/core/emdash_core/agent/tools/tasks.py

class WaitForTaskTool(TaskManagementTool):
    """Physically wait for a task to complete."""

    name = "wait_for_task"
    description = """
    Wait for a blocking task to complete before continuing.
    This PAUSES your execution until the task is done.

    Use when you need to work on a task that's blocked by
    another task being worked on by a different session.

    Example:
        wait_for_task(task_id="task-abc123", timeout_seconds=300)
    """

    async def execute(
        self,
        task_id: str,
        timeout_seconds: float = 300,
        **kwargs
    ) -> ToolResult:
        store = TaskStore()
        task_list_id = get_current_task_list()

        # Check if already complete
        task = store.get_task(task_list_id, task_id)
        if not task:
            return ToolResult.error(f"Task {task_id} not found")

        if task.status == TaskStatus.COMPLETED:
            return ToolResult.success({
                "status": "already_completed",
                "task": {"id": task.id, "title": task.title}
            })

        if not task.claimed_by:
            return ToolResult.error({
                "status": "not_started",
                "message": f"Task '{task.title}' is not being worked on. "
                          "Claim it yourself or wait for another agent to start."
            })

        # Actually wait
        completed = await TaskWaiter.wait_for_task(
            task_id=task_id,
            timeout=timeout_seconds
        )

        if completed:
            task = store.get_task(task_list_id, task_id)
            return ToolResult.success({
                "status": "completed",
                "task": {"id": task.id, "title": task.title},
                "message": f"Task '{task.title}' is now complete!"
            })
        else:
            return ToolResult.error({
                "status": "timeout",
                "message": f"Timed out after {timeout_seconds}s waiting for '{task.title}'"
            })
```

**Tasks:**
- [ ] Implement `TaskWaiter` with asyncio Futures
- [ ] Add `wait_for_any` for multiple tasks
- [ ] Integrate with `TaskBroadcaster` to trigger notifications
- [ ] Implement `WaitForTaskTool` for agents
- [ ] Add timeout handling and cleanup

---

### Phase 3: Updated Agent Tools with Labels

**Goal:** Update agent tools to use new task system with labels support.

**Modified Files:**
- `packages/core/emdash_core/agent/tools/tasks.py`

**New Tools:**

```python
# packages/core/emdash_core/agent/tools/tasks.py

from emdash_core.tasks.store import TaskStore
from emdash_core.tasks.feature_flag import is_tasks_v2_enabled, get_current_task_list
from emdash_core.agent.session import get_session_id


class WriteTaskTool(TaskManagementTool):
    """Create a new task with labels and dependencies."""

    name = "write_task"
    description = """Create a new task in the current task list.

    Use labels to categorize tasks for filtering:
    - ["backend", "api"] - Backend API work
    - ["frontend", "react"] - Frontend UI work
    - ["testing"] - Test writing
    - ["docs"] - Documentation

    Examples:
        write_task(
            title="Build API endpoints",
            labels=["backend", "api", "auth"],
            description="Create REST endpoints for authentication"
        )

        write_task(
            title="Build login form",
            labels=["frontend", "react"],
            depends_on=["task-abc123"]  # Depends on API task
        )
    """

    def execute(
        self,
        title: str,
        labels: list[str] | None = None,
        description: str = "",
        depends_on: list[str] | None = None,
        priority: int = 0,
        **kwargs,
    ) -> ToolResult:
        if not is_tasks_v2_enabled():
            # Fall back to old system
            return self._execute_legacy(title, description)

        store = TaskStore()
        task_list_id = get_current_task_list()

        try:
            task = store.add_task(
                task_list_id=task_list_id,
                title=title,
                description=description,
                labels=labels or [],
                depends_on=depends_on or [],
                priority=priority,
            )
            return ToolResult.success({
                "task_id": task.id,
                "title": task.title,
                "labels": task.labels,
                "depends_on": task.depends_on,
                "message": f"Created task '{title}' with labels {labels or []}"
            })
        except ValueError as e:
            return ToolResult.error(str(e))


class ClaimTaskTool(TaskManagementTool):
    """Claim a task to work on it."""

    name = "claim_task"
    description = """Claim a task before starting work on it.

    A task can only be claimed if:
    - It's not already claimed by another session
    - All its dependencies are completed

    Examples:
        claim_task(task_id="task-abc123")
    """

    def execute(self, task_id: str, **kwargs) -> ToolResult:
        store = TaskStore()
        task_list_id = get_current_task_list()
        session_id = get_session_id()

        success, message = store.claim_task(task_list_id, task_id, session_id)

        if success:
            task = store.get_task(task_list_id, task_id)
            return ToolResult.success({
                "task_id": task_id,
                "title": task.title,
                "labels": task.labels,
                "status": "claimed",
                "message": message
            })
        else:
            # Include blocking info if blocked
            blocking = store.get_blocking_tasks(task_list_id, task_id)
            return ToolResult.error({
                "message": message,
                "blocking_tasks": [
                    {"id": t.id, "title": t.title, "status": t.status.value, "claimed_by": t.claimed_by}
                    for t in blocking
                ] if blocking else []
            })


class CompleteTaskTool(TaskManagementTool):
    """Mark a claimed task as completed."""

    name = "complete_task"
    description = """Mark a task as completed. You must have claimed it first."""

    def execute(self, task_id: str, **kwargs) -> ToolResult:
        store = TaskStore()
        task_list_id = get_current_task_list()
        session_id = get_session_id()

        success, message = store.complete_task(task_list_id, task_id, session_id)

        if success:
            return ToolResult.success({
                "task_id": task_id,
                "status": "completed",
                "message": message
            })
        else:
            return ToolResult.error(message)


class GetClaimableTasksTool(TaskManagementTool):
    """Get tasks that can be claimed, optionally filtered by labels."""

    name = "get_claimable_tasks"
    description = """Get tasks that are ready to be claimed.

    Optionally filter by labels to find relevant work:
        get_claimable_tasks(labels=["backend"])  # Only backend tasks
        get_claimable_tasks(labels=["frontend", "ui"])  # Frontend/UI tasks
        get_claimable_tasks()  # All available tasks
    """

    def execute(self, labels: list[str] | None = None, **kwargs) -> ToolResult:
        store = TaskStore()
        task_list_id = get_current_task_list()

        tasks = store.get_claimable_tasks(task_list_id, labels=labels)

        return ToolResult.success({
            "count": len(tasks),
            "filter_labels": labels,
            "tasks": [
                {
                    "id": t.id,
                    "title": t.title,
                    "labels": t.labels,
                    "depends_on": t.depends_on,
                    "priority": t.priority,
                }
                for t in tasks
            ]
        })


class GetTasksByLabelsTool(TaskManagementTool):
    """Get all tasks matching given labels."""

    name = "get_tasks_by_labels"
    description = """Get tasks matching specific labels.

    Examples:
        get_tasks_by_labels(labels=["backend"])  # Tasks with 'backend' label
        get_tasks_by_labels(labels=["api", "auth"], match_all=True)  # Must have BOTH labels
    """

    def execute(
        self,
        labels: list[str],
        match_all: bool = False,
        **kwargs
    ) -> ToolResult:
        store = TaskStore()
        task_list_id = get_current_task_list()

        tasks = store.get_tasks_by_labels(task_list_id, labels, match_all=match_all)

        # Group by status
        by_status = {"pending": [], "in_progress": [], "completed": [], "blocked": []}
        for t in tasks:
            status_key = t.status.value
            by_status.get(status_key, by_status["pending"]).append({
                "id": t.id,
                "title": t.title,
                "labels": t.labels,
                "claimed_by": t.claimed_by,
            })

        return ToolResult.success({
            "filter_labels": labels,
            "match_all": match_all,
            "total": len(tasks),
            "by_status": by_status,
        })


class DelegateTaskTool(TaskManagementTool):
    """Delegate a task to a subagent."""

    name = "delegate_task"
    description = """Spawn a subagent to work on a specific task.

    The subagent will:
    - Claim the task automatically
    - Work on it with full context
    - Notify when complete

    Example:
        delegate_task(
            task_id="task-abc123",
            instructions="Use FastAPI, follow patterns in src/api/"
        )
    """

    async def execute(
        self,
        task_id: str,
        instructions: str = "",
        **kwargs
    ) -> ToolResult:
        store = TaskStore()
        task_list_id = get_current_task_list()

        task = store.get_task(task_list_id, task_id)
        if not task:
            return ToolResult.error(f"Task {task_id} not found")

        if task.claimed_by:
            return ToolResult.error(f"Task already claimed by {task.claimed_by}")

        # Check dependencies
        blocking = store.get_blocking_tasks(task_list_id, task_id)
        if blocking:
            return ToolResult.error({
                "message": "Cannot delegate blocked task",
                "blocking": [{"id": t.id, "title": t.title} for t in blocking]
            })

        # Generate subagent session ID
        subagent_session_id = f"subagent-{uuid.uuid4().hex[:8]}"

        # Pre-claim for subagent
        store.claim_task(task_list_id, task_id, subagent_session_id)

        # Build prompt with context
        prompt = f"""
You are assigned to complete this task:

**Task:** {task.title}
**ID:** {task.id}
**Labels:** {', '.join(task.labels)}
**Description:** {task.description}

{instructions}

When done, call: complete_task("{task.id}")
"""

        # Spawn subagent
        result = await spawn_subagent(
            prompt=prompt,
            env={
                "EMDASH_TASKS_V2": "1",
                "EMDASH_TASK_LIST": task_list_id,
                "EMDASH_SESSION_ID": subagent_session_id,
                "EMDASH_WORK_ON": task_id,
            }
        )

        return ToolResult.success({
            "delegated": True,
            "task_id": task_id,
            "subagent_id": subagent_session_id,
            "message": f"Delegated '{task.title}' to subagent"
        })
```

**Tasks:**
- [ ] Implement `WriteTaskTool` with labels support
- [ ] Implement `ClaimTaskTool` with blocking info
- [ ] Implement `CompleteTaskTool` with ownership verification
- [ ] Implement `GetClaimableTasksTool` with label filtering
- [ ] Implement `GetTasksByLabelsTool` for discovery
- [ ] Implement `DelegateTaskTool` for subagent spawning
- [ ] Keep backwards compatibility with existing `write_todo` name

---

### Phase 4: API Endpoints

**Goal:** Create REST API endpoints for task management.

**New Files:**
- `packages/core/emdash_core/api/tasks_api.py`

**Endpoints:**

```python
# packages/core/emdash_core/api/tasks_api.py

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

# Task List endpoints
@router.get("/lists")
async def list_task_lists() -> list[TaskListMetadata]:
    """Get all task lists."""

@router.post("/lists")
async def create_task_list(name: str, description: str = "") -> TaskList:
    """Create a new task list."""

@router.get("/lists/{list_id}")
async def get_task_list(list_id: str) -> TaskList:
    """Get a specific task list with all tasks."""

@router.delete("/lists/{list_id}")
async def delete_task_list(list_id: str) -> dict:
    """Delete a task list."""

# Task endpoints
@router.post("/lists/{list_id}/tasks")
async def add_task(list_id: str, task: TaskCreate) -> Task:
    """Add a task to a list."""

@router.patch("/lists/{list_id}/tasks/{task_id}")
async def update_task(list_id: str, task_id: str, updates: TaskUpdate) -> Task:
    """Update a task."""

@router.delete("/lists/{list_id}/tasks/{task_id}")
async def delete_task(list_id: str, task_id: str) -> dict:
    """Delete a task."""

# Dependency endpoints
@router.post("/lists/{list_id}/tasks/{task_id}/dependencies")
async def add_dependency(list_id: str, task_id: str, depends_on: str) -> Task:
    """Add a dependency to a task."""

@router.delete("/lists/{list_id}/tasks/{task_id}/dependencies/{dep_id}")
async def remove_dependency(list_id: str, task_id: str, dep_id: str) -> Task:
    """Remove a dependency from a task."""

# Ready tasks
@router.get("/lists/{list_id}/ready")
async def get_ready_tasks(list_id: str) -> list[Task]:
    """Get tasks ready to be worked on."""

# SSE endpoint for real-time updates
@router.get("/lists/{list_id}/events")
async def task_events(list_id: str, session_id: str) -> EventSourceResponse:
    """Subscribe to real-time task updates."""
```

**Tasks:**
- [ ] Create API endpoints for task list CRUD
- [ ] Create API endpoints for task CRUD
- [ ] Create API endpoints for dependency management
- [ ] Create SSE endpoint for broadcasting
- [ ] Add authentication/authorization
- [ ] Add request validation with Pydantic models

---

### Phase 5: CLI Integration

**Goal:** Update CLI handlers for new task features.

**New Files:**
- `packages/cli/emdash_cli/commands/agent/handlers/tasks.py` (rename from todos.py)

**New Commands:**

```
/tasks                     - Show current task list with dependencies
/task-add <title>          - Add a task
/task-add <title> --after <id>  - Add task that depends on another
/task-done <id>            - Mark task as completed
/task-block <id> <dep_id>  - Add dependency
/task-unblock <id> <dep_id> - Remove dependency
/task-list                 - Show available task lists
/task-list switch <name>   - Switch to a task list
/task-list create <name>   - Create new task list
/task-ready                - Show tasks ready to work on
```

**Visual Display:**

```
┌─ Task List: feature-auth ─────────────────────────────────┐
│                                                           │
│  ● 1. Design API schema                   [completed]     │
│  ● 2. Create database models              [completed]     │
│  │                                                        │
│  ◐ 3. Implement auth endpoints            [in_progress]   │
│     └── depends on: 1, 2                                  │
│  │                                                        │
│  ○ 4. Write tests                         [pending]       │
│     └── depends on: 3                                     │
│  ○ 5. Add documentation                   [pending]       │
│     └── depends on: 3, 4                                  │
│                                                           │
├───────────────────────────────────────────────────────────┤
│  ○ 2  ◐ 1  ● 2  │  Ready: 0  │  Sessions: 2               │
└───────────────────────────────────────────────────────────┘
```

**Tasks:**
- [ ] Rename `todos.py` to `tasks.py`
- [ ] Update `/todos` → `/tasks` command
- [ ] Add dependency visualization in tree format
- [ ] Add `/task-list` commands for list management
- [ ] Add `/task-ready` command
- [ ] Show active sessions working on same list
- [ ] Add color-coding for dependency status

---

### Phase 6: Feature Flag & Environment Variables

**Goal:** Enable new Tasks system via environment variable.

**Usage:**

```bash
# Enable Tasks v2 system
export EMDASH_TASKS_V2=1

# Optionally specify task list (defaults to "default")
export EMDASH_TASK_LIST="feature-auth"

# Start emdash
em
```

**Implementation:**

```python
# packages/core/emdash_core/tasks/feature_flag.py

import os

def is_tasks_v2_enabled() -> bool:
    """Check if new Tasks system is enabled via env var."""
    return os.environ.get("EMDASH_TASKS_V2", "").lower() in ("1", "true", "yes")

def get_current_task_list() -> str:
    """Get task list name from env var, defaults to 'default'."""
    return os.environ.get("EMDASH_TASK_LIST", "default")
```

```python
# packages/cli/emdash_cli/commands/agent/interactive.py

from emdash_core.tasks.feature_flag import is_tasks_v2_enabled, get_current_task_list

def start_session():
    if is_tasks_v2_enabled():
        task_list_id = get_current_task_list()
        store = TaskStore()
        store.join_task_list(task_list_id, session_id)
        console.print(f"[dim]Using Tasks v2: {task_list_id}[/dim]")
```

**Tasks:**
- [ ] Create `feature_flag.py` module
- [ ] Read `EMDASH_TASKS_V2` environment variable
- [ ] Read `EMDASH_TASK_LIST` environment variable
- [ ] Auto-join task list on session start when enabled
- [ ] Auto-leave task list on session end
- [ ] Show indicator in CLI when Tasks v2 is active

---

### Phase 7: Sub-Agent Integration

**Goal:** Allow subagents to collaborate on the same task list.

**Key Feature:** When spawning a subagent, it inherits the parent's task list and can update tasks.

```python
# Subagent spawning with shared task list
class TaskTool(BaseTool):
    """Spawn a subagent that shares the same task list."""

    def execute(self, prompt: str, **kwargs) -> ToolResult:
        # Get parent's task list
        task_list_id = self.get_current_task_list_id()

        # Spawn subagent with same task list
        subagent = spawn_subagent(
            prompt=prompt,
            task_list_id=task_list_id,  # Share task list
            **kwargs
        )

        return subagent.run()
```

**Workflow Example:**

```
Main Session (working on feature-auth)
├── Creates tasks 1-5
├── Starts task 1
│
├── Spawns Explore subagent
│   ├── Joins feature-auth task list
│   ├── Picks up task 2 (marks as in_progress)
│   ├── Completes task 2
│   └── Notifies main session via broadcast
│
├── Receives notification: "Task 2 completed by explore-agent"
├── Continues with task 3
└── ...
```

**Tasks:**
- [ ] Pass task list ID to subagent spawn
- [ ] Auto-join task list in subagent
- [ ] Track which session owns each task
- [ ] Prevent duplicate work (task claiming)
- [ ] Notify parent when subtask completes

---

## 4. Feature Flag Strategy

### Environment Variable Toggle

The new Tasks system is enabled via environment variable - no backwards compatibility or migration needed.

```bash
# Old behavior (default) - in-memory TodoState
em

# New Tasks v2 system - file-based with dependencies
EMDASH_TASKS_V2=1 em

# With specific task list
EMDASH_TASKS_V2=1 EMDASH_TASK_LIST=feature-auth em
```

### Implementation

```python
# packages/core/emdash_core/tasks/feature_flag.py

import os

def is_tasks_v2_enabled() -> bool:
    """Check if new Tasks system is enabled."""
    return os.environ.get("EMDASH_TASKS_V2", "").lower() in ("1", "true", "yes")

def get_current_task_list() -> str | None:
    """Get task list from environment."""
    if not is_tasks_v2_enabled():
        return None
    return os.environ.get("EMDASH_TASK_LIST", "default")
```

```python
# packages/core/emdash_core/agent/tools/tasks.py

from emdash_core.tasks.feature_flag import is_tasks_v2_enabled

class WriteTodoTool(TaskManagementTool):
    def execute(self, title: str, **kwargs) -> ToolResult:
        if is_tasks_v2_enabled():
            # New system - file persistence, dependencies
            from emdash_core.tasks.store import TaskStore
            store = TaskStore()
            task = store.add_task(
                task_list_id=get_current_task_list(),
                task=Task(
                    title=title,
                    depends_on=kwargs.get("depends_on", [])
                )
            )
        else:
            # Old system - in-memory singleton
            task = self.state.add_task(title=title)

        return ToolResult.success_result({"task": task.to_dict()})
```

### CLI Handler Switching

```python
# packages/cli/emdash_cli/commands/agent/handlers/todos.py

from emdash_core.tasks.feature_flag import is_tasks_v2_enabled

def handle_todos(args: str, client, session_id: str | None, pending_todos: list[str]) -> None:
    if is_tasks_v2_enabled():
        # Use new Tasks v2 handler with dependency tree
        handle_tasks_v2(args, client, session_id)
    else:
        # Existing todo handler
        handle_todos_v1(args, client, session_id, pending_todos)
```

### Behavior Summary

| Feature | `EMDASH_TASKS_V2` not set | `EMDASH_TASKS_V2=1` |
|---------|---------------------------|---------------------|
| Storage | In-memory (`TaskState`) | File (`.emdash/tasks/`) |
| Persistence | Lost on session end | Persists forever |
| Dependencies | Not supported | Full support |
| Cross-session | Not supported | Supported |
| Broadcasting | Not supported | SSE + file watchers |
| Commands | `/todos`, `/todo-add` | `/tasks`, `/task-add` |
```

---

## 5. Dependencies

### New Python Dependencies

```toml
# pyproject.toml additions

[project.dependencies]
watchdog = ">=3.0.0"    # File system watching
filelock = ">=3.0.0"    # Cross-process file locking
```

### Internal Dependencies

```
TaskStore
   └── FileWatcher (watchdog)
   └── FileLock (filelock)

TaskBroadcaster
   └── TaskStore
   └── SSE (already in project)

TaskTools
   └── TaskStore
   └── TaskBroadcaster
```

---

## 6. Testing Strategy

### Unit Tests

```python
# tests/tasks/test_store.py

def test_create_task_list():
    store = TaskStore(repo_root=tmp_path)
    task_list = store.create_task_list("test", "Test list")
    assert task_list.name == "test"
    assert (tmp_path / ".emdash" / "tasks" / f"{task_list.id}.json").exists()

def test_add_dependency():
    store = TaskStore(repo_root=tmp_path)
    task_list = store.create_task_list("test")
    task1 = store.add_task(task_list.id, Task(title="Task 1"))
    task2 = store.add_task(task_list.id, Task(title="Task 2"))

    store.add_dependency(task_list.id, task2.id, task1.id)

    updated = store.get_task(task_list.id, task2.id)
    assert task1.id in updated.depends_on

def test_detect_cycle():
    """Should prevent circular dependencies."""
    store = TaskStore(repo_root=tmp_path)
    # ... create cycle ...
    with pytest.raises(CyclicDependencyError):
        store.add_dependency(task_list.id, task1.id, task3.id)

def test_get_ready_tasks():
    """Only return tasks with completed dependencies."""
    store = TaskStore(repo_root=tmp_path)
    # ... setup tasks with deps ...
    ready = store.get_ready_tasks(task_list.id)
    assert len(ready) == 1
    assert ready[0].id == task1.id  # No deps
```

### Integration Tests

```python
# tests/tasks/test_broadcasting.py

async def test_broadcast_on_update():
    """Updates should be broadcast to all subscribers."""
    store = TaskStore()
    broadcaster = TaskBroadcaster.get_broadcaster("list-1", store)

    events = []
    async def collect_events():
        async for event in broadcaster.subscribe("session-1"):
            events.append(event)
            if len(events) >= 1:
                break

    # Subscribe in background
    task = asyncio.create_task(collect_events())

    # Update from another "session"
    await broadcaster.broadcast(TaskEvent(
        type="task_updated",
        task_list_id="list-1",
        task_id="task-1",
        data={"status": "completed"}
    ))

    await task
    assert len(events) == 1
    assert events[0].type == "task_updated"
```

### CLI Tests

```python
# tests/cli/test_task_commands.py

def test_task_add_with_dependency(cli_runner):
    result = cli_runner.invoke(["task-add", "New task", "--after", "1"])
    assert result.exit_code == 0
    assert "depends on: 1" in result.output
```

---

## 7. Implementation Roadmap

### Phase 1: Core Task Store (Week 1)
- [ ] Create `packages/core/emdash_core/tasks/` module
- [ ] Implement `Task` and `TaskList` models
- [ ] Implement `TaskStore` with file persistence
- [ ] Add dependency graph validation
- [ ] Write comprehensive unit tests

### Phase 2: Broadcasting System (Week 1-2)
- [ ] Implement `FileWatcher` using watchdog
- [ ] Create `TaskBroadcaster` class
- [ ] Add subscription/unsubscription logic
- [ ] Integrate with existing SSE system
- [ ] Test cross-session updates

### Phase 3: Updated Agent Tools (Week 2)
- [ ] Update `WriteTaskTool` with dependencies
- [ ] Add new task management tools
- [ ] Maintain backwards compatibility aliases
- [ ] Update agent prompts to use new tools
- [ ] Test tool execution

### Phase 4: API Endpoints (Week 2-3)
- [ ] Create `tasks_api.py` router
- [ ] Implement CRUD endpoints
- [ ] Add SSE endpoint for events
- [ ] Add Pydantic request/response models
- [ ] API documentation

### Phase 5: CLI Integration (Week 3)
- [ ] Update CLI handlers
- [ ] Add dependency visualization
- [ ] Add task list management commands
- [ ] Show active sessions indicator
- [ ] User experience polish

### Phase 6: Environment Variable Support (Week 3)
- [ ] Add CLI `--task-list` option
- [ ] Read environment variable
- [ ] Auto-join/leave on session lifecycle
- [ ] Update documentation

### Phase 7: Sub-Agent Integration (Week 4)
- [ ] Pass task list to subagent spawn
- [ ] Task claiming mechanism
- [ ] Parent notification on completion
- [ ] End-to-end testing with subagents

### Phase 8: Polish & Documentation (Week 4)
- [ ] Update README with new features
- [ ] Document `EMDASH_TASKS_V2` environment variable
- [ ] Add examples and tutorials
- [ ] Performance optimization
- [ ] Release v0.2.0

---

## 8. Key Considerations

### Concurrency & Locking

- Use `filelock` for exclusive file access during writes
- Read operations don't require locks (JSON atomic reads)
- Consider optimistic locking with version numbers for frequent updates

### Performance

- Cache task lists in memory after first load
- Debounce file watcher events (multiple rapid changes → single reload)
- Limit SSE connections per task list

### Error Handling

- Graceful handling of corrupted task files
- Auto-repair or notify user
- Backup before destructive operations

### Security

- Validate task list names (no path traversal)
- Sanitize task content
- Consider task list access controls in future

---

## 9. Future Enhancements

### Potential V2 Features

1. **Task Templates** - Reusable task patterns
2. **Task Estimates** - Time/complexity estimates
3. **Task History** - Audit log of all changes
4. **Task Comments** - Discussion threads on tasks
5. **Task Labels/Tags** - Categorization
6. **GitHub Integration** - Sync with GitHub Issues
7. **Metrics Dashboard** - Velocity, burn-down charts
8. **Task Search** - Full-text search across task lists

---

## 10. References

### Inspiration
- [Claude Code Tasks Announcement](https://x.com/trq212/status/1881408016968863820) - Original feature announcement
- [Beads by Steve Yegge](https://github.com/steveyegge/beads) - Community project inspiration

### Related emdash Features
- Session Store - `packages/cli/emdash_cli/session_store.py` (similar pattern)
- Skills System - `packages/core/emdash_core/agent/skills.py`
- MCP Manager - `packages/core/emdash_core/agent/mcp/manager.py`

### Libraries
- [watchdog](https://pypi.org/project/watchdog/) - File system watching
- [filelock](https://pypi.org/project/filelock/) - Cross-platform file locking
