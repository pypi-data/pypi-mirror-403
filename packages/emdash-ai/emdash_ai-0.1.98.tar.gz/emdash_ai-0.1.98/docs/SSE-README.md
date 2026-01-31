# Emdash Core SSE API Reference

This document lists all HTTP SSE (Server-Sent Events) streaming endpoints available in emdash-core.

## Common Response Headers

All SSE endpoints return:
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```

## Common Event Types

| Event | Description |
|-------|-------------|
| `SESSION_START` | Session initialized with ID and metadata |
| `TOOL_START` | Tool execution begins |
| `TOOL_RESULT` | Tool execution completed |
| `THINKING` | Agent reasoning/thinking content |
| `RESPONSE` | Final text response |
| `PARTIAL_RESPONSE` | Streaming partial response |
| `PROGRESS` | Progress update |
| `CLARIFICATION` | User input needed |
| `WARNING` | Warning message |
| `ERROR` | Error occurred |
| `SESSION_END` | Session completed |

---

## Agent Endpoints

### 1. Start Agent Chat

**POST** `/api/agent/chat`

Start a new agent chat session with SSE streaming.

**Request Body:**
```json
{
  "message": "string (required) - User message/task",
  "session_id": "string (optional) - Session ID for continuity",
  "model": "string (optional) - LLM model to use",
  "images": [
    {
      "data": "string - Base64 encoded image",
      "format": "string - Image format (png, jpg)"
    }
  ],
  "history": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "options": {
    "max_iterations": 100,
    "verbose": true,
    "mode": "code | research | review | spec | plan",
    "context_threshold": 0.6
  }
}
```

**Response Headers:**
```
X-Session-ID: <session-id>
```

**Example:**
```bash
curl -N -X POST http://localhost:8765/api/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Find authentication code"}'
```

---

### 2. Continue Agent Chat

**POST** `/api/agent/chat/{session_id}/continue`

Continue an existing chat session.

**Path Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `session_id` | string | Session ID (required) |

**Request Body:** Same as Start Agent Chat

---

### 3. Approve Plan

**POST** `/api/agent/chat/{session_id}/plan/approve`

Approve the pending plan and transition to code mode.

**Path Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `session_id` | string | Session ID (required) |

---

### 4. Reject Plan (Provide Feedback)

**POST** `/api/agent/chat/{session_id}/plan/reject`

Reject the pending plan with feedback for revision.

**Path Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `session_id` | string | Session ID (required) |

**Query Parameters:**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `feedback` | string | "" | User feedback on rejection |

---

### 5. Approve Plan Mode Entry

**POST** `/api/agent/chat/{session_id}/planmode/approve`

Approve the agent's request to enter plan mode.

**Path Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `session_id` | string | Session ID (required) |

---

### 6. Reject Plan Mode Entry

**POST** `/api/agent/chat/{session_id}/planmode/reject`

Reject the agent's request to enter plan mode.

**Path Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `session_id` | string | Session ID (required) |

**Query Parameters:**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `feedback` | string | "" | Reason for rejecting plan mode |

---

### 7. Answer Clarification

**POST** `/api/agent/chat/{session_id}/clarification/answer`

Answer a pending clarification question from the agent.

**Path Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `session_id` | string | Session ID (required) |

**Query Parameters:**
| Name | Type | Description |
|------|------|-------------|
| `answer` | string | User's answer to the clarification (required) |

---

## Project Generation

### 8. Generate PROJECT.md

**POST** `/api/projectmd/generate`

Generate PROJECT.md by exploring the codebase with AI.

**Request Body:**
```json
{
  "output": "PROJECT.md",
  "save": true,
  "model": "string (optional)"
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `output` | string | "PROJECT.md" | Output file path |
| `save` | bool | true | Save to file |
| `model` | string | null | LLM model to use |

---

## Research & Analysis

### 9. Deep Research

**POST** `/api/research`

Deep research with multi-LLM loops and critic evaluation.

**Request Body:**
```json
{
  "goal": "string (required) - Research goal",
  "max_iterations": 5,
  "budget": 50000,
  "model": "string (optional)",
  "researcher_model": "string (optional)"
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `goal` | string | - | Research goal (required) |
| `max_iterations` | int | 5 | Max research iterations |
| `budget` | int | 50000 | Token budget |
| `model` | string | null | LLM for main tasks |
| `researcher_model` | string | null | LLM for research |

---

### 10. Team Focus Analysis

**POST** `/api/team/focus`

Analyze team's recent focus and work-in-progress from git history.

**Request Body:**
```json
{
  "days": 7,
  "model": "string (optional)",
  "include_graph": true
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `days` | int | 7 | Number of days to analyze |
| `model` | string | null | LLM for summaries |
| `include_graph` | bool | true | Include graph analysis |

---

## Code Review

### 11. Generate PR Review

**POST** `/api/review`

Generate a pull request review.

**Request Body:**
```json
{
  "pr_number": 123,
  "pr_url": "string (optional)",
  "search": "string (optional)",
  "state": "open | closed | all",
  "model": "string (optional)",
  "post_review": false,
  "verdict": false
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `pr_number` | int | null | PR number |
| `pr_url` | string | null | PR URL |
| `search` | string | null | Search for PR by text |
| `state` | string | "open" | PR state filter |
| `model` | string | null | LLM model |
| `post_review` | bool | false | Post review to GitHub |
| `verdict` | bool | false | Include APPROVE/REQUEST_CHANGES |

---

### 12. Create Reviewer Profile

**POST** `/api/review/create-profile`

Create a reviewer profile by analyzing repository reviewers.

**Query Parameters:**
| Name | Type | Default | Description |
|------|------|---------|-------------|
| `top_reviewers` | int | 5 | Number of top reviewers |
| `top_contributors` | int | 10 | Number of top contributors |
| `max_prs` | int | 50 | Maximum PRs to analyze |
| `model` | string | null | LLM model |

---

## Specification & Tasks

### 13. Generate Feature Specification

**POST** `/api/spec/generate`

Generate a detailed feature specification.

**Request Body:**
```json
{
  "feature": "string (required) - Feature description",
  "project_md": "string (optional)",
  "model": "string (optional)",
  "verbose": false
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `feature` | string | - | Feature description (required) |
| `project_md` | string | null | PROJECT.md content |
| `model` | string | null | LLM model |
| `verbose` | bool | false | Verbose output |

---

### 14. Generate Implementation Tasks

**POST** `/api/tasks/generate`

Generate implementation tasks from a specification.

**Request Body:**
```json
{
  "spec_name": "string (optional)",
  "spec_content": "string (optional)",
  "project_md": "string (optional)",
  "model": "string (optional)"
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `spec_name` | string | null | Specification name |
| `spec_content` | string | null | Specification content |
| `project_md` | string | null | PROJECT.md content |
| `model` | string | null | LLM model |

---

## Repository Indexing

### 15. Start Repository Indexing

**POST** `/api/index/start`

Start indexing a repository with SSE streaming progress.

**Request Body:**
```json
{
  "repo_path": "string (required)",
  "options": {
    "changed_only": false,
    "index_git": false,
    "index_github": 0,
    "detect_communities": true,
    "describe_communities": false,
    "community_limit": 20,
    "model": "string (optional)"
  }
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `repo_path` | string | - | Path to repository (required) |
| `options.changed_only` | bool | false | Only index changed files |
| `options.index_git` | bool | false | Index git history |
| `options.index_github` | int | 0 | Number of GitHub PRs to index |
| `options.detect_communities` | bool | true | Run community detection |
| `options.describe_communities` | bool | false | Use LLM to describe communities |
| `options.community_limit` | int | 20 | Max communities to describe |
| `options.model` | string | null | Model for descriptions |

---

## Summary

| # | Endpoint | Method | Path |
|---|----------|--------|------|
| 1 | Start Agent Chat | POST | `/api/agent/chat` |
| 2 | Continue Agent Chat | POST | `/api/agent/chat/{session_id}/continue` |
| 3 | Approve Plan | POST | `/api/agent/chat/{session_id}/plan/approve` |
| 4 | Reject Plan | POST | `/api/agent/chat/{session_id}/plan/reject` |
| 5 | Approve Plan Mode | POST | `/api/agent/chat/{session_id}/planmode/approve` |
| 6 | Reject Plan Mode | POST | `/api/agent/chat/{session_id}/planmode/reject` |
| 7 | Answer Clarification | POST | `/api/agent/chat/{session_id}/clarification/answer` |
| 8 | Generate PROJECT.md | POST | `/api/projectmd/generate` |
| 9 | Deep Research | POST | `/api/research` |
| 10 | Team Focus | POST | `/api/team/focus` |
| 11 | Generate PR Review | POST | `/api/review` |
| 12 | Create Reviewer Profile | POST | `/api/review/create-profile` |
| 13 | Generate Spec | POST | `/api/spec/generate` |
| 14 | Generate Tasks | POST | `/api/tasks/generate` |
| 15 | Start Indexing | POST | `/api/index/start` |
