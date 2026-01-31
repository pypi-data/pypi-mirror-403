# Emdash Benchmarks

Terminal-bench benchmarks for the emdash coding agent using Harbor framework.

## Prerequisites

1. **Python 3.12+** (Harbor requirement)

2. **Docker runtime** (one of):
   - [Colima](https://github.com/abiosoft/colima): `brew install colima && colima start`
   - [Rancher Desktop](https://rancherdesktop.io/): Install from website

3. **uv** (Python package manager):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

4. **API keys** (set in environment):
   ```bash
   export ANTHROPIC_API_KEY="your-key"
   # or
   export OPENAI_API_KEY="your-key"
   ```

## Setup

```bash
cd benchmarks

# Install all dependencies (creates venv automatically)
uv sync

# Install local emdash (required for agent)
uv pip install -e ..
```

## Usage

### Quick start

```bash
./run_benchmark.sh
```

### Custom model

```bash
MODEL=anthropic/claude-sonnet-4 ./run_benchmark.sh
```

### Adjust parallelism

```bash
PARALLEL=8 ./run_benchmark.sh
```

### Single task (for testing)

```bash
./run_benchmark.sh -n 1
```

### Verbose output

```bash
uv run harbor run -d terminal-bench@2.0 \
    --agent-import-path agents.emdash_coding:EmdashCodingAgent \
    -m anthropic/claude-haiku-4-5 \
    --verbose
```

### Dry run

```bash
uv run harbor run -d terminal-bench@2.0 \
    --agent-import-path agents.emdash_coding:EmdashCodingAgent \
    --dry-run
```

## Results

Results are stored in `results/` with timestamps. To submit to the leaderboard, follow the instructions in the [Harbor documentation](https://harborframework.com/docs/running-tbench).

## Configuration

See `configs/default.yaml` for configuration options.

## Troubleshooting

**Docker not running**:
```bash
# For Colima
colima start

# For Rancher - start from Applications
```

**Harbor not found**:
```bash
uv pip install harbor
```

**Agent import error**:
```bash
# Ensure you're in the benchmarks directory
cd benchmarks
uv sync
uv pip install -e ..
```
