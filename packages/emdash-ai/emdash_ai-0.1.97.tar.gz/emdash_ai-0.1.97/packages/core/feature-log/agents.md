# Agents System

This document explains how agents work in emdash, including built-in agents, spawning, custom agents, and configuration.

## Overview

Emdash uses a sub-agent architecture where specialized agents can be spawned to handle focused tasks. Each agent has:
- Its own system prompt
- Isolated message history
- Specific toolkit (set of tools)
- Real-time event streaming to parent

---

## 1. Built-in Agents

**Location**: `agent/prompts/subagents.py:196-207`

| Agent | Purpose | Tools |
|-------|---------|-------|
| **Explore** | Fast codebase exploration - search files, read code, find patterns | glob, grep, read_file, list_files, semantic_search |
| **Plan** | Design implementation plans - analyze architecture, write structured plans | glob, grep, read_file, list_files, semantic_search |
| **Bash** | Command execution (planned) | Shell execution |
| **Research** | Documentation research (planned) | Web search, documentation fetching |

### Explore Agent

**Location**: `agent/prompts/subagents.py:16-78`

Read-only exploration agent for quick codebase analysis. Used when:
- Finding files or code patterns
- Understanding code structure
- Gathering context for a task

### Plan Agent

**Location**: `agent/prompts/subagents.py:81-153`

Software architect agent for designing implementation strategies. Returns:
- Step-by-step implementation plans
- Critical files identification
- Architectural trade-offs

---

## 2. Agent Spawning

### TaskTool

**Location**: `agent/tools/task.py:21-306`

The `TaskTool` is the entry point for spawning sub-agents:

```python
def execute(
    description: str = "",          # Short (3-5 word) description
    prompt: str = "",               # The task for the agent
    subagent_type: str = "Explore", # Agent type (Explore, Plan, or custom)
    model_tier: str = "fast",       # Model tier (fast, standard, powerful)
    max_turns: int = 10,            # Maximum API round-trips
    run_in_background: bool = False,# Run asynchronously
    resume: Optional[str] = None,   # Agent ID to resume from
    thoroughness: str = "medium",   # Search depth (quick, medium, thorough)
) -> ToolResult
```

### Execution Modes

**Synchronous** (`task.py:128-180`):
- Direct in-process execution
- Blocks until complete
- Returns full result

**Background** (`task.py:182-238`):
- Async execution with task manager
- Returns immediately with task ID
- Completion notification sent later

### InProcessSubAgent

**Location**: `agent/inprocess_subagent.py:53-438`

The actual agent runner:

```python
InProcessSubAgent(
    subagent_type: str,              # Type of agent
    repo_root: Path,                 # Repository root
    emitter=None,                    # Parent emitter for events
    model: Optional[str] = None,     # Model override
    max_turns: int = 10,             # Max iterations
    agent_id: Optional[str] = None,  # Optional agent ID
    thoroughness: str = "medium",    # Search thoroughness
)
```

**Features**:
- Real-time event streaming to parent emitter
- Isolated message histories per sub-agent
- Automatic context compaction at 80% limit
- Agent ID generation for event tagging

### SubAgentResult

**Location**: `agent/inprocess_subagent.py:28-50`

```python
@dataclass
class SubAgentResult:
    success: bool
    agent_type: str
    agent_id: str
    task: str
    summary: str
    files_explored: list[str]
    findings: list[dict]
    iterations: int
    tools_used: list[str]
    execution_time: float
    exploration_steps: list[dict] = None
    error: Optional[str] = None
```

---

## 3. Custom Agents

Custom agents are defined in `.emdash/agents/*.md` files.

### File Format

**Location**: `agent/agents.py:173-214`

```yaml
---
description: GitHub integration agent
model: claude-sonnet-4-20250514    # Optional model override
tools: [grep, glob, read_file]     # Optional tool list override
rules: [rule_name_1, rule_name_2]  # References .emdash/rules/*.md
skills: [skill_name_1]              # References .emdash/skills/
verifiers: [verifier_name]          # References .emdash/verifiers.json
mcp_servers:                        # Optional MCP servers
  github:
    command: github-mcp-server
    args: []
    env:
      GITHUB_TOKEN: ${GITHUB_TOKEN}
    enabled: true
    timeout: 30
---

# System Prompt

You are a GitHub integration specialist...

## Instructions

Your specific instructions here...

# Examples

## Example 1
User: Find GitHub PRs
Agent: I'll search for pull request patterns...
```

### CustomAgent Dataclass

**Location**: `agent/agents.py:74-102`

