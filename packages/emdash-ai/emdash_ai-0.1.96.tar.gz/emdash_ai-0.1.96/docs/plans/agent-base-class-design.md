# Agent Base Class Architecture Design

## Overview

This document outlines a refactored agent architecture that uses a base class to enable two distinct agent types:
1. **CodingMainAgent** - Full-featured coding assistant with file operations, execution, and code-specific sub-agents
2. **CoworkerAgent** - General-purpose assistant without coding capabilities, focused on research, planning, and collaboration

Both inherit from a common `BaseAgent` abstract class, sharing infrastructure while having specialized toolkits and sub-agents.

---

## Architecture Diagram

```
                            +------------------+
                            |    BaseAgent     |
                            |   (abstract)     |
                            +------------------+
                            | - provider       |
                            | - emitter        |
                            | - messages[]     |
                            | - toolkit        |
                            | - token_tracking |
                            +--------+---------+
                                     |
              +----------------------+----------------------+
              |                                             |
    +---------v----------+                      +-----------v---------+
    |  CodingMainAgent   |                      |   CoworkerAgent     |
    +--------------------+                      +---------------------+
    | - CodingToolkit    |                      | - CoworkerToolkit   |
    | - checkpoint_mgr   |                      | - task_state        |
    | - plan_mode        |                      +---------------------+
    +--------------------+
              |                                             |
    +---------v----------+                      +-----------v---------+
    |   Sub-Agents       |                      |    Sub-Agents       |
    +--------------------+                      +---------------------+
    | - CodingExplorer   |                      | - Researcher        |
    | - CodingPlanner    |                      | - GeneralPlanner    |
    | - BashRunner       |                      | - Summarizer        |
    | - TestRunner       |                      | - Brainstormer      |
    +--------------------+                      +---------------------+
```

---

## 1. BaseAgent Abstract Class

The base class provides core agent loop functionality without any domain-specific behavior.

### Core Responsibilities

```python
class BaseAgent(ABC):
    """Abstract base class for all agent types.

    Provides:
    - LLM provider integration
    - Event emission framework
    - Message history management
    - Token usage tracking
    - Context management and compaction
    - Tool execution loop
    """
```

### Shared State

| Property | Type | Description |
|----------|------|-------------|
| `provider` | `LLMProvider` | LLM backend (Claude, OpenAI, etc.) |
| `toolkit` | `BaseToolkit` | Abstract - subclasses provide specific toolkit |
| `emitter` | `AgentEventEmitter` | Event streaming for UI |
| `_messages` | `list[dict]` | Conversation history |
| `_total_input_tokens` | `int` | Token usage tracking |
| `_total_output_tokens` | `int` | Token usage tracking |
| `max_iterations` | `int` | Safety limit on iterations |
| `system_prompt` | `str` | Built from toolkit + domain-specific additions |

### Abstract Methods (Subclasses Must Implement)

```python
@abstractmethod
def _get_toolkit(self) -> BaseToolkit:
    """Return the toolkit appropriate for this agent type."""
    pass

@abstractmethod
def _build_system_prompt(self) -> str:
    """Build the system prompt for this agent type."""
    pass

@abstractmethod
def _get_available_subagents(self) -> dict[str, Type[BaseSubAgent]]:
    """Return dict of subagent_type -> SubAgent class."""
    pass
```

### Shared Methods

```python
# Core execution
def run(self, query: str, context: str = None, images: list = None) -> str
def chat(self, message: str, images: list = None) -> str

# Agent loop
def _run_loop(self, messages: list, tools: list) -> tuple[str, list]
def _execute_tools_parallel(self, parsed_calls: list) -> list

# Context management
def _check_context_overflow(self, messages: list) -> list
def _format_context_reminder(self) -> str

# Token tracking
def get_token_usage(self) -> dict

# Lifecycle
def reset(self) -> None
def close(self) -> None
```

---

## 2. CodingMainAgent

Full-featured coding assistant. This is the current `AgentRunner` with inheritance.

### CodingToolkit (Full Tool Set)

