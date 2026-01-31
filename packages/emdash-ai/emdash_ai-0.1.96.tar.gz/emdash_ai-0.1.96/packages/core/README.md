# EmDash Core

FastAPI server providing all business logic for the EmDash code intelligence platform.

## Quick Start

```bash
cd packages/core
uv sync
uv run emdash-core --port 8765
```

Server available at `http://localhost:8765`
API docs at `http://localhost:8765/docs`

---

## API Endpoints

### Health (`/api/health`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Full health check with database status |
| GET | `/ready` | Kubernetes readiness probe |
| GET | `/live` | Kubernetes liveness probe |

**GET `/api/health`**
```bash
curl http://localhost:8765/api/health
```
Response:
```json
{
  "status": "healthy",
  "version": "0.1.3",
  "uptime_seconds": 123.45,
  "repo_root": "/path/to/repo",
  "database": {
    "connected": true,
    "node_count": 1234,
    "relationship_count": 5678
  },
  "timestamp": "2025-01-10T12:00:00"
}
```

---

### Authentication (`/api/auth`)

GitHub OAuth device flow authentication.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/login` | Start GitHub OAuth device flow |
| POST | `/login/poll/{user_code}` | Poll for login completion |
| POST | `/logout` | Sign out |
| GET | `/status` | Get authentication status |

**POST `/api/auth/login`**
```bash
curl -X POST http://localhost:8765/api/auth/login
```
Response:
```json
{
  "user_code": "ABCD-1234",
  "verification_uri": "https://github.com/login/device",
  "expires_in": 900,
  "interval": 5
}
```

**POST `/api/auth/login/poll/{user_code}`**

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_code` | path | User code from login response |

```bash
curl -X POST http://localhost:8765/api/auth/login/poll/ABCD-1234
```
Response:
```json
{
  "status": "success",
  "username": "octocat"
}
```

**GET `/api/auth/status`**
```bash
curl http://localhost:8765/api/auth/status
```
Response:
```json
{
  "authenticated": true,
  "username": "octocat",
  "scope": "repo,read:org"
}
```

---

### Database (`/api/db`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/init` | Initialize database schema |
| POST | `/clear` | Clear all data |
| GET | `/stats` | Get database statistics |
| GET | `/test` | Test database connection |

**POST `/api/db/init`**
```bash
curl -X POST http://localhost:8765/api/db/init
```

**POST `/api/db/clear`**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `confirm` | query | `false` | Must be `true` to proceed |

```bash
curl -X POST "http://localhost:8765/api/db/clear?confirm=true"
```

**GET `/api/db/stats`**
```bash
curl http://localhost:8765/api/db/stats
```
Response:
```json
{
  "node_count": 1234,
  "relationship_count": 5678,
  "file_count": 100,
  "function_count": 500,
  "class_count": 50,
  "community_count": 10
}
```

---

### Agent Chat (`/api/agent`)

Interactive AI agent with SSE streaming.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat` | Start agent chat (SSE) |
| POST | `/chat/{session_id}/continue` | Continue session (SSE) |
| GET | `/sessions` | List active sessions |
| DELETE | `/sessions/{session_id}` | Delete session |

**POST `/api/agent/chat`**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `message` | body | required | User message |
| `model` | body | config default | LLM model to use |
| `session_id` | body | auto-generated | Session ID for continuity |
| `options.max_iterations` | body | `20` | Max agent iterations |
| `images` | body | `[]` | Image attachments |

```bash
curl -N -X POST http://localhost:8765/api/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Find the authentication code",
    "model": "claude-3-5-sonnet-20241022",
    "options": {"max_iterations": 20}
  }'
```

SSE Events:
- `session_start` - Session initialized
- `tool_start` - Tool execution started
- `tool_result` - Tool completed
- `thinking` - Agent reasoning
- `response` / `partial_response` - Agent output
- `error` / `warning` - Error messages
- `session_end` - Session complete

---

### Indexing (`/api/index`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/start` | Start indexing (SSE) |
| GET | `/status` | Get index status |

