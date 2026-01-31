# System Prompt Building

This document explains how system prompts are constructed, what gets loaded into them, and how agent spawning works.

## Overview

The system prompt is built dynamically from multiple components:
1. **Base prompt** - Core instructions and workflow patterns
2. **Tools section** - Available tools grouped by category
3. **Session context** - Repository info, branch, git status
4. **Agents section** - Built-in and custom agents
5. **Rules section** - Project-specific guidelines
6. **Skills section** - Loaded skill definitions

---

## 1. System Prompt Building Workflow

### Main Builder Function

**Location**: `agent/prompts/main_agent.py:35-69`

```python
def build_system_prompt(toolkit) -> str:
    """Build the complete system prompt with dynamic tool descriptions."""
    tools_section = build_tools_section(toolkit)
    agents_section = build_agents_section(toolkit)
    skills_section = build_skills_section()
    rules_section = build_rules_section()
    session_section = build_session_context_section(toolkit)

    prompt = BASE_SYSTEM_PROMPT.format(tools_section=tools_section)

    # Add sections in order
    if session_section:
        prompt += "\n" + session_section
    if agents_section:
        prompt += "\n" + agents_section
    if rules_section:
        prompt += "\n" + rules_section
    if skills_section:
        prompt += "\n" + skills_section

    return prompt
```

### Assembly Order

1. **BASE_SYSTEM_PROMPT** - Core orchestrator instructions with `{tools_section}` placeholder
2. **Session Context** - Git repository state
3. **Agents Section** - Available sub-agents
4. **Rules Section** - Project guidelines
5. **Skills Section** - Skill definitions

---

## 2. Base System Prompt Components

**Location**: `agent/prompts/main_agent.py:28` and `agent/prompts/workflow.py`

The base prompt includes workflow patterns:

| Pattern | Purpose |
|---------|---------|
| `EXPLORATION_DECISION_RULES` | Binary gate decision framework |
| `WORKFLOW_PATTERNS` | Complex task workflow steps |
| `EXPLORATION_STRATEGY` | Multi-step exploration approach |
| `PARALLEL_EXECUTION` | Parallel tool execution guidance |
| `VERIFICATION_AND_CRITIQUE` | Quality assurance checks |
| `OUTPUT_GUIDELINES` | Expected output format |

---

## 3. Tools Section

**Location**: `agent/prompts/main_agent.py:173-244`

Tools are dynamically grouped by category:
- Search & Discovery
- Graph Traversal
- Analytics
- Planning
- History
- Other

Each tool entry includes:
- Tool name
- First sentence of description (cleaned, MCP prefixes removed)

---

## 4. Session Context Section

**Location**: `agent/prompts/main_agent.py:72-114`

Injected when in a git repository:

```markdown
## Session Context

Repository: {repo_name}
Branch: {current_branch}
Working Directory: {cwd}

Git Status:
{git_status}
```

---

## 5. Rules Loading and Injection

### Rules Source

Rules are loaded from: `.emdash/rules/*.md` files

### Rules Loader

**Location**: `agent/rules.py:13-59`

```python
def load_rules(rules_dir: Optional[Path] = None) -> str:
    """Load rules from .emdash/rules/ directory."""
    if rules_dir is None:
        rules_dir = Path.cwd() / ".emdash" / "rules"

    if not rules_dir.exists():
        return ""

    rules_parts = []

    # Load all .md files in sorted order
    for md_file in sorted(rules_dir.glob("*.md")):
        content = md_file.read_text().strip()
        if content:
            rules_parts.append(content)

    return "\n\n---\n\n".join(rules_parts)
```

### Rules Formatting

**Location**: `agent/rules.py:103-123`

Wraps rules in a section:

```markdown
## Project Guidelines

The following rules and guidelines should be followed:

{rules_content}
```

### Agent-Specific Rules

**Location**: `agent/rules.py:62-100`

Function `get_rules_for_agent()` can load:
1. General rules from `*.md`
2. Agent-specific rules from `{agent_name}.md`

---

## 6. Skills Section

**Location**: `agent/skills.py`

Skills are loaded from:
1. Built-in skills bundled with emdash_core
2. User repo skills in `.emdash/skills/`

The `SkillRegistry` class manages skill loading and formatting for prompt injection.

---

## 7. Agent Spawning

### TaskTool - Spawning Entry Point

**Location**: `agent/tools/task.py:21-181`

```python
class TaskTool(BaseTool):
    """Spawn a sub-agent to handle complex, multi-step tasks autonomously."""

    def execute(
        self,
        description: str = "",
        prompt: str = "",
        subagent_type: str = "Explore",
        model_tier: str = "fast",
        max_turns: int = 10,
        run_in_background: bool = False,
        resume: Optional[str] = None,
        thoroughness: str = "medium",
    ) -> ToolResult:
```