```python
class CodingToolkit(BaseToolkit):
    """Full toolkit for coding agents."""

    TOOLS = [
        # File Operations
        "read_file", "write_to_file", "delete_file", "apply_diff", "edit_file",

        # Search & Navigation
        "glob", "grep", "semantic_search", "list_files",

        # Execution
        "execute_command", "web",

        # Task Management
        "write_todo", "update_todo_list", "ask_choice_questions",
        "attempt_completion",

        # Planning
        "enter_plan_mode", "exit_plan", "write_plan",

        # Sub-agents
        "task", "task_output", "kill_task", "list_tasks",

        # Skills
        "skill", "list_skills",
    ]
```

### CodingMainAgent Sub-Agents

| Sub-Agent | Toolkit | Purpose |
|-----------|---------|---------|
| `CodingExplorer` | `ExploreToolkit` | Fast codebase navigation, file search |
| `CodingPlanner` | `PlanToolkit` | Architecture analysis, implementation planning |
| `BashRunner` | `BashToolkit` | Command execution specialist |
| `TestRunner` | `TestToolkit` | Test discovery and execution |

### Code-Specific Features

```python
class CodingMainAgent(BaseAgent):
    """Main agent for coding tasks."""

    def __init__(self, ...):
        super().__init__(...)
        self._checkpoint_manager = checkpoint_manager
        self._plan_mode = False

    # Code-specific methods
    def _create_checkpoint(self) -> None
    def _handle_plan_mode(self, result: ToolResult) -> None
    def _validate_file_operations(self, tool_calls: list) -> None
```

---

## 3. CoworkerAgent

General-purpose assistant without coding capabilities. Focused on research, brainstorming, planning (non-code), and collaboration.

### CoworkerToolkit (Non-Coding Tool Set)

```python
class CoworkerToolkit(BaseToolkit):
    """Toolkit for general-purpose coworker agents."""

    TOOLS = [
        # Research (Read-Only)
        "web_search", "web_fetch", "read_document",

        # Task Management
        "write_todo", "update_todo_list", "ask_choice_questions",

        # Memory/Context
        "save_note", "recall_notes", "summarize",

        # Collaboration
        "ask_clarification", "present_options",

        # Sub-agents
        "task", "task_output",
    ]
```

### CoworkerAgent Sub-Agents

| Sub-Agent | Toolkit | Purpose |
|-----------|---------|---------|
| `Researcher` | `ResearchToolkit` | Web research, document analysis |
| `GeneralPlanner` | `PlannerToolkit` | Non-code project planning |
| `Summarizer` | `SummaryToolkit` | Document/conversation summarization |
| `Brainstormer` | `BrainstormToolkit` | Idea generation, creative thinking |

### Coworker-Specific Features

```python
class CoworkerAgent(BaseAgent):
    """General-purpose coworker agent without coding capabilities."""

    def __init__(self,
                 personality: str = "helpful_professional",
                 domain_context: str = None,
                 ...):
        super().__init__(...)
        self._personality = personality
        self._domain_context = domain_context
        self._notes: list[dict] = []  # In-session memory

    # Coworker-specific methods
    def _inject_personality(self) -> str
    def _handle_research_request(self, query: str) -> str
    def brainstorm(self, topic: str, constraints: list = None) -> list[str]
    def summarize_conversation(self) -> str
```

---

## 4. BaseSubAgent Abstract Class

Sub-agents also need a base class for consistency.

```python
class BaseSubAgent(ABC):
    """Abstract base class for sub-agents."""

    def __init__(
        self,
        repo_root: Path,
        emitter: AgentEventEmitter = None,
        model: str = None,
        max_turns: int = 10,
        thoroughness: str = "medium",
    ):
        self.repo_root = repo_root
        self.emitter = emitter
        self.max_turns = max_turns
        self.thoroughness = thoroughness
        self.toolkit = self._get_toolkit()
        self.provider = get_provider(model or DEFAULT_MODEL)
        self.system_prompt = self._build_system_prompt()

    @abstractmethod
    def _get_toolkit(self) -> BaseToolkit:
        """Return the toolkit for this sub-agent."""
        pass

    @abstractmethod
    def _build_system_prompt(self) -> str:
        """Build the system prompt for this sub-agent."""
        pass

    def run(self, prompt: str) -> SubAgentResult:
        """Execute the sub-agent task."""
        # Common execution loop (from InProcessSubAgent)
        ...
```