**POST `/api/index/start`**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `repo_path` | body | required | Path to repository |
| `options.changed_only` | body | `false` | Only index changed files |
| `options.index_git` | body | `true` | Index git history |
| `options.index_github` | body | `0` | Number of GitHub PRs to index |
| `options.detect_communities` | body | `true` | Run community detection |
| `options.describe_communities` | body | `false` | Use LLM to describe communities |
| `options.community_limit` | body | `20` | Max communities to describe |
| `options.model` | body | `null` | Model for descriptions |

```bash
curl -N -X POST http://localhost:8765/api/index/start \
  -H "Content-Type: application/json" \
  -d '{
    "repo_path": "/path/to/repo",
    "options": {
      "changed_only": false,
      "index_git": true,
      "index_github": 50
    }
  }'
```

---

### Search (`/api/search`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/` | Full search with options |
| GET | `/quick` | Quick search |

**POST `/api/search`**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | body | required | Search query |
| `type` | body | `semantic` | `semantic` or `text` |
| `limit` | body | `20` | Maximum results |
| `entity_types` | body | `[]` | Filter: `File`, `Function`, `Class` |
| `min_score` | body | `0.0` | Minimum similarity score |
| `include_importance` | body | `true` | Include importance ranking |
| `include_snippets` | body | `true` | Include code snippets |

```bash
curl -X POST http://localhost:8765/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "authentication login",
    "type": "semantic",
    "limit": 10
  }'
```

**GET `/api/search/quick`**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `q` | query | required | Search query |
| `limit` | query | `10` | Maximum results |

```bash
curl "http://localhost:8765/api/search/quick?q=login&limit=5"
```

---

### Analytics (`/api/analyze`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/pagerank` | Compute PageRank scores |
| GET | `/betweenness` | Compute betweenness centrality |
| GET | `/communities` | Detect code communities |
| GET | `/communities/{id}` | Get community details |
| GET | `/areas` | Get area importance metrics |
| GET | `/commit-importance` | Score by commit frequency |

**GET `/api/analyze/pagerank`**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `top` | query | `20` | Number of top results |
| `damping` | query | `0.85` | PageRank damping factor |

```bash
curl "http://localhost:8765/api/analyze/pagerank?top=10"
```

**GET `/api/analyze/communities`**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `top` | query | `10` | Number of communities |
| `resolution` | query | `1.0` | Louvain resolution |
| `include_members` | query | `false` | Include member details |
| `query` | query | `null` | Filter by semantic query |

```bash
curl "http://localhost:8765/api/analyze/communities?top=5&include_members=true"
```

**GET `/api/analyze/areas`**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `depth` | query | `2` | Directory depth |
| `days` | query | `90` | Days of history |
| `top` | query | `20` | Number of areas |
| `sort` | query | `importance` | Sort: `importance`, `commits`, `churn`, `authors` |
| `include_files` | query | `false` | Include individual files |

```bash
curl "http://localhost:8765/api/analyze/areas?days=30&sort=churn"
```

---

### Query (`/api/query`)

Graph traversal and relationship queries.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/find-class/{name}` | Find class by name |
| GET | `/find-function/{name}` | Find function by name |
| POST | `/expand` | Expand node relationships |
| GET | `/callers/{qualified_name}` | Get function callers |
| GET | `/callees/{qualified_name}` | Get function callees |
| GET | `/hierarchy/{class_name}` | Get class hierarchy |
| GET | `/dependencies/{file_path}` | Get file dependencies |
| GET | `/knowledge-silos` | Detect knowledge silos |

**POST `/api/query/expand`**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `entity_type` | body | required | `File`, `Class`, or `Function` |
| `qualified_name` | body | required | Qualified name |
| `max_hops` | body | `2` | Max traversal depth |
| `include_source` | body | `true` | Include source code |

```bash
curl -X POST http://localhost:8765/api/query/expand \
  -H "Content-Type: application/json" \
  -d '{
    "entity_type": "Function",
    "qualified_name": "emdash.agent.runner.AgentRunner.run"
  }'
