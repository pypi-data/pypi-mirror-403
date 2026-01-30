"""Database operations for Sensei."""

import json
import re
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from sensei.models import (
    Artifact,
    ArtifactType,
    Assessment,
    Task,
    TaskDetail,
    TaskStatus,
    TaskType,
)

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    parent_id TEXT REFERENCES tasks(id),
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    path TEXT,
    due_date TEXT,
    created_at TEXT NOT NULL,
    completed_at TEXT,
    metadata TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS artifacts (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL REFERENCES tasks(id),
    path TEXT NOT NULL,
    type TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS assessments (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL REFERENCES tasks(id),
    score REAL,
    passed INTEGER,
    feedback TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);
CREATE INDEX IF NOT EXISTS idx_tasks_parent_id ON tasks(parent_id);
CREATE INDEX IF NOT EXISTS idx_tasks_path ON tasks(path);
CREATE INDEX IF NOT EXISTS idx_artifacts_task_id ON artifacts(task_id);
CREATE INDEX IF NOT EXISTS idx_assessments_task_id ON assessments(task_id);
"""


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:50]


def init_db(path: Path) -> sqlite3.Connection:
    """Initialize the database and create tables if they don't exist."""
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def get_connection(db_path: Path) -> sqlite3.Connection:
    """Get a database connection."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_task(row: sqlite3.Row) -> Task:
    """Convert a database row to a Task model."""
    return Task(
        id=row["id"],
        parent_id=row["parent_id"],
        type=TaskType(row["type"]),
        title=row["title"],
        description=row["description"],
        status=TaskStatus(row["status"]),
        path=row["path"],
        due_date=datetime.fromisoformat(row["due_date"]) if row["due_date"] else None,
        created_at=datetime.fromisoformat(row["created_at"]),
        completed_at=datetime.fromisoformat(row["completed_at"])
        if row["completed_at"]
        else None,
        metadata=json.loads(row["metadata"]) if row["metadata"] else {},
    )


def _row_to_artifact(row: sqlite3.Row) -> Artifact:
    """Convert a database row to an Artifact model."""
    return Artifact(
        id=row["id"],
        task_id=row["task_id"],
        path=row["path"],
        type=ArtifactType(row["type"]),
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def _row_to_assessment(row: sqlite3.Row) -> Assessment:
    """Convert a database row to an Assessment model."""
    return Assessment(
        id=row["id"],
        task_id=row["task_id"],
        score=row["score"],
        passed=bool(row["passed"]) if row["passed"] is not None else None,
        feedback=row["feedback"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


def create_task(
    conn: sqlite3.Connection,
    title: str,
    task_type: TaskType,
    parent_id: str | None = None,
    description: str | None = None,
    due_date: datetime | None = None,
    path: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> Task:
    """Create a new task."""
    task_id = str(uuid.uuid4())
    now = datetime.now()
    meta = metadata or {}

    conn.execute(
        """
        INSERT INTO tasks
            (id, parent_id, type, title, description, status,
             path, due_date, created_at, metadata)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            task_id,
            parent_id,
            task_type.value,
            title,
            description,
            TaskStatus.PENDING.value,
            path,
            due_date.isoformat() if due_date else None,
            now.isoformat(),
            json.dumps(meta),
        ),
    )
    conn.commit()

    return Task(
        id=task_id,
        parent_id=parent_id,
        type=task_type,
        title=title,
        description=description,
        status=TaskStatus.PENDING,
        path=path,
        due_date=due_date,
        created_at=now,
        completed_at=None,
        metadata=meta,
    )


def get_task(conn: sqlite3.Connection, task_id: str) -> Task | None:
    """Get a task by ID."""
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        return None
    return _row_to_task(row)


def get_task_detail(conn: sqlite3.Connection, task_id: str) -> TaskDetail | None:
    """Get a task with its artifacts and recent assessments."""
    task = get_task(conn, task_id)
    if task is None:
        return None

    artifacts = list_artifacts(conn, task_id)
    assessments = list_assessments(conn, task_id)

    return TaskDetail(
        **task.model_dump(),
        artifacts=artifacts,
        assessments=assessments,
    )


def list_tasks(
    conn: sqlite3.Connection,
    status: TaskStatus | None = None,
    task_type: TaskType | None = None,
    due_before: datetime | None = None,
    parent_id: str | None = None,
    path: str | None = None,
    limit: int = 20,
) -> list[Task]:
    """List tasks with optional filters."""
    query = "SELECT * FROM tasks WHERE 1=1"
    params: list[Any] = []

    if status is not None:
        query += " AND status = ?"
        params.append(status.value)

    if task_type is not None:
        query += " AND type = ?"
        params.append(task_type.value)

    if due_before is not None:
        query += " AND due_date IS NOT NULL AND due_date <= ?"
        params.append(due_before.isoformat())

    if parent_id is not None:
        query += " AND parent_id = ?"
        params.append(parent_id)

    if path is not None:
        query += " AND path = ?"
        params.append(path)

    query += " ORDER BY due_date ASC NULLS LAST, created_at DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    return [_row_to_task(row) for row in rows]