### Sub-Agent Implementations

```python
# Coding sub-agents
class CodingExplorer(BaseSubAgent):
    """Explore codebases efficiently."""
    def _get_toolkit(self) -> ExploreToolkit
    def _build_system_prompt(self) -> str  # Uses EXPLORE_PROMPT

class CodingPlanner(BaseSubAgent):
    """Design implementation plans for code changes."""
    def _get_toolkit(self) -> PlanToolkit
    def _build_system_prompt(self) -> str  # Uses PLAN_PROMPT

# Coworker sub-agents
class Researcher(BaseSubAgent):
    """Research topics from web and documents."""
    def _get_toolkit(self) -> ResearchToolkit
    def _build_system_prompt(self) -> str  # Uses RESEARCH_PROMPT

class GeneralPlanner(BaseSubAgent):
    """Plan non-code projects and workflows."""
    def _get_toolkit(self) -> GeneralPlanToolkit
    def _build_system_prompt(self) -> str  # Uses GENERAL_PLAN_PROMPT
```

---

## 5. Toolkit Hierarchy

```
BaseToolkit (abstract)
├── CodingToolkit (full: read, write, execute, search)
│   ├── ExploreToolkit (read-only: search, glob, grep, read)
│   ├── PlanToolkit (read-only: same as Explore)
│   ├── BashToolkit (execute_command only)
│   └── TestToolkit (test execution tools)
│
└── CoworkerToolkit (no file ops: web, notes, collaboration)
    ├── ResearchToolkit (web_search, web_fetch, summarize)
    ├── GeneralPlanToolkit (notes, planning, no code)
    ├── SummaryToolkit (summarization focused)
    └── BrainstormToolkit (idea generation tools)
```

### Tool Registration Pattern

```python
class ExploreToolkit(BaseToolkit):
    """Read-only exploration toolkit."""

    TOOLS = ["read_file", "glob", "grep", "semantic_search", "list_files"]

    def _register_tools(self) -> None:
        """Register exploration tools."""
        self.register_tool(ReadFileTool(repo_root=self.repo_root))
        self.register_tool(GlobTool(repo_root=self.repo_root))
        self.register_tool(GrepTool(repo_root=self.repo_root))
        self.register_tool(SemanticSearchTool(repo_root=self.repo_root))
        self.register_tool(ListFilesTool(repo_root=self.repo_root))
```

---

## 6. Configuration & Instantiation

### Agent Factory

```python
class AgentFactory:
    """Factory for creating agents with appropriate configuration."""

    @staticmethod
    def create_coding_agent(
        model: str = DEFAULT_MODEL,
        repo_root: Path = None,
        emitter: AgentEventEmitter = None,
        **kwargs
    ) -> CodingMainAgent:
        """Create a coding-focused main agent."""
        return CodingMainAgent(
            model=model,
            repo_root=repo_root or Path.cwd(),
            emitter=emitter,
            **kwargs
        )

    @staticmethod
    def create_coworker_agent(
        model: str = DEFAULT_MODEL,
        personality: str = "helpful_professional",
        domain_context: str = None,
        emitter: AgentEventEmitter = None,
        **kwargs
    ) -> CoworkerAgent:
        """Create a general-purpose coworker agent."""
        return CoworkerAgent(
            model=model,
            personality=personality,
            domain_context=domain_context,
            emitter=emitter,
            **kwargs
        )
```

### CLI Integration

```python
# In CLI, user selects agent type
agent_type = config.get("agent_type", "coding")

if agent_type == "coding":
    agent = AgentFactory.create_coding_agent(
        model=selected_model,
        repo_root=Path.cwd(),
        emitter=event_emitter,
    )
elif agent_type == "coworker":
    agent = AgentFactory.create_coworker_agent(
        model=selected_model,
        personality=config.get("personality", "helpful_professional"),
        domain_context=config.get("domain_context"),
        emitter=event_emitter,
    )
```

