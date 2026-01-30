# Contributing to Sensei

## Development Setup

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)
- make (optional, for shortcuts)

### Clone and install dependencies

```bash
git clone git@github.com:tdfirth/sensei.git
cd sensei
uv sync
```

This creates a `.venv` and installs all dependencies including dev tools (ruff, ty, pytest).

## Development Workflow

### Quick commands with Make

```bash
make install    # Install dependencies
make format     # Format code with ruff
make lint       # Run ruff linter
make typecheck  # Run ty type checker
make test       # Run pytest

make check      # Run all checks (what CI runs)
make all        # Format + run all checks
```

### Manual commands

```bash
uv run ruff format src/ tests/        # Format code
uv run ruff check src/ tests/         # Lint
uv run ruff check --fix src/ tests/   # Lint and auto-fix
uv run ty check src/                  # Type check
uv run pytest tests/ -v               # Run tests
```

### Running the dev version

Use `uv run` to run commands with the local development version.

**From the sensei repo directory:**

```bash
cd /path/to/sensei
uv run sensei --help
```

**From any other directory** (e.g., a test project):

```bash
cd /tmp/my-test-project
uv run --project /path/to/sensei sensei init
uv run --project /path/to/sensei sensei task list
```

The `--project` flag tells uv where to find the sensei source. This works even if you have the public version installed globally via `uv tool install notice-me-sensei`—the `uv run --project` command uses the local dev version, while the bare `sensei` command uses the global tool installation.

**Tip:** Create a shell alias for convenience:

```bash
alias sensei-dev='uv run --project /path/to/sensei sensei'
```

Then you can use `sensei-dev init`, `sensei-dev task list`, etc. from anywhere.

### Building the package

```bash
uv build
```

This creates `dist/notice_me_sensei-X.X.X.tar.gz` and `dist/notice_me_sensei-X.X.X-py3-none-any.whl`.

### Testing in a fresh environment

**Option 1: Use `--project` (recommended for quick iteration)**

```bash
mkdir /tmp/test-sensei && cd /tmp/test-sensei
uv run --project /path/to/sensei sensei init
uv run --project /path/to/sensei sensei task create "Test" --type learning
uv run --project /path/to/sensei sensei task list
```

**Option 2: Install as a global tool temporarily**

This replaces any existing global installation:

```bash
uv tool install --force /path/to/sensei
sensei --help

# To restore the published version later:
uv tool install --force notice-me-sensei
```

**Option 3: Test the built wheel with uvx**

```bash
uv build
cd /tmp && mkdir test-sensei && cd test-sensei
uvx --from /path/to/sensei/dist/notice_me_sensei-0.1.0-py3-none-any.whl sensei init
```

## Project Structure

```
sensei/
├── src/sensei/
│   ├── __init__.py
│   ├── cli.py          # Typer CLI
│   ├── mcp.py          # FastMCP server
│   ├── db.py           # SQLite operations
│   ├── models.py       # Pydantic models
│   ├── srs.py          # Spaced repetition algorithm
│   ├── init.py         # Project initialization
│   └── templates/      # SKILL.md, CLAUDE.md, settings.local.json
├── tests/
│   ├── conftest.py     # Pytest fixtures
│   ├── test_cli.py     # CLI integration tests
│   ├── test_db.py      # Database unit tests
│   ├── test_mcp.py     # MCP tool tests
│   ├── test_srs.py     # SRS algorithm tests
│   └── test_init.py    # Project init tests
├── pyproject.toml
├── Makefile
├── README.md
└── CONTRIBUTING.md
```

## Code Style

We use [ruff](https://docs.astral.sh/ruff/) for formatting and linting, and [ty](https://github.com/astral-sh/ty) for type checking.

- **Type hints everywhere** — all function signatures fully typed
- **Functional where practical** — pure functions, minimal state
- **Classes where appropriate** — Pydantic models, CLI groups
- **No unnecessary abstraction** — if a function does the job, don't wrap it

## Testing Philosophy

- **No mocks for the database** — tests use real SQLite files in temp directories
- **Integration tests for CLI** — use Typer's `CliRunner`
- **Test the internal functions for MCP** — the `_` prefixed functions in `mcp.py`

## Making Changes

1. Create a branch for your changes
2. Write tests for new functionality
3. Run `make check` to ensure all checks pass
4. Update README.md if adding user-facing features
5. Submit a pull request

CI will run the same checks on your PR.

## Publishing (Maintainers)

```bash
# Bump version in pyproject.toml
# Then:
uv build
uv publish
```
