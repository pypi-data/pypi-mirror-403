# EmDash - Graph-Based Coding Intelligence System

> "The Senior Engineer Context Engine" - An AI-powered code intelligence platform that builds a knowledge graph of your codebase to provide intelligent code exploration, generation, and analysis.

## Overview

EmDash is a sophisticated multi-agent code intelligence system that combines:
- **Knowledge Graph**: Code structure stored in a graph database (Kuzu)
- **Multi-Layer Indexing**: AST parsing, git history, and GitHub PRs
- **Specialized Agents**: Explore, Plan, Research, and Code agents
- **MCP Integration**: Model Context Protocol for tool extensibility
- **SSE Streaming**: Real-time updates for all operations

### Core Philosophy

EmDash treats codebase understanding as a graph problem. Instead of treating code as flat text, it:
1. Parses code into entities (functions, classes, modules)
2. Creates relationships (calls, imports, inherits)
3. Uses graph algorithms (PageRank, community detection) for insights
4. Provides semantic search via embeddings

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          EMDASH ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                        CLI LAYER (Python)                        │   │
│  │  em / emdash command-line interface with TUI                     │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                  │                                      │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      API CLIENT (httpx)                          │   │
│  │  HTTP/SSE client communicating with server                        │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                  │                                      │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                  CORE SERVER (FastAPI + Python)                 │   │
│  │                                                                  │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │   │
│  │  │  API Routes │  │  Agent      │  │  Session Management     │  │   │
│  │  │  - /chat    │  │  Orchestrator│ │  - History              │  │   │
│  │  │  - /search  │  │  - Runner   │  │  - Checkpoints          │  │   │
│  │  │  - /index   │  │  - Hooks    │  │  - Continuity           │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────┘  │   │
│  │                                                                  │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │   │
│  │  │   Graph     │  │   Context   │  │  Skills & Rules Engine  │  │   │
│  │  │  Database   │  │   Service   │  │  - Custom agents        │  │   │
│  │  │  (Kuzu)     │  │   - Rerank  │  │  - Skills              │  │   │
│  │  │  - Nodes    │  │   - Longevity│ │  - Rules              │  │   │
│  │  │  - Edges    │  │   - Session │  │  - Hooks               │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────┘  │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                  │                                      │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    TYPE-SCRIPT PACKAGES                          │   │
│  │                                                                  │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌─────────────────────┐  │   │
│  │  │   client-ts   │  │   core-ts      │  │  desktop (Electron) │  │   │
│  │  │  TypeScript   │  │  TypeScript   │  │  GUI application    │  │   │
│  │  │  API client   │  │  Agent system  │  │  (in development)   │  │   │
│  │  └────────────────┘  └────────────────┘  └─────────────────────┘  │   │
│  │                                                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Component Layers

```
┌──────────────────────────────────────────────────────────────┐
│  LAYER 1: User Interface                                      │
│  ├── CLI (em/emdash commands)                                 │
│  ├── TUI (Textual-based rich interface)                       │
│  └── TypeScript Client (@emdash/client)                        │
├──────────────────────────────────────────────────────────────┤
│  LAYER 2: API Gateway                                         │
│  ├── FastAPI server on port 8765                             │
│  ├── SSE streaming for all agent operations                   │
│  └── CORS for Electron/web clients                           │
├──────────────────────────────────────────────────────────────┤
│  LAYER 3: Agent System                                        │
│  ├── Main Agent (full-featured coding)                        │
│  ├── Explore Agent (read-only research)                       │
│  ├── Plan Agent (design & architecture)                       │
│  ├── Bash Agent (shell execution)                             │
│  └── Sub-agents (specialized tasks)                          │
├──────────────────────────────────────────────────────────────┤
│  LAYER 4: Context Engine                                      │
│  ├── Session Context (conversation memory)                    │
│  ├── Reranking (relevance scoring)                            │
│  ├── Longevity (context persistence)                          │
│  └── Context Providers (explored/touched areas)               │
├──────────────────────────────────────────────────────────────┤
│  LAYER 5: Knowledge Graph                                     │
│  ├── Kuzu Graph Database (optional)                           │
│  ├── Code Structure (Layer A: AST parsing)                    │
│  ├── Git History (Layer B: commits, changes)                  │
│  └── GitHub PRs (Layer C: reviews, discussions)              │
├──────────────────────────────────────────────────────────────┤
│  LAYER 6: Ingestion Pipeline                                  │
│  ├── Language Parsers (Python, TypeScript, etc.)               │
│  ├── Change Detection (git diff)                              │
│  └── Community Detection (Louvain algorithm)                  │
├──────────────────────────────────────────────────────────────┤
│  LAYER 7: Embeddings & Vector Store                            │
│  ├── OpenAI/Fireworks embeddings                              │
│  ├── In-memory vector store                                   │
│  └── Semantic code search                                      │
└──────────────────────────────────────────────────────────────┘
```

