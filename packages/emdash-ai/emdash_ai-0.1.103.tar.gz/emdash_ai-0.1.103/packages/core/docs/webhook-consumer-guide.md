# Webhook Consumer Implementation Guide

This document explains how core fires webhooks on project/task mutations,
the exact payload shapes for each event, and how to build a consumer
that persists data to any backend (Firebase, SQLite, S3, etc.).

---

## Architecture Overview

```
┌──────────────────────────────────────────────┐
│  Core (FastAPI, in-memory state)             │
│                                              │
│  API endpoints ──▶ ProjectManager            │
│        │              │                      │
│        │         mutations fire               │
│        │              │                      │
│        │         WebhookRegistry.dispatch()   │
│        │              │                      │
│        │         POST to all matching hooks   │
└────────┼──────────────┼──────────────────────┘
         │              │
         ▼              ▼
   Reads (HTTP)    Webhooks (HTTP POST)
         │              │
┌────────┼──────────────┼──────────────────────┐
│  Consumer (your code)                        │
│                                              │
│  1. Register webhook at startup              │
│  2. Load existing data from store            │
│  3. Push initial state to core via /sync     │
│  4. Receive ongoing webhooks → persist       │
│  5. Listen for external changes → sync back  │
└──────────────────────────────────────────────┘
```

Core holds **in-memory state** and is the source of truth during runtime.
The consumer provides **durable storage**. On startup the consumer loads
from its store and pushes to core. After that, webhooks keep the store
in sync with core's mutations.

---

## Quick Start: Consumer Lifecycle

```
1. POST /api/multiuser/webhooks/register   → get hook_id
2. Load data from your store (Firebase, files, DB, ...)
3. POST /api/multiuser/sync/projects       → push projects to core
4. POST /api/multiuser/sync/tasks          → push tasks to core
5. Start listening for external changes (SSE, file watcher, DB trigger, ...)
6. Receive webhook POSTs from core on mutations → persist to store
7. On shutdown: DELETE /api/multiuser/webhooks/{hook_id}
```

---

## 1. Webhook Registration

### Register

```
POST /api/multiuser/webhooks/register
```

**Request:**
```json
{
  "url": "http://localhost:9100/hooks",
  "events": ["project.*", "task.*"],
  "secret": "optional-shared-secret"
}
```

- `url` — Your HTTP endpoint that will receive POST requests
- `events` — Glob patterns (fnmatch). Examples:
  - `["*"]` — all events
  - `["project.*"]` — all project events
  - `["task.assigned", "task.status_changed"]` — specific events only
- `secret` — Optional. If set, every webhook POST includes an `X-Webhook-Secret` header

**Response:**
```json
{
  "hook_id": "550e8400-e29b-41d4-a716-446655440000",
  "url": "http://localhost:9100/hooks",
  "events": ["project.*", "task.*"]
}
```

### Unregister

```
DELETE /api/multiuser/webhooks/{hook_id}
```