---

## 7. Prompt Architecture

### Base Prompt Template

```python
BASE_AGENT_PROMPT = """You are an AI assistant.

## Communication Style
- Be concise and direct
- Use markdown formatting
- Avoid unnecessary verbosity

## Tool Usage
{tool_section}

## Available Sub-Agents
{subagent_section}
"""
```

### CodingMainAgent Prompt

```python
CODING_AGENT_PROMPT = BASE_AGENT_PROMPT + """

## Your Role
You are a senior software engineer helping with coding tasks.

## File Operations
- Always read files before modifying
- Never introduce security vulnerabilities
- Follow existing code conventions

## Planning
- Use plan mode for complex multi-step changes
- Break down large tasks into manageable steps

{rules_section}
{skills_section}
"""
```

### CoworkerAgent Prompt

```python
COWORKER_AGENT_PROMPT = BASE_AGENT_PROMPT + """

## Your Role
You are a helpful {personality} assistant.
{domain_context}

## Capabilities
- Research topics using web search
- Analyze documents and summarize information
- Help plan projects and organize tasks
- Brainstorm ideas and solutions

## Limitations
- You cannot modify files or execute code
- Focus on research, planning, and collaboration

## Style
{personality_traits}
"""
```

---

## 8. Implementation Plan

### Phase 1: Extract BaseAgent
1. Create `base_agent.py` with `BaseAgent` abstract class
2. Extract common functionality from `AgentRunner`:
   - Message management
   - Token tracking
   - Event emission
   - Tool execution loop
   - Context management
3. Make `AgentRunner` inherit from `BaseAgent`
4. Verify all tests pass

### Phase 2: Create BaseSubAgent
1. Create `base_subagent.py` with `BaseSubAgent` abstract class
2. Refactor `InProcessSubAgent` to inherit from `BaseSubAgent`
3. Create specific sub-agent classes:
   - `CodingExplorer`
   - `CodingPlanner`
4. Update `get_toolkit()` to use class-based lookup

### Phase 3: Create CodingMainAgent
1. Rename/refactor `AgentRunner` to `CodingMainAgent`
2. Move coding-specific logic:
   - Checkpoint management
   - Plan mode handling
   - File operation validation
3. Implement `_get_toolkit()` -> `CodingToolkit`
4. Implement `_get_available_subagents()`

### Phase 4: Create CoworkerAgent
1. Create `CoworkerToolkit` with non-coding tools:
   - `web_search` (existing)
   - `web_fetch` (existing)
   - `save_note` (new)
   - `recall_notes` (new)
   - `summarize` (new)
2. Create `CoworkerAgent` class
3. Create coworker sub-agents:
   - `Researcher`
   - `GeneralPlanner`
   - `Summarizer`
   - `Brainstormer`
4. Create coworker-specific prompts

### Phase 5: Integration & Testing
1. Create `AgentFactory` for instantiation
2. Update CLI to support agent type selection
3. Add configuration options
4. Write comprehensive tests
5. Update documentation

---

## 9. File Structure