---

## Main Components

### 1. emdash-core (Python)

**Location**: `packages/core/`

FastAPI server containing all business logic.

**Key Modules**:

| Module | Purpose |
|--------|---------|
| `emdash_core/agent/` | Multi-agent system with hooks, prompts, and runners |
| `emdash_core/api/` | REST API endpoints (FastAPI routes) |
| `emdash_core/graph/` | Knowledge graph with Kuzu DB |
| `emdash_core/context/` | Session-based context and reranking |
| `emdash_core/ingestion/` | Code parsing and indexing |
| `emdash_core/embeddings/` | Vector embeddings service |
| `emdash_core/mcp/` | Model Context Protocol client |
| `emdash_core/auth/` | GitHub OAuth authentication |
| `emdash_core/swarm/` | Multi-agent parallel execution |

**Key Files**:

```python
# Server entry point
packages/core/emdash_core/server.py          # FastAPI app creation

# Agent system
packages/core/emdash_core/agent/agents.py    # Agent implementations
packages/core/emdash_core/agent/runner.py    # Agent execution loop
packages/core/emdash_core/agent/hooks.py     # Event hooks system
packages/core/emdash_core/agent/prompts/     # System prompts

# Graph database
packages/core/emdash_core/graph/connection.py # Kuzu DB connection
packages/core/emdash_core/graph/schema.py     # Node/edge schemas
packages/core/emdash_core/graph/writer.py    # Graph building
packages/core/emdash_core/graph/queries.py    # Graph traversal

# API routes
packages/core/emdash_core/api/routes/chat.py       # Agent chat
packages/core/emdash_core/api/routes/index.py     # Indexing
packages/core/emdash_core/api/routes/search.py     # Search
packages/core/emdash_core/api/routes/swarm.py      # Parallel tasks
```

### 2. emdash-cli (Python)

**Location**: `packages/cli/`

Command-line interface for the EmDash system.

**Key Modules**:

| Module | Purpose |
|--------|---------|
| `emdash_cli/commands/` | CLI command groups (agent, db, auth, etc.) |
| `emdash_cli/client.py` | HTTP client for server communication |
| `emdash_cli/sse_renderer.py` | SSE streaming with TUI rendering |
| `emdash_cli/design.py` | UI styling and themes |
| `emdash_cli/server_manager.py` | Server lifecycle management |

**Commands**:

```bash
em              # Start the AI coding agent
emdash index    # Index codebase into knowledge graph
emdash auth     # GitHub OAuth authentication
emdash search   # Semantic code search
emdash registry # Browse community skills/rules
emdash agent    # Interactive agent REPL
emdash server   # Server management
```

**Slash Commands** (inside agent REPL):

| Category | Commands |
|----------|-----------|
| Mode | `/plan`, `/code`, `/mode` |
| Generation | `/projectmd`, `/research`, `/pr` |
| Status | `/status`, `/context`, `/compact` |
| Tasks | `/todos`, `/todo-add` |
| Session | `/session save`, `/session load`, `/reset` |
| Config | `/agents`, `/rules`, `/skills`, `/hooks`, `/mcp` |
| Verification | `/verify`, `/verify-loop` |

### 3. core-ts (TypeScript)

**Location**: `packages/core-ts/`

TypeScript implementation of the agent system with Vercel AI SDK.

**Project Structure**:

