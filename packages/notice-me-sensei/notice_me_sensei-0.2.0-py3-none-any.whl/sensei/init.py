"""Project initialization for Sensei."""

import sqlite3
from importlib import resources
from pathlib import Path

from sensei.migrations import apply_migrations


def get_template(name: str) -> str:
    """Load a template file from the templates directory."""
    template_files = resources.files("sensei.templates")
    template_path = template_files.joinpath(name)
    return template_path.read_text()


def get_db_path(project_root: Path) -> Path:
    """Get the database path, preferring new location.

    New location: .sensei/sensei.db
    Old location: sensei.db (for backwards compatibility)
    """
    new_path = project_root / ".sensei" / "sensei.db"
    old_path = project_root / "sensei.db"

    if new_path.exists():
        return new_path
    if old_path.exists():
        return old_path
    # Default to new location for new projects
    return new_path


def is_sensei_project(path: Path) -> bool:
    """Check if a path is a sensei project (has sensei.db in either location)."""
    new_path = path / ".sensei" / "sensei.db"
    old_path = path / "sensei.db"
    return new_path.exists() or old_path.exists()


def init_db(path: Path) -> sqlite3.Connection:
    """Initialize the database with migrations.

    Args:
        path: Path to the database file.

    Returns:
        Database connection.
    """
    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    apply_migrations(conn)
    return conn


def init_project(path: Path) -> None:
    """
    Initialize a new sensei project.

    Creates:
    - .sensei/sensei.db
    - .claude/skills/sensei/SKILL.md
    - topics/
    - practice/
    - references/
    - CLAUDE.md
    - .mcp.json
    """
    # Create directories
    claude_dir = path / ".claude"
    skills_dir = claude_dir / "skills" / "sensei"
    sensei_dir = path / ".sensei"
    topics_dir = path / "topics"
    practice_dir = path / "practice"
    references_dir = path / "references"

    skills_dir.mkdir(parents=True, exist_ok=True)
    sensei_dir.mkdir(parents=True, exist_ok=True)
    topics_dir.mkdir(parents=True, exist_ok=True)
    practice_dir.mkdir(parents=True, exist_ok=True)
    references_dir.mkdir(parents=True, exist_ok=True)

    # Write skill file
    skill_content = get_template("SKILL.md")
    (skills_dir / "SKILL.md").write_text(skill_content)

    # Write MCP server config
    mcp_content = get_template("mcp.json")
    (path / ".mcp.json").write_text(mcp_content)

    # Write CLAUDE.md
    claude_md_content = get_template("CLAUDE.md")
    (path / "CLAUDE.md").write_text(claude_md_content)

    # Initialize database in new location
    db_path = sensei_dir / "sensei.db"
    conn = init_db(db_path)
    conn.close()


def find_project_root(start: Path | None = None) -> Path | None:
    """
    Find the sensei project root by walking up from start path.

    Returns None if no project root is found.
    """
    if start is None:
        start = Path.cwd()

    current = start.resolve()
    while current != current.parent:
        if is_sensei_project(current):
            return current
        current = current.parent

    # Check root
    if is_sensei_project(current):
        return current

    return None
