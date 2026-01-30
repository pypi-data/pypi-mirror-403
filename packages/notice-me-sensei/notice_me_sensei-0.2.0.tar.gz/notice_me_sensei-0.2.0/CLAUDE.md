# Sensei Development Guide

## Project Overview

Sensei is an MCP server for study task management with spaced repetition. It provides tools for creating, managing, and scheduling study tasks with SRS (Spaced Repetition System) support.

## Development Workflow

### Running Checks

Always run `make check` before committing to ensure code quality:

```bash
make check  # Runs lint, typecheck, and tests with format verification
```

Individual checks:
- `make lint` - Run ruff linter
- `make typecheck` - Run ty type checker
- `make test` - Run pytest
- `make format` - Auto-format code with ruff

### Quick Development Cycle

```bash
make all  # Format code and run all checks
```

## Code Structure

- `src/sensei/mcp.py` - MCP tool definitions (public API)
- `src/sensei/db.py` - Database operations (SQLite)
- `src/sensei/models.py` - Pydantic data models
- `src/sensei/srs.py` - Spaced repetition algorithm
- `src/sensei/cli.py` - Command-line interface
- `tests/` - pytest test suite

## Implementation Patterns

### MCP Tools Pattern

1. Internal functions (prefixed with `_`) contain business logic
2. Decorated functions (`@mcp.tool()`) wrap internal functions
3. Tests call internal functions directly

```python
def _task_create(...) -> dict:
    # Business logic here
    return task.model_dump(mode="json")

@mcp.tool()
def sensei_study_create(...) -> dict:
    """Docstring for Claude."""
    return _task_create(...)
```

### Database Pattern

- Use `get_db_connection()` to get connection
- Use `_resolve_task_id()` for partial ID support
- Return Pydantic models, serialize with `.model_dump(mode="json")`

### Error Handling

- Raise `ValueError` with descriptive messages
- MCP framework handles conversion to error responses
