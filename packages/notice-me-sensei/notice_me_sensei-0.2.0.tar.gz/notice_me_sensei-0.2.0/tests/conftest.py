"""Test fixtures for Sensei."""

import tempfile
from pathlib import Path

import pytest

from sensei.db import get_connection
from sensei.init import get_db_path, init_db, init_project


@pytest.fixture
def tmp_db():
    """Create a temporary database for testing with migrations applied."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    conn = init_db(db_path)
    yield conn
    conn.close()
    db_path.unlink(missing_ok=True)


@pytest.fixture
def tmp_project():
    """Create an ephemeral sensei project for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)
        init_project(project_path)
        yield project_path


@pytest.fixture
def tmp_project_conn(tmp_project):
    """Get database connection for a tmp project."""
    db_path = get_db_path(tmp_project)
    conn = get_connection(db_path)
    yield conn
    conn.close()


@pytest.fixture
def mcp_project(tmp_project, monkeypatch):
    """Set up a project for MCP tool testing."""
    # Change to project directory so find_project_root works
    monkeypatch.chdir(tmp_project)
    yield tmp_project
