"""Database operations for Sensei."""

import json
import re
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from sensei.models import (
    Artifact,
    ArtifactType,
    Assessment,
    ContentType,
    Reference,
    Task,
    TaskDetail,
    TaskStatus,
    TaskType,
)


def slugify(text: str, max_length: int = 50) -> str:
    """Convert text to a URL-friendly slug.

    Args:
        text: Text to slugify
        max_length: Maximum length of the slug (default 50)

    Returns:
        Lowercase slug with only alphanumeric chars and hyphens.
    """
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:max_length]


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
    path_prefix: str | None = None,
    blocked: bool | None = None,
    limit: int = 20,
) -> list[Task]:
    """List tasks with optional filters.

    Args:
        conn: Database connection
        status: Filter by status
        task_type: Filter by type
        due_before: Filter by due date
        parent_id: Filter by parent task ID
        path: Exact path match
        path_prefix: Path starts with this prefix
        blocked: If True, only tasks with unresolved blockers;
                 if False, only unblocked tasks
        limit: Maximum number of results
    """
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

    if path_prefix is not None:
        query += " AND path LIKE ?"
        params.append(path_prefix + "%")

    if blocked is not None:
        if blocked:
            # Only tasks with unresolved blockers
            query += """ AND id IN (
                SELECT td.task_id FROM task_dependencies td
                JOIN tasks t ON td.blocked_by_id = t.id
                WHERE t.status != 'completed'
            )"""
        else:
            # Only unblocked tasks (no unresolved blockers)
            query += """ AND id NOT IN (
                SELECT td.task_id FROM task_dependencies td
                JOIN tasks t ON td.blocked_by_id = t.id
                WHERE t.status != 'completed'
            )"""

    query += " ORDER BY due_date ASC NULLS LAST, created_at DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    return [_row_to_task(row) for row in rows]


def update_task(
    conn: sqlite3.Connection,
    task_id: str,
    title: str | None = None,
    parent_id: str | None = None,
    status: TaskStatus | None = None,
    due_date: datetime | None = None,
    description: str | None = None,
    path: str | None = None,
    metadata: dict[str, Any] | None = None,
    clear_parent: bool = False,
) -> Task | None:
    """Update task fields.

    Args:
        conn: Database connection
        task_id: Task ID to update
        title: New title
        parent_id: New parent task ID
        status: New status
        due_date: New due date
        description: New description
        path: New path
        metadata: New metadata (replaces existing)
        clear_parent: If True, set parent_id to NULL (make it a root task)
    """
    task = get_task(conn, task_id)
    if task is None:
        return None

    updates: list[str] = []
    params: list[Any] = []

    if title is not None:
        updates.append("title = ?")
        params.append(title)

    if parent_id is not None:
        updates.append("parent_id = ?")
        params.append(parent_id)
    elif clear_parent:
        updates.append("parent_id = NULL")

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


def delete_task(conn: sqlite3.Connection, task_id: str, cascade: bool = False) -> int:
    """Delete a task.

    Args:
        conn: Database connection
        task_id: Task ID to delete
        cascade: If True, delete all descendant tasks. If False and task has
                 children, raises ValueError.

    Returns:
        Count of deleted tasks

    Raises:
        ValueError: If task has children and cascade is False
    """
    # Check if task exists
    task = get_task(conn, task_id)
    if task is None:
        raise ValueError(f"Task not found: {task_id}")

    # Check for children
    children = conn.execute(
        "SELECT id FROM tasks WHERE parent_id = ?", (task_id,)
    ).fetchall()

    if children and not cascade:
        raise ValueError(
            f"Task has {len(children)} children. Use cascade=True to delete them."
        )

    if cascade:
        # Get all descendants using recursive CTE
        descendants = conn.execute(
            """
            WITH RECURSIVE descendant_tree AS (
                SELECT id FROM tasks WHERE id = ?
                UNION ALL
                SELECT t.id FROM tasks t
                JOIN descendant_tree dt ON t.parent_id = dt.id
            )
            SELECT id FROM descendant_tree
            """,
            (task_id,),
        ).fetchall()
        descendant_ids = [row["id"] for row in descendants]

        # Delete related artifacts and assessments first
        placeholders = ",".join("?" * len(descendant_ids))
        conn.execute(
            f"DELETE FROM artifacts WHERE task_id IN ({placeholders})",
            descendant_ids,
        )
        conn.execute(
            f"DELETE FROM assessments WHERE task_id IN ({placeholders})",
            descendant_ids,
        )
        conn.execute(
            f"DELETE FROM task_dependencies WHERE task_id IN ({placeholders}) "
            f"OR blocked_by_id IN ({placeholders})",
            descendant_ids + descendant_ids,
        )
        conn.execute(
            f"DELETE FROM tasks WHERE id IN ({placeholders})",
            descendant_ids,
        )
        conn.commit()
        return len(descendant_ids)
    else:
        # Delete single task
        conn.execute("DELETE FROM artifacts WHERE task_id = ?", (task_id,))
        conn.execute("DELETE FROM assessments WHERE task_id = ?", (task_id,))
        conn.execute(
            "DELETE FROM task_dependencies WHERE task_id = ? OR blocked_by_id = ?",
            (task_id, task_id),
        )
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        return 1