```python
@dataclass
class CustomAgent:
    name: str                        # From filename
    description: str = ""
    model: Optional[str] = None      # Optional model override
    system_prompt: str = ""          # Custom system prompt
    tools: list[str] = field(default_factory=list)
    mcp_servers: list[AgentMCPServerConfig] = field(default_factory=list)
    rules: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    verifiers: list[str] = field(default_factory=list)
    examples: list[dict] = field(default_factory=list)
    file_path: Optional[Path] = None
```

### Loading Custom Agents

**Location**: `agent/agents.py:104-155`

- `load_agents(agents_dir)` - Load all `.md` files from `.emdash/agents/`
- Agent name = filename stem (e.g., `github.md` → `github`)
- Frontmatter parsed with PyYAML
- System prompt = content before `# Examples`

### Prompt Composition

**Location**: `agent/prompts/subagents.py:210-253`

```python
def get_subagent_prompt(subagent_type: str, repo_root=None) -> str:
    # 1. Check built-in agents first
    if subagent_type in SUBAGENT_PROMPTS:
        return SUBAGENT_PROMPTS[subagent_type]

    # 2. Check custom agents
    custom_agent = get_custom_agent(subagent_type, repo_root)
    if custom_agent:
        prompt_parts = [custom_agent.system_prompt]

        # 3. Inject rules if specified
        if custom_agent.rules:
            rules_content = _load_rules_by_names(custom_agent.rules)
            prompt_parts.append(f"\n\n## Rules\n\n{rules_content}")

        # 4. Inject skills if specified
        if custom_agent.skills:
            skills_content = _load_skills_by_names(custom_agent.skills)
            prompt_parts.append(f"\n\n## Skills\n\n{skills_content}")

        return "".join(prompt_parts)
```

### Custom Agent Toolkit

**Location**: `agent/toolkits/__init__.py:45-91`

- Custom agents use **ExploreToolkit by default** (read-only, safe)
- Can specify custom MCP servers in frontmatter
- Tools list can override default toolkit tools

---

## 4. Agent Configuration

### Model Selection

**Provider Factory**: `agent/providers/factory.py`

**Default Model** (line 16-19):
- Environment: `EMDASH_MODEL` or `EMDASH_DEFAULT_MODEL`
- Default: `fireworks:accounts/fireworks/models/minimax-m2p1`

**Model Tiers** (`task.py:279`):
| Tier | Description |
|------|-------------|
| `fast` | Cheap/quick models |
| `standard` | Balanced models |
| `powerful` | Most capable (future) |

### Thoroughness Levels

**Location**: `agent/inprocess_subagent.py:112-136`

| Level | Behavior | Stop Criteria |
|-------|----------|---------------|
| `quick` | Basic searches, find 2-3 files, minimal exploration | Quick wins |
| `medium` | Moderate exploration, follow 1-2 import levels | Reasonable confidence |
| `thorough` | Comprehensive analysis, deep cross-references | Exhausted all areas |

Thoroughness is injected into the system prompt.

### Max Turns

- Default: 10 iterations
- Each turn = 1 LLM call + tool executions
- Configurable via `max_turns` parameter

### Context Management

**Location**: `agent/inprocess_subagent.py:250-279`

- **Threshold**: 80% of context limit triggers compaction
- **Auto-compaction**: `reduce_context_for_retry()`
- **Overflow handling**: Retry with reduced context

---

## 5. Agent Communication

### Event System

**Location**: `agent/events.py`

**EventType Enum** (lines 13-50):

```python
class EventType(Enum):
    # Tool lifecycle
    TOOL_START = "tool_start"
    TOOL_RESULT = "tool_result"

    # Sub-agent lifecycle
    SUBAGENT_START = "subagent_start"
    SUBAGENT_END = "subagent_end"

    # Agent thinking/progress
    THINKING = "thinking"
    PROGRESS = "progress"

    # Output
    RESPONSE = "response"
    PARTIAL_RESPONSE = "partial_response"
    ASSISTANT_TEXT = "assistant_text"

    # Errors
    ERROR = "error"
    WARNING = "warning"
```

### Event Flow

```
1. TaskTool.execute() starts
   ↓
2. Emit SUBAGENT_START
   - agent_type, prompt (first 100 chars), description
   ↓
3. InProcessSubAgent.run() executes loop
   ↓
4. For each tool call:
   - Emit TOOL_START (name, args, subagent_id, subagent_type)
   - Execute tool
   - Emit TOOL_RESULT (name, success, summary, subagent_id)
   ↓
5. On assistant response:
   - Emit THINKING (content, subagent_id, subagent_type)
   ↓
6. Loop until no tool calls
   ↓
7. Return SubAgentResult
   ↓
8. Emit SUBAGENT_END
   - success, iterations, files_explored, execution_time
```