**Response:**
```json
{
  "status": "unregistered",
  "hook_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### List

```
GET /api/multiuser/webhooks
```

**Response:**
```json
{
  "webhooks": [
    {
      "hook_id": "550e8400-...",
      "url": "http://localhost:9100/hooks",
      "events": ["project.*", "task.*"],
      "created_at": "2025-01-15T10:00:00.000000",
      "metadata": {}
    }
  ]
}
```

---

## 2. Webhook Payload Format

Every webhook is delivered as an HTTP POST to your registered URL.

**Headers:**
```
Content-Type: application/json
X-Webhook-Secret: <your-secret>    (only if secret was set)
```

**Body:**
```json
{
  "event_id": "a1b2c3d4-...",
  "event": "project.created",
  "data": { ... },
  "timestamp": "2025-01-15T10:30:00.000000"
}
```

| Field        | Type   | Description                                        |
|-------------|--------|----------------------------------------------------|
| `event_id`  | string | Unique ID for this delivery (UUID)                 |
| `event`     | string | Event name (see event catalog below)               |
| `data`      | object | Full object dict (shape depends on event)          |
| `timestamp` | string | ISO-8601 UTC timestamp of when the event was fired |

### Echo Loop Prevention

When `origin_user_id` is passed to `dispatch()`, the data includes an
`_origin` field:

```json
{
  "event": "task.assigned",
  "data": {
    "task_id": "...",
    "_origin": "user_123",
    ...
  }
}
```

Your listener should skip events where `_origin` matches the local user
to avoid infinite sync loops (Alice writes → store → listener → core →
webhook → store → listener → ...).

---

## 3. Event Catalog

### Project Events

| Event                    | Trigger                          | Data Shape              |
|-------------------------|----------------------------------|-------------------------|
| `project.created`       | New project created              | Full `Project` dict     |
| `project.updated`       | Project name/desc/settings changed | Full `Project` dict   |
| `project.deleted`       | Project deleted                  | `{project_id, team_id}` |
| `project.member_added`  | Member added to project          | `{project_id, member}`  |
| `project.member_removed`| Member removed from project      | `{project_id, user_id}` |

### Task Events

| Event                 | Trigger                        | Data Shape                              |
|----------------------|--------------------------------|-----------------------------------------|
| `task.created`       | New task created               | Full `Task` dict                        |
| `task.updated`       | Task fields changed            | Full `Task` dict                        |
| `task.deleted`       | Task deleted                   | `{task_id, project_id}`                 |
| `task.assigned`      | Task assigned to user          | Full `Task` dict                        |
| `task.unassigned`    | Assignee removed               | Full `Task` dict                        |
| `task.status_changed`| Status transition              | Full `Task` dict + `old_status` field   |
| `task.commented`     | Comment added                  | `{task_id, comment}`                    |
| `task.session_linked`| Agent session linked to task   | Full `Task` dict                        |

---

## 4. Data Model Shapes

### Project

```json
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "team_id": "team_abc",
  "name": "Backend Refactor",
  "description": "Refactor the API layer",
  "created_by": "user_123",
  "created_at": "2025-01-15T10:00:00.000000",
  "updated_at": "2025-01-15T10:00:00.000000",
  "members": [
    {
      "user_id": "user_123",
      "display_name": "Alice",
      "role": "lead",
      "joined_at": "2025-01-15T10:00:00.000000",
      "metadata": {}
    }
  ],
  "settings": {}
}
```

**Fields:**

| Field         | Type          | Description                                |
|--------------|---------------|--------------------------------------------|
| `project_id` | string (UUID) | Unique project identifier                  |
| `team_id`    | string        | Owning team                                |
| `name`       | string        | Project name                               |
| `description`| string        | Optional description                       |
| `created_by` | string        | User ID of creator                         |
| `created_at` | string        | ISO-8601 creation timestamp                |
| `updated_at` | string        | ISO-8601 last update timestamp             |
| `members`    | array         | List of `ProjectMember` objects            |
| `settings`   | object        | Arbitrary settings dict                    |

### ProjectMember

| Field          | Type   | Values                                |
|---------------|--------|---------------------------------------|
| `user_id`     | string | User identifier                       |
| `display_name`| string | Human-readable name                   |
| `role`        | string | `"lead"`, `"contributor"`, `"observer"` |
| `joined_at`   | string | ISO-8601 timestamp                    |
| `metadata`    | object | Arbitrary metadata                    |

### Task

```json
{
  "task_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Fix login bug",
  "description": "Users get 500 on /login when email has +",
  "status": "in_progress",
  "priority": "high",
  "assignee_id": "user_456",
  "assignee_name": "Bob",
  "reporter_id": "user_123",
  "reporter_name": "Alice",
  "created_at": "2025-01-15T11:00:00.000000",
  "updated_at": "2025-01-15T12:30:00.000000",
  "due_date": "2025-01-20T00:00:00.000000",
  "labels": ["bug", "auth"],
  "comments": [
    {
      "comment_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "task_id": "7c9e6679-...",
      "user_id": "user_123",
      "display_name": "Alice",
      "content": "Reproduced on staging",
      "created_at": "2025-01-15T11:30:00.000000"
    }
  ],
  "linked_session_id": null,
  "metadata": {}
}
```

**Fields:**

| Field               | Type          | Description                                              |
|--------------------|---------------|----------------------------------------------------------|
| `task_id`          | string (UUID) | Unique task identifier                                   |
| `project_id`      | string (UUID) | Parent project                                           |
| `title`           | string        | Task title                                               |
| `description`     | string        | Optional description                                     |
| `status`          | string        | `"open"`, `"in_progress"`, `"in_review"`, `"done"`, `"cancelled"` |
| `priority`        | string        | `"low"`, `"medium"`, `"high"`, `"critical"`              |
| `assignee_id`     | string\|null  | Assigned user ID                                         |
| `assignee_name`   | string\|null  | Assigned user display name                               |
| `reporter_id`     | string        | Reporter user ID                                         |
| `reporter_name`   | string        | Reporter display name                                    |
| `created_at`      | string        | ISO-8601 timestamp                                       |
| `updated_at`      | string        | ISO-8601 timestamp                                       |
| `due_date`        | string\|null  | Optional due date (ISO-8601)                             |
| `labels`          | array[string] | Tags/labels                                              |
| `comments`        | array         | List of `TaskComment` objects                            |
| `linked_session_id`| string\|null | Linked agent session ID                                  |
| `metadata`        | object        | Arbitrary metadata                                       |

### TaskComment

| Field          | Type   | Description           |
|---------------|--------|-----------------------|
| `comment_id`  | string | Unique comment ID     |
| `task_id`     | string | Parent task           |
| `user_id`     | string | Author user ID        |
| `display_name`| string | Author display name   |
| `content`     | string | Comment text          |
| `created_at`  | string | ISO-8601 timestamp    |

---

## 5. Webhook Payload Examples

### project.created

Fired when `POST /api/multiuser/project/create` succeeds.

```json
{
  "event_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "event": "project.created",
  "data": {
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "team_id": "team_abc",
    "name": "Backend Refactor",
    "description": "Refactor the API layer",
    "created_by": "user_123",
    "created_at": "2025-01-15T10:00:00.000000",
    "updated_at": "2025-01-15T10:00:00.000000",
    "members": [
      {
        "user_id": "user_123",
        "display_name": "Alice",
        "role": "lead",
        "joined_at": "2025-01-15T10:00:00.000000",
        "metadata": {}
      }
    ],
    "settings": {}
  },
  "timestamp": "2025-01-15T10:00:00.100000"
}
```

### project.updated

Fired when `PATCH /api/multiuser/project/{project_id}` succeeds.

```json
{
  "event_id": "...",
  "event": "project.updated",
  "data": {
    "project_id": "550e8400-...",
    "team_id": "team_abc",
    "name": "Backend Refactor v2",
    "description": "Updated scope",
    "created_by": "user_123",
    "created_at": "2025-01-15T10:00:00.000000",
    "updated_at": "2025-01-15T14:00:00.000000",
    "members": [ ... ],
    "settings": {}
  },
  "timestamp": "2025-01-15T14:00:00.100000"
}
```

### project.deleted

Fired when `DELETE /api/multiuser/project/{project_id}` succeeds.

```json
{
  "event_id": "...",
  "event": "project.deleted",
  "data": {
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "team_id": "team_abc"
  },
  "timestamp": "2025-01-15T15:00:00.000000"
}
```

### project.member_added

Fired when `POST /api/multiuser/project/{project_id}/members` succeeds.

```json
{
  "event_id": "...",
  "event": "project.member_added",
  "data": {
    "project_id": "550e8400-...",
    "member": {
      "user_id": "user_456",
      "display_name": "Bob",
      "role": "contributor",
      "joined_at": "2025-01-15T11:00:00.000000",
      "metadata": {}
    }
  },
  "timestamp": "2025-01-15T11:00:00.100000"
}
```

### project.member_removed

Fired when `DELETE /api/multiuser/project/{project_id}/members/{user_id}` succeeds.

```json
{
  "event_id": "...",
  "event": "project.member_removed",
  "data": {
    "project_id": "550e8400-...",
    "user_id": "user_456"
  },
  "timestamp": "2025-01-15T12:00:00.000000"
}
```

### task.created

Fired when `POST /api/multiuser/project/{project_id}/tasks` succeeds.

```json
{
  "event_id": "...",
  "event": "task.created",
  "data": {
    "task_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "project_id": "550e8400-...",
    "title": "Fix login bug",
    "description": "Users get 500 on /login when email has +",
    "status": "open",
    "priority": "high",
    "assignee_id": null,
    "assignee_name": null,
    "reporter_id": "user_123",
    "reporter_name": "Alice",
    "created_at": "2025-01-15T11:00:00.000000",
    "updated_at": "2025-01-15T11:00:00.000000",
    "due_date": null,
    "labels": ["bug", "auth"],
    "comments": [],
    "linked_session_id": null,
    "metadata": {}
  },
  "timestamp": "2025-01-15T11:00:00.100000"
}
```

### task.assigned

Fired when `POST /api/multiuser/task/{task_id}/assign` succeeds.

```json
{
  "event_id": "...",
  "event": "task.assigned",
  "data": {
    "task_id": "7c9e6679-...",
    "project_id": "550e8400-...",
    "title": "Fix login bug",
    "status": "open",
    "priority": "high",
    "assignee_id": "user_456",
    "assignee_name": "Bob",
    "reporter_id": "user_123",
    "reporter_name": "Alice",
    "created_at": "2025-01-15T11:00:00.000000",
    "updated_at": "2025-01-15T11:30:00.000000",
    "...": "... (full Task dict)"
  },
  "timestamp": "2025-01-15T11:30:00.100000"
}
```

### task.unassigned

Fired when `POST /api/multiuser/task/{task_id}/unassign` succeeds.
Data is the full `Task` dict with `assignee_id: null`, `assignee_name: null`.

### task.status_changed

Fired when `POST /api/multiuser/task/{task_id}/transition` succeeds.
Includes an extra `old_status` field.

```json
{
  "event_id": "...",
  "event": "task.status_changed",
  "data": {
    "task_id": "7c9e6679-...",
    "project_id": "550e8400-...",
    "title": "Fix login bug",
    "status": "in_progress",
    "old_status": "open",
    "priority": "high",
    "assignee_id": "user_456",
    "assignee_name": "Bob",
    "...": "... (full Task dict)"
  },
  "timestamp": "2025-01-15T12:00:00.000000"
}
```

### task.updated

Fired when `PATCH /api/multiuser/task/{task_id}` succeeds.
Data is the full `Task` dict with updated fields.

### task.deleted

Fired when `DELETE /api/multiuser/task/{task_id}` succeeds.

```json
{
  "event_id": "...",
  "event": "task.deleted",
  "data": {
    "task_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "project_id": "550e8400-e29b-41d4-a716-446655440000"
  },
  "timestamp": "2025-01-15T13:00:00.000000"
}
```

### task.commented

Fired when `POST /api/multiuser/task/{task_id}/comment` succeeds.

```json
{
  "event_id": "...",
  "event": "task.commented",
  "data": {
    "task_id": "7c9e6679-...",
    "comment": {
      "comment_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "task_id": "7c9e6679-...",
      "user_id": "user_123",
      "display_name": "Alice",
      "content": "Reproduced on staging",
      "created_at": "2025-01-15T11:30:00.000000"
    }
  },
  "timestamp": "2025-01-15T11:30:00.100000"
}
```

### task.session_linked

Fired when `POST /api/multiuser/task/{task_id}/link-session` succeeds.
Data is the full `Task` dict with `linked_session_id` set.

---

## 6. Sync API (Initial Load)

On startup, the consumer loads from its durable store and pushes to core
so core can serve reads.

### Sync Projects

```
POST /api/multiuser/sync/projects
```

**Request:**
```json
{
  "projects": [
    {
      "project_id": "550e8400-...",
      "team_id": "team_abc",
      "name": "Backend Refactor",
      "description": "",
      "created_by": "user_123",
      "created_at": "2025-01-15T10:00:00.000000",
      "updated_at": "2025-01-15T10:00:00.000000",
      "members": [ ... ],
      "settings": {}
    }
  ]
}
```

**Response:**
```json
{
  "synced": 3
}
```

### Sync Tasks

```
POST /api/multiuser/sync/tasks
```

**Request:**
```json
{
  "tasks": [
    {
      "task_id": "7c9e6679-...",
      "project_id": "550e8400-...",
      "title": "Fix login bug",
      "status": "open",
      "priority": "high",
      "...": "... (all Task fields)"
    }
  ]
}
```

**Response:**
```json
{
  "synced": 12
}
```

---

## 7. Project & Task API Endpoints

All endpoints are under `/api/multiuser/`.

### Projects

| Method | Path                                  | Description                 | Request Body              |
|--------|---------------------------------------|-----------------------------|---------------------------|
| POST   | `/project/create`                     | Create project              | `CreateProjectRequest`    |
| GET    | `/project/{project_id}`               | Get project                 | —                         |
| PATCH  | `/project/{project_id}`               | Update project              | `UpdateProjectRequest`    |
| DELETE | `/project/{project_id}?user_id=...`   | Delete project (lead only)  | —                         |
| GET    | `/team/{team_id}/projects`            | List team's projects        | —                         |
| POST   | `/project/{project_id}/members`       | Add member                  | `AddProjectMemberRequest` |
| DELETE | `/project/{project_id}/members/{uid}` | Remove member               | —                         |

### Tasks

| Method | Path                                   | Description              | Request Body             |
|--------|----------------------------------------|--------------------------|--------------------------|
| POST   | `/project/{project_id}/tasks`          | Create task              | `CreateTaskRequest`      |
| GET    | `/project/{project_id}/tasks`          | List project tasks       | —                        |
| GET    | `/task/{task_id}`                      | Get task                 | —                        |
| PATCH  | `/task/{task_id}`                      | Update task              | `UpdateTaskRequest`      |
| DELETE | `/task/{task_id}`                      | Delete task              | —                        |
| POST   | `/task/{task_id}/assign`               | Assign task              | `AssignTaskRequest`      |
| POST   | `/task/{task_id}/unassign`             | Unassign task            | —                        |
| POST   | `/task/{task_id}/transition`           | Change status            | `TransitionTaskRequest`  |
| POST   | `/task/{task_id}/comment`              | Add comment              | `AddTaskCommentRequest`  |
| POST   | `/task/{task_id}/link-session`         | Link agent session       | `LinkTaskSessionRequest` |
| GET    | `/user/{user_id}/tasks?status=...`     | User's assigned tasks    | —                        |

### Request Body Examples

**CreateProjectRequest:**
```json
{
  "team_id": "team_abc",
  "name": "Backend Refactor",
  "user_id": "user_123",
  "display_name": "Alice",
  "description": "Refactor the API layer"
}
```

**CreateTaskRequest:**
```json
{
  "title": "Fix login bug",
  "reporter_id": "user_123",
  "reporter_name": "Alice",
  "description": "Users get 500 on /login when email has +",
  "priority": "high",
  "assignee_id": "user_456",
  "assignee_name": "Bob",
  "due_date": "2025-01-20T00:00:00",
  "labels": ["bug", "auth"]
}
```

**AssignTaskRequest:**
```json
{
  "assignee_id": "user_456",
  "assignee_name": "Bob"
}
```

**TransitionTaskRequest:**
```json
{
  "status": "in_progress"
}
```

**AddTaskCommentRequest:**
```json
{
  "user_id": "user_123",
  "display_name": "Alice",
  "content": "Reproduced on staging"
}
```

**UpdateProjectRequest** (all fields optional):
```json
{
  "name": "Backend Refactor v2",
  "description": "Updated scope",
  "settings": { "visibility": "public" }
}
```

**UpdateTaskRequest** (all fields optional):
```json
{
  "title": "Fix login bug (urgent)",
  "priority": "critical",
  "labels": ["bug", "auth", "urgent"]
}
```

**AddProjectMemberRequest:**
```json
{
  "user_id": "user_456",
  "display_name": "Bob",
  "role": "contributor"
}
```

**LinkTaskSessionRequest:**
```json
{
  "session_id": "session_789"
}
```

---

## 8. Implementing a Custom Consumer

### Minimal Python Example

```python
import asyncio
import httpx
from aiohttp import web