def update_task(
    conn: sqlite3.Connection,
    task_id: str,
    status: TaskStatus | None = None,
    due_date: datetime | None = None,
    description: str | None = None,
    path: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> Task | None:
    """Update task fields."""
    task = get_task(conn, task_id)
    if task is None:
        return None

    updates: list[str] = []
    params: list[Any] = []

    if status is not None:
        updates.append("status = ?")
        params.append(status.value)

    if due_date is not None:
        updates.append("due_date = ?")
        params.append(due_date.isoformat())

    if description is not None:
        updates.append("description = ?")
        params.append(description)

    if path is not None:
        updates.append("path = ?")
        params.append(path)

    if metadata is not None:
        updates.append("metadata = ?")
        params.append(json.dumps(metadata))

    if updates:
        query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
        params.append(task_id)
        conn.execute(query, params)
        conn.commit()

    return get_task(conn, task_id)


def complete_task(conn: sqlite3.Connection, task_id: str) -> Task | None:
    """Mark a task as completed."""
    task = get_task(conn, task_id)
    if task is None:
        return None

    now = datetime.now()
    conn.execute(
        "UPDATE tasks SET status = ?, completed_at = ? WHERE id = ?",
        (TaskStatus.COMPLETED.value, now.isoformat(), task_id),
    )
    conn.commit()

    return get_task(conn, task_id)


def create_artifact(
    conn: sqlite3.Connection,
    task_id: str,
    path: str,
    artifact_type: ArtifactType,
) -> Artifact:
    """Create an artifact linked to a task."""
    artifact_id = str(uuid.uuid4())
    now = datetime.now()

    conn.execute(
        """
        INSERT INTO artifacts (id, task_id, path, type, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (artifact_id, task_id, path, artifact_type.value, now.isoformat()),
    )
    conn.commit()

    return Artifact(
        id=artifact_id,
        task_id=task_id,
        path=path,
        type=artifact_type,
        created_at=now,
    )


def list_artifacts(conn: sqlite3.Connection, task_id: str) -> list[Artifact]:
    """List artifacts for a task."""
    rows = conn.execute(
        "SELECT * FROM artifacts WHERE task_id = ? ORDER BY created_at DESC",
        (task_id,),
    ).fetchall()
    return [_row_to_artifact(row) for row in rows]


def create_assessment(
    conn: sqlite3.Connection,
    task_id: str,
    passed: bool | None = None,
    score: float | None = None,
    feedback: str | None = None,
) -> Assessment:
    """Record an assessment for a task."""
    assessment_id = str(uuid.uuid4())
    now = datetime.now()

    conn.execute(
        """
        INSERT INTO assessments (id, task_id, score, passed, feedback, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            assessment_id,
            task_id,
            score,
            int(passed) if passed is not None else None,
            feedback,
            now.isoformat(),
        ),
    )
    conn.commit()

    return Assessment(
        id=assessment_id,
        task_id=task_id,
        score=score,
        passed=passed,
        feedback=feedback,
        created_at=now,
    )


def list_assessments(conn: sqlite3.Connection, task_id: str) -> list[Assessment]:
    """List assessments for a task."""
    rows = conn.execute(
        "SELECT * FROM assessments WHERE task_id = ? ORDER BY created_at DESC",
        (task_id,),
    ).fetchall()
    return [_row_to_assessment(row) for row in rows]


def get_latest_assessment(conn: sqlite3.Connection, task_id: str) -> Assessment | None:
    """Get the most recent assessment for a task."""
    row = conn.execute(
        "SELECT * FROM assessments WHERE task_id = ? ORDER BY created_at DESC LIMIT 1",
        (task_id,),
    ).fetchone()
    if row is None:
        return None
    return _row_to_assessment(row)


def search_tasks(conn: sqlite3.Connection, query: str, limit: int = 20) -> list[Task]:
    """Full-text search on task titles and descriptions."""
    search_pattern = f"%{query}%"
    rows = conn.execute(
        """
        SELECT * FROM tasks
        WHERE title LIKE ? OR description LIKE ?
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (search_pattern, search_pattern, limit),
    ).fetchall()
    return [_row_to_task(row) for row in rows]


def _is_marimo_notebook(filepath: Path) -> bool:
    """Check if a Python file is a marimo notebook by peeking at the head."""
    try:
        with open(filepath, encoding="utf-8") as f:
            # Read first ~20 lines to check for marimo import
            for _ in range(20):
                line = f.readline()
                if not line:
                    break
                if "import marimo" in line or "from marimo" in line:
                    return True
        return False
    except (OSError, UnicodeDecodeError):
        return False


def infer_artifact_type(path: str, base_path: Path | None = None) -> ArtifactType:
    """Infer artifact type from file path and contents."""
    path_lower = path.lower()
    filename = Path(path).name.lower()

    # Markdown files are notes
    if path_lower.endswith(".md"):
        return ArtifactType.NOTE

    # PDF files
    if path_lower.endswith(".pdf"):
        return ArtifactType.PDF

    # Jupyter notebooks
    if path_lower.endswith(".ipynb"):
        return ArtifactType.NOTEBOOK

    # Python files need more inspection
    if path_lower.endswith(".py"):
        # Test files: test_*.py pattern
        if filename.startswith("test_") or filename == "conftest.py":
            return ArtifactType.TEST_HARNESS

        # Check if it's a marimo notebook
        full_path = Path(path) if base_path is None else base_path / path
        if full_path.exists() and _is_marimo_notebook(full_path):
            return ArtifactType.NOTEBOOK

        # Otherwise it's code
        return ArtifactType.CODE

    return ArtifactType.OTHER