```

**GET `/api/query/knowledge-silos`**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `threshold` | query | `0.7` | Min importance score |
| `max_authors` | query | `2` | Max authors for silo |
| `top` | query | `20` | Number of silos |

```bash
curl "http://localhost:8765/api/analyze/knowledge-silos?max_authors=1"
```

---

### Embeddings (`/api/embed`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/status` | Get embedding coverage |
| POST | `/index` | Generate embeddings |
| GET | `/models` | List available models |
| POST | `/test` | Test embedding generation |

**POST `/api/embed/index`**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `include_prs` | body | `true` | Index PR embeddings |
| `include_functions` | body | `true` | Index function embeddings |
| `include_classes` | body | `true` | Index class embeddings |
| `reindex` | body | `false` | Reindex all |

```bash
curl -X POST http://localhost:8765/api/embed/index \
  -H "Content-Type: application/json" \
  -d '{"reindex": true}'
```

**POST `/api/embed/test`**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text` | query | required | Text to embed |
| `model` | query | `null` | Model name |

```bash
curl -X POST "http://localhost:8765/api/embed/test?text=hello%20world"
```

---

### PROJECT.md (`/api/projectmd`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/generate` | Generate PROJECT.md (SSE) |

**POST `/api/projectmd/generate`**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `output` | body | `PROJECT.md` | Output filename |
| `save` | body | `true` | Save to file |
| `model` | body | config default | LLM model |

```bash
curl -N -X POST http://localhost:8765/api/projectmd/generate \
  -H "Content-Type: application/json" \
  -d '{"output": "PROJECT.md", "save": true}'
```

---

### Specification (`/api/spec`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/generate` | Generate feature spec (SSE) |

**POST `/api/spec/generate`**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `feature` | body | required | Feature description |
| `project_md` | body | `null` | PROJECT.md content |
| `model` | body | config default | LLM model |
| `verbose` | body | `false` | Verbose output |

```bash
curl -N -X POST http://localhost:8765/api/spec/generate \
  -H "Content-Type: application/json" \
  -d '{"feature": "Add user authentication with OAuth"}'
```

---

### Tasks (`/api/tasks`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/generate` | Generate implementation tasks (SSE) |

**POST `/api/tasks/generate`**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `spec_name` | body | `null` | Specification name |
| `spec_content` | body | `null` | Specification content |
| `project_md` | body | `null` | PROJECT.md content |
| `model` | body | config default | LLM model |

```bash
curl -N -X POST http://localhost:8765/api/tasks/generate \
  -H "Content-Type: application/json" \
  -d '{"spec_content": "# Feature Spec\n..."}'
```

---

### Planning (`/api/plan`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/context` | Get planning context |
| GET | `/similar` | Find similar PRs |

**POST `/api/plan/context`**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `description` | body | required | Feature description |
| `similar_prs` | body | `5` | Number of similar PRs |

```bash
curl -X POST http://localhost:8765/api/plan/context \
  -H "Content-Type: application/json" \
  -d '{"description": "Add dark mode support"}'
```

**GET `/api/plan/similar`**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `description` | query | required | Feature description |
| `limit` | query | `5` | Max results |

```bash
curl "http://localhost:8765/api/plan/similar?description=authentication&limit=3"
```

---

### Team (`/api/team`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/focus` | Get team focus analysis (SSE) |

**POST `/api/team/focus`**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `days` | body | `7` | Days to analyze |
| `model` | body | config default | LLM for summaries |
| `include_graph` | body | `true` | Include graph analysis |

```bash
curl -N -X POST http://localhost:8765/api/team/focus \
  -H "Content-Type: application/json" \
  -d '{"days": 14}'
```

---

### Research (`/api/research`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/` | Deep research (SSE) |

**POST `/api/research`**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `goal` | body | required | Research goal |
| `max_iterations` | body | `5` | Max iterations |
| `budget` | body | `50000` | Token budget |
| `model` | body | config default | Main LLM model |
| `researcher_model` | body | `null` | Research LLM model |

```bash
curl -N -X POST http://localhost:8765/api/research \
  -H "Content-Type: application/json" \
  -d '{"goal": "How does authentication work in this codebase?"}'
```

---

### Review (`/api/review`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/` | Generate PR review (SSE) |
| POST | `/create-profile` | Create reviewer profile (SSE) |