CORE_URL = "http://localhost:8000"
MY_PORT = 9100


async def handle_webhook(request):
    """Receive webhook events from core."""
    payload = await request.json()
    event = payload["event"]
    data = payload["data"]

    if event == "project.created":
        await save_project(data)
    elif event == "project.updated":
        await save_project(data)
    elif event == "project.deleted":
        await delete_project(data["project_id"])
    elif event in ("task.created", "task.updated", "task.assigned",
                    "task.unassigned", "task.status_changed",
                    "task.session_linked"):
        await save_task(data)
    elif event == "task.deleted":
        await delete_task(data["task_id"])
    elif event == "task.commented":
        # Comment is nested; the full task is updated via task.updated
        pass

    return web.Response(status=200)


async def save_project(data: dict):
    """Persist project to your store."""
    project_id = data["project_id"]
    # Write to Firebase, SQLite, S3, etc.
    print(f"Saved project {project_id}: {data['name']}")


async def save_task(data: dict):
    """Persist task to your store."""
    task_id = data["task_id"]
    print(f"Saved task {task_id}: {data['title']} [{data['status']}]")


async def delete_project(project_id: str):
    print(f"Deleted project {project_id}")


async def delete_task(task_id: str):
    print(f"Deleted task {task_id}")


async def main():
    # 1. Start local HTTP server
    app = web.Application()
    app.router.add_post("/hooks", handle_webhook)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", MY_PORT)
    await site.start()
    print(f"Webhook receiver listening on port {MY_PORT}")

    # 2. Register webhook with core
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{CORE_URL}/api/multiuser/webhooks/register",
            json={
                "url": f"http://127.0.0.1:{MY_PORT}/hooks",
                "events": ["project.*", "task.*"],
            },
        )
        hook_id = resp.json()["hook_id"]
        print(f"Registered webhook: {hook_id}")

        # 3. Load from your store and sync to core
        projects = load_projects_from_store()
        tasks = load_tasks_from_store()

        if projects:
            await client.post(
                f"{CORE_URL}/api/multiuser/sync/projects",
                json={"projects": projects},
            )
        if tasks:
            await client.post(
                f"{CORE_URL}/api/multiuser/sync/tasks",
                json={"tasks": tasks},
            )

    # 4. Run until interrupted
    try:
        await asyncio.Event().wait()
    finally:
        # 5. Cleanup
        async with httpx.AsyncClient() as client:
            await client.delete(
                f"{CORE_URL}/api/multiuser/webhooks/{hook_id}"
            )
        await runner.cleanup()


