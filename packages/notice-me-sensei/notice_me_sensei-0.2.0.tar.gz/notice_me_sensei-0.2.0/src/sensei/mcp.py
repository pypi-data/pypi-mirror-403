"""MCP server for Sensei."""

import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Literal

from fastmcp import FastMCP

from sensei.db import (
    add_blocker,
    bulk_update_tasks,
    create_artifact,
    create_assessment,
    create_reference,
    create_task,
    delete_reference,
    get_connection,
    get_reference,
    get_task,
    get_task_blockers,
    get_task_detail,
    get_tasks_blocked_by,
    infer_artifact_type,
    list_artifacts,
    list_assessments,
    list_tasks,
    remove_blocker,
    search_references,
    search_tasks,
    slugify,
    update_reference,
)
from sensei.db import (
    complete_task as db_complete_task,
)
from sensei.db import (
    delete_task as db_delete_task,
)
from sensei.db import (
    move_task as db_move_task,
)
from sensei.db import (
    update_task as db_update_task,
)
from sensei.init import find_project_root, get_db_path
from sensei.models import ArtifactType, ContentType, TaskStatus, TaskType
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
    return get_connection(get_db_path(project_root))


def _ensure_path_exists(path: str) -> None:
    """Create directory for task path if it doesn't exist."""
    project_root = find_project_root()
    if project_root is None:
        return
    full_path = project_root / path
    full_path.mkdir(parents=True, exist_ok=True)


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

    if path:
        _ensure_path_exists(path)

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
    path_prefix: str | None = None,
    blocked: bool | None = None,
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
        path_prefix=path_prefix,
        blocked=blocked,
        limit=limit,
    )

    return [t.model_dump(mode="json") for t in tasks]


def _task_get(id: str) -> dict:
    """Get task details including artifacts, assessments, and dependencies."""
    conn = get_db_connection()
    full_id = _resolve_task_id(conn, id)

    detail = get_task_detail(conn, full_id)
    if detail is None:
        raise ValueError(f"Task not found: {id}")

    result = detail.model_dump(mode="json")

    # Add dependency information
    result["blocked_by"] = get_task_blockers(conn, full_id)
    result["blocks"] = get_tasks_blocked_by(conn, full_id)

    return result


def _task_update(
    id: str,
    title: str | None = None,
    parent_id: str | None = None,
    status: Literal["pending", "active", "completed", "archived"] | None = None,
    due_date: str | None = None,
    description: str | None = None,
    path: str | None = None,
    add_blocked_by: list[str] | None = None,
    remove_blocked_by: list[str] | None = None,
) -> dict:
    """Update task fields.

    Args:
        id: Task ID (can be partial)
        title: New title
        parent_id: New parent task ID. Use empty string "" to make it a root task.
        status: New status
        due_date: New due date (ISO format)
        description: New description
        path: New path
        add_blocked_by: Task IDs to add as blockers
        remove_blocked_by: Task IDs to remove as blockers
    """
    conn = get_db_connection()
    full_id = _resolve_task_id(conn, id)

    if path:
        _ensure_path_exists(path)

    status_enum = TaskStatus(status) if status else None
    due_dt = datetime.fromisoformat(due_date) if due_date else None

    # Handle parent_id: empty string means clear parent
    clear_parent = parent_id == ""
    actual_parent_id = None if parent_id == "" else parent_id

    # Resolve partial parent_id to full ID
    if actual_parent_id:
        actual_parent_id = _resolve_task_id(conn, actual_parent_id)

    task = db_update_task(
        conn,
        full_id,
        title=title,
        parent_id=actual_parent_id,
        status=status_enum,
        due_date=due_dt,
        description=description,
        path=path,
        clear_parent=clear_parent,
    )

    if task is None:
        raise ValueError(f"Task not found: {id}")

    # Handle dependency updates
    if add_blocked_by:
        for blocker_id in add_blocked_by:
            blocker_full_id = _resolve_task_id(conn, blocker_id)
            add_blocker(conn, full_id, blocker_full_id)

    if remove_blocked_by:
        for blocker_id in remove_blocked_by:
            blocker_full_id = _resolve_task_id(conn, blocker_id)
            remove_blocker(conn, full_id, blocker_full_id)

    # Return updated task with dependencies
    return _task_get(full_id)


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


