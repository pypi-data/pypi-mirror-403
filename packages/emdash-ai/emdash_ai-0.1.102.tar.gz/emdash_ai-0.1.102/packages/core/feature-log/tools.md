# Tools System

This document explains the tools available to the agent, how they are registered, and how MCP (Model Context Protocol) integration works.

## Overview

The agent has access to **35+ built-in tools** across multiple categories, plus the ability to load additional tools dynamically via MCP servers.

---

## 1. Built-in Tools

### Search Tools (Category: SEARCH)

**Location**: `agent/tools/search.py`

| Tool | Line | Purpose |
|------|------|---------|
| `semantic_search` | 10 | Natural language code search using embeddings |
| `text_search` | 111 | Exact text matching in code |
| `grep` | 205 | Fast ripgrep-based file content search |
| `glob` | 311 | File path pattern matching (e.g., `**/*.py`) |

### Traversal Tools (Category: TRAVERSAL)

**Location**: `agent/tools/traversal.py`

| Tool | Purpose |
|------|---------|
| `expand_node` | Get node context and relationships |
| `get_callers` | Find functions that call a given function |
| `get_callees` | Find functions called by a given function |
| `get_class_hierarchy` | Explore class inheritance tree |
| `get_file_dependencies` | Find file import dependencies |
| `get_impact_analysis` | Analyze impact of changes |
| `get_neighbors` | Get adjacent nodes in the graph |

### Analytics Tools (Category: ANALYTICS)

**Location**: `agent/tools/analytics.py`

| Tool | Line | Purpose |
|------|------|---------|
| `get_area_importance` | 9 | Code area metrics and importance scores |
| `get_top_pagerank` | 118 | PageRank metrics for code elements |
| `get_communities` | 266 | Community detection in code graph |
| `get_community_members` | 367 | Get members of a detected community |

### File Operations Tools (Category: PLANNING)

**Location**: `agent/tools/coding.py`

| Tool | Line | Purpose |
|------|------|---------|
| `read_file` | 55 | Read file contents (with optional line range) |
| `write_to_file` | 149 | Write content to a file |
| `edit_file` | 241 | Edit specific sections of a file |
| `apply_diff` | 364 | Apply unified diff patches |
| `delete_file` | 576 | Delete a file |
| `list_files` | 628 | List directory contents |
| `execute_command` | 717 | Run shell commands |

### LSP Tools (Language Server Protocol)

**Location**: `agent/tools/lsp.py`

| Tool | Line | Purpose |
|------|------|---------|
| `lsp_find_definition` | 26 | Go to definition |
| `lsp_find_references` | 113 | Find all references |
| `lsp_rename_symbol` | 207 | Rename across codebase |
| `lsp_get_diagnostics` | 301 | Get errors and warnings |

### GitHub/MCP Tools (Category: HISTORY)

**Location**: `agent/tools/github_mcp.py`

| Tool | Line | Purpose |
|------|------|---------|
| `github_search_code` | 85 | Search code on GitHub |
| `github_get_file_content` | 148 | Get file from GitHub |
| `github_pr_details` | 204 | Get PR details |
| `github_list_prs` | 254 | List pull requests |
| `github_search_repos` | 314 | Search repositories |
| `github_search_prs` | 358 | Search pull requests |
| `github_get_issue` | 421 | Get issue details |
| `github_view_repo_structure` | 471 | View repo file tree |
| `github_create_review` | 530 | Create PR review |

### Planning/State Tools

**Location**: `agent/tools/modes.py`

| Tool | Line | Purpose |
|------|------|---------|
| `enter_plan_mode` | 77 | Enter planning mode |
| `exit_plan_mode` | 170 | Exit planning mode |
| `get_mode` | 276 | Get current agent mode |

### Other Tools

| Tool | Purpose |
|------|---------|
| `write_todo` | Create/update todo items |
| `update_todo_list` | Batch update todos |
| `ask_choice_questions` | Ask user multiple choice |
| `attempt_completion` | Signal task completion |
| `plan_exploration` | Plan exploration strategy |
| `skill` | Execute a loaded skill |
| `list_skills` | List available skills |
| `web` | Web access tool |

