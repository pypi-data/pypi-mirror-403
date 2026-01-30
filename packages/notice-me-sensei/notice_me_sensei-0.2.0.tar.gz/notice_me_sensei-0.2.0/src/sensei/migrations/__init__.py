"""Database migration system for Sensei."""

__all__ = [
    "apply_migrations",
    "check_fts5_available",
    "ensure_migrations_table",
    "get_applied_migrations",
    "get_migration_files",
    "get_pending_migrations",
    "migrate_db_location",
]

import sqlite3
from datetime import datetime
from importlib import resources
from pathlib import Path


def get_migration_files() -> list[tuple[str, str]]:
    """Get all migration SQL files in order.

    Returns:
        List of (migration_name, sql_content) tuples sorted by name.
    """
    migration_files = resources.files("sensei.migrations")
    migrations: list[tuple[str, str]] = []

    for item in migration_files.iterdir():
        if item.name.endswith(".sql"):
            content = item.read_text()
            migrations.append((item.name, content))

    return sorted(migrations, key=lambda x: x[0])


def ensure_migrations_table(conn: sqlite3.Connection) -> None:
    """Create the migrations tracking table if it doesn't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS _sensei_migrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            applied_at TEXT NOT NULL
        )
    """)
    conn.commit()


def get_applied_migrations(conn: sqlite3.Connection) -> set[str]:
    """Get the set of already applied migration names."""
    ensure_migrations_table(conn)
    rows = conn.execute("SELECT name FROM _sensei_migrations").fetchall()
    return {row[0] for row in rows}


def get_pending_migrations(conn: sqlite3.Connection) -> list[tuple[str, str]]:
    """Get migrations that haven't been applied yet.

    Returns:
        List of (migration_name, sql_content) tuples.
    """
    applied = get_applied_migrations(conn)
    all_migrations = get_migration_files()
    return [(name, sql) for name, sql in all_migrations if name not in applied]


def apply_migration(conn: sqlite3.Connection, name: str, sql: str) -> None:
    """Apply a single migration.

    Args:
        conn: Database connection
        name: Migration file name
        sql: SQL content to execute
    """
    conn.executescript(sql)
    conn.execute(
        "INSERT INTO _sensei_migrations (name, applied_at) VALUES (?, ?)",
        (name, datetime.now().isoformat()),
    )
    conn.commit()


def apply_migrations(conn: sqlite3.Connection) -> list[str]:
    """Apply all pending migrations.

    Args:
        conn: Database connection

    Returns:
        List of applied migration names.
    """
    ensure_migrations_table(conn)
    pending = get_pending_migrations(conn)
    applied: list[str] = []

    for name, sql in pending:
        apply_migration(conn, name, sql)
        applied.append(name)

    return applied


def check_fts5_available(conn: sqlite3.Connection) -> bool:
    """Check if FTS5 extension is available."""
    try:
        conn.execute("CREATE VIRTUAL TABLE _fts5_test USING fts5(test)")
        conn.execute("DROP TABLE _fts5_test")
        return True
    except sqlite3.OperationalError:
        return False


def migrate_db_location(old_path: Path, new_path: Path) -> bool:
    """Move database from old location to new location.

    Args:
        old_path: Current database path
        new_path: Target database path

    Returns:
        True if migration occurred, False if no migration needed.
    """
    if not old_path.exists():
        return False

    if new_path.exists():
        # Don't overwrite existing database
        return False

    # Ensure parent directory exists
    new_path.parent.mkdir(parents=True, exist_ok=True)

    # Move the database file
    old_path.rename(new_path)
    return True