```
packages/core-ts/src/
├── agent/
│   ├── runner.ts              # AgentRunner with tool loop
│   ├── subagent.ts            # SubAgentRunner
│   ├── client.ts              # AI SDK provider setup
│   ├── custom-agent.ts        # Custom agent loading
│   ├── agents/                # Agent configurations
│   │   ├── main.ts            # Main coding agent
│   │   ├── explore.ts         # Read-only exploration
│   │   ├── plan.ts            # Planning agent
│   │   └── bash.ts            # Shell execution
│   ├── tools/                 # Tool definitions
│   │   ├── coding.ts          # File operations
│   │   ├── search.ts          # grep, glob
│   │   ├── shell.ts           # execute_command
│   │   ├── task.ts            # Sub-agent spawning
│   │   ├── modes.ts           # Mode switching
│   │   └── skills.ts          # Skill system
│   └── prompts/               # Prompt templates
├── api/
│   ├── router.ts              # Hono router
│   └── agent.ts               # POST /agent/chat
├── swarm/
│   ├── worktree-manager.ts    # Git worktree lifecycle
│   ├── task-runner.ts         # Parallel execution
│   └── types.ts               # Swarm types
├── embeddings/
│   ├── service.ts            # Embedding generation
│   ├── store.ts               # Vector storage
│   └── providers/             # OpenAI, Fireworks
├── mcp/
│   ├── client.ts              # MCP JSON-RPC client
│   ├── manager.ts             # Server lifecycle
│   └── tool-factory.ts         # Tool conversion
├── graph/
│   ├── connection.ts          # Kuzu connection
│   ├── schema.ts              # Graph schema
│   └── queries.ts             # Graph queries
└── context/
    ├── service.ts             # Context management
    └── reranker.ts            # Relevance reranking
```

### 4. client-ts (TypeScript)

**Location**: `packages/sdk-ts/`

TypeScript client library for the emdash-core API.

**Features**:

```typescript
// Server management
const server = new ServerManager({ port: 8765 });
await server.start();

// Agent chat with SSE streaming
const result = await client.agentChat(
  { message: 'Find authentication code' },
  {
    callbacks: {
      onThinking: (e) => console.log('Thinking:', e.content),
      onToolStart: (e) => console.log('Tool:', e.tool_name),
      onResponse: (e) => console.log('Response:', e.content),
    },
  }
);

// Project generation
await client.generateProjectMd({ output: 'PROJECT.md' });

// Deep research
await client.research({ goal: 'Analyze auth patterns' });

// Code review
await client.review({ pr_number: 123, verdict: true });
```

---

## Data Flow

