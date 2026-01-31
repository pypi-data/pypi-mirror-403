# Tasks v2: Cross-Session Task Management with Labels and Dependencies

## Overview

Tasks v2 is a comprehensive task management system designed for multi-agent collaboration. It enables agents to work together on complex projects by providing:

- **Labels-based clustering** - Filter and assign tasks by category (e.g., `backend`, `frontend`, `api`)
- **Task dependencies** - Define which tasks must complete before others can start
- **Cross-session collaboration** - Multiple agents can work on the same task list simultaneously
- **Async waiting** - Agents can physically wait for blocked tasks to complete
- **File-based persistence** - Tasks survive across sessions

## Enabling Tasks v2

Set the environment variable:

```bash
export EMDASH_TASKS_V2=1
```

## Core Concepts

### Task

A task represents a unit of work with the following properties:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique identifier (auto-generated) |
| `title` | string | Short description of the task |
| `description` | string | Detailed description |
| `status` | enum | `pending`, `in_progress`, `completed`, `blocked` |
| `labels` | list[str] | Categories for filtering (e.g., `["backend", "api"]`) |
| `depends_on` | list[str] | Task IDs that must complete first |
| `claimed_by` | string | Session ID of the agent working on it |
| `priority` | int | Higher = more important (default: 0) |

### Task List

A collection of tasks stored in `.emdash/tasks/{list_id}.json`. The default list is called `default`.

### Labels

Labels enable task clustering without pre-assignment:

```python
# When planning, categorize tasks
store.add_task("project", "Build REST API", labels=["backend", "api"])
store.add_task("project", "Create login page", labels=["frontend", "auth"])

# Later, an agent can filter by their specialty
backend_tasks = store.get_claimable_tasks("project", labels=["backend"])
```

### Dependencies

Tasks can depend on other tasks:

```python
# Create tasks with dependencies
api_task = store.add_task("project", "Build API endpoints")
frontend_task = store.add_task(
    "project",
    "Integrate with API",
    depends_on=[api_task.id]  # Must wait for API to complete
)
```

The system prevents:
- Claiming tasks with incomplete dependencies
- Creating dependency cycles

## Usage

### Environment Variables

| Variable | Description |
|----------|-------------|
| `EMDASH_TASKS_V2` | Set to `1` to enable Tasks v2 |
| `EMDASH_TASK_LIST` | Name of the task list (default: `default`) |
| `EMDASH_SESSION_ID` | Unique session identifier |
| `EMDASH_LABELS` | Comma-separated labels for this agent |
| `EMDASH_WORK_ON` | Comma-separated task IDs to work on |
| `EMDASH_PARENT_SESSION_ID` | Parent session for subagents |

### Python API

```python
from emdash_core.tasks import TaskStore, TaskWaiter, is_tasks_v2_enabled

# Check if enabled
if is_tasks_v2_enabled():
    store = TaskStore()

    # Create or get task list
    task_list = store.get_or_create_task_list("my-project")

    # Add tasks
    task1 = store.add_task(
        "my-project",
        "Setup database",
        labels=["backend", "infra"],
        priority=10
    )

    task2 = store.add_task(
        "my-project",
        "Build API endpoints",
        labels=["backend", "api"],
        depends_on=[task1.id]
    )

    # Get claimable tasks (unclaimed, unblocked)
    claimable = store.get_claimable_tasks("my-project", labels=["backend"])

    # Claim a task
    success, msg = store.claim_task("my-project", task1.id, session_id)

    # Complete a task
    success, msg = store.complete_task("my-project", task1.id, session_id)
```

### Waiting for Dependencies

When a task is blocked by dependencies, agents can wait:

```python
from emdash_core.tasks import TaskWaiter

# Wait for a specific task
completed = await TaskWaiter.wait_for_task("task-123", timeout=300)

# Wait for any of several tasks
first_completed = await TaskWaiter.wait_for_any(
    ["task-1", "task-2", "task-3"],
    timeout=300
)

# Notify waiters when completing a task
await TaskWaiter.notify_completion("task-123")
```

## Multi-Agent Workflow

### Scenario: Frontend and Backend Agents

1. **Main agent creates the plan:**
   ```python
   store.add_task("project", "Build user API", labels=["backend"])
   store.add_task("project", "Build product API", labels=["backend"])
   store.add_task("project", "Create login page", labels=["frontend"],
                  depends_on=[user_api.id])
   store.add_task("project", "Create product list", labels=["frontend"],
                  depends_on=[product_api.id])
   ```

2. **Backend agent starts:**
   ```bash
   EMDASH_TASKS_V2=1 EMDASH_LABELS=backend emdash
   ```

   The agent queries for `labels=["backend"]` tasks and claims them.

3. **Frontend agent starts:**
   ```bash
   EMDASH_TASKS_V2=1 EMDASH_LABELS=frontend emdash
   ```

   The agent queries for `labels=["frontend"]` tasks. Tasks with incomplete
   dependencies are excluded from claimable tasks.

4. **Frontend waits if needed:**
   ```python
   # If login page depends on user API which isn't done yet
   blocking = store.get_blocking_tasks("project", login_task.id)
   if blocking:
       await TaskWaiter.wait_for_task(blocking[0].id, timeout=600)
   ```

## File Storage

Tasks are stored in `.emdash/tasks/` as JSON files:

```
.emdash/
└── tasks/
    ├── default.json
    └── my-project.json
```

Each file contains:
```json
{
  "id": "my-project",
  "name": "my-project",
  "description": "",
  "tasks": [...],
  "active_sessions": [...],
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

## Concurrency Safety

- **File locking**: Uses `filelock` to prevent concurrent writes
- **Optimistic locking**: Version numbers prevent lost updates
- **Session tracking**: Heartbeats detect stale sessions
- **Task claiming**: Only one agent can claim a task at a time

## Agent Tools

When Tasks v2 is enabled, agents have access to:

| Tool | Description |
|------|-------------|
| `WriteTodoTool` | Create/update tasks with labels and dependencies |
| `ClaimTaskTool` | Claim a task for the current session |
| `CompleteTaskTool` | Mark a claimed task as completed |
| `ReleaseTaskTool` | Release a task back to pending |
| `GetClaimableTasksTool` | Get tasks available to claim |
| `GetTasksByLabelsTool` | Filter tasks by labels |
| `WaitForTaskTool` | Wait for a task to complete |

## Best Practices

1. **Use descriptive labels** - `["backend", "api", "auth"]` is better than `["b"]`
2. **Set priorities** - Higher priority tasks are shown first
3. **Keep dependencies minimal** - Only add necessary dependencies
4. **Release if blocked** - If you can't complete a task, release it
5. **Use heartbeats** - Call `store.heartbeat()` periodically for long tasks