def _task_delete(id: str, cascade: bool = False) -> dict:
    """Delete a task.

    Args:
        id: Task ID to delete
        cascade: If True, delete all descendant tasks. If False and task has
                 children, return an error.

    Returns:
        {"deleted": int} - count of deleted tasks
    """
    conn = get_db_connection()
    full_id = _resolve_task_id(conn, id)
    deleted = db_delete_task(conn, full_id, cascade=cascade)
    return {"deleted": deleted}


def _task_move(
    id: str,
    new_parent_id: str | None,
    new_path: str | None = None,
) -> dict:
    """Move a task (and its subtree) to a new parent.

    Args:
        id: Task ID to move
        new_parent_id: New parent task ID, or None/"" to make it a root task
        new_path: Optional new path for the task. If provided, all descendant
                  paths will be rebased (old_path prefix replaced with new_path)

    Returns:
        {"moved": int} - count of tasks with updated paths
    """
    conn = get_db_connection()
    full_id = _resolve_task_id(conn, id)

    # Handle empty string as None for new_parent_id
    actual_parent_id = None if new_parent_id == "" else new_parent_id
    if actual_parent_id:
        actual_parent_id = _resolve_task_id(conn, actual_parent_id)

    if new_path:
        _ensure_path_exists(new_path)

    moved = db_move_task(conn, full_id, actual_parent_id, new_path)
    return {"moved": moved}


def _parse_relative_date(date_str: str, base_date: datetime) -> datetime:
    """Parse a relative date string like '+7d', '+2w', '+1m'."""
    if not date_str.startswith("+") and not date_str.startswith("-"):
        # Absolute date
        return datetime.fromisoformat(date_str)

    match = re.match(r"([+-])(\d+)([dwm])", date_str)
    if not match:
        raise ValueError(f"Invalid relative date format: {date_str}")

    sign = 1 if match.group(1) == "+" else -1
    value = int(match.group(2)) * sign
    unit = match.group(3)

    if unit == "d":
        return base_date + timedelta(days=value)
    elif unit == "w":
        return base_date + timedelta(weeks=value)
    elif unit == "m":
        # Approximate month as 30 days
        return base_date + timedelta(days=value * 30)
    else:
        raise ValueError(f"Invalid relative date unit: {unit}")


def _task_bulk_create(
    tasks: list[dict[str, Any]],
    base_path: str | None = None,
    base_due_date: str | None = None,
) -> dict:
    """Create multiple tasks at once.

    Args:
        tasks: List of task definitions. Each can have:
            - title (required)
            - type (required)
            - description
            - path (can be relative if base_path provided)
            - due_date (relative like "+7d", "+2w" if base_due_date set)
            - parent_id (or "parent_ref" to ref another task by index)
            - children (nested task definitions, auto-sets parent_id)
        base_path: Prefix for all relative paths
        base_due_date: Base date for relative due_date (ISO format or "today")

    Returns:
        {"created": int, "task_ids": list[str]}
    """
    conn = get_db_connection()

    # Parse base_due_date
    base_dt: datetime | None = None
    if base_due_date:
        if base_due_date.lower() == "today":
            base_dt = datetime.now()
        else:
            base_dt = datetime.fromisoformat(base_due_date)

    created_ids: list[str] = []
    index_to_id: dict[int, str] = {}

    def create_task_recursive(
        task_def: dict[str, Any], index: int, parent_id: str | None = None
    ) -> str:
        """Create a single task and its children."""
        title = task_def.get("title")
        task_type = task_def.get("type")

        if not title or not task_type:
            raise ValueError(
                f"Task at index {index} missing required 'title' or 'type'"
            )

        # Build path
        path = task_def.get("path")
        if path and base_path:
            # Combine base_path with relative path
            path = f"{base_path}/{path}"
        elif not path and base_path:
            path = base_path

        # Build due_date
        due_date_str = task_def.get("due_date")
        due_dt: datetime | None = None
        if due_date_str:
            if base_dt and (
                due_date_str.startswith("+") or due_date_str.startswith("-")
            ):
                due_dt = _parse_relative_date(due_date_str, base_dt)
            else:
                due_dt = datetime.fromisoformat(due_date_str)

        # Resolve parent
        actual_parent_id = parent_id
        if task_def.get("parent_id"):
            actual_parent_id = _resolve_task_id(conn, task_def["parent_id"])
        elif task_def.get("parent_ref") is not None:
            ref_index = task_def["parent_ref"]
            if ref_index not in index_to_id:
                raise ValueError(
                    f"Task at index {index} references parent_ref {ref_index} "
                    "which hasn't been created yet"
                )
            actual_parent_id = index_to_id[ref_index]

        # Ensure path directory exists
        if path:
            _ensure_path_exists(path)

        # Create task
        type_enum = TaskType(task_type)
        metadata = {}
        if type_enum == TaskType.SRS:
            metadata = get_initial_srs_metadata()
            if due_dt is None:
                due_dt = calculate_due_date_from_days(1)

        task = create_task(
            conn,
            title=title,
            task_type=type_enum,
            parent_id=actual_parent_id,
            description=task_def.get("description"),
            due_date=due_dt,
            path=path,
            metadata=metadata,
        )

        created_ids.append(task.id)
        index_to_id[index] = task.id

        # Create children
        children = task_def.get("children", [])
        for child_def in children:
            create_task_recursive(child_def, len(created_ids), parent_id=task.id)

        return task.id

    # Create all top-level tasks
    for i, task_def in enumerate(tasks):
        create_task_recursive(task_def, i)

    return {"created": len(created_ids), "task_ids": created_ids}