def move_task(
    conn: sqlite3.Connection,
    task_id: str,
    new_parent_id: str | None,
    new_path: str | None = None,
) -> int:
    """Move a task (and its subtree) to a new parent.

    Args:
        conn: Database connection
        task_id: Task ID to move
        new_parent_id: New parent task ID, or None to make it a root task
        new_path: Optional new path for the task. If provided, all descendant
                  paths will be rebased (old_path prefix replaced with new_path)

    Returns:
        Count of tasks with updated paths
    """
    task = get_task(conn, task_id)
    if task is None:
        raise ValueError(f"Task not found: {task_id}")

    # Update parent
    if new_parent_id is None:
        conn.execute("UPDATE tasks SET parent_id = NULL WHERE id = ?", (task_id,))
    else:
        # Verify new parent exists
        parent = get_task(conn, new_parent_id)
        if parent is None:
            raise ValueError(f"Parent task not found: {new_parent_id}")
        conn.execute(
            "UPDATE tasks SET parent_id = ? WHERE id = ?", (new_parent_id, task_id)
        )

    moved_count = 1

    # Rebase paths if new_path provided
    if new_path is not None:
        old_path = task.path

        # Update this task's path
        conn.execute("UPDATE tasks SET path = ? WHERE id = ?", (new_path, task_id))

        # Update descendant paths if old_path was set
        if old_path:
            # Get all descendants with paths starting with old_path
            descendants = conn.execute(
                "SELECT id, path FROM tasks WHERE path LIKE ? AND id != ?",
                (old_path + "%", task_id),
            ).fetchall()

            for desc in descendants:
                if desc["path"]:
                    # Replace old_path prefix with new_path
                    updated_path = new_path + desc["path"][len(old_path) :]
                    conn.execute(
                        "UPDATE tasks SET path = ? WHERE id = ?",
                        (updated_path, desc["id"]),
                    )
                    moved_count += 1

    conn.commit()
    return moved_count


def get_task_blockers(conn: sqlite3.Connection, task_id: str) -> list[str]:
    """Get IDs of tasks that block the given task."""
    rows = conn.execute(
        "SELECT blocked_by_id FROM task_dependencies WHERE task_id = ?",
        (task_id,),
    ).fetchall()
    return [row["blocked_by_id"] for row in rows]


def get_tasks_blocked_by(conn: sqlite3.Connection, task_id: str) -> list[str]:
    """Get IDs of tasks that are blocked by the given task."""
    rows = conn.execute(
        "SELECT task_id FROM task_dependencies WHERE blocked_by_id = ?",
        (task_id,),
    ).fetchall()
    return [row["task_id"] for row in rows]


