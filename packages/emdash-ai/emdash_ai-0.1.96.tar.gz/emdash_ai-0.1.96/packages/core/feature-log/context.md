# Context Management

This document explains how context is managed in emdash, including what gets sent to the LLM, how compaction works, and how file tracking is handled.

## Overview

Context management in emdash involves three main components:
1. **Dynamic System Prompt** - Base instructions + runtime state
2. **Message History** - Previous conversation messages
3. **File Tracking** - List of files already read in the session

---

## 1. What Context is Sent to the LLM

### System Prompt Structure

The system prompt is built dynamically and includes:

**Base prompt** (`agent/prompts/main_agent.py:35-69`):
- Core agent identity and capabilities
- Tool usage guidelines
- Response formatting rules

**Session context injection** (`agent/runner/agent_runner.py:80-83`):
- Repository information
- Current branch and git status
- Rules and skills sections

**Files read list** (`agent/runner/agent_runner.py:422-426`):
```python
files_read = self.toolkit.get_files_read()
if files_read:
    files_list = ", ".join(files_read[-20:])  # Limit to last 20 files
    dynamic_system += f"\n\n## Files Already Read (DO NOT re-read these)\n{files_list}"
```

### Context Frame (Optional)

Controlled by: `EMDASH_INJECT_CONTEXT_FRAME` environment variable

When enabled, injects reranked context items relevant to the current query (`agent/runner/agent_runner.py:191-230`):

```xml
<context-frame>
Relevant context for query: {query}
Found N relevant items (ranked by relevance score):
  - [Function] ClassName.method_name (score: 0.95)
  - [File] path/to/file.py
...
</context-frame>
```

---

## 2. How Compaction Works

### Trigger Conditions

Compaction is triggered when context usage exceeds a threshold (`agent/runner/context.py:126-308`).

**Configuration**:
| Variable | Default | Description |
|----------|---------|-------------|
| `EMDASH_CONTEXT_COMPACT_THRESHOLD` | `0.8` | Trigger at 80% of context limit |
| `EMDASH_CONTEXT_COMPACT_TARGET` | `0.5` | Reduce to 50% after compaction |

**Call site** (`agent/runner/agent_runner.py:409-412`):
```python
messages = maybe_compact_context(
    messages, self.provider, self.emitter, self.system_prompt,
    toolkit=self.toolkit
)
```

### Compaction Strategy

The compaction creates a **structured continuation summary** following a standardized format:

**Header** (exact text):
> This session is being continued from a previous conversation that ran out of context. The summary below covers the earlier portion of the conversation.

**Analysis Section** (chronological phases):
1. **Initial Request** - The original user intent
2. **Exploration Phase** - Investigation, comparisons, discoveries
3. **Planning / Design Phase** - Architecture, workflows, plans
4. **Decisions / Constraints** - Explicit choices, rejections, constraints
5. **Implementation Work** - What was created, modified, or wired up
6. **Open Issues / Remaining Work** - What is not finished or unresolved

**Summary Section** (thematic):
1. **Primary Request and Intent** - Overarching goal and hard requirements
2. **Key Technical Concepts** - Core ideas and mechanisms (concept: description format)
3. **Artifacts and Code Sections** - File paths, types, and responsibilities
4. **Open Tasks / Next Steps** - Status markers (✅ done, 🔄 in progress, ⏳ pending)

**Compaction Rules**:
- Preserve: user intent, explicit decisions, artifact names, open issues
- Remove: small talk, repeated restatements, trial-and-error details
- Prefer names over implementations (mention files/modules by name, not code)
- Respect uncertainty (use "planned", "discussed", "in progress" when appropriate)
- Target 300-800 words

### Message Preservation

```python
KEEP_RECENT = 6  # Keep 6 most recent messages for immediate context
```

**Structure after compaction**:
1. First message (original user request)
2. Continuation summary (structured Analysis + Summary sections)
3. Last 6 recent messages (for immediate context)

### Summarization Model

Uses `claude-3-5-haiku` for fast, efficient summarization. The prompt focuses on **intent, decisions, and artifacts** - not raw data or code dumps (`context.py:212-276`).

### File Knowledge Extraction

During compaction, file knowledge is extracted from middle messages (`context.py:311-376`):
```python
def extract_file_knowledge(messages: list[dict]) -> str:
    """Extract file paths and brief descriptions from tool results."""
    # Identifies which files were read in middle messages
    # Returns formatted list limited to 20 files
```

---

## 3. How Read Files List is Injected as Trace

### File Tracking System

Files are tracked in the session state (`agent/session.py`):

```python
# Line 47: Initialize tracking
self._files_read: set[str] = set()

# Line 84-86: Track when file is read
if tool_name == "read_file" and "path" in params:
    self._files_read.add(params["path"])

# Line 114-120: Get tracked files
def get_files_read(self) -> list[str]:
    return list(self._files_read)
```

### Injection into System Prompt

Before every LLM call (`agent/runner/agent_runner.py:422-426`):

```python
files_read = self.toolkit.get_files_read()
if files_read:
    files_list = ", ".join(files_read[-20:])
    dynamic_system += f"\n\n## Files Already Read (DO NOT re-read these)\n{files_list}"
```

This prevents redundant file re-reads by telling the LLM which files it has already seen.

### Reset on Compaction

When compaction occurs, file tracking is cleared (`agent/session.py:136-152`):

```python
def partial_reset_for_compaction(self) -> None:
    """Partial reset for context compaction."""
    self._files_read.clear()  # CLEAR FILE TRACKING
    # Keep only last 10 exploration steps
    if len(self.steps) > 10:
        self.steps = self.steps[-10:]
```

**Why?** After compaction, the actual file contents are no longer in the context window. The summary tells the LLM: *"I can re-read any files if I need their exact content"*.

---

## Configuration Reference

| Environment Variable | Default | Purpose |
|---------------------|---------|---------|
| `EMDASH_INJECT_CONTEXT_FRAME` | `false` | Enable context frame injection |
| `EMDASH_CONTEXT_COMPACT_THRESHOLD` | `0.8` | Trigger compaction at 80% |
| `EMDASH_CONTEXT_COMPACT_TARGET` | `0.5` | Reduce to 50% after compaction |
| `EMDASH_MAX_CONTEXT_MESSAGES` | `25` | Max messages before compaction |
| `CONTEXT_MIN_SCORE` | `0.5` | Minimum relevance score |
| `CONTEXT_MAX_ITEMS` | `50` | Max context items |
| `CONTEXT_RERANK_ENABLED` | `true` | Enable relevance reranking |
| `CONTEXT_RERANK_TOP_K` | `20` | Top K items after reranking |

---

## Key Files

- `agent/runner/agent_runner.py` - Main agent loop, context injection
- `agent/runner/context.py` - Compaction logic
- `agent/session.py` - File tracking state
- `agent/prompts/main_agent.py` - Base system prompt
