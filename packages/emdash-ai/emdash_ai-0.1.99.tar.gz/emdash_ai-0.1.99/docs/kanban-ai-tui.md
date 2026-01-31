# Kanban AI Management TUI

## Vision

A **parallel AI task management TUI** - not another chat interface, but a visual Kanban board in the terminal where multiple AI agents work on tasks simultaneously while you watch progress in real-time.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  EMDASH AI KANBAN                                          [a]dd  [q]uit   │
├─────────────────┬─────────────────┬─────────────────┬─────────────────────┤
│   📋 BACKLOG    │  🧠 PLANNING    │  ⚡ IN PROGRESS │     ✅ DONE         │
├─────────────────┼─────────────────┼─────────────────┼─────────────────────┤
│                 │                 │                 │                     │
│ ┌─────────────┐ │ ┌─────────────┐ │ ┌─────────────┐ │ ┌─────────────────┐ │
│ │ Add dark    │ │ │ Fix auth    │ │ │ Add tests   │ │ │ Refactor utils  │ │
│ │ mode toggle │ │ │ bug         │ │ │ for API     │ │ │                 │ │
│ │             │ │ │             │ │ │             │ │ │ ✓ 12 files      │ │
│ │ [Enter] →   │ │ │ ◐ Planning  │ │ │ ◐ Writing   │ │ │   modified      │ │
│ └─────────────┘ │ │   step 2/5  │ │ │   tests...  │ │ └─────────────────┘ │
│                 │ └─────────────┘ │ └─────────────┘ │                     │
│ ┌─────────────┐ │                 │                 │ ┌─────────────────┐ │
│ │ Optimize    │ │                 │ ┌─────────────┐ │ │ Add pagination  │ │
│ │ database    │ │                 │ │ Update docs │ │ │                 │ │
│ │ queries     │ │                 │ │             │ │ │ ✓ 3 files       │ │
│ │             │ │                 │ │ ◐ Reading   │ │ │   modified      │ │
│ └─────────────┘ │                 │ │   files...  │ │ └─────────────────┘ │
│                 │                 │ └─────────────┘ │                     │
└─────────────────┴─────────────────┴─────────────────┴─────────────────────┘
│ Task: Add tests for API │ Reading: src/api/routes.py │ Tools: 3 │ Time: 2m │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Core Concept

### The Flow

```
User adds task → BACKLOG → PLANNING → IN PROGRESS → DONE
     ↓              ↓          ↓            ↓          ↓
  Description    Queued    AI plans     AI codes    Complete
                           the work     the work    with summary
```

### Key Differentiators

1. **Parallel Execution** - Multiple tasks can be in PLANNING or IN PROGRESS simultaneously
2. **Visual Progress** - See AI thinking, reading files, writing code in real-time
3. **Non-blocking** - Add new tasks while others are running
4. **Keyboard-driven** - Fast navigation with vim-like keys
5. **Persistent** - Board state survives restarts

---

## Architecture

### Components

```
packages/cli/emdash_cli/tui/
├── kanban/
│   ├── __init__.py
│   ├── app.py              # Main Textual app
│   ├── board.py            # Board widget (columns container)
│   ├── column.py           # Column widget (task list)
│   ├── card.py             # Task card widget
│   ├── detail_panel.py     # Right panel for task details/logs
│   ├── input_modal.py      # Modal for adding/editing tasks
│   ├── models.py           # Task, Column, Board data models
│   ├── state.py            # Board state management
│   ├── executor.py         # Task execution manager
│   └── styles.tcss         # Textual CSS styles
```

### Data Models