def add_blocker(conn: sqlite3.Connection, task_id: str, blocked_by_id: str) -> None:
    """Add a blocking dependency."""
    dep_id = str(uuid.uuid4())
    now = datetime.now()
    try:
        conn.execute(
            """
            INSERT INTO task_dependencies (id, task_id, blocked_by_id, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (dep_id, task_id, blocked_by_id, now.isoformat()),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        # Dependency already exists, ignore
        pass


def remove_blocker(conn: sqlite3.Connection, task_id: str, blocked_by_id: str) -> None:
    """Remove a blocking dependency."""
    conn.execute(
        "DELETE FROM task_dependencies WHERE task_id = ? AND blocked_by_id = ?",
        (task_id, blocked_by_id),
    )
    conn.commit()


def bulk_update_tasks(
    conn: sqlite3.Connection,
    task_ids: list[str] | None = None,
    path_prefix: str | None = None,
    parent_id: str | None = None,
    status_filter: TaskStatus | None = None,
    new_status: TaskStatus | None = None,
    path_replace_old: str | None = None,
    path_replace_new: str | None = None,
    due_date_shift_days: int | None = None,
) -> int:
    """Update multiple tasks matching a filter.

    Args:
        conn: Database connection
        task_ids: Specific task IDs to update
        path_prefix: Tasks with paths starting with this
        parent_id: Direct children of this task
        status_filter: Tasks with this status
        new_status: Set status to this value
        path_replace_old: Old path prefix to replace
        path_replace_new: New path prefix
        due_date_shift_days: Shift all due dates by this many days

    Returns:
        Count of updated tasks
    """
    # Build filter query
    filter_query = "SELECT id, path, due_date FROM tasks WHERE 1=1"
    filter_params: list[Any] = []

    if task_ids:
        placeholders = ",".join("?" * len(task_ids))
        filter_query += f" AND id IN ({placeholders})"
        filter_params.extend(task_ids)

    if path_prefix:
        filter_query += " AND path LIKE ?"
        filter_params.append(path_prefix + "%")

    if parent_id:
        filter_query += " AND parent_id = ?"
        filter_params.append(parent_id)

    if status_filter:
        filter_query += " AND status = ?"
        filter_params.append(status_filter.value)

    rows = conn.execute(filter_query, filter_params).fetchall()
    updated_count = 0

    for row in rows:
        updates: list[str] = []
        params: list[Any] = []

        if new_status is not None:
            updates.append("status = ?")
            params.append(new_status.value)

        if path_replace_old is not None and path_replace_new is not None:
            current_path = row["path"]
            if current_path and current_path.startswith(path_replace_old):
                new_path = path_replace_new + current_path[len(path_replace_old) :]
                updates.append("path = ?")
                params.append(new_path)

        if due_date_shift_days is not None:
            current_due = row["due_date"]
            if current_due:
                current_dt = datetime.fromisoformat(current_due)
                new_dt = current_dt + timedelta(days=due_date_shift_days)
                updates.append("due_date = ?")
                params.append(new_dt.isoformat())

        if updates:
            query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
            params.append(row["id"])
            conn.execute(query, params)
            updated_count += 1

    conn.commit()
    return updated_count


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


# Reference operations


def _row_to_reference(row: sqlite3.Row) -> Reference:
    """Convert a database row to a Reference model."""
    return Reference(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        authors=row["authors"],
        url=row["url"],
        file_path=row["file_path"],
        content_type=ContentType(row["content_type"]),
        tags=json.loads(row["tags"]) if row["tags"] else [],
        metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"])
        if row["updated_at"]
        else None,
    )


def create_reference(
    conn: sqlite3.Connection,
    title: str,
    content_type: ContentType,
    description: str | None = None,
    authors: str | None = None,
    url: str | None = None,
    file_path: str | None = None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> Reference:
    """Create a new reference.

    Args:
        conn: Database connection
        title: Reference title
        content_type: Type of content (webpage, pdf, etc.)
        description: Optional description
        authors: Optional authors string
        url: Optional source URL
        file_path: Optional local file path (relative to references/)
        tags: Optional list of tags
        metadata: Optional additional metadata

    Returns:
        Created Reference object.
    """
    ref_id = str(uuid.uuid4())
    now = datetime.now()
    tags_json = json.dumps(tags or [])
    meta_json = json.dumps(metadata or {})

    conn.execute(
        """
        INSERT INTO "references"
            (id, title, description, authors, url, file_path,
             content_type, tags, metadata, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ref_id,
            title,
            description,
            authors,
            url,
            file_path,
            content_type.value,
            tags_json,
            meta_json,
            now.isoformat(),
        ),
    )
    conn.commit()

    return Reference(
        id=ref_id,
        title=title,
        description=description,
        authors=authors,
        url=url,
        file_path=file_path,
        content_type=content_type,
        tags=tags or [],
        metadata=metadata or {},
        created_at=now,
        updated_at=None,
    )


