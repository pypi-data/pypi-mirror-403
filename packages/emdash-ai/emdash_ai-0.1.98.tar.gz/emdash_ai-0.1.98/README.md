# emdash-ai

Graph-based coding intelligence system - The 'Senior Engineer' Context Engine

## Quick Install (macOS)

```bash
brew install uv cmake
uv tool install emdash-ai
```

## Quick Install (Linux)

```bash
# Install dependencies
sudo apt-get install cmake  # Debian/Ubuntu
# or: sudo dnf install cmake  # Fedora

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.cargo/bin:$PATH"

uv tool install emdash-ai
```

> **Note:** After installation, you may need to reload your shell config:
> ```bash
> source ~/.zshrc  # or ~/.bashrc
> ```

### Update

```bash
uv tool upgrade emdash-ai
```

## Requirements

- Python 3.10+ (3.10-3.13 recommended)
- cmake (for building the graph database)

## Usage

```bash
em              # Start the AI coding agent
emdash index    # Index your codebase
emdash agent    # Start the AI agent (alternative)
```

## Slash Commands

Once inside the agent REPL, use these slash commands:

### Mode Switching

| Command | Description |
|---------|-------------|
| `/plan` | Switch to plan mode (explore codebase, create plans) |
| `/code` | Switch to code mode (execute file changes) |
| `/mode` | Show current operating mode |

### Generation & Research

| Command | Description |
|---------|-------------|
| `/projectmd` | Generate PROJECT.md describing your codebase architecture |
| `/pr [url]` | Review a pull request (e.g., `/pr 123` or `/pr https://github.com/org/repo/pull/123`) |
| `/research [goal]` | Deep research on a topic (e.g., `/research How does auth work?`) |

### Status & Context

| Command | Description |
|---------|-------------|
| `/status` | Show index and PROJECT.md status |
| `/context` | Show current context frame (tokens, reranked items) |
| `/compact` | Compact message history using LLM summarization |
| `/spec` | Show current specification from plan mode |

### Todo Management

| Command | Description |
|---------|-------------|
| `/todos` | Show current agent todo list |
| `/todo-add [title]` | Add a todo item for the agent |

### Session Management

| Command | Description |
|---------|-------------|
| `/session` | Interactive session menu |
| `/session save [name]` | Save current session |
| `/session load [name]` | Load a saved session |
| `/session list` | List all saved sessions |
| `/session delete [name]` | Delete a session |
| `/reset` | Reset session state |

### Configuration

| Command | Description |
|---------|-------------|
| `/agents` | Manage agents (create, show, edit, delete) |
| `/rules` | Manage rules that guide agent behavior |
| `/skills` | Manage reusable skills |
| `/hooks` | Manage event hooks (triggers on tool_start, session_end, etc.) |
| `/mcp` | Manage MCP servers |
| `/registry` | Browse and install community skills, rules, agents, and verifiers |
| `/setup` | Interactive setup wizard |

### Verification

| Command | Description |
|---------|-------------|
| `/verify` | Run verification checks on current work |
| `/verify-loop [task]` | Run task in loop until all verifications pass |

### Authentication & Diagnostics

| Command | Description |
|---------|-------------|
| `/auth` | GitHub authentication (login, logout, status) |
| `/doctor` | Check environment and diagnose issues |

### Help & Exit

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/quit` | Exit the agent (also `/exit`, `/q`) |

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Space` | Auto-complete commands |
| `Alt+Enter` | Multi-line input |
| `Ctrl+V` | Paste image from clipboard |
| `@filename` | Reference a file in your prompt |

## Features

- Graph-based code analysis
- Semantic code search
- AI-powered code exploration
- MCP server integration
- Session persistence
- Custom agents, rules, and skills
- Event hooks for automation
- Verification loops

## Configuration

Configuration files are stored in `.emdash/` in your project root:

```
.emdash/
├── agents/       # Custom agent definitions
├── rules/        # Coding rules and guidelines
├── skills/       # Reusable skills
├── sessions/     # Saved sessions
└── hooks.json    # Event hooks configuration
```

Global config at `~/.config/emdash/`:
```
~/.config/emdash/
├── mcp.json      # MCP server configuration
└── config.json   # Global settings
```

## Troubleshooting

### Build fails with "cmake: command not found"

If you see `Failed to build kuzu` with cmake errors:

```bash
# macOS
brew install cmake

# Linux (Debian/Ubuntu)
sudo apt-get install cmake

# Then retry
uv tool install emdash-ai
```

### "permission denied: em"

If you get `zsh: permission denied: em` or similar:

```bash
# Check if uv tool installed it
uv tool list

# Reinstall
uv tool uninstall emdash-ai && uv tool install emdash-ai
```

### Command not found

If `em` or `emdash` is not found, add `~/.local/bin` to your PATH:

```bash
# For zsh (add to ~/.zshrc)
export PATH="$HOME/.local/bin:$PATH"

# For bash (add to ~/.bashrc or ~/.bash_profile)
export PATH="$HOME/.local/bin:$PATH"

# Then reload
source ~/.zshrc  # or ~/.bashrc
```

### Debug installation

```bash
# Check which em is being found
which em
type em

# Check permissions
ls -la ~/.local/bin/em

# Check installed version
uv tool list
```

### Uninstall

```bash
uv tool uninstall emdash-ai
```

## Running Terminal-Bench

Run the [terminal-bench](https://github.com/runloopai/terminal-bench) benchmark to evaluate agent performance.

### Prerequisites

- Docker running (Colima or Rancher Desktop)
- Harbor installed: `pip install harbor`

### Setup

```bash
cd benchmarks
uv venv .venv
uv pip install -r requirements.txt
```

### Run

```bash
./benchmarks/scripts/run.sh
```

With custom settings:

```bash
MODEL="qwen3-vl-235b" PARALLEL=2 ./benchmarks/scripts/run.sh
```

| Variable | Default | Description |
|----------|---------|-------------|
| `MODEL` | claude-haiku-4-5 | Model to benchmark |
| `PARALLEL` | 4 | Concurrent tasks |
| `DATASET` | terminal-bench@2.0 | Dataset to run |
