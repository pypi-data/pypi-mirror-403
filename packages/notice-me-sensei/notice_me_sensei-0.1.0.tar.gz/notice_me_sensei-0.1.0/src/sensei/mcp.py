"""MCP server for Sensei."""

from datetime import datetime
from typing import Literal

from fastmcp import FastMCP

from sensei.db import (
    complete_task as db_complete_task,
)
from sensei.db import (
    create_artifact,
    create_assessment,
    create_task,
    get_connection,
    get_task,
    get_task_detail,
    infer_artifact_type,
    list_artifacts,
    list_assessments,
    list_tasks,
    search_tasks,
)
from sensei.db import (
    update_task as db_update_task,
)
from sensei.init import find_project_root
from sensei.models import ArtifactType, TaskStatus, TaskType
from sensei.srs import (
    calculate_due_date_from_days,
    calculate_next_interval,
    get_initial_srs_metadata,
)


def get_db_connection():
    """Get database connection for the current project."""
    project_root = find_project_root()
    if project_root is None:
        raise RuntimeError("Not in a sensei project. Run 'sensei init' first.")
    return get_connection(project_root / "sensei.db")


def _resolve_task_id(conn, partial_id: str) -> str:
    """Resolve a partial task ID to full ID."""
    tasks = list_tasks(conn, limit=1000)
    matching = [t for t in tasks if t.id.startswith(partial_id)]

    if not matching:
        raise ValueError(f"Task not found: {partial_id}")
    if len(matching) > 1:
        raise ValueError(f"Ambiguous task ID. Matches: {[t.id[:8] for t in matching]}")

    return matching[0].id


# Core business logic functions (testable)
def _task_create(
    title: str,
    type: Literal["learning", "implementation", "srs", "test", "review"],
    parent_id: str | None = None,
    description: str | None = None,
    due_date: str | None = None,
    path: str | None = None,
) -> dict:
    """Create a new study task."""
    conn = get_db_connection()
    type_enum = TaskType(type)
    due_dt = datetime.fromisoformat(due_date) if due_date else None

    metadata = {}
    if type_enum == TaskType.SRS:
        metadata = get_initial_srs_metadata()
        if due_dt is None:
            due_dt = calculate_due_date_from_days(1)

    task = create_task(
        conn,
        title=title,
        task_type=type_enum,
        parent_id=parent_id,
        description=description,
        due_date=due_dt,
        path=path,
        metadata=metadata,
    )

    return task.model_dump(mode="json")