### Event Tagging

Sub-agent events are tagged with:
- `subagent_id` - Unique agent identifier
- `subagent_type` - Agent type (Explore, Plan, custom)

---

## 6. Todo State Injection

The agent tracks todo items and injects their state into the context after todo-modifying tool calls.

### Todo Storage

**Location**: `agent/tools/tasks.py:60-156`

```python
class TaskState:
    """Singleton managing all todo state."""
    tasks: list[Task] = []

    def add_task(title, status="pending") -> Task
    def update_status(task_id, status) -> bool
    def get_all_tasks() -> list[dict]
```

### Todo Tools

| Tool | Location | Purpose |
|------|----------|---------|
| `write_todo` | `tasks.py:173-234` | Create new todos |
| `update_todo_list` | `tasks.py:237-325` | Update task status |

### Snapshot Tracking

**Location**: `agent/runner/agent_runner.py:107-108, 146-150`

```python
# Track todo state for change detection
self._last_todo_snapshot: str = ""

def _get_todo_snapshot(self) -> str:
    """Get current todo state as JSON for comparison."""
    state = TaskState.get_instance()
    return json.dumps(state.get_all_tasks(), sort_keys=True)
```

### Todo Reminder Format

**Location**: `agent/runner/agent_runner.py:151-168`

```python
def _format_todo_reminder(self) -> str:
    """Format current todos as XML reminder."""
    # Returns format:
    # <todo-state>
    # Tasks: X completed, Y in progress, Z pending
    #   1. ⬚ Task title 1
    #   2. 🔄 Task title 2
    #   3. ✅ Task title 3
    # </todo-state>
```

Status icons:
- `⬚` - pending
- `🔄` - in_progress
- `✅` - completed

### Injection Point

**Location**: `agent/runner/agent_runner.py:663-670`

After `write_todo` or `update_todo_list` tool execution:

```python
if tool_call.name in ("write_todo", "update_todo_list"):
    new_snapshot = self._get_todo_snapshot()
    if new_snapshot != self._last_todo_snapshot:
        self._last_todo_snapshot = new_snapshot
        reminder = self._format_todo_reminder()
        if reminder:
            result_json += f"\n\n{reminder}"
```

The todo state is appended to the tool result message, so the LLM sees the current state after any todo modification.

### System Prompt Guidance

**Location**: `agent/prompts/workflow.py:501-551`

The system prompt includes `TODO_LIST_GUIDANCE` instructing the agent:
- Use todos when 2+ steps or multiple files
- Mark tasks in_progress before starting
- Mark completed immediately after finishing
- Don't stop until ALL todos are complete

---

## 7. Background Execution

### BackgroundTaskManager

**Location**: `agent/background.py:88-482`

**Features**:
- Singleton pattern
- ThreadPoolExecutor with 10 workers
- Background monitoring thread (checks every 500ms)
- Notification system for completion

**Task Types** (lines 24-35):
- `TaskType.SHELL` - Shell command execution
- `TaskType.SUBAGENT` - Sub-agent execution

**Task Status**:
- `RUNNING`, `COMPLETED`, `FAILED`, `KILLED`

### Starting Background Agent

```python
def start_subagent(
    future: Future,           # From run_subagent_async()
    agent_type: str,          # e.g., "Explore", "Plan"
    description: str = "",
) -> str:
    # Returns task_id for tracking
```

### Completion Notification

Task completion notifications are injected into agent context:
```
[Background sub-agent {task_id} ({agent_type}) {status}]
Summary: {result.summary}
```

---

## 8. Agent Resumption

Agents can be resumed using their agent ID:

```python
TaskTool.execute(
    prompt="Continue the analysis",
    subagent_type="Explore",
    resume="abc123"  # Previous agent ID
)
```

When resumed:
- Full previous context is preserved
- Agent continues from where it left off
- Same agent ID is maintained

---

## Key Files Reference

| Component | File |
|-----------|------|
| Task Tool | `agent/tools/task.py` |
| InProcess Execution | `agent/inprocess_subagent.py` |
| Toolkit Registry | `agent/toolkits/__init__.py` |
| BaseToolkit | `agent/toolkits/base.py` |
| ExploreToolkit | `agent/toolkits/explore.py` |
| PlanToolkit | `agent/toolkits/plan.py` |
| Custom Agents | `agent/agents.py` |
| Agent Prompts | `agent/prompts/subagents.py` |
| Events | `agent/events.py` |
| Background Tasks | `agent/background.py` |
| Provider Factory | `agent/providers/factory.py` |
| Todo State | `agent/tools/tasks.py` |
