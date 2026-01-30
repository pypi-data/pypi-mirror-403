"""Tests for the migration system."""

import sqlite3
import tempfile
from pathlib import Path

from sensei.migrations import (
    apply_migrations,
    ensure_migrations_table,
    get_applied_migrations,
    get_migration_files,
    get_pending_migrations,
    migrate_db_location,
)


def test_get_migration_files():
    """Test that migration files are discovered in order."""
    migrations = get_migration_files()
    assert len(migrations) >= 2
    names = [name for name, _ in migrations]
    assert names[0] == "001_initial.sql"
    assert names[1] == "002_references.sql"
    # Verify they are sorted
    assert names == sorted(names)


def test_ensure_migrations_table():
    """Test that migrations table is created."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        ensure_migrations_table(conn)

        # Check table exists
        result = conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='_sensei_migrations'"
        ).fetchone()
        assert result is not None

        conn.close()
    finally:
        db_path.unlink(missing_ok=True)


def test_get_applied_migrations_empty():
    """Test getting applied migrations from empty db."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        applied = get_applied_migrations(conn)
        assert applied == set()

        conn.close()
    finally:
        db_path.unlink(missing_ok=True)


def test_get_pending_migrations():
    """Test getting pending migrations."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        pending = get_pending_migrations(conn)
        assert len(pending) >= 2
        names = [name for name, _ in pending]
        assert "001_initial.sql" in names
        assert "002_references.sql" in names

        conn.close()
    finally:
        db_path.unlink(missing_ok=True)


def test_apply_migrations():
    """Test applying all migrations."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        applied = apply_migrations(conn)
        assert len(applied) >= 2
        assert "001_initial.sql" in applied
        assert "002_references.sql" in applied

        # Verify tables were created
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = {row["name"] for row in tables}

        assert "tasks" in table_names
        assert "artifacts" in table_names
        assert "assessments" in table_names
        assert "task_dependencies" in table_names
        assert "references" in table_names
        assert "_sensei_migrations" in table_names

        conn.close()
    finally:
        db_path.unlink(missing_ok=True)


def test_apply_migrations_idempotent():
    """Test that applying migrations twice is safe."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        # Apply once
        applied1 = apply_migrations(conn)
        assert len(applied1) >= 2

        # Apply again - should return empty list
        applied2 = apply_migrations(conn)
        assert applied2 == []

        # Check no pending
        pending = get_pending_migrations(conn)
        assert pending == []

        conn.close()
    finally:
        db_path.unlink(missing_ok=True)


def test_migrate_db_location():
    """Test moving database to new location."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)
        old_path = project_path / "sensei.db"
        new_path = project_path / ".sensei" / "sensei.db"

        # Create old database
        conn = sqlite3.connect(old_path)
        conn.execute("CREATE TABLE test (id TEXT)")
        conn.close()

        # Migrate
        result = migrate_db_location(old_path, new_path)
        assert result is True
        assert not old_path.exists()
        assert new_path.exists()

        # Verify content preserved
        conn = sqlite3.connect(new_path)
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        assert any(row[0] == "test" for row in tables)
        conn.close()


def test_migrate_db_location_no_old():
    """Test migration when old db doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)
        old_path = project_path / "sensei.db"
        new_path = project_path / ".sensei" / "sensei.db"

        result = migrate_db_location(old_path, new_path)
        assert result is False


def test_migrate_db_location_new_exists():
    """Test migration when new db already exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)
        old_path = project_path / "sensei.db"
        new_path = project_path / ".sensei" / "sensei.db"

        # Create both
        old_path.write_text("old")
        new_path.parent.mkdir(parents=True)
        new_path.write_text("new")

        result = migrate_db_location(old_path, new_path)
        assert result is False
        assert old_path.exists()  # Old not deleted
        assert new_path.read_text() == "new"  # New not overwritten