### Agent Chat Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    AGENT CHAT FLOW                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. USER INPUT                                                   │
│     ┌─────────┐                                                  │
│     │ "Fix login bug" │                                        │
│     └────┬────┘                                                  │
│          │                                                       │
│          ▼                                                       │
│  2. CONTEXT RETRIEVAL                                            │
│     ┌────────────────────────────────────────────┐              │
│     │ Session Context:                          │              │
│     │ - Explored areas (from context providers) │              │
│     │ - Touched files (recent modifications)    │              │
│     │ - Reranked code entities                  │              │
│     │ - Conversation history                   │              │
│     └────────────────────┬───────────────────────┘              │
│                          │                                       │
│                          ▼                                       │
│  3. TOOL EXECUTION LOOP                                          │
│     ┌────────────────────────────────────────┐                 │
│     │ FOR each iteration:                    │                 │
│     │   1. Build system prompt               │                 │
│     │   2. Call LLM with message + tools      │                 │
│     │   3. Get tool calls from LLM          │                 │
│     │   4. Execute tools (with hooks)        │                 │
│     │   5. Return results to LLM            │                 │
│     │   6. If response, break               │                 │
│     └────────────────────────────────────────┘                 │
│                          │                                       │
│                          ▼                                       │
│  4. SSE STREAMING                                                │
│     ┌────────────────────────────────────────┐                 │
│     │ Event types streamed:                  │                 │
│     │ - session_start: { session_id }       │                 │
│     │ - thinking: { content }                │                 │
│     │ - tool_start: { tool_name, input }     │                 │
│     │ - tool_result: { tool_name, result }  │                 │
│     │ - partial_response: { content, delta }│                 │
│     │ - session_end: { summary }            │                 │
│     └────────────────────────────────────────┘                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Indexing Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    INDEXING FLOW                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. PARSE CODE (Layer A: AST)                                    │
│     ┌────────────────────────────────────────┐                 │
│     │ Language Parsers:                     │                 │
│     │ - Python (astroid)                     │                 │
│     │ - TypeScript (tree-sitter)             │                 │
│     │ Extracts:                              │                 │
│     │ - Files, Functions, Classes             │                 │
│     │ - Imports, Calls                      │                 │
│     │ - Inheritance, Decorators              │                 │
│     └────────────────────────────────────────┘                 │
│                          │                                       │
│                          ▼                                       │
│  2. GIT HISTORY (Layer B - optional)                             │
│     ┌────────────────────────────────────────┐                 │
│     │ GitPython:                             │                 │
│     │ - Commits, branches                    │                 │
│     │ - Modified files per commit           │                 │
│     │ - Author information                   │                 │
│     └────────────────────────────────────────┘                 │
│                          │                                       │
│                          ▼                                       │
│  3. GITHUB PRS (Layer C - optional)                              │
│     ┌────────────────────────────────────────┐                 │
│     │ PyGitHub:                              │                 │
│     │ - PR titles, descriptions              │                 │
│     │ - Code changes                        │                 │
│     │ - Reviews, comments                   │                 │
│     └────────────────────────────────────────┘                 │
│                          │                                       │
│                          ▼                                       │
│  4. GRAPH CONSTRUCTION                                           │
│     ┌────────────────────────────────────────┐                 │
│     │ Kuzu Graph:                           │                 │
│     │ - Create nodes (File, Func, Class)    │                 │
│     │ - Create edges (CALLS, IMPORTS, etc.) │                 │
│     │ - Build call graph                    │                 │
│     │ - Create import graph                 │                 │
│     └────────────────────────────────────────┘                 │
│                          │                                       │
│                          ▼                                       │
│  5. COMMUNITY DETECTION                                          │
│     ┌────────────────────────────────────────┐                 │
│     │ Louvain Algorithm:                    │                 │
│     │ - Detect code modules/communities     │                 │
│     │ - Calculate modularity                │                 │
│     │ - Optionally describe with LLM        │                 │
│     └────────────────────────────────────────┘                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Session Continuity Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                 SESSION CONTINUITY FLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Session Start:                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │ New Session │───▶│ Load Context│───▶│ Init Agent  │         │
│  │ (ID: abc)   │    │ from DB     │    │ Runner      │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│                                                              │
│  Session Continue:                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │ Session ID  │───▶│ Load From   │───▶│ Append To    │         │
│  │ Continue    │    │ Checkpoint  │    │ History     │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│                                                              │
│  Session End:                                               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │ Checkpoint  │───▶│ Save To     │───▶│ Return       │         │
│  │ Created     │    │ Git Branch  │    │ Summary      │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

### 1. Agent Modes

**Decision**: Separate "Plan Mode" from "Code Mode"

**Rationale**:
- Different mental models needed for exploration vs. implementation
- Plan mode encourages careful thinking without file modifications
- Code mode has full write access but with accountability
- Prevents accidental modifications during exploration

**Implementation**:
- `AgentMode` enum: `plan`, `code`, `explore`, `research`
- System prompts differ by mode
- Tool access restricted in explore mode

```python
# Plan mode prompt emphasizes analysis
PLANS_PROMPT = """You are in PLAN MODE. Your role is to:
1. Explore and understand the codebase structure
2. Design implementation plans with detailed steps
3. Consider edge cases and dependencies
4. Create documentation for the plan
DO NOT write production code - create plans only."""

# Code mode prompt enables modifications
CODE_PROMPT = """You are in CODE MODE. Your role is to:
1. Implement features and fix bugs
2. Read code to understand patterns
3. Make targeted file modifications
4. Verify your changes work correctly
You have full tool access for code changes."""
```

### 2. Context Engine with Session

**Decision**: Session-based context with reranking

**Rationale**:
- LLM context windows are limited
- Not all code is equally relevant
- Prioritize recently touched and explored files
- Allow context to "age out" naturally

**Implementation**:

```python
class SessionContextManager:
    """Manages conversation context with reranking."""

    def __init__(self):
        self._explored = ExploredAreasProvider()
        self._touched = TouchedAreasProvider()
        self._reranker = ContextReranker()

    async def get_context(
        self,
        query: str,
        max_items: int = 20
    ) -> list[ScoredContextItem]:
        """Get reranked context for a query."""

        # Gather candidates from providers
        candidates = await asyncio.gather(
            self._explored.get_recent(max=50),
            self._touched.get_recent(max=50),
        )

        # Rerank by relevance to query
        reranked = await self._reranker.rerank(
            query=query,
            items=flatten(candidates),
            max_items=max_items,
        )

        return reranked
```