```python
# models.py

from enum import Enum
from pydantic import BaseModel
from datetime import datetime

class ColumnId(str, Enum):
    BACKLOG = "backlog"
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    DONE = "done"

class AIStatus(str, Enum):
    IDLE = "idle"
    QUEUED = "queued"
    PLANNING = "planning"
    IMPLEMENTING = "implementing"
    REVIEWING = "reviewing"
    COMPLETE = "complete"
    FAILED = "failed"

class Task(BaseModel):
    id: str
    title: str
    description: str
    column: ColumnId = ColumnId.BACKLOG
    ai_status: AIStatus = AIStatus.IDLE
    created_at: datetime
    updated_at: datetime

    # Planning output
    plan: str | None = None
    plan_steps: list[str] = []
    current_step: int = 0

    # Execution tracking
    files_modified: list[str] = []
    tools_used: int = 0
    thinking_log: list[str] = []  # Recent AI thoughts
    current_activity: str = ""     # "Reading src/foo.py"

    # Results
    summary: str | None = None
    error: str | None = None
    execution_time_seconds: float = 0

class Board(BaseModel):
    tasks: dict[str, Task] = {}
    column_order: list[ColumnId] = [
        ColumnId.BACKLOG,
        ColumnId.PLANNING,
        ColumnId.IN_PROGRESS,
        ColumnId.DONE
    ]
```

### State Management

```python
# state.py

class BoardState:
    """Reactive board state with persistence."""

    def __init__(self, storage_path: Path):
        self.board: Board
        self.storage_path = storage_path
        self._subscribers: list[Callable] = []

    def add_task(self, title: str, description: str) -> Task:
        """Add new task to backlog."""

    def move_task(self, task_id: str, column: ColumnId) -> None:
        """Move task between columns."""

    def update_task(self, task_id: str, **updates) -> None:
        """Update task fields and notify subscribers."""

    def get_tasks_by_column(self, column: ColumnId) -> list[Task]:
        """Get all tasks in a column."""

    def subscribe(self, callback: Callable) -> None:
        """Subscribe to state changes."""

    def save(self) -> None:
        """Persist board to disk."""

    def load(self) -> None:
        """Load board from disk."""
```

### Task Executor

```python
# executor.py

class TaskExecutor:
    """Manages parallel AI task execution."""

    def __init__(
        self,
        board_state: BoardState,
        max_concurrent: int = 2  # Max parallel tasks
    ):
        self.board_state = board_state
        self.max_concurrent = max_concurrent
        self._running: dict[str, asyncio.Task] = {}
        self._queue: asyncio.Queue[str] = asyncio.Queue()

    async def start_task(self, task_id: str) -> None:
        """Start executing a task (planning or implementation)."""

    async def _run_planning(self, task: Task) -> None:
        """Run AI planning phase."""
        # Uses existing SpecificationAgent or planning tools
        # Streams events to update task.thinking_log
        # On complete: move to IN_PROGRESS

    async def _run_implementation(self, task: Task) -> None:
        """Run AI implementation phase."""
        # Uses AgentRunner with the plan
        # Streams events to update progress
        # On complete: move to DONE

    def cancel_task(self, task_id: str) -> None:
        """Cancel a running task."""

    @property
    def can_start_more(self) -> bool:
        """Check if we can start more tasks."""
        return len(self._running) < self.max_concurrent
```

---

## UI Components

### 1. Main App

```python
# app.py

class KanbanApp(App):
    """Kanban AI Management TUI."""

    CSS_PATH = "styles.tcss"
    BINDINGS = [
        Binding("a", "add_task", "Add Task"),
        Binding("enter", "start_task", "Start Task"),
        Binding("d", "delete_task", "Delete"),
        Binding("e", "edit_task", "Edit"),
        Binding("v", "view_details", "View Details"),
        Binding("h", "move_left", "Move Left"),
        Binding("l", "move_right", "Move Right"),
        Binding("j", "next_task", "Next Task"),
        Binding("k", "prev_task", "Prev Task"),
        Binding("q", "quit", "Quit"),
        Binding("?", "help", "Help"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Board()
        yield DetailPanel()  # Optional right panel
        yield Footer()
```

### 2. Board Widget