```
packages/core/emdash_core/agent/
├── base/
│   ├── __init__.py
│   ├── base_agent.py          # BaseAgent abstract class
│   └── base_subagent.py       # BaseSubAgent abstract class
│
├── coding/
│   ├── __init__.py
│   ├── main_agent.py          # CodingMainAgent
│   ├── toolkit.py             # CodingToolkit
│   ├── prompts.py             # Coding-specific prompts
│   └── subagents/
│       ├── __init__.py
│       ├── explorer.py        # CodingExplorer
│       ├── planner.py         # CodingPlanner
│       ├── bash_runner.py     # BashRunner
│       └── test_runner.py     # TestRunner
│
├── coworker/
│   ├── __init__.py
│   ├── main_agent.py          # CoworkerAgent
│   ├── toolkit.py             # CoworkerToolkit
│   ├── prompts.py             # Coworker-specific prompts
│   └── subagents/
│       ├── __init__.py
│       ├── researcher.py      # Researcher
│       ├── planner.py         # GeneralPlanner
│       ├── summarizer.py      # Summarizer
│       └── brainstormer.py    # Brainstormer
│
├── tools/                      # Shared tools
│   ├── base.py
│   ├── file_ops.py            # File operation tools (coding only)
│   ├── search.py              # Search tools
│   ├── web.py                 # Web tools
│   ├── notes.py               # Note-taking tools (new)
│   └── collaboration.py       # Collaboration tools (new)
│
├── toolkits/
│   ├── __init__.py
│   ├── base.py                # BaseToolkit
│   ├── coding/                # Coding toolkits
│   │   ├── main.py
│   │   ├── explore.py
│   │   └── plan.py
│   └── coworker/              # Coworker toolkits
│       ├── main.py
│       ├── research.py
│       └── brainstorm.py
│
├── factory.py                  # AgentFactory
└── runner/                     # Keep for backwards compat, delegates to coding/
```

---

## 10. Backwards Compatibility

To maintain backwards compatibility:

1. Keep `AgentRunner` as an alias:
```python
# In agent/runner/__init__.py
from ..coding.main_agent import CodingMainAgent as AgentRunner
```

2. Keep `InProcessSubAgent` functional:
```python
# In agent/inprocess_subagent.py
def run_subagent(...):
    """Backwards-compatible function."""
    # Use the new class-based approach internally
    subagent_class = get_subagent_class(subagent_type)
    agent = subagent_class(...)
    return agent.run(prompt)
```

3. Maintain existing toolkit registration:
```python
TOOLKIT_REGISTRY = {
    "Explore": "emdash_core.agent.coding.subagents.explorer:CodingExplorer",
    "Plan": "emdash_core.agent.coding.subagents.planner:CodingPlanner",
    # ... etc
}
```

---

## 11. Example Usage

### Coding Agent (Current Behavior)

```python
from emdash_core.agent import AgentFactory

# Create coding agent
agent = AgentFactory.create_coding_agent(
    model="claude-opus-4-20250514",
    repo_root=Path("/path/to/project"),
)

# Use for coding tasks
response = agent.run("Implement a user authentication system")
```

### Coworker Agent (New)

```python
from emdash_core.agent import AgentFactory

# Create coworker agent for marketing team
agent = AgentFactory.create_coworker_agent(
    model="claude-opus-4-20250514",
    personality="creative_collaborator",
    domain_context="You are helping a marketing team plan product launches",
)

# Use for non-coding tasks
response = agent.run("Research our competitors' recent product launches and summarize key trends")
response = agent.run("Help me brainstorm 10 taglines for our new product")
response = agent.run("Create a project plan for the Q3 marketing campaign")
```

---

## 12. Future Extensions

This architecture enables:

1. **Domain-Specific Agents**: Legal, medical, financial coworkers with specialized tools
2. **Custom Sub-Agents**: Users can create agents in `.emdash/agents/` that inherit from `BaseSubAgent`
3. **Hybrid Agents**: Agents that combine coding and non-coding capabilities for specific use cases
4. **Agent Composition**: Main agents that delegate to multiple specialized sub-agents
5. **Agent SDK Migration**: Clean path to Anthropic Agent SDK when ready

---

## Appendix: Tool Categories

### Coding-Only Tools
- `write_to_file`, `delete_file`, `apply_diff`, `edit_file`
- `execute_command`
- `enter_plan_mode`, `exit_plan`, `write_plan`
- `skill`, `list_skills`

### Shared Tools (Both Agent Types)
- `read_file` (coding) / `read_document` (coworker)
- `web_search`, `web_fetch`
- `write_todo`, `update_todo_list`
- `ask_choice_questions`
- `task`, `task_output`

### Coworker-Only Tools
- `save_note`, `recall_notes`
- `summarize`
- `brainstorm_ideas`
- `compare_options`