### 3. Hook System for Extensibility

**Decision**: Event hooks for automation

**Rationale**:
- Users want custom actions at specific points
- Can't anticipate all use cases
- Simple YAML/JSON configuration
- Scriptability without core modifications

**Implementation**:

```yaml
# .emdash/hooks.yaml
hooks:
  - name: "Pre-commit lint"
    trigger: "tool_start"
    condition: "tool.name == 'execute_command' and 'lint' in tool.input"
    actions:
      - type: "shell"
        command: "echo 'Running linter...'"

  - name: "Auto-save checkpoint"
    trigger: "session_end"
    actions:
      - type: "checkpoint"
        create: true
        message: "Auto-save on session end"

  - name: "Notify on error"
    trigger: "error"
    condition: "error.severity == 'critical'"
    actions:
      - type: "notification"
        type: "slack"
        channel: "#dev-alerts"
```

### 4. MCP (Model Context Protocol)

**Decision**: MCP integration for tool extensibility

**Rationale**:
- Ecosystem-wide standard for tools
- Prevents tool duplication
- Enables third-party integrations
- Sandboxed execution per server

**Implementation**:

```json
// ~/.config/emdash/mcp.json
{
  "servers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"],
      "enabled": true
    },
    "github": {
      "command": "uvx",
      "args": ["mcp-server-github"],
      "env": {
        "GITHUB_PERSONAL_TOKEN": "${GITHUB_TOKEN}"
      },
      "enabled": true
    }
  }
}
```

### 5. Swarm for Parallel Tasks

**Decision**: Git worktree-based parallel execution

**Rationale**:
- Subtasks may conflict if in same branch
- Isolated environments prevent conflicts
- Automatic merge when all complete
- No manual branch management

**Implementation**:

```python
class SwarmRunner:
    """Runs tasks in parallel using git worktrees."""

    async def run(self, tasks: list[SwarmTask]) -> SwarmResult:
        manager = WorktreeManager(self.repo_root)
        await manager.init()

        # Create worktree for each task
        worktrees = []
        for task in tasks:
            wt = await manager.create_worktree(task)
            worktrees.append((task, wt))

        # Run all in parallel
        results = await asyncio.gather(
            *[self._run_in_worktree(task, wt) for task, wt in worktrees]
        )

        # Merge back
        for (task, wt), result in zip(worktrees, results):
            if result.status == "completed":
                await manager.merge_worktree(wt.id)

        await manager.cleanup()
        return merge_results(results)
```

### 6. Checkpointing with Git

**Decision**: Git-based session persistence

**Rationale**:
- Version control for context
- Shareable sessions via branches
- No external database needed
- Full history preserved

**Implementation**:

```python
class CheckpointManager:
    """Manages session checkpoints as git commits."""

    def create(self, message: str) -> Checkpoint:
        """Create checkpoint on current branch."""
        # Get current session state
        state = self._get_session_state()

        # Commit to branch
        self._git.add(".")
        self._git.commit(f"-m", f"emdash: {message}")

        # Return checkpoint metadata
        return Checkpoint(
            sha=self._git.revparse("HEAD"),
            timestamp=datetime.now(),
            message=message,
        )

    def restore(self, checkpoint: Checkpoint):
        """Restore from checkpoint."""
        self._git.checkout(checkpoint.sha)
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+ (for TypeScript packages)
- Git
- Poetry (Python package manager)

### Installation

```bash
# Method 1: Quick install (creates ~/.emdash)
curl -sSL "https://gist.githubusercontent.com/..." | bash

# Method 2: Development setup
git clone https://github.com/mendyEdri/emdash.dev.git
cd emdash.dev

# Install Python dependencies
uv sync

# Install TypeScript packages
cd packages/sdk-ts && npm install
cd ../core-ts && npm install

# Build TypeScript packages
cd packages/sdk-ts && npm run build
cd ../core-ts && npm run build
```

### Running

```bash
# Start the server (default port 8765)
emdash server start

# Or directly with Python
cd packages/core
uv run emdash-core --port 8765

# Start the agent
em "Fix the login bug"

