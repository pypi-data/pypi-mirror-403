# Anthropic Agent SDK Integration Plan for emdash

## Executive Summary

This document outlines a strategy for integrating the Anthropic Agent SDK into emdash's agent architecture. The integration is significantly simplified by the fact that **Skills and MCP are natively supported** in the Agent SDK, meaning emdash can leverage these features directly rather than maintaining custom implementations.

### Key Insight: Native Support Simplifies Integration

| Feature | emdash Current | Agent SDK Native | Migration Path |
|---------|----------------|------------------|----------------|
| **Skills** | Custom `.emdash/skills/` | Native `.claude/skills/` | Migrate skill files, use `setting_sources` |
| **MCP** | Custom `MCP Manager` | Native `mcp_servers` option | Direct integration, keep Graph MCP |
| **Tools** | Custom `BaseTool` | Built-in + `@tool` decorator | Use SDK built-ins, wrap custom tools |
| **Sub-agents** | Custom `SubAgentRunner` | Native `AgentDefinition` | Use SDK agents config |

---

## 1. Current Architecture Analysis

### emdash Agent Stack

```
┌─────────────────────────────────────────────────────────────┐
│                     REST API / CLI                          │
├─────────────────────────────────────────────────────────────┤
│                     AgentRunner                             │
│  - Main execution loop                                      │
│  - Context management & token tracking                      │
│  - Plan mode support                                        │
│  - Checkpoint management                                    │
├─────────────────────────────────────────────────────────────┤
│                     AgentToolkit                            │
│  - Tool registry (~17 native tools)                         │
│  - MCP dynamic tools                                        │
│  - Mode-specific filtering                                  │
├─────────────────────────────────────────────────────────────┤
│                     LLMProvider                             │
│  - OpenAI-compatible API wrapper                            │
│  - Multi-provider: OpenAI, Anthropic, Fireworks            │
│  - Extended thinking support                                │
├─────────────────────────────────────────────────────────────┤
│                     Event System                            │
│  - SSE streaming                                            │
│  - Real-time UI updates                                     │
└─────────────────────────────────────────────────────────────┘
```

### Key emdash Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `AgentRunner` | `packages/core/emdash_core/agent/runner/agent_runner.py` | Main execution loop |
| `AgentToolkit` | `packages/core/emdash_core/agent/toolkit.py` | Tool registry & dispatch |
| `LLMProvider` | `packages/core/emdash_core/agent/providers/` | LLM abstraction |
| `EventEmitter` | `packages/core/emdash_core/agent/events.py` | Streaming events |
| `MCP Manager` | `packages/core/emdash_core/agent/mcp/` | External tool integration |

### emdash Unique Features to Preserve

1. **Plan/Code Mode Workflow** - Two-phase approach for complex tasks
2. **Semantic Search** - Natural language code search with embeddings
3. **Graph MCP Server** - Code dependency analysis (PageRank, community detection)
4. **Sub-agent Orchestration** - In-process and subprocess agents
5. **Skills System** - Markdown-based skill definitions
6. **Research Agents** - Multi-agent deep research system

---

## 2. Anthropic Agent SDK Overview

### SDK Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              query() / ClaudeSDKClient                      │
├─────────────────────────────────────────────────────────────┤
│                 Claude Code CLI (bundled)                   │
├─────────────────────────────────────────────────────────────┤
│              Claude API (native Anthropic)                  │
├─────────────────────────────────────────────────────────────┤
│                    MCP Servers                              │
│  - In-process SDK servers (@tool decorator)                 │
│  - External stdio/http servers                              │
└─────────────────────────────────────────────────────────────┘
```

### Key SDK Features

| Feature | Description |
|---------|-------------|
| `query()` | Simple async function for one-off queries |
| `ClaudeSDKClient` | Bidirectional client with custom tools/hooks |
| `@tool` decorator | In-process MCP server tools |
| `create_sdk_mcp_server()` | Create MCP servers from Python functions |
| Hooks | Intercept `PreToolUse`, `PostToolUse`, `UserPromptSubmit`, etc. |
| Permission modes | `default`, `acceptEdits`, `plan`, `bypassPermissions` |

### SDK Types

```python
# Core types
ClaudeAgentOptions     # Configuration options
AssistantMessage       # Claude responses
ToolUseBlock          # Tool invocations
HookMatcher           # Hook configuration

# MCP server configs
McpStdioServerConfig  # External subprocess servers
McpSdkServerConfig    # In-process SDK servers
```

### Native Skills Support

The SDK natively supports Agent Skills - the same system used in Claude.ai and Claude Code:

```python
from claude_agent_sdk import query, ClaudeAgentOptions