def load_projects_from_store():
    """Load projects from your durable store."""
    return []  # Replace with your storage read logic


def load_tasks_from_store():
    """Load tasks from your durable store."""
    return []  # Replace with your storage read logic


if __name__ == "__main__":
    asyncio.run(main())
```

### Consumer Checklist

- [ ] Start HTTP server to receive webhook POSTs
- [ ] Register with core at startup (`POST /webhooks/register`)
- [ ] Load existing data from your store
- [ ] Push initial state to core (`POST /sync/projects`, `POST /sync/tasks`)
- [ ] Handle all webhook events and persist to store
- [ ] Implement echo loop prevention (check `_origin` field)
- [ ] Start a listener for external changes to your store
- [ ] Sync external changes back to core via the mutation APIs
- [ ] Unregister webhook on shutdown (`DELETE /webhooks/{hook_id}`)
- [ ] Handle webhook delivery failures gracefully (core doesn't retry by default)

---

## 9. Existing Backend Implementations

The CLI package includes two ready-made backends:

### Firebase Backend

- **Handler:** `packages/cli/emdash_cli/handlers/firebase_webhook_handler.py`
  - Receives webhooks → writes to Firebase Realtime Database via REST
- **Listener:** `packages/cli/emdash_cli/handlers/firebase_listener.py`
  - Streams SSE from Firebase → syncs changes to core
- **Config:** Set `FIREBASE_DATABASE_URL` and optionally `FIREBASE_API_KEY`

### Local File Backend

- **Handler:** `packages/cli/emdash_cli/handlers/localfile_webhook_handler.py`
  - Receives webhooks → writes JSON files to `{storage_root}/projects/` and `tasks/`
- **Listener:** `packages/cli/emdash_cli/handlers/localfile_listener.py`
  - Polls file mtimes → syncs changes to core
- **Config:** Set `EMDASH_STORAGE_ROOT` (defaults to `~/.emdash/projects`)

### Orchestrator

`packages/cli/emdash_cli/handlers/project_sync.py` provides `ProjectSyncManager`
which wires together the handler, listener, and lifecycle for any backend.
Use `create_project_sync()` for auto-detection from environment variables:

```python
from emdash_cli.handlers import create_project_sync