# Index a repository
emdash index start /path/to/repo --with-git
```

### Environment Variables

```bash
# Required for LLM
export ANTHROPIC_API_KEY="claude-..."

# Optional
export OPENAI_API_KEY="sk-..."
export FIREWORKS_API_KEY="..."
export GITHUB_TOKEN="ghp_..."
```

### Configuration

```yaml
# ~/.config/emdash/config.yaml
server:
  host: "127.0.0.1"
  port: 8765

models:
  default: "claude-sonnet-4-20250514"
  planning: "claude-opus-4-20250514"
  fast: "claude-3-5-haiku-20241022"

features:
  enable_graph: true
  enable_embeddings: true
  enable_swarm: false
  max_iterations: 100

graph:
  path: "~/.emdash/graph/kuzu_db"
  detect_communities: true
```

---

## File Structure

```
emdash.dev/
├── .emdash/                    # Per-project configuration
│   ├── agents/                 # Custom agent definitions
│   │   └── *.md               # Agent YAML with system prompt
│   ├── rules/                  # Coding rules/guidelines
│   │   └── *.md               # Rule definitions
│   ├── skills/                 # Reusable skills
│   │   └── */SKILL.md         # Skill implementations
│   ├── sessions/              # Saved sessions
│   │   └── */session.json     # Session data
│   ├── hooks.json             # Event hooks config
│   └── mcp.json               # MCP server config
│
├── packages/
│   ├── core/                  # Python FastAPI server
│   │   ├── emdash_core/
│   │   │   ├── agent/         # Agent system
│   │   │   ├── api/           # REST API
│   │   │   ├── graph/         # Knowledge graph
│   │   │   ├── context/       # Session context
│   │   │   ├── embeddings/    # Vector embeddings
│   │   │   ├── ingestion/     # Code parsing
│   │   │   ├── mcp/           # MCP client
│   │   │   ├── swarm/         # Parallel execution
│   │   │   └── ...
│   │   ├── pyproject.toml
│   │   └── README.md
│   │
│   ├── core-ts/               # TypeScript agent system
│   │   ├── src/
│   │   │   ├── agent/         # Agent runner
│   │   │   ├── api/           # Hono routes
│   │   │   ├── swarm/         # Worktree manager
│   │   │   ├── embeddings/    # Embedding service
│   │   │   └── ...
│   │   ├── package.json
│   │   └── DESIGN.md
│   │
│   ├── cli/                   # Python CLI
│   │   ├── emdash_cli/
│   │   │   ├── commands/      # CLI commands
│   │   │   ├── client.py      # HTTP client
│   │   │   ├── sse_renderer.py# SSE rendering
│   │   │   └── design.py      # UI styling
│   │   ├── pyproject.toml
│   │   └── README.md
│   │
│   ├── client/               # TypeScript client library
│   │   ├── src/
│   │   │   ├── client.ts      # EmdashClient
│   │   │   ├── server.ts      # ServerManager
│   │   │   ├── sse.ts         # SSE handling
│   │   │   └── types/         # TypeScript types
│   │   ├── package.json
│   │   └── README.md
│   │
│   └── desktop/              # Electron desktop app (future)
│
├── .gitignore
├── package.json              # Root npm workspace
├── pyproject.toml            # Poetry workspace
├── README.md                 # Quick start guide
└── PROJECT.md                # This file
```

---

## Configuration File Reference

### Agent Configuration (`.emdash/agents/*.md`)

```yaml
---
name: "security-audit"
description: "Security-focused code reviewer"
model: "claude-opus-4-20250514"
mode: "explore"
max_iterations: 50
tools:
  - read_file
  - grep
  - glob
system_prompt: |
  You are a security expert reviewing code for:
  - SQL injection vulnerabilities
  - XSS patterns
  - Authentication bypasses
  - Sensitive data exposure

  Always provide specific file locations and code snippets.
```

### Rules Configuration (`.emdash/rules/*.md`)

```yaml
---
name: "python-best-practices"
description: "Python coding standards"
tags: ["python", "best-practices", "pydantic"]
rules:
  - "Use type hints for all function signatures"
  - "Prefer Pydantic models over dictionaries"
  - "Use async/await for I/O operations"
  - "Keep functions under 50 lines"
```

### Skills Configuration (`.emdash/skills/*/SKILL.md`)

```yaml
---
name: "frontend-design"
description: "Create production-grade frontend interfaces"
parameters:
  - name: "component_name"
    type: "string"
    required: true
  - name: "design_system"
    type: "string"
    default: "tailwind"