def _task_bulk_update(
    filter: dict[str, Any],
    updates: dict[str, Any],
) -> dict:
    """Update multiple tasks matching a filter.

    Args:
        filter: Query filter (at least one required):
            - ids: list[str] - specific task IDs
            - path_prefix: str - tasks with paths starting with this
            - parent_id: str - direct children of this task
            - status: str - tasks with this status
        updates: Fields to update:
            - status: str
            - path_replace: {"old": str, "new": str} - replace path prefix
            - due_date_shift: str - shift all due dates (e.g., "+7d", "-3d")

    Returns:
        {"updated": int}
    """
    conn = get_db_connection()

    # Validate filter - at least one required
    if not any(filter.get(k) for k in ["ids", "path_prefix", "parent_id", "status"]):
        raise ValueError(
            "At least one filter required: ids, path_prefix, parent_id, or status"
        )

    # Parse filter
    task_ids: list[str] | None = None
    if filter.get("ids"):
        task_ids = [_resolve_task_id(conn, tid) for tid in filter["ids"]]

    path_prefix = filter.get("path_prefix")
    parent_id = filter.get("parent_id")
    if parent_id:
        parent_id = _resolve_task_id(conn, parent_id)
    status_filter = TaskStatus(filter["status"]) if filter.get("status") else None

    # Parse updates
    new_status = TaskStatus(updates["status"]) if updates.get("status") else None

    path_replace_old: str | None = None
    path_replace_new: str | None = None
    if updates.get("path_replace"):
        path_replace_old = updates["path_replace"].get("old")
        path_replace_new = updates["path_replace"].get("new")

    due_date_shift_days: int | None = None
    if updates.get("due_date_shift"):
        shift_str = updates["due_date_shift"]
        match = re.match(r"([+-])(\d+)([dwm])", shift_str)
        if match:
            sign = 1 if match.group(1) == "+" else -1
            value = int(match.group(2)) * sign
            unit = match.group(3)
            if unit == "d":
                due_date_shift_days = value
            elif unit == "w":
                due_date_shift_days = value * 7
            elif unit == "m":
                due_date_shift_days = value * 30
        else:
            raise ValueError(f"Invalid due_date_shift format: {shift_str}")

    updated = bulk_update_tasks(
        conn,
        task_ids=task_ids,
        path_prefix=path_prefix,
        parent_id=parent_id,
        status_filter=status_filter,
        new_status=new_status,
        path_replace_old=path_replace_old,
        path_replace_new=path_replace_new,
        due_date_shift_days=due_date_shift_days,
    )

    return {"updated": updated}


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
def sensei_study_create(
    title: str,
    type: Literal["learning", "implementation", "srs", "test", "review"],
    parent_id: str | None = None,
    description: str | None = None,
    due_date: str | None = None,
    path: str | None = None,
) -> dict:
    """Create a new sensei study task for learning with spaced repetition."""
    return _task_create(title, type, parent_id, description, due_date, path)