def _task_list(
    status: Literal["pending", "active", "completed", "archived"] | None = None,
    type: Literal["learning", "implementation", "srs", "test", "review"] | None = None,
    due_before: str | None = None,
    parent_id: str | None = None,
    path: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """List tasks with optional filters."""
    conn = get_db_connection()
    status_enum = TaskStatus(status) if status else None
    type_enum = TaskType(type) if type else None

    due_dt = None
    if due_before:
        if due_before.lower() == "today":
            due_dt = datetime.now().replace(hour=23, minute=59, second=59)
        else:
            due_dt = datetime.fromisoformat(due_before)

    tasks = list_tasks(
        conn,
        status=status_enum,
        task_type=type_enum,
        due_before=due_dt,
        parent_id=parent_id,
        path=path,
        limit=limit,
    )

    return [t.model_dump(mode="json") for t in tasks]


def _task_get(id: str) -> dict:
    """Get task details including artifacts and recent assessments."""
    conn = get_db_connection()
    full_id = _resolve_task_id(conn, id)

    detail = get_task_detail(conn, full_id)
    if detail is None:
        raise ValueError(f"Task not found: {id}")

    return detail.model_dump(mode="json")


def _task_update(
    id: str,
    status: Literal["pending", "active", "completed", "archived"] | None = None,
    due_date: str | None = None,
    description: str | None = None,
    path: str | None = None,
) -> dict:
    """Update task fields."""
    conn = get_db_connection()
    full_id = _resolve_task_id(conn, id)

    status_enum = TaskStatus(status) if status else None
    due_dt = datetime.fromisoformat(due_date) if due_date else None

    task = db_update_task(
        conn,
        full_id,
        status=status_enum,
        due_date=due_dt,
        description=description,
        path=path,
    )

    if task is None:
        raise ValueError(f"Task not found: {id}")

    return task.model_dump(mode="json")


def _task_complete(id: str) -> dict:
    """Mark a task as completed."""
    conn = get_db_connection()
    full_id = _resolve_task_id(conn, id)

    task = db_complete_task(conn, full_id)
    if task is None:
        raise ValueError(f"Task not found: {id}")

    return task.model_dump(mode="json")


def _task_schedule_next(
    task_id: str,
    days: int | None = None,
    notes: str | None = None,
) -> dict:
    """Create a follow-up SRS task."""
    conn = get_db_connection()
    full_id = _resolve_task_id(conn, task_id)

    original = get_task(conn, full_id)
    if original is None:
        raise ValueError(f"Task not found: {task_id}")

    # Calculate next interval
    if days is not None:
        due_dt = calculate_due_date_from_days(days)
        new_metadata = original.metadata.copy()
    else:
        # Get latest assessment
        assessments = list_assessments(conn, original.id)
        if assessments:
            latest = assessments[0]
            passed = latest.passed if latest.passed is not None else True
            score = latest.score
        else:
            passed = True
            score = None

        new_metadata, due_dt = calculate_next_interval(original.metadata, passed, score)

    description = original.description
    if notes:
        description = f"{description}\n\n---\nNotes: {notes}" if description else notes

    # Use same parent, or use original as parent if no parent
    parent_id = original.parent_id or original.id

    new_task = create_task(
        conn,
        title=original.title,
        task_type=TaskType.SRS,
        parent_id=parent_id,
        description=description,
        due_date=due_dt,
        path=original.path,
        metadata=new_metadata,
    )

    return new_task.model_dump(mode="json")


def _artifact_add(
    task_id: str,
    path: str,
    type: Literal["note", "code", "notebook", "pdf", "test_harness", "other"]
    | None = None,
) -> dict:
    """Link an artifact to a task."""
    conn = get_db_connection()
    full_id = _resolve_task_id(conn, task_id)

    if type:
        type_enum = ArtifactType(type)
    else:
        project_root = find_project_root()
        type_enum = infer_artifact_type(path, base_path=project_root)

    artifact = create_artifact(conn, full_id, path, type_enum)
    return artifact.model_dump(mode="json")


def _artifact_list(task_id: str) -> list[dict]:
    """List artifacts for a task."""
    conn = get_db_connection()
    full_id = _resolve_task_id(conn, task_id)

    artifacts = list_artifacts(conn, full_id)
    return [a.model_dump(mode="json") for a in artifacts]


def _assessment_record(
    task_id: str,
    passed: bool | None = None,
    score: float | None = None,
    feedback: str | None = None,
) -> dict:
    """Record an assessment for a task."""
    conn = get_db_connection()
    full_id = _resolve_task_id(conn, task_id)

    assessment = create_assessment(
        conn, full_id, passed=passed, score=score, feedback=feedback
    )
    return assessment.model_dump(mode="json")


def _assessment_history(task_id: str) -> list[dict]:
    """Get assessment history for a task."""
    conn = get_db_connection()
    full_id = _resolve_task_id(conn, task_id)

    assessments = list_assessments(conn, full_id)
    return [a.model_dump(mode="json") for a in assessments]


def _search(query: str, limit: int = 20) -> list[dict]:
    """Full-text search on task titles and descriptions."""
    conn = get_db_connection()
    tasks = search_tasks(conn, query, limit=limit)
    return [t.model_dump(mode="json") for t in tasks]


# MCP server and tool definitions
mcp = FastMCP("sensei")


@mcp.tool()
def task_create(
    title: str,
    type: Literal["learning", "implementation", "srs", "test", "review"],
    parent_id: str | None = None,
    description: str | None = None,
    due_date: str | None = None,
    path: str | None = None,
) -> dict:
    """Create a new study task."""
    return _task_create(title, type, parent_id, description, due_date, path)


@mcp.tool()
def task_list(
    status: Literal["pending", "active", "completed", "archived"] | None = None,
    type: Literal["learning", "implementation", "srs", "test", "review"] | None = None,
    due_before: str | None = None,
    parent_id: str | None = None,
    path: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """List tasks with optional filters."""
    return _task_list(status, type, due_before, parent_id, path, limit)


@mcp.tool()
def task_get(id: str) -> dict:
    """Get task details including artifacts and recent assessments."""
    return _task_get(id)


@mcp.tool()
def task_update(
    id: str,
    status: Literal["pending", "active", "completed", "archived"] | None = None,
    due_date: str | None = None,
    description: str | None = None,
    path: str | None = None,
) -> dict:
    """Update task fields."""
    return _task_update(id, status, due_date, description, path)


@mcp.tool()
def task_complete(id: str) -> dict:
    """Mark a task as completed."""
    return _task_complete(id)


@mcp.tool()
def task_schedule_next(
    task_id: str,
    days: int | None = None,
    notes: str | None = None,
) -> dict:
    """Create a follow-up SRS task based on assessment history."""
    return _task_schedule_next(task_id, days, notes)


@mcp.tool()
def artifact_add(
    task_id: str,
    path: str,
    type: Literal["note", "code", "notebook", "pdf", "test_harness", "other"]
    | None = None,
) -> dict:
    """Link an artifact to a task."""
    return _artifact_add(task_id, path, type)


@mcp.tool()
def artifact_list(task_id: str) -> list[dict]:
    """List artifacts for a task."""
    return _artifact_list(task_id)


@mcp.tool()
def assessment_record(
    task_id: str,
    passed: bool | None = None,
    score: float | None = None,
    feedback: str | None = None,
) -> dict:
    """Record an assessment for a task."""
    return _assessment_record(task_id, passed, score, feedback)


@mcp.tool()
def assessment_history(task_id: str) -> list[dict]:
    """Get assessment history for a task."""
    return _assessment_history(task_id)


@mcp.tool()
def search(query: str, limit: int = 20) -> list[dict]:
    """Full-text search on task titles and descriptions."""
    return _search(query, limit)


def run_server():
    """Run the MCP server."""
    mcp.run()
