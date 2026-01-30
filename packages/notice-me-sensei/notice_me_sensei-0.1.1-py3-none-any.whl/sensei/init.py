"""Project initialization for Sensei."""

from importlib import resources
from pathlib import Path

from sensei.db import init_db


def get_template(name: str) -> str:
    """Load a template file from the templates directory."""
    template_files = resources.files("sensei.templates")
    template_path = template_files.joinpath(name)
    return template_path.read_text()


def init_project(path: Path) -> None:
    """
    Initialize a new sensei project.

    Creates:
    - .claude/skills/sensei/SKILL.md
    - .claude/settings.local.json
    - topics/
    - practice/
    - sensei.db
    - CLAUDE.md
    """
    # Create directories
    claude_dir = path / ".claude"
    skills_dir = claude_dir / "skills" / "sensei"
    topics_dir = path / "topics"
    practice_dir = path / "practice"

    skills_dir.mkdir(parents=True, exist_ok=True)
    topics_dir.mkdir(parents=True, exist_ok=True)
    practice_dir.mkdir(parents=True, exist_ok=True)

    # Write skill file
    skill_content = get_template("SKILL.md")
    (skills_dir / "SKILL.md").write_text(skill_content)

    # Write Claude settings
    settings_content = get_template("settings.local.json")
    (claude_dir / "settings.local.json").write_text(settings_content)

    # Write CLAUDE.md
    claude_md_content = get_template("CLAUDE.md")
    (path / "CLAUDE.md").write_text(claude_md_content)

    # Initialize database
    db_path = path / "sensei.db"
    conn = init_db(db_path)
    conn.close()


def is_sensei_project(path: Path) -> bool:
    """Check if a path is a sensei project (has sensei.db)."""
    return (path / "sensei.db").exists()


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
