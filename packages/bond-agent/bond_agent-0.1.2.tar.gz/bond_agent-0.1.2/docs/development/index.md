# Development

This guide covers setting up a development environment, running tests, and contributing to Bond.

## Prerequisites

- **Python 3.11+** (3.11 or 3.12 recommended)
- **uv** package manager ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
- **Git** for version control

## Quick Setup

Clone the repository and install dependencies:

```bash
# Clone the repo
git clone https://github.com/renbytes/bond-agent.git
cd bond-agent

# Install all development dependencies
uv sync --group dev
```

This installs:

- Core dependencies (pydantic, pydantic-ai, etc.)
- Testing tools (pytest, pytest-asyncio, pytest-cov)
- Code quality tools (ruff, mypy, pre-commit)

## Running Tests

Bond uses pytest with async support:

```bash
# Run all tests with coverage
uv run pytest

# Run specific test file
uv run pytest tests/unit/tools/githunter/test_tools.py

# Run tests matching a pattern
uv run pytest -k "blame"

# Run with verbose output
uv run pytest -v

# Generate HTML coverage report
uv run pytest --cov-report=html
```

The default pytest configuration (in `pyproject.toml`) enables:

- Automatic async mode (`asyncio_mode = "auto"`)
- Coverage reporting for `src/bond`
- Verbose output with missing line reporting

## Code Quality

### Ruff (Formatting & Linting)

Ruff handles both code formatting and linting:

```bash
# Check formatting
uv run ruff format --check src tests

# Auto-format code
uv run ruff format src tests

# Run linter
uv run ruff check src tests

# Auto-fix linter issues
uv run ruff check --fix src tests
```

### MyPy (Type Checking)

Bond uses strict type checking:

```bash
# Run type checker
uv run mypy src/bond
```

### Pre-commit Hooks

Install pre-commit hooks to run checks automatically before each commit:

```bash
# Install hooks
uv run pre-commit install

# Run manually on all files
uv run pre-commit run --all-files
```

The pre-commit hooks run:

1. `ruff format --check` - Formatting check
2. `ruff check` - Linting
3. `mypy` - Type checking

## CI/CD Pipeline

GitHub Actions runs on every push and pull request to `main`:

| Job | Description |
|-----|-------------|
| `lint` | Runs ruff format and lint checks |
| `typecheck` | Runs mypy type checking |
| `test` | Runs pytest on Python 3.11 and 3.12 |
| `docs` | Builds documentation with mkdocs |

Additional workflows:

- **docs.yml**: Deploys documentation to GitHub Pages on pushes to `main`
- **publish.yml**: Publishes to PyPI on version tags

## Project Structure

```
src/bond/
├── __init__.py          # Package exports
├── agent.py             # BondAgent implementation
├── utils.py             # StreamHandlers and utilities
├── tools/               # Bundled toolsets
│   ├── githunter/       # Git forensics tools
│   ├── memory/          # Semantic memory tools
│   └── schema/          # Schema extraction tools
└── trace/               # Execution tracing
    ├── capture.py       # Trace capture
    ├── replay.py        # Trace replay
    └── backends/        # Storage backends
```

Each tool module follows a consistent pattern:

```
tools/my_tool/
├── __init__.py          # Public API exports
├── _protocols.py        # Protocol definition
├── _models.py           # Pydantic request/response models
├── _adapter.py          # Protocol implementation
└── tools.py             # Tool functions
```

## Building Documentation

```bash
# Install docs dependencies
uv sync --extra docs

# Serve locally with hot reload
uv run mkdocs serve

# Build static site
uv run mkdocs build --strict
```

Documentation is served at http://127.0.0.1:8000 when running locally.

## Next Steps

- [Adding Tools](adding-tools.md) - Guide for adding new toolsets
- [Testing](testing.md) - Testing patterns and practices