@mcp.tool()
def sensei_study_list(
    status: Literal["pending", "active", "completed", "archived"] | None = None,
    type: Literal["learning", "implementation", "srs", "test", "review"] | None = None,
    due_before: str | None = None,
    parent_id: str | None = None,
    path: str | None = None,
    path_prefix: str | None = None,
    blocked: bool | None = None,
    limit: int = 20,
) -> list[dict]:
    """List sensei study tasks with optional filters.

    Args:
        status: Filter by task status
        type: Filter by task type
        due_before: Filter tasks due before this date (ISO format or "today")
        parent_id: Filter by parent task ID
        path: Exact path match
        path_prefix: Path starts with this prefix
        blocked: If True, only tasks with unresolved blockers; if False, only unblocked
        limit: Maximum number of results
    """
    return _task_list(
        status, type, due_before, parent_id, path, path_prefix, blocked, limit
    )


@mcp.tool()
def sensei_study_get(id: str) -> dict:
    """Get sensei study task details including artifacts and assessments."""
    return _task_get(id)


@mcp.tool()
def sensei_study_update(
    id: str,
    title: str | None = None,
    parent_id: str | None = None,
    status: Literal["pending", "active", "completed", "archived"] | None = None,
    due_date: str | None = None,
    description: str | None = None,
    path: str | None = None,
    add_blocked_by: list[str] | None = None,
    remove_blocked_by: list[str] | None = None,
) -> dict:
    """Update sensei study task fields.

    Args:
        id: Task ID (can be partial)
        title: New title
        parent_id: New parent task ID. Use empty string "" to make it a root task.
        status: New status
        due_date: New due date (ISO format)
        description: New description
        path: New path
        add_blocked_by: Task IDs that block this task
        remove_blocked_by: Task IDs to remove as blockers
    """
    return _task_update(
        id,
        title,
        parent_id,
        status,
        due_date,
        description,
        path,
        add_blocked_by,
        remove_blocked_by,
    )


@mcp.tool()
def sensei_study_complete(id: str) -> dict:
    """Mark a sensei study task as completed."""
    return _task_complete(id)


@mcp.tool()
def sensei_study_schedule_next(
    task_id: str,
    days: int | None = None,
    notes: str | None = None,
) -> dict:
    """Create a follow-up SRS review task based on spaced repetition algorithm."""
    return _task_schedule_next(task_id, days, notes)


@mcp.tool()
def sensei_study_delete(
    id: str,
    cascade: bool = False,
) -> dict:
    """Delete a sensei study task.

    Args:
        id: Task ID to delete (can be partial)
        cascade: If True, delete all descendant tasks. If False and task has
                 children, returns an error.

    Returns:
        {"deleted": int} - count of deleted tasks
    """
    return _task_delete(id, cascade)


@mcp.tool()
def sensei_study_move(
    id: str,
    new_parent_id: str | None = None,
    new_path: str | None = None,
) -> dict:
    """Move a sensei study task (and its subtree) to a new parent.

    Args:
        id: Task ID to move (can be partial)
        new_parent_id: New parent task ID, or None/"" to make it a root task
        new_path: Optional new path for the task. If provided, all descendant
                  paths will be rebased (old_path prefix replaced with new_path)

    Returns:
        {"moved": int} - count of tasks with updated paths
    """
    return _task_move(id, new_parent_id, new_path)