def get_reference(conn: sqlite3.Connection, ref_id: str) -> Reference | None:
    """Get a reference by ID.

    Args:
        conn: Database connection
        ref_id: Reference ID (can be partial)

    Returns:
        Reference object or None if not found.
    """
    # Try exact match first
    row = conn.execute('SELECT * FROM "references" WHERE id = ?', (ref_id,)).fetchone()

    if row is None:
        # Try partial match
        rows = conn.execute(
            'SELECT * FROM "references" WHERE id LIKE ?', (ref_id + "%",)
        ).fetchall()
        if len(rows) == 1:
            row = rows[0]
        elif len(rows) > 1:
            raise ValueError(
                f"Ambiguous reference ID. Matches: {[r['id'][:8] for r in rows]}"
            )

    if row is None:
        return None
    return _row_to_reference(row)


def search_references(
    conn: sqlite3.Connection,
    query: str | None = None,
    content_type: ContentType | None = None,
    tags: list[str] | None = None,
    limit: int = 20,
) -> list[Reference]:
    """Search references.

    Args:
        conn: Database connection
        query: FTS query string (searches title, description, authors)
        content_type: Filter by content type
        tags: Filter by tags (any match)
        limit: Maximum results

    Returns:
        List of matching references.
    """
    # Check if FTS5 is available by checking for the references_fts table
    fts_available = (
        conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='references_fts'"
        ).fetchone()
        is not None
    )

    if query and fts_available:
        # Use FTS5 for text search
        base_query = """
            SELECT r.* FROM "references" r
            JOIN references_fts fts ON r.rowid = fts.rowid
            WHERE references_fts MATCH ?
        """
        params: list[Any] = [query]
    elif query:
        # Fallback to LIKE search
        base_query = """
            SELECT * FROM "references"
            WHERE title LIKE ? OR description LIKE ? OR authors LIKE ?
        """
        search_pattern = f"%{query}%"
        params = [search_pattern, search_pattern, search_pattern]
    else:
        base_query = 'SELECT * FROM "references" WHERE 1=1'
        params = []

    if content_type:
        base_query += " AND content_type = ?"
        params.append(content_type.value)

    if tags:
        # Filter by any matching tag using JSON
        for tag in tags:
            base_query += " AND tags LIKE ?"
            params.append(f'%"{tag}"%')

    base_query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(base_query, params).fetchall()
    return [_row_to_reference(row) for row in rows]


def update_reference(
    conn: sqlite3.Connection,
    ref_id: str,
    title: str | None = None,
    description: str | None = None,
    authors: str | None = None,
    url: str | None = None,
    file_path: str | None = None,
    content_type: ContentType | None = None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> Reference | None:
    """Update reference fields.

    Args:
        conn: Database connection
        ref_id: Reference ID
        title: New title
        description: New description
        authors: New authors
        url: New URL
        file_path: New file path
        content_type: New content type
        tags: New tags (replaces existing)
        metadata: New metadata (replaces existing)

    Returns:
        Updated Reference or None if not found.
    """
    ref = get_reference(conn, ref_id)
    if ref is None:
        return None

    updates: list[str] = []
    params: list[Any] = []

    if title is not None:
        updates.append("title = ?")
        params.append(title)

    if description is not None:
        updates.append("description = ?")
        params.append(description)

    if authors is not None:
        updates.append("authors = ?")
        params.append(authors)

    if url is not None:
        updates.append("url = ?")
        params.append(url)

    if file_path is not None:
        updates.append("file_path = ?")
        params.append(file_path)

    if content_type is not None:
        updates.append("content_type = ?")
        params.append(content_type.value)

    if tags is not None:
        updates.append("tags = ?")
        params.append(json.dumps(tags))

    if metadata is not None:
        updates.append("metadata = ?")
        params.append(json.dumps(metadata))

    if updates:
        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())

        query = f'UPDATE "references" SET {", ".join(updates)} WHERE id = ?'
        params.append(ref.id)
        conn.execute(query, params)
        conn.commit()

    return get_reference(conn, ref.id)


def delete_reference(conn: sqlite3.Connection, ref_id: str) -> bool:
    """Delete a reference.

    Args:
        conn: Database connection
        ref_id: Reference ID

    Returns:
        True if deleted, False if not found.
    """
    ref = get_reference(conn, ref_id)
    if ref is None:
        return False

    conn.execute('DELETE FROM "references" WHERE id = ?', (ref.id,))
    conn.commit()
    return True