```python
# board.py

class Board(Widget):
    """Container for columns."""

    def compose(self) -> ComposeResult:
        for column_id in self.state.column_order:
            yield Column(column_id)

    def on_state_change(self, event: StateChange) -> None:
        """React to state changes and update UI."""
```

### 3. Column Widget

```python
# column.py

class Column(Widget):
    """A single column containing task cards."""

    COLUMN_TITLES = {
        ColumnId.BACKLOG: "📋 BACKLOG",
        ColumnId.PLANNING: "🧠 PLANNING",
        ColumnId.IN_PROGRESS: "⚡ IN PROGRESS",
        ColumnId.DONE: "✅ DONE",
    }

    def compose(self) -> ComposeResult:
        yield Static(self.title, classes="column-header")
        yield VerticalScroll(id=f"tasks-{self.column_id}")
```

### 4. Card Widget

```python
# card.py

class Card(Widget):
    """A task card with real-time status updates."""

    def compose(self) -> ComposeResult:
        yield Static(self.task.title, classes="card-title")
        yield Static(self.task.description[:50], classes="card-desc")
        yield StatusIndicator(self.task)

    def watch_task(self) -> None:
        """Update card when task state changes."""
```

### 5. Status Indicator

```python
# Shows AI activity on card

class StatusIndicator(Widget):
    """Shows current AI activity with animation."""

    SPINNERS = ["◐", "◓", "◑", "◒"]

    STATUS_LABELS = {
        AIStatus.QUEUED: "Queued...",
        AIStatus.PLANNING: "Planning",
        AIStatus.IMPLEMENTING: "Implementing",
        AIStatus.REVIEWING: "Reviewing",
    }

    def render(self) -> str:
        if self.task.ai_status == AIStatus.IDLE:
            return ""
        if self.task.ai_status == AIStatus.COMPLETE:
            return f"✓ {len(self.task.files_modified)} files"

        spinner = self.SPINNERS[self._frame % 4]
        label = self.STATUS_LABELS[self.task.ai_status]
        activity = self.task.current_activity[:20]
        return f"{spinner} {label}: {activity}"
```

### 6. Detail Panel

```python
# detail_panel.py

class DetailPanel(Widget):
    """Right panel showing task details and live logs."""

    def compose(self) -> ComposeResult:
        yield Static("", id="task-title")
        yield Static("", id="task-description")
        yield Divider()
        yield Static("Plan:", classes="section-header")
        yield Static("", id="task-plan")
        yield Divider()
        yield Static("Activity:", classes="section-header")
        yield RichLog(id="activity-log")  # Streaming AI thoughts
```

---

## Keyboard Navigation

| Key | Action |
|-----|--------|
| `a` | Add new task (opens modal) |
| `Enter` | Start selected task (move backlog→planning→progress) |
| `h/l` | Move between columns |
| `j/k` | Move between tasks in column |
| `d` | Delete selected task |
| `e` | Edit selected task |
| `v` | Toggle detail panel |
| `Space` | Expand/collapse card |
| `c` | Cancel running task |
| `r` | Retry failed task |
| `q` | Quit |
| `?` | Show help |

---

## Event Integration

### Connecting to Existing Event System

```python
# executor.py

async def _run_implementation(self, task: Task) -> None:
    """Execute task with event streaming."""

    async for event in self._stream_agent(task):
        match event["type"]:
            case "thinking":
                self.board_state.update_task(
                    task.id,
                    thinking_log=[*task.thinking_log[-10:], event["data"]["content"]],
                )

            case "tool_start":
                tool_name = event["data"]["tool"]
                args = event["data"].get("args", {})
                activity = self._format_activity(tool_name, args)
                self.board_state.update_task(
                    task.id,
                    current_activity=activity,
                    tools_used=task.tools_used + 1,
                )

            case "tool_result":
                # Track file modifications
                if event["data"].get("tool") in ["edit", "write"]:
                    file_path = event["data"]["args"].get("path")
                    if file_path:
                        self.board_state.update_task(
                            task.id,
                            files_modified=[*task.files_modified, file_path],
                        )

            case "response":
                # Task complete
                self.board_state.update_task(
                    task.id,
                    column=ColumnId.DONE,
                    ai_status=AIStatus.COMPLETE,
                    summary=event["data"]["content"][:200],
                )

            case "error":
                self.board_state.update_task(
                    task.id,
                    ai_status=AIStatus.FAILED,
                    error=event["data"]["message"],
                )
```