### In-Process Sub-Agent Runner

**Location**: `agent/inprocess_subagent.py:53-137`

```python
class InProcessSubAgent:
    """Sub-agent that runs in the same process."""

    def __init__(
        self,
        subagent_type: str,
        repo_root: Path,
        emitter=None,
        model: Optional[str] = None,
        max_turns: int = 10,
        agent_id: Optional[str] = None,
        thoroughness: str = "medium",
    ):
        # Get toolkit for agent type
        self.toolkit = get_toolkit(subagent_type, repo_root)

        # Get system prompt for this agent type
        base_prompt = get_subagent_prompt(subagent_type, repo_root=repo_root)
        self.system_prompt = self._inject_thoroughness(base_prompt)
```

### Sub-Agent Prompt Retrieval

**Location**: `agent/prompts/subagents.py:210-253`

```python
def get_subagent_prompt(subagent_type: str, repo_root=None) -> str:
    """Get the system prompt for a sub-agent type."""

    # Check built-in agents first
    if subagent_type in SUBAGENT_PROMPTS:
        return SUBAGENT_PROMPTS[subagent_type]

    # Check custom agents
    custom_agent = get_custom_agent(subagent_type, repo_root)
    if custom_agent:
        prompt_parts = [custom_agent.system_prompt]

        # Inject rules if specified
        if custom_agent.rules:
            rules_content = _load_rules_by_names(custom_agent.rules, repo_root)
            if rules_content:
                prompt_parts.append(f"\n\n## Rules\n\n{rules_content}")

        # Inject skills if specified
        if custom_agent.skills:
            skills_content = _load_skills_by_names(custom_agent.skills, repo_root)
            if skills_content:
                prompt_parts.append(f"\n\n## Skills\n\n{skills_content}")

        return "".join(prompt_parts)
```

---

## 8. Built-in Sub-Agents

**Location**: `agent/prompts/subagents.py:15-201`

| Agent | Lines | Purpose | Tools |
|-------|-------|---------|-------|
| **Explore** | 16-78 | Read-only codebase exploration | glob, grep, read_file, list_files, semantic_search |
| **Plan** | 81-153 | Software architecture design | Same as Explore |
| **Bash** | 156-174 | Command execution | bash |
| **Research** | 177-193 | Documentation research | web tools |

### Toolkit Registry

**Location**: `agent/toolkits/__init__.py:45-91`

```python
TOOLKIT_REGISTRY: Dict[str, str] = {
    "Explore": "emdash_core.agent.toolkits.explore:ExploreToolkit",
    "Plan": "emdash_core.agent.toolkits.plan:PlanToolkit",
}
```

Custom agents use `ExploreToolkit` by default.

---

## 9. Thoroughness Injection

**Location**: `agent/inprocess_subagent.py:112-136`

Sub-agents receive thoroughness guidance:

| Level | Behavior |
|-------|----------|
| `quick` | Basic searches, most obvious matches first |
| `medium` | Moderate exploration, check multiple locations |
| `thorough` | Comprehensive analysis across codebase |

```python
def _inject_thoroughness(self, prompt: str) -> str:
    """Inject thoroughness level into the system prompt."""
    thoroughness_guidance = {
        "quick": "Do basic searches only...",
        "medium": "Do moderate exploration...",
        "thorough": "Do comprehensive analysis...",
    }
    return prompt + "\n" + guidance
```

---

## 10. Custom Agents

**Location**: `agent/agents.py:104-150`

Custom agents are loaded from `.emdash/agents/*.md` with frontmatter:

```yaml
---
description: Agent description
model: claude-3-5-sonnet
tools:
  - read_file
  - glob
mcp_servers:
  - server_name
rules:
  - rule_name
skills:
  - skill_name
---

# System Prompt Content

Your custom system prompt here...
```

---

## Key Files Reference

| Component | File | Key Function |
|-----------|------|--------------|
| Main Builder | `prompts/main_agent.py` | `build_system_prompt()` |
| Tools Section | `prompts/main_agent.py` | `build_tools_section()` |
| Session Context | `prompts/main_agent.py` | `build_session_context_section()` |
| Rules Loading | `rules.py` | `load_rules()` |
| Rules Formatting | `rules.py` | `format_rules_for_prompt()` |
| Sub-Agent Spawning | `tools/task.py` | `TaskTool` class |
| In-Process Runner | `inprocess_subagent.py` | `InProcessSubAgent` class |
| Sub-Agent Prompts | `prompts/subagents.py` | `get_subagent_prompt()` |
| Toolkit Registry | `toolkits/__init__.py` | `get_toolkit()` |
| Custom Agents | `agents.py` | `load_agents()` |
| Skills Registry | `skills.py` | `SkillRegistry` class |
