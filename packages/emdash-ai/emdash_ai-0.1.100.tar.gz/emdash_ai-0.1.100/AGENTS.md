# Repository Guidelines

## Project Structure & Module Organization
- `emdash/` holds the core Python package (CLI, ingestion, graph, analytics, queries, utils).
- `emdash/ingestion/parsers/` includes AST parsers; the TypeScript parser depends on `node` + `typescript`.
- `tests/` and root-level `test_*.py` files contain pytest tests; `tests/fixtures/` holds fixtures.
- `vscode-extension/` contains the VSCode integration, and `team/` stores team-related assets.
- `exmples/` holds sample content (note the spelling).

## Build, Test, and Development Commands
- `uv sync` installs all dependencies and sets up the development environment.
- `uv run pytest` runs the test suite.
- `uv run black emdash/` formats Python code.
- `uv run ruff check emdash/` runs lint checks.
- `uv run mypy emdash/` runs type checks.
- `npm install` installs TypeScript parser dependencies.
- `npm run parse` runs the TypeScript parser directly.

## Coding Style & Naming Conventions
- Python formatting uses Black and Ruff with `line-length = 100` (see `pyproject.toml`).
- Type checking uses MyPy with Python 3.10 settings.
- Tests follow pytest naming: files `test_*.py`, functions `test_*`.

## Testing Guidelines
- Framework: pytest (optional coverage via `pytest --cov` if needed).
- Keep new tests near related modules (e.g., `tests/` or root `test_*.py`).

## Commit & Pull Request Guidelines
- Git history shows short, informal subjects (e.g., "wip - deep research"). No strict convention is enforced; keep subjects concise and descriptive.
- PRs should include a clear summary, linked issue if applicable, and notes on how to test. Provide screenshots only for UI changes (e.g., `vscode-extension/`).

## Security & Configuration Tips
- Copy `.env.example` to `.env` and set Neo4j + optional API keys before running CLI features.
- Avoid committing secrets; add local overrides to `.env`.