---

## Styling (Textual CSS)

```css
/* styles.tcss */

Screen {
    layout: horizontal;
}

Board {
    layout: horizontal;
    width: 100%;
    height: 1fr;
}

Column {
    width: 1fr;
    height: 100%;
    border: solid $primary;
    margin: 0 1;
}

.column-header {
    background: $primary;
    color: $text;
    text-align: center;
    padding: 1;
    text-style: bold;
}

Card {
    height: auto;
    margin: 1;
    padding: 1;
    border: round $secondary;
    background: $surface;
}

Card:focus {
    border: round $accent;
    background: $surface-lighten-1;
}

Card.running {
    border: round $success;
}

Card.failed {
    border: round $error;
}

.card-title {
    text-style: bold;
}

.card-desc {
    color: $text-muted;
}

StatusIndicator {
    color: $accent;
    text-style: italic;
}

DetailPanel {
    width: 40;
    border-left: solid $primary;
    padding: 1;
    display: none;
}

DetailPanel.visible {
    display: block;
}
```

---

## Storage

### Board Persistence

```python
# Location: .emdash/kanban/board.json

{
    "tasks": {
        "task-uuid-1": {
            "id": "task-uuid-1",
            "title": "Add dark mode",
            "description": "Add a dark mode toggle to settings",
            "column": "done",
            "ai_status": "complete",
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-15T10:15:00Z",
            "plan": "1. Add theme context\n2. Create toggle component...",
            "files_modified": ["src/theme.py", "src/settings.py"],
            "summary": "Added dark mode toggle with system preference detection"
        }
    }
}
```

---

## Implementation Phases

### Phase 1: Core Board UI
- [ ] Create Kanban app with static columns
- [ ] Implement Card widget with basic display
- [ ] Add keyboard navigation (h/j/k/l)
- [ ] Implement add task modal
- [ ] Add board persistence

### Phase 2: Task Execution
- [ ] Connect to existing AgentRunner
- [ ] Implement planning phase streaming
- [ ] Implement implementation phase streaming
- [ ] Add real-time status updates on cards
- [ ] Track file modifications and tools used

### Phase 3: Parallel Execution
- [ ] Add task queue management
- [ ] Support multiple concurrent tasks
- [ ] Add task cancellation
- [ ] Implement retry for failed tasks

### Phase 4: Detail Panel
- [ ] Add collapsible right panel
- [ ] Stream AI thinking to activity log
- [ ] Show plan steps with progress
- [ ] Display file diff preview

### Phase 5: Polish
- [ ] Add animations and transitions
- [ ] Improve error handling
- [ ] Add task filtering/search
- [ ] Add keyboard shortcuts help overlay

---

## CLI Integration

```bash
# Launch Kanban TUI
em tui --kanban
emdash tui --kanban

# Or make it the default TUI mode
em tui  # Opens Kanban by default
```

---

## Future Enhancements

1. **Task Dependencies** - Link tasks so one starts after another completes
2. **Git Integration** - Auto-create branches per task, show PR status
3. **Templates** - Pre-defined task templates (bug fix, feature, refactor)
4. **Filters** - Filter tasks by status, age, labels
5. **Multiple Boards** - Project-specific boards
6. **Export** - Export board as markdown report
7. **Collaboration** - Sync board across team (via server)