---

## 2. Tool Architecture

### Base Tool Class

**Location**: `agent/tools/base.py:68`

```python
class BaseTool(ABC):
    """Abstract base class for all tools."""

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        pass

    def get_schema(self) -> dict:
        """Return OpenAI function calling schema."""
        pass
```

### ToolResult

**Location**: `agent/tools/base.py:20`

Standardized return type for all tools:

```python
@dataclass
class ToolResult:
    success: bool
    data: Any = None
    error: Optional[str] = None
    suggestions: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def success_result(cls, data, **metadata):
        return cls(success=True, data=data, metadata=metadata)

    @classmethod
    def error_result(cls, error, suggestions=None):
        return cls(success=False, error=error, suggestions=suggestions)
```

### Tool Categories

**Location**: `agent/tools/base.py:9`

```python
class ToolCategory(Enum):
    SEARCH = "search"
    TRAVERSAL = "traversal"
    ANALYTICS = "analytics"
    HISTORY = "history"
    PLANNING = "planning"
```

---

## 3. Toolkit System

### BaseToolkit

**Location**: `agent/toolkits/base.py`

Toolkits group tools and manage their lifecycle:

```python
class BaseToolkit(ABC):
    def _register_tools(self):
        """Register tools available in this toolkit."""
        pass

    def execute(self, tool_name: str, **params) -> ToolResult:
        """Execute a tool by name."""
        tool = self.get_tool(tool_name)
        return tool.execute(**params)

    def get_all_schemas(self) -> List[dict]:
        """Get OpenAI schemas for all registered tools."""
        pass
```

### Built-in Toolkits

**Location**: `agent/toolkits/__init__.py:18-23`

```python
TOOLKIT_REGISTRY: Dict[str, str] = {
    "Explore": "emdash_core.agent.toolkits.explore:ExploreToolkit",
    "Plan": "emdash_core.agent.toolkits.plan:PlanToolkit",
}
```

### ExploreToolkit (Read-only)

**Location**: `agent/toolkits/explore.py:28-34`

Safe, read-only exploration tools:
- `read_file`
- `list_files`
- `glob`
- `grep`
- `semantic_search`

### PlanToolkit

**Location**: `agent/toolkits/plan.py:34-40`

Same tools as ExploreToolkit, used by Plan sub-agent.

---

## 4. MCP (Model Context Protocol) Integration

MCP provides a standardized way to add dynamic tools from external servers.

### Configuration

**Location**: `agent/mcp/config.py`

MCP servers are configured in `.emdash/mcp.json`:

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@anthropic/github-mcp-server"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      },
      "enabled": false
    },
    "emdash-graph": {
      "command": "emdash-graph-mcp",
      "args": [],
      "env": {
        "EMDASH_GRAPH_DB_PATH": "${EMDASH_GRAPH_DB_PATH}"
      },
      "enabled": false
    }
  }
}
```

### MCPServerConfig

**Location**: `agent/mcp/config.py:18`

```python
@dataclass
class MCPServerConfig:
    name: str
    command: str
    args: List[str]
    env: Dict[str, str]
    enabled: bool = False
    timeout: int = 30
```

Features:
- Environment variable resolution: `${VAR}` syntax
- Special handling for `GITHUB_TOKEN`, `EMDASH_GRAPH_DB_PATH`

### MCP Server Manager

**Location**: `agent/mcp/manager.py:19`

Manages MCP server lifecycle:

```python
class MCPServerManager:
    def start_server(self, name: str):
        """Start a specific MCP server."""
        pass

    def start_all_enabled(self):
        """Start all enabled servers."""
        pass

    def call_tool(self, tool_name: str, arguments: dict):
        """Execute a tool on an MCP server."""
        pass

    def get_all_tools(self) -> List[MCPToolInfo]:
        """List all available tools from all servers."""
        pass