sync = create_project_sync(
    core_url="http://localhost:8000",
    user_id="user_123",
    team_id="team_abc",
)
await sync.start()   # register + initial sync + start listener
# ...
await sync.stop()    # unregister + stop listener + cleanup
```

**Environment variables:**

| Variable                    | Effect                                       |
|----------------------------|-----------------------------------------------|
| `EMDASH_MULTIUSER_PROVIDER=firebase` | Use Firebase backend                |
| `EMDASH_MULTIUSER_PROVIDER=local`    | Use local file backend              |
| (unset)                              | Firebase if `FIREBASE_DATABASE_URL` is set, else local |
| `FIREBASE_DATABASE_URL`             | Firebase Realtime Database URL       |
| `FIREBASE_API_KEY`                  | Optional Firebase API key            |
| `EMDASH_STORAGE_ROOT`              | Local file storage root (default `~/.emdash/projects`) |

---

## 10. Protocol Contracts

To implement a new backend, satisfy these Python protocols
(defined in `project_sync.py`):

```python
class WebhookHandler(Protocol):
    """Receives events from core and persists to store."""
    async def handle(self, event_name: str, payload: dict) -> None: ...
    async def close(self) -> None: ...

class StoreListener(Protocol):
    """Watches store for external changes and syncs to core."""
    async def start(self, team_id: str) -> None: ...
    async def stop(self) -> None: ...

class StoreLoader(Protocol):
    """Loads initial data from store (optional)."""
    def load_all_projects(self) -> list[dict]: ...
    def load_all_tasks(self) -> list[dict]: ...
```

Then register your backend with a factory function:

```python
def create_my_backend(
    core_url: str,
    user_id: str,
    **config,
) -> tuple[WebhookHandler, StoreListener, StoreLoader]:
    handler = MyHandler(**config)
    listener = MyListener(core_url=core_url, my_user_id=user_id, **config)
    loader = handler  # or a separate loader
    return handler, listener, loader
```