output: "Creates component file with proper styling"
```

### Hooks Configuration (`.emdash/hooks.json`)

```json
{
  "hooks": [
    {
      "name": "Lint on commit",
      "trigger": "tool_start",
      "condition": "tool.name == 'execute_command' and 'lint' in tool.args",
      "actions": [
        {
          "type": "shell",
          "command": "echo 'Running linter...'",
          "on": "start"
        }
      ]
    }
  ]
}
```

### MCP Configuration (`~/.config/emdash/mcp.json`)

```json
{
  "servers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"],
      "enabled": true
    },
    "github": {
      "command": "uvx",
      "args": ["mcp-server-github"],
      "env": {
        "GITHUB_PERSONAL_TOKEN": "${GITHUB_TOKEN}"
      },
      "enabled": true
    }
  }
}
```

---

## Graph Schema

### Nodes

| Type | Properties |
|------|------------|
| `File` | path, name, language, size, last_modified |
| `Function` | name, qualified_name, start_line, end_line, visibility |
| `Class` | name, qualified_name, start_line, end_line, base_classes |
| `Module` | name, path, package |
| `Import` | from_module, to_module, alias |
| `Commit` | sha, message, author, timestamp |
| `PR` | number, title, author, state, merged |

### Edges

| Source | Relationship | Target |
|--------|--------------|--------|
| `Class` | `INHERITS_FROM` | `Class` |
| `Function` | `CALLS` | `Function` |
| `File` | `IMPORTS` | `File` |
| `File` | `DEFINES` | `Function` |
| `File` | `DEFINES` | `Class` |
| `Commit` | `MODIFIES` | `File` |
| `PR` | `CONTAINS` | `Commit` |

---

## API Reference

### Core Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/agent/chat` | Start agent session (SSE) |
| `POST` | `/api/agent/chat/{id}/continue` | Continue session (SSE) |
| `GET` | `/api/agent/sessions` | List active sessions |
| `DELETE` | `/api/agent/sessions/{id}` | Delete session |
| `POST` | `/api/index/start` | Start indexing (SSE) |
| `GET` | `/api/index/status` | Get index status |
| `POST` | `/api/search` | Semantic code search |
| `POST` | `/api/query/expand` | Expand graph relationships |

### SSE Events

| Event | Payload |
|-------|---------|
| `session_start` | `{ session_id: string }` |
| `thinking` | `{ content: string }` |
| `tool_start` | `{ tool_name: string, input: object }` |
| `tool_result` | `{ tool_name: string, result: object }` |
| `partial_response` | `{ content: string, delta: string }` |
| `response` | `{ content: string }` |
| `session_end` | `{ summary: string, usage: object }` |
| `error` | `{ message: string, code: string }` |
| `warning` | `{ message: string }` |
| `clarification` | `{ question: string, options: string[] }` |

---

## Contributing

### Development Setup

```bash
# Clone repository
git clone https://github.com/mendyEdri/emdash.dev.git
cd emdash.dev

# Setup Python (uv)
uv sync

# Setup TypeScript
cd packages/core-ts && npm install
cd ../client && npm install

# Run tests
uv run pytest
cd packages/core-ts && npm run test

# Type check
cd packages/core-ts && npm run type-check
```

### Adding New Tools

1. Define tool in `packages/core/emdash_core/agent/tools/`
2. Register in tool registry
3. Add to appropriate agent's tool list
4. Add tests
5. Document in tool reference

### Adding New Commands

1. Add command module in `packages/cli/emdash_cli/commands/`
2. Register in `packages/cli/emdash_cli/main.py`
3. Add to help text
4. Document slash commands

---

## License

MIT License - See LICENSE file for details.

---

## Acknowledgments

- [Claude](https://claude.ai) - AI assistance for development
- [Kuzu](https://github.com/kuzudb/kuzu) - Graph database
- [FastAPI](https://fastapi.tiangolo.com/) - Python web framework
- [Hono](https://hono.dev/) - TypeScript web framework
- [Vercel AI SDK](https://sdk.vercel.ai/) - TypeScript AI tooling