options = ClaudeAgentOptions(
    cwd="/path/to/project",
    # Enable Skills from filesystem
    setting_sources=["user", "project"],
    # Allow the Skill tool
    allowed_tools=["Skill", "Read", "Write", "Bash"]
)

async for message in query(prompt="Help me with this task", options=options):
    print(message)
```

**Skill Locations:**
- **Project Skills**: `.claude/skills/` - shared via git
- **User Skills**: `~/.claude/skills/` - personal skills

**Skill Format (SKILL.md):**
```markdown
---
name: my-skill
description: What this skill does and when to use it
---

# Instructions

[Detailed instructions Claude follows when skill is active]
```

### Native MCP Support

The SDK has full MCP support with multiple server types:

```python
from claude_agent_sdk import tool, create_sdk_mcp_server, ClaudeAgentOptions

# 1. In-process SDK MCP server (recommended for custom tools)
@tool("semantic_search", "Search code semantically", {"query": str})
async def semantic_search(args):
    results = await run_semantic_search(args["query"])
    return {"content": [{"type": "text", "text": results}]}

sdk_server = create_sdk_mcp_server(
    name="emdash",
    version="1.0.0",
    tools=[semantic_search]
)

# 2. External stdio server (for existing MCP servers like graph-mcp)
options = ClaudeAgentOptions(
    mcp_servers={
        "emdash": sdk_server,              # In-process
        "graph": {                          # External
            "type": "stdio",
            "command": "python",
            "args": ["-m", "emdash_graph_mcp.server"]
        }
    },
    allowed_tools=[
        "mcp__emdash__semantic_search",
        "mcp__graph__expand_node",
    ]
)
```

---

## 3. Integration Strategy

### Recommended Approach: SDK-First with Native Features

Given the native support for Skills and MCP, we recommend a **simplified SDK-first approach**:

1. **Use SDK as primary runtime** - Replace `AgentRunner` with `ClaudeSDKClient`
2. **Leverage native Skills** - Migrate `.emdash/skills/` to `.claude/skills/`
3. **Keep Graph MCP** - Use SDK's native external MCP support
4. **Wrap unique tools** - Only wrap emdash-specific tools (semantic search) as SDK MCP

### What We Can Delete (Native Support)

| Component | Reason to Delete |
|-----------|------------------|
| `emdash_core/agent/skills.py` | SDK has native Skills support |
| `emdash_core/agent/mcp/manager.py` | SDK handles MCP lifecycle |
| `emdash_core/agent/mcp/client.py` | SDK handles MCP communication |
| Custom tool implementations | Use SDK built-in: Read, Write, Bash, Glob, Grep |

### What We Keep (Unique Value)

| Component | Reason to Keep |
|-----------|----------------|
| `semantic_search` tool | Core differentiator, not in SDK |
| `graph-mcp` server | Unique code analysis features |
| Event bridge | UI/CLI streaming compatibility |
| Plan mode hooks | Workflow control via SDK hooks |

### Simplified Integration Phases

```
Phase 1: Direct SDK Usage      Phase 2: Skills Migration     Phase 3: Cleanup
─────────────────────────     ─────────────────────────     ──────────────────
Replace AgentRunner with      Move .emdash/skills/ to       Remove legacy code
ClaudeSDKClient               .claude/skills/               Delete MCP manager
Wrap semantic_search          Enable setting_sources        Simplify codebase
Keep graph-mcp as external    Test skill loading            Update docs
```

---

## 4. Phase 1: Direct SDK Usage

### 4.1 Replace AgentRunner with ClaudeSDKClient

Instead of wrapping the SDK in a provider, use it directly as the agent runtime.

**File:** `packages/core/emdash_core/agent/runner/sdk_runner.py`

```python
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    tool,
    create_sdk_mcp_server,
    AssistantMessage,
    TextBlock,
    ToolUseBlock,
    HookMatcher,
)
from ..events import AgentEventEmitter, EventType