@mcp.tool()
def sensei_study_bulk_create(
    tasks: list[dict[str, Any]],
    base_path: str | None = None,
    base_due_date: str | None = None,
) -> dict:
    """Create multiple sensei study tasks at once.

    Args:
        tasks: List of task definitions. Each can have:
            - title (required)
            - type (required): learning, implementation, srs, test, review
            - description
            - path (can be relative if base_path provided)
            - due_date (relative like "+7d", "+2w", "+1m" if base_due_date set)
            - parent_id (or "parent_ref" to ref another task in batch by index)
            - children (nested task definitions, auto-sets parent_id)
        base_path: Prefix for all relative paths
        base_due_date: Base date for relative due_date (ISO format or "today")

    Returns:
        {"created": int, "task_ids": list[str]}

    Example:
        sensei_study_bulk_create(
            base_path="topics/phase1",
            base_due_date="2026-02-01",
            tasks=[{
                "title": "Week 1-2: Foundations",
                "type": "learning",
                "path": "week1-2",
                "due_date": "+14d",
                "children": [
                    {"title": "Read paper X", "type": "learning"},
                    {"title": "Implement Y", "type": "implementation"},
                ]
            }]
        )
    """
    return _task_bulk_create(tasks, base_path, base_due_date)


@mcp.tool()
def sensei_study_bulk_update(
    filter: dict[str, Any],
    updates: dict[str, Any],
) -> dict:
    """Update multiple sensei study tasks matching a filter.

    Args:
        filter: Query filter (at least one required):
            - ids: list[str] - specific task IDs
            - path_prefix: str - tasks with paths starting with this
            - parent_id: str - direct children of this task
            - status: str - tasks with this status
        updates: Fields to update:
            - status: str - new status
            - path_replace: {"old": str, "new": str} - replace path prefix
            - due_date_shift: str - shift all due dates (e.g., "+7d", "-3d")

    Returns:
        {"updated": int}

    Examples:
        # Shift all Phase 1 tasks by 1 week:
        sensei_study_bulk_update(
            filter={"path_prefix": "topics/phase1"},
            updates={"due_date_shift": "+7d"}
        )

        # Rename path prefix:
        sensei_study_bulk_update(
            filter={"path_prefix": "topics/old"},
            updates={"path_replace": {"old": "topics/old", "new": "topics/new"}}
        )
    """
    return _task_bulk_update(filter, updates)


@mcp.tool()
def sensei_artifact_add(
    task_id: str,
    path: str,
    type: Literal["note", "code", "notebook", "pdf", "test_harness", "other"]
    | None = None,
) -> dict:
    """Link a study artifact (notes, code, etc.) to a sensei task."""
    return _artifact_add(task_id, path, type)


@mcp.tool()
def sensei_artifact_list(task_id: str) -> list[dict]:
    """List study artifacts linked to a sensei task."""
    return _artifact_list(task_id)


@mcp.tool()
def sensei_assessment_record(
    task_id: str,
    passed: bool | None = None,
    score: float | None = None,
    feedback: str | None = None,
) -> dict:
    """Record a learning assessment for a sensei study task."""
    return _assessment_record(task_id, passed, score, feedback)


@mcp.tool()
def sensei_assessment_history(task_id: str) -> list[dict]:
    """Get assessment history for a sensei study task."""
    return _assessment_history(task_id)


@mcp.tool()
def sensei_search(query: str, limit: int = 20) -> list[dict]:
    """Search sensei study tasks by title and description."""
    return _search(query, limit)


# Reference management functions