**POST `/api/review`**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `pr_number` | body | `null` | PR number |
| `pr_url` | body | `null` | PR URL |
| `search` | body | `null` | Search for PR |
| `state` | body | `open` | PR state filter |
| `model` | body | config default | LLM model |
| `post_review` | body | `false` | Post to GitHub |
| `verdict` | body | `false` | Include verdict |

```bash
curl -N -X POST http://localhost:8765/api/review \
  -H "Content-Type: application/json" \
  -d '{"pr_number": 123}'
```

**POST `/api/review/create-profile`**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `top_reviewers` | query | `5` | Top reviewers to analyze |
| `top_contributors` | query | `10` | Top contributors |
| `max_prs` | query | `50` | Max PRs to analyze |
| `model` | query | config default | LLM model |

```bash
curl -N -X POST "http://localhost:8765/api/review/create-profile?top_reviewers=3"
```

---

### Swarm (`/api/swarm`)

Multi-agent parallel execution.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/run` | Run swarm tasks (SSE) |
| GET | `/status` | Get swarm status |
| GET | `/sessions` | List swarm sessions |
| POST | `/cleanup` | Clean up worktrees |
| POST | `/merge` | Merge completed branches |

**POST `/api/swarm/run`**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tasks` | body | required | List of task descriptions |
| `model` | body | config default | LLM model |
| `workers` | body | `3` | Parallel workers |
| `timeout` | body | `300` | Timeout per task (seconds) |
| `base_branch` | body | current | Base branch |
| `auto_merge` | body | `true` | Auto-merge completed |
| `llm_merge` | body | `false` | Use LLM for conflicts |

```bash
curl -N -X POST http://localhost:8765/api/swarm/run \
  -H "Content-Type: application/json" \
  -d '{
    "tasks": ["Add login button", "Add logout button", "Add profile page"],
    "workers": 3
  }'
```

**POST `/api/swarm/cleanup`**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `force` | query | `false` | Force cleanup |

```bash
curl -X POST "http://localhost:8765/api/swarm/cleanup?force=true"
```

**POST `/api/swarm/merge`**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `llm_merge` | query | `false` | Use LLM for conflicts |
| `target` | query | `null` | Target branch |

```bash
curl -X POST "http://localhost:8765/api/swarm/merge?target=main"
```

---

### Context (`/api/context`)

Session context management.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Get current context |
| DELETE | `/` | Clear context |
| GET | `/prompt` | Get context as prompt |

```bash
curl http://localhost:8765/api/context
curl -X DELETE http://localhost:8765/api/context
curl http://localhost:8765/api/context/prompt
```

---

### Rules/Templates (`/api/rules`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/list` | List all templates |
| GET | `/{name}` | Get template content |
| POST | `/init` | Initialize custom templates |

**GET `/api/rules/{template_name}`**

| Parameter | Type | Description |
|-----------|------|-------------|
| `template_name` | path | Template name: `spec`, `tasks`, `project`, `focus`, `pr-review` |

```bash
curl http://localhost:8765/api/rules/spec
```

**POST `/api/rules/init`**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `global_templates` | query | `false` | Use `~/.emdash-rules` |
| `force` | query | `false` | Overwrite existing |

```bash
curl -X POST "http://localhost:8765/api/rules/init?global_templates=false"
```

---

## SSE Event Types

All streaming endpoints return Server-Sent Events with these types:

| Event | Description |
|-------|-------------|
| `session_start` | Session initialized |
| `session_end` | Session completed |
| `thinking` | Agent reasoning |
| `tool_start` | Tool execution started |
| `tool_result` | Tool completed |
| `response` | Final response |
| `partial_response` | Streaming response chunk |
| `progress` | Progress update with percent |
| `clarification` | Agent needs input |
| `error` | Error occurred |
| `warning` | Warning message |

---

## Configuration

Environment variables or `~/.config/emdash/config`:

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Anthropic Claude API key |
| `OPENAI_API_KEY` | OpenAI API key |
| `FIREWORKS_API_KEY` | Fireworks AI API key |
| `GITHUB_TOKEN` | GitHub personal access token |
| `EMDASH_DATABASE_PATH` | Custom database path |
| `EMDASH_DEFAULT_MODEL` | Default LLM model |