class SDKAgentRunner:
    """Agent runner using Anthropic Agent SDK directly."""

    def __init__(
        self,
        model: str = "claude-sonnet-4-20250514",
        cwd: str | None = None,
        emitter: AgentEventEmitter | None = None,
    ):
        self.model = model
        self.cwd = cwd
        self.emitter = emitter
        self._emdash_server = self._create_emdash_mcp_server()

    def _create_emdash_mcp_server(self):
        """Create in-process MCP server for emdash-specific tools."""

        @tool("semantic_search", "Search code using natural language", {"query": str, "limit": int})
        async def semantic_search(args):
            # Import your existing semantic search implementation
            from emdash_core.search import run_semantic_search
            results = await run_semantic_search(args["query"], limit=args.get("limit", 10))
            return {"content": [{"type": "text", "text": results}]}

        return create_sdk_mcp_server(
            name="emdash",
            version="1.0.0",
            tools=[semantic_search]
        )

    def _get_options(self, system_prompt: str | None = None) -> ClaudeAgentOptions:
        """Build SDK options with native features."""

        return ClaudeAgentOptions(
            model=self.model,
            cwd=self.cwd,
            system_prompt=system_prompt,

            # Native Skills support
            setting_sources=["user", "project"],

            # Native MCP support
            mcp_servers={
                "emdash": self._emdash_server,     # In-process (semantic search)
                "graph": {                          # External (graph analysis)
                    "type": "stdio",
                    "command": "python",
                    "args": ["-m", "emdash_graph_mcp.server"]
                }
            },

            # Allow SDK built-in tools + our custom tools
            allowed_tools=[
                # SDK built-ins (no need to implement!)
                "Read", "Write", "Bash", "Glob", "Grep", "Skill",
                # emdash custom tools
                "mcp__emdash__semantic_search",
                # Graph MCP tools
                "mcp__graph__expand_node",
                "mcp__graph__get_callers",
                "mcp__graph__get_callees",
            ],

            # Plan mode via SDK's native permission mode
            permission_mode="acceptEdits",
        )

    async def run(self, prompt: str, system_prompt: str | None = None):
        """Execute agent with SDK."""

        options = self._get_options(system_prompt)

        async with ClaudeSDKClient(options=options) as client:
            await client.query(prompt)

            async for message in client.receive_response():
                await self._process_message(message)

    async def _process_message(self, message):
        """Bridge SDK messages to emdash event system."""

        if self.emitter is None:
            return

        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    await self.emitter.emit(EventType.PARTIAL_RESPONSE, {"text": block.text})
                elif isinstance(block, ToolUseBlock):
                    await self.emitter.emit(EventType.TOOL_START, {
                        "tool": block.name,
                        "input": block.input
                    })
```

### 4.2 Usage Example

```python
from emdash_core.agent.runner.sdk_runner import SDKAgentRunner
from emdash_core.agent.events import AgentEventEmitter, RichConsoleHandler

async def main():
    emitter = AgentEventEmitter()
    emitter.add_handler(RichConsoleHandler())

    runner = SDKAgentRunner(
        model="claude-sonnet-4-20250514",
        cwd="/path/to/project",
        emitter=emitter
    )

    await runner.run("Find all authentication functions and explain how they work")
```

### 4.3 What This Gives Us For Free

With this approach, we get these features **without implementing them**:

| Feature | SDK Provides | emdash Implementation Deleted |
|---------|--------------|-------------------------------|
| File reading | `Read` tool | `read_file` tool |
| File writing | `Write` tool | `write_file` tool |
| Shell execution | `Bash` tool | `execute_command` tool |
| File search | `Glob` tool | `glob` tool |
| Content search | `Grep` tool | `grep` tool |
| Skills | `Skill` tool | Custom skills loader |
| MCP management | Native | `MCP Manager` |
| Context tracking | Native | Token counter |
| Permission handling | Native | Custom permission system |

---

## 5. Phase 2: Skills Migration

### 5.1 Migrate Skills to Native Format

Move skills from `.emdash/skills/` to `.claude/skills/` using the standard Agent Skills format.

**Before (emdash format):**
```
.emdash/
└── skills/
    └── code-review/
        └── SKILL.md
```

**After (SDK native format):**
```
.claude/
└── skills/
    └── code-review/
        └── SKILL.md
```

### 5.2 Skill Format Compatibility

The good news: emdash's skill format is already compatible with SDK's native format!

**Both use the same YAML frontmatter + markdown structure:**

```markdown
---
name: code-review
description: Performs thorough code reviews following best practices
---

# Code Review Skill

## Guidelines
- Check for security vulnerabilities
- Verify error handling
- Review naming conventions

## Process
1. Read the file to review
2. Analyze against guidelines
3. Provide actionable feedback
```

### 5.3 Migration Script

**File:** `scripts/migrate_skills.py`

```python
#!/usr/bin/env python3
"""Migrate emdash skills to SDK native format."""

import shutil
from pathlib import Path