```

### MCP Client (JSON-RPC)

**Location**: `agent/mcp/client.py:60`

Low-level MCP protocol implementation:

```python
class GenericMCPClient:
    def start(self):
        """Start MCP server subprocess."""
        pass

    def list_tools(self) -> List[MCPToolInfo]:
        """Get available tools from server."""
        pass

    def call_tool(self, name: str, arguments: dict) -> MCPResponse:
        """Execute tool via JSON-RPC."""
        pass
```

### Dynamic Tool Factory

**Location**: `agent/mcp/tool_factory.py:16`

Wraps MCP tools as native BaseTool instances:

```python
class MCPDynamicTool(BaseTool):
    """Bridges MCP tools to native agent toolkit."""

    def execute(self, **kwargs) -> ToolResult:
        response = self.manager.call_tool(self.tool_name, kwargs)
        return ToolResult.success_result(response.content)
```

Factory function:

```python
def create_tools_from_mcp(manager: MCPServerManager) -> List[BaseTool]:
    """Create BaseTool wrappers for all MCP server tools."""
    pass
```

### MCP in Toolkits

**Location**: `agent/toolkits/base.py:55-106`

Toolkits initialize MCP servers automatically:

1. Filter to enabled servers
2. Create MCPServerManager
3. Start all enabled servers
4. Create tool wrappers via `create_tools_from_mcp()`
5. Register tools in toolkit

---

## 5. Default MCP Servers

**Location**: `packages/cli/.emdash/mcp.json`

| Server | Purpose | Default |
|--------|---------|---------|
| `github` | GitHub API operations | disabled |
| `emdash-graph` | Graph database traversal | disabled |
| `cclsp` | Code Language Server Protocol | disabled |

### Graph MCP Server

**Location**: `packages/graph-mcp/emdash_graph_mcp/server.py`

Exposes 12 graph traversal and analytics tools:
- `expand_node`, `get_callers`, `get_callees`
- `get_class_hierarchy`, `get_file_dependencies`
- `get_impact_analysis`, `get_neighbors`
- `get_area_importance`, `get_top_pagerank`
- `get_communities`, `get_community_members`

---

## 6. Tool Execution Flow

```
Agent
  └── Toolkit.execute(tool_name, **params)
        └── BaseTool.execute(**kwargs)
              └── Returns ToolResult
```

### From Agent Runner

**Location**: `agent/runner/agent_runner.py`

1. LLM requests tool call with name and parameters
2. Agent runner calls `toolkit.execute(tool_name, **params)`
3. Toolkit looks up tool and calls `tool.execute(**params)`
4. Tool returns `ToolResult`
5. Result is formatted and sent back to LLM

### Tool Schema Generation

Tools provide OpenAI function calling schemas:

```python
{
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Read file contents",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path"},
                "start_line": {"type": "integer"},
                "end_line": {"type": "integer"}
            },
            "required": ["path"]
        }
    }
}
```

---

## 7. MCP Management Command

**Location**: `packages/cli/emdash_cli/commands/agent/handlers/mcp.py`

The `/mcp` command provides:
- Interactive server list with toggle
- Edit config in editor
- Server enable/disable via keyboard navigation

---

## Key Files Reference

| Component | File |
|-----------|------|
| Tool Base | `agent/tools/base.py` |
| All Tools Export | `agent/tools/__init__.py` |
| Toolkit Base | `agent/toolkits/base.py` |
| Explore Toolkit | `agent/toolkits/explore.py` |
| Toolkit Registry | `agent/toolkits/__init__.py` |
| MCP Config | `agent/mcp/config.py` |
| MCP Manager | `agent/mcp/manager.py` |
| MCP Client | `agent/mcp/client.py` |
| MCP Tool Factory | `agent/mcp/tool_factory.py` |
| Graph MCP Server | `packages/graph-mcp/emdash_graph_mcp/server.py` |
| Default MCP Config | `packages/cli/.emdash/mcp.json` |