def _reference_create(
    title: str,
    content_type: Literal[
        "webpage", "pdf", "arxiv", "book", "video", "paper", "documentation", "other"
    ],
    description: str | None = None,
    authors: str | None = None,
    url: str | None = None,
    file_path: str | None = None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict:
    """Create a new reference.

    Args:
        title: Reference title
        content_type: Type of content
        description: Optional description or summary
        authors: Optional authors string
        url: Optional source URL
        file_path: Optional local file path (relative to references/)
        tags: Optional list of tags
        metadata: Optional additional metadata

    Returns:
        Created reference as dict.
    """
    conn = get_db_connection()
    type_enum = ContentType(content_type)

    ref = create_reference(
        conn,
        title=title,
        content_type=type_enum,
        description=description,
        authors=authors,
        url=url,
        file_path=file_path,
        tags=tags,
        metadata=metadata,
    )

    return ref.model_dump(mode="json")


def _reference_search(
    query: str | None = None,
    id: str | None = None,
    content_type: Literal[
        "webpage", "pdf", "arxiv", "book", "video", "paper", "documentation", "other"
    ]
    | None = None,
    tags: list[str] | None = None,
    limit: int = 20,
) -> list[dict]:
    """Search references.

    Args:
        query: FTS query string (searches title, description, authors)
        id: Direct lookup by ID (partial match supported)
        content_type: Filter by content type
        tags: Filter by tags (any match)
        limit: Maximum results

    Returns:
        List of matching references.
    """
    conn = get_db_connection()

    # Direct lookup by ID
    if id:
        ref = get_reference(conn, id)
        if ref:
            return [ref.model_dump(mode="json")]
        return []

    type_enum = ContentType(content_type) if content_type else None
    refs = search_references(
        conn, query=query, content_type=type_enum, tags=tags, limit=limit
    )
    return [r.model_dump(mode="json") for r in refs]


def _reference_update(
    id: str,
    title: str | None = None,
    description: str | None = None,
    authors: str | None = None,
    url: str | None = None,
    file_path: str | None = None,
    content_type: Literal[
        "webpage", "pdf", "arxiv", "book", "video", "paper", "documentation", "other"
    ]
    | None = None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict:
    """Update a reference.

    Args:
        id: Reference ID (partial match supported)
        title: New title
        description: New description
        authors: New authors
        url: New URL
        file_path: New file path
        content_type: New content type
        tags: New tags (replaces existing)
        metadata: New metadata (replaces existing)

    Returns:
        Updated reference as dict.
    """
    conn = get_db_connection()
    type_enum = ContentType(content_type) if content_type else None

    ref = update_reference(
        conn,
        ref_id=id,
        title=title,
        description=description,
        authors=authors,
        url=url,
        file_path=file_path,
        content_type=type_enum,
        tags=tags,
        metadata=metadata,
    )

    if ref is None:
        raise ValueError(f"Reference not found: {id}")

    return ref.model_dump(mode="json")


def _reference_delete(id: str) -> dict:
    """Delete a reference.

    Args:
        id: Reference ID (partial match supported)

    Returns:
        {"deleted": True} on success.
    """
    conn = get_db_connection()
    if not delete_reference(conn, id):
        raise ValueError(f"Reference not found: {id}")
    return {"deleted": True}


def _get_references_dir() -> Path:
    """Get the references directory path."""
    project_root = find_project_root()
    if project_root is None:
        raise RuntimeError("Not in a sensei project. Run 'sensei init' first.")
    return project_root / "references"


def _reference_save_file(
    title: str,
    content: str,
    content_type: Literal[
        "webpage", "pdf", "arxiv", "book", "video", "paper", "documentation", "other"
    ],
    extension: str = ".md",
    description: str | None = None,
    authors: str | None = None,
    url: str | None = None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict:
    """Save content to a file and create a reference entry.

    This is a convenience function that:
    1. Slugifies the title to create a filename
    2. Writes the content to references/{slug}{extension}
    3. Creates a reference entry with the file_path

    Args:
        title: Reference title (used for filename)
        content: File content to write
        content_type: Type of content
        extension: File extension (default .md for markdown)
        description: Optional description
        authors: Optional authors
        url: Optional source URL
        tags: Optional tags
        metadata: Optional metadata

    Returns:
        Created reference as dict.
    """
    refs_dir = _get_references_dir()
    refs_dir.mkdir(parents=True, exist_ok=True)

    # Create filename from title
    slug = slugify(title, max_length=80)
    filename = f"{slug}{extension}"
    file_path = refs_dir / filename

    # Handle duplicate filenames
    counter = 1
    while file_path.exists():
        filename = f"{slug}-{counter}{extension}"
        file_path = refs_dir / filename
        counter += 1

    # Write content
    file_path.write_text(content)

    # Create reference entry
    relative_path = f"references/{filename}"
    return _reference_create(
        title=title,
        content_type=content_type,
        description=description,
        authors=authors,
        url=url,
        file_path=relative_path,
        tags=tags,
        metadata=metadata,
    )


# Reference MCP tools


@mcp.tool()
def sensei_reference_create(
    title: str,
    content_type: Literal[
        "webpage", "pdf", "arxiv", "book", "video", "paper", "documentation", "other"
    ],
    description: str | None = None,
    authors: str | None = None,
    url: str | None = None,
    file_path: str | None = None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict:
    """Create a new study reference (paper, book, webpage, etc.).

    Use this to track study materials with metadata. For web pages and documents,
    you can optionally save the content locally using sensei_reference_save.

    Args:
        title: Reference title
        content_type: Type of content (webpage, pdf, arxiv, book, video, paper,
            documentation, other)
        description: Optional description or summary
        authors: Optional authors string
        url: Optional source URL
        file_path: Optional local file path relative to project root
            (e.g., references/paper.pdf)
        tags: Optional list of tags for categorization
        metadata: Optional additional metadata
            (e.g., {"year": 2024, "venue": "NeurIPS"})

    Returns:
        Created reference with id, title, content_type, etc.
    """
    return _reference_create(
        title, content_type, description, authors, url, file_path, tags, metadata
    )


@mcp.tool()
def sensei_reference_search(
    query: str | None = None,
    id: str | None = None,
    content_type: Literal[
        "webpage", "pdf", "arxiv", "book", "video", "paper", "documentation", "other"
    ]
    | None = None,
    tags: list[str] | None = None,
    limit: int = 20,
) -> list[dict]:
    """Search study references.

    Search by text (uses full-text search on title, description, authors),
    lookup by ID, or filter by content_type and tags.

    Args:
        query: Full-text search query (searches title, description, authors)
        id: Direct lookup by reference ID (partial ID supported)
        content_type: Filter by content type
        tags: Filter by tags (matches references with any of these tags)
        limit: Maximum number of results (default 20)

    Returns:
        List of matching references.
    """
    return _reference_search(query, id, content_type, tags, limit)


@mcp.tool()
def sensei_reference_update(
    id: str,
    title: str | None = None,
    description: str | None = None,
    authors: str | None = None,
    url: str | None = None,
    file_path: str | None = None,
    content_type: Literal[
        "webpage", "pdf", "arxiv", "book", "video", "paper", "documentation", "other"
    ]
    | None = None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict:
    """Update a study reference.

    Args:
        id: Reference ID (partial ID supported)
        title: New title
        description: New description
        authors: New authors
        url: New URL
        file_path: New file path
        content_type: New content type
        tags: New tags (replaces existing tags)
        metadata: New metadata (replaces existing metadata)

    Returns:
        Updated reference.
    """
    return _reference_update(
        id, title, description, authors, url, file_path, content_type, tags, metadata
    )


@mcp.tool()
def sensei_reference_delete(id: str) -> dict:
    """Delete a study reference.

    Note: This only removes the reference entry from the database.
    Any associated files in references/ are not deleted.

    Args:
        id: Reference ID to delete (partial ID supported)

    Returns:
        {"deleted": True} on success.
    """
    return _reference_delete(id)


@mcp.tool()
def sensei_reference_save(
    title: str,
    content: str,
    content_type: Literal[
        "webpage", "pdf", "arxiv", "book", "video", "paper", "documentation", "other"
    ],
    extension: str = ".md",
    description: str | None = None,
    authors: str | None = None,
    url: str | None = None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict:
    """Save content to a file and create a reference entry.

    This is a convenience tool that:
    1. Slugifies the title to create a human-readable filename
    2. Writes the content to references/{slug}{extension}
    3. Creates a reference entry linking to the file

    Use this for saving web pages (as markdown), notes, or other text content.
    For binary files like PDFs, download them separately and use sensei_reference_create
    with the file_path parameter.

    Args:
        title: Reference title (used for filename, e.g., "Attention Is All You
            Need" -> attention-is-all-you-need.md)
        content: File content to write
        content_type: Type of content
        extension: File extension (default .md for markdown)
        description: Optional description or summary
        authors: Optional authors
        url: Optional source URL
        tags: Optional tags for categorization
        metadata: Optional additional metadata

    Returns:
        Created reference with file_path set to the saved file.
    """
    return _reference_save_file(
        title,
        content,
        content_type,
        extension,
        description,
        authors,
        url,
        tags,
        metadata,
    )


def run_server():
    """Run the MCP server."""
    mcp.run()