def migrate_skills(project_root: Path):
    """Move skills from .emdash/ to .claude/"""

    emdash_skills = project_root / ".emdash" / "skills"
    claude_skills = project_root / ".claude" / "skills"

    if not emdash_skills.exists():
        print("No .emdash/skills/ directory found")
        return

    # Create .claude/skills/ if needed
    claude_skills.mkdir(parents=True, exist_ok=True)

    # Copy each skill directory
    for skill_dir in emdash_skills.iterdir():
        if skill_dir.is_dir():
            dest = claude_skills / skill_dir.name
            if dest.exists():
                print(f"Skill {skill_dir.name} already exists in .claude/skills/, skipping")
                continue
            shutil.copytree(skill_dir, dest)
            print(f"Migrated skill: {skill_dir.name}")

    print("\nMigration complete!")
    print("You can now delete .emdash/skills/ if no longer needed")

if __name__ == "__main__":
    migrate_skills(Path.cwd())
```

### 5.4 Enable Skills in SDK Runner

Update the SDK runner to load skills:

```python
options = ClaudeAgentOptions(
    cwd="/path/to/project",

    # Enable native Skills loading
    setting_sources=["user", "project"],

    # Allow Skill tool
    allowed_tools=["Skill", "Read", "Write", "Bash", ...],
)
```

**Skill locations after migration:**
- **Project Skills**: `.claude/skills/` - committed to git, shared with team
- **User Skills**: `~/.claude/skills/` - personal, not committed

---

## 6. Phase 3: Advanced Integration

### 6.1 Hook System for Plan Mode

Use SDK hooks to implement emdash's Plan/Code mode workflow:

```python
async def plan_mode_hook(input_data, tool_use_id, context):
    """Control tool access based on plan mode."""

    tool_name = input_data["tool_name"]
    current_mode = get_current_mode()  # plan or code

    if current_mode == "plan":
        # Restrict to read-only tools in plan mode
        write_tools = ["write_file", "apply_diff", "delete_file", "execute_command"]
        if tool_name in write_tools:
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": "Write operations not allowed in plan mode",
                }
            }
    return {}

options = ClaudeAgentOptions(
    hooks={
        "PreToolUse": [
            HookMatcher(hooks=[plan_mode_hook]),
        ],
    }
)
```

### 6.2 Sub-Agent Migration

Convert `InProcessSubAgent` and `SubAgentRunner` to use SDK's native session forking:

```python
# SDK-native sub-agent spawning
options = ClaudeAgentOptions(
    agents={
        "explore": AgentDefinition(
            description="Fast code exploration agent",
            prompt="Explore the codebase to answer questions",
            tools=["mcp__emdash__semantic_search", "mcp__emdash__grep"],
            model="haiku"
        ),
        "plan": AgentDefinition(
            description="Software architect agent",
            prompt="Design implementation plans",
            tools=["mcp__emdash__*", "mcp__graph__*"],
            model="sonnet"
        ),
    },
    fork_session=True  # Enable session forking for sub-agents
)
```

### 6.3 Event System Bridge

Create an event bridge to map SDK messages to emdash events:

```python
from claude_agent_sdk import AssistantMessage, ToolUseBlock, ResultMessage
from emdash_core.agent.events import EventType, AgentEventEmitter

class SDKEventBridge:
    """Bridge SDK messages to emdash event system."""

    def __init__(self, emitter: AgentEventEmitter):
        self.emitter = emitter

    async def process_message(self, message):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    await self.emitter.emit(EventType.PARTIAL_RESPONSE, {
                        "text": block.text
                    })
                elif isinstance(block, ToolUseBlock):
                    await self.emitter.emit(EventType.TOOL_START, {
                        "tool": block.name,
                        "input": block.input
                    })

        elif isinstance(message, ResultMessage):
            await self.emitter.emit(EventType.SESSION_END, {
                "duration_ms": message.duration_ms,
                "cost_usd": message.total_cost_usd,
            })
```

---

## 7. Architecture After Integration

```
┌─────────────────────────────────────────────────────────────┐
│                     REST API / CLI                          │
├─────────────────────────────────────────────────────────────┤
│                  AgentRunner (Updated)                      │
│  - Uses AgentSDKProvider for Claude models                  │
│  - Maintains context/token tracking                         │
│  - Plan mode via SDK hooks                                  │
├─────────────────────────────────────────────────────────────┤
│                   SDK Layer                                 │
│  ┌─────────────────────┐  ┌─────────────────────────────┐  │
│  │  ClaudeSDKClient    │  │  Hooks                      │  │
│  │  - Native Claude    │  │  - PreToolUse (plan mode)   │  │
│  │  - Extended think   │  │  - PostToolUse (logging)    │  │
│  └─────────────────────┘  └─────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                   MCP Servers                               │
│  ┌─────────────────────┐  ┌─────────────────────────────┐  │
│  │  emdash-tools       │  │  graph-mcp                  │  │
│  │  (SDK in-process)   │  │  (External stdio)           │  │
│  │  - semantic_search  │  │  - expand_node              │  │
│  │  - grep, glob       │  │  - get_callers              │  │
│  │  - read/write_file  │  │  - get_communities          │  │
│  └─────────────────────┘  └─────────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                   Event Bridge                              │
│  - Maps SDK messages to emdash EventType                    │
│  - SSE streaming to UI                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. Implementation Roadmap

### Phase 1: Direct SDK Usage

- [ ] Add `claude-agent-sdk>=0.1.19` to dependencies
- [ ] Create `SDKAgentRunner` class using `ClaudeSDKClient`
- [ ] Wrap `semantic_search` as SDK MCP tool
- [ ] Configure Graph MCP as external server
- [ ] Basic integration tests

### Phase 2: Skills Migration

- [ ] Create skills migration script
- [ ] Move `.emdash/skills/` to `.claude/skills/`
- [ ] Enable `setting_sources` in SDK options
- [ ] Test skill loading and invocation
- [ ] Update documentation

### Phase 3: Workflow Integration

- [ ] Implement Plan mode via SDK hooks
- [ ] Create event bridge for UI/CLI streaming
- [ ] Migrate sub-agents to SDK `AgentDefinition`
- [ ] End-to-end testing

### Phase 4: Cleanup & Optimization

- [ ] Delete legacy implementations:
  - `emdash_core/agent/skills.py`
  - `emdash_core/agent/mcp/manager.py`
  - `emdash_core/agent/mcp/client.py`
  - Redundant tool implementations
- [ ] Update API endpoints to use SDK runner
- [ ] Performance benchmarking
- [ ] User migration guide

---

## 9. Key Considerations

### Benefits of SDK Integration

1. **Native Claude Access** - Direct API access without OpenAI-compatible wrapper
2. **Extended Thinking** - Native support for Claude's thinking mode
3. **In-Process MCP** - No subprocess overhead for custom tools
4. **Hooks System** - Powerful interception points for workflow control
5. **Future-Proof** - Official SDK with ongoing Anthropic support

### Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Breaking existing workflows | Gradual migration, provider abstraction |
| Performance regression | Benchmark before/after, optimize event bridge |
| Feature parity gap | Map all emdash features to SDK equivalents |
| SDK instability | Pin versions, thorough testing |

### Backwards Compatibility

- Existing `model` parameter continues to work
- Add `sdk:` prefix for explicit SDK usage
- Environment variable toggle for default behavior
- Deprecation warnings for legacy APIs

---

## 10. Dependencies

### New Dependencies

```toml
# pyproject.toml
[project.dependencies]
claude-agent-sdk = ">=0.1.19"
anyio = ">=4.0.0"  # SDK requirement
```

### Version Requirements

- Python: 3.10+
- claude-agent-sdk: 0.1.19+
- Bundled Claude CLI: 2.1.1+

---

## 11. Testing Strategy

### Unit Tests

```python
# tests/agent/providers/test_agent_sdk_provider.py

async def test_basic_query():
    provider = AgentSDKProvider(model="claude-sonnet-4-20250514")
    response = await provider.chat([
        {"role": "user", "content": "What is 2+2?"}
    ])
    assert "4" in response.content

async def test_tool_execution():
    provider = AgentSDKProvider()
    response = await provider.chat(
        messages=[{"role": "user", "content": "Read test.py"}],
        tools=[{"name": "read_file", ...}]
    )
    assert len(response.tool_calls) > 0
```

### Integration Tests

- Plan mode workflow with SDK hooks
- Sub-agent spawning via SDK agents
- Event streaming through bridge
- MCP tool invocation

---

## 12. References

### SDK Documentation
- [Claude Agent SDK GitHub](https://github.com/anthropics/claude-agent-sdk-python)
- [Agent SDK Overview](https://platform.claude.com/docs/en/agent-sdk/overview)
- [Agent Skills in the SDK](https://platform.claude.com/docs/en/agent-sdk/skills)
- [MCP in the SDK](https://platform.claude.com/docs/en/agent-sdk/mcp)

### Skills Resources
- [Agent Skills GitHub](https://github.com/anthropics/skills)
- [Agent Skills Standard](https://agentskills.io)
- [Building Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)

### emdash Internal
- [emdash Agent Architecture](../architecture/agent-system.md)
