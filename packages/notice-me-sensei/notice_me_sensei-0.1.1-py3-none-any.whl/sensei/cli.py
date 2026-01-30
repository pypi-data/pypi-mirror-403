"""Command-line interface for Sensei using Typer."""

import json
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Annotated

import typer

from sensei.db import (
    complete_task,
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
    update_task,
)
from sensei.init import find_project_root, init_project, is_sensei_project
from sensei.models import ArtifactType, TaskStatus, TaskType
from sensei.srs import (
    calculate_due_date_from_days,
    calculate_next_interval,
    get_initial_srs_metadata,
)

app = typer.Typer(help="Sensei - AI-powered personal learning coach")
task_app = typer.Typer(help="Manage tasks")
artifact_app = typer.Typer(help="Manage artifacts")

app.add_typer(task_app, name="task")
app.add_typer(artifact_app, name="artifact")


class TaskTypeChoice(str, Enum):
    learning = "learning"
    implementation = "implementation"
    srs = "srs"
    test = "test"
    review = "review"


class TaskStatusChoice(str, Enum):
    pending = "pending"
    active = "active"
    completed = "completed"
    archived = "archived"


class ArtifactTypeChoice(str, Enum):
    note = "note"
    code = "code"
    notebook = "notebook"
    pdf = "pdf"
    test_harness = "test_harness"
    other = "other"


def get_project_context():
    """Get the current project context."""
    project_root = find_project_root()
    if project_root is None:
        typer.echo("Error: Not in a sensei project. Run 'sensei init' first.", err=True)
        raise typer.Exit(1)
    return project_root


def get_db():
    """Get database connection for current project."""
    project_root = get_project_context()
    db_path = project_root / "sensei.db"
    if not db_path.exists():
        typer.echo("Error: Database not found. Run 'sensei init' first.", err=True)
        raise typer.Exit(1)
    return get_connection(db_path)


def resolve_task_id(conn, partial_id: str) -> str:
    """Resolve a partial task ID to a full ID."""
    tasks = list_tasks(conn, limit=1000)
    matching = [t for t in tasks if t.id.startswith(partial_id)]

    if not matching:
        typer.echo(f"Error: Task not found: {partial_id}", err=True)
        raise typer.Exit(1)
    if len(matching) > 1:
        typer.echo(
            f"Error: Ambiguous task ID. Matches: {[t.id[:8] for t in matching]}",
            err=True,
        )
        raise typer.Exit(1)

    return matching[0].id


@app.command()
def init(
    path: Annotated[Path, typer.Option(help="Path to initialize project in")] = Path(
        "."
    ),
):
    """Initialize a new sensei project."""
    project_path = path.resolve()

    if is_sensei_project(project_path):
        typer.echo(f"Project already initialized at {project_path}")
        return

    init_project(project_path)
    typer.echo(f"Initialized sensei project at {project_path}")
    typer.echo("\nCreated:")
    typer.echo("  .claude/skills/sensei/SKILL.md")
    typer.echo("  .claude/settings.local.json")
    typer.echo("  topics/")
    typer.echo("  practice/")
    typer.echo("  sensei.db")
    typer.echo("  CLAUDE.md")


@app.command()
def status():
    """Show project summary."""
    conn = get_db()

    # Get counts by status
    pending = list_tasks(conn, status=TaskStatus.PENDING, limit=1000)
    active = list_tasks(conn, status=TaskStatus.ACTIVE, limit=1000)

    # Get due today
    today_end = datetime.now().replace(hour=23, minute=59, second=59)
    due_today = list_tasks(
        conn, status=TaskStatus.PENDING, due_before=today_end, limit=1000
    )

    # Get overdue
    now = datetime.now()
    overdue = [t for t in pending if t.due_date and t.due_date < now]

    typer.echo("Sensei Project Status")
    typer.echo("=" * 40)
    typer.echo(f"Pending tasks:  {len(pending)}")
    typer.echo(f"Active tasks:   {len(active)}")
    typer.echo(f"Due today:      {len(due_today)}")
    typer.echo(f"Overdue:        {len(overdue)}")

    if due_today:
        typer.echo("\nDue Today:")
        for task in due_today[:5]:
            typer.echo(f"  [{task.id[:8]}] {task.title}")


# Task subcommands
@task_app.command("list")
def task_list_cmd(
    status: Annotated[
        TaskStatusChoice | None, typer.Option(help="Filter by status")
    ] = None,
    task_type: Annotated[
        TaskTypeChoice | None, typer.Option("--type", help="Filter by type")
    ] = None,
    due_before: Annotated[
        str | None, typer.Option(help="Filter by due date (ISO8601 or 'today')")
    ] = None,
    path: Annotated[str | None, typer.Option(help="Filter by path")] = None,
    limit: Annotated[int, typer.Option(help="Maximum number of results")] = 20,
):
    """List tasks with optional filters."""
    conn = get_db()

    status_enum = TaskStatus(status.value) if status else None
    type_enum = TaskType(task_type.value) if task_type else None

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
        path=path,
        limit=limit,
    )

    if not tasks:
        typer.echo("No tasks found.")
        return

    for t in tasks:
        due_str = t.due_date.strftime("%Y-%m-%d") if t.due_date else "no due date"
        typer.echo(
            f"[{t.id[:8]}] {t.title} ({t.type.value}, {t.status.value}, {due_str})"
        )


@task_app.command("create")
def task_create_cmd(
    title: Annotated[str, typer.Argument(help="Task title")],
    task_type: Annotated[TaskTypeChoice, typer.Option("--type", help="Task type")],
    parent: Annotated[str | None, typer.Option(help="Parent task ID")] = None,
    description: Annotated[str | None, typer.Option(help="Task description")] = None,
    due: Annotated[str | None, typer.Option(help="Due date (ISO8601)")] = None,
    path: Annotated[str | None, typer.Option(help="Related directory path")] = None,
):
    """Create a new task."""
    conn = get_db()

    type_enum = TaskType(task_type.value)
    due_dt = datetime.fromisoformat(due) if due else None

    metadata = {}
    if type_enum == TaskType.SRS:
        metadata = get_initial_srs_metadata()
        if due_dt is None:
            due_dt = calculate_due_date_from_days(1)

    task = create_task(
        conn,
        title=title,
        task_type=type_enum,
        parent_id=parent,
        description=description,
        due_date=due_dt,
        path=path,
        metadata=metadata,
    )

    typer.echo(f"Created task [{task.id[:8]}] {task.title}")


@task_app.command("show")
def task_show_cmd(
    task_id: Annotated[str, typer.Argument(help="Task ID (can be partial)")],
):
    """Show task details."""
    conn = get_db()
    full_id = resolve_task_id(conn, task_id)

    detail = get_task_detail(conn, full_id)
    if detail is None:
        typer.echo(f"Error: Task not found: {task_id}", err=True)
        raise typer.Exit(1)

    typer.echo(f"ID:          {detail.id}")
    typer.echo(f"Title:       {detail.title}")
    typer.echo(f"Type:        {detail.type.value}")
    typer.echo(f"Status:      {detail.status.value}")
    typer.echo(f"Path:        {detail.path or '(none)'}")
    typer.echo(
        f"Due:         {detail.due_date.isoformat() if detail.due_date else '(none)'}"
    )
    typer.echo(f"Created:     {detail.created_at.isoformat()}")
    if detail.completed_at:
        typer.echo(f"Completed:   {detail.completed_at.isoformat()}")
    if detail.description:
        typer.echo(f"\nDescription:\n{detail.description}")
    if detail.metadata:
        typer.echo(f"\nMetadata:    {json.dumps(detail.metadata)}")

    if detail.artifacts:
        typer.echo("\nArtifacts:")
        for a in detail.artifacts:
            typer.echo(f"  [{a.id[:8]}] {a.path} ({a.type.value})")

    if detail.assessments:
        typer.echo("\nRecent Assessments:")
        for ass in detail.assessments[:5]:
            passed_str = (
                "passed" if ass.passed else "failed" if ass.passed is False else "N/A"
            )
            score_str = f"score={ass.score}" if ass.score is not None else ""
            typer.echo(
                f"  [{ass.created_at.strftime('%Y-%m-%d')}] {passed_str} {score_str}"
            )


@task_app.command("update")
def task_update_cmd(
    task_id: Annotated[str, typer.Argument(help="Task ID (can be partial)")],
    status: Annotated[TaskStatusChoice | None, typer.Option(help="New status")] = None,
    due: Annotated[str | None, typer.Option(help="Due date (ISO8601)")] = None,
    description: Annotated[str | None, typer.Option(help="Task description")] = None,
    path: Annotated[str | None, typer.Option(help="Related directory path")] = None,
):
    """Update task fields."""
    conn = get_db()
    full_id = resolve_task_id(conn, task_id)

    status_enum = TaskStatus(status.value) if status else None
    due_dt = datetime.fromisoformat(due) if due else None

    task = update_task(
        conn,
        full_id,
        status=status_enum,
        due_date=due_dt,
        description=description,
        path=path,
    )
    if task:
        typer.echo(f"Updated task [{task.id[:8]}] {task.title}")


@task_app.command("complete")
def task_complete_cmd(
    task_id: Annotated[str, typer.Argument(help="Task ID (can be partial)")],
):
    """Mark task as completed."""
    conn = get_db()
    full_id = resolve_task_id(conn, task_id)

    task = complete_task(conn, full_id)
    if task:
        typer.echo(f"Completed task [{task.id[:8]}] {task.title}")


@task_app.command("schedule-next")
def task_schedule_next_cmd(
    task_id: Annotated[str, typer.Argument(help="Task ID (can be partial)")],
    days: Annotated[
        int | None, typer.Option(help="Days until next review (overrides algorithm)")
    ] = None,
    notes: Annotated[str | None, typer.Option(help="Notes for the new task")] = None,
):
    """Create a follow-up SRS task."""
    conn = get_db()
    full_id = resolve_task_id(conn, task_id)

    original = get_task(conn, full_id)
    if original is None:
        typer.echo(f"Error: Task not found: {task_id}", err=True)
        raise typer.Exit(1)

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

    typer.echo(
        f"Created follow-up task [{new_task.id[:8]}] due {due_dt.strftime('%Y-%m-%d')}"
    )


# Artifact subcommands
@artifact_app.command("add")
def artifact_add_cmd(
    task_id: Annotated[str, typer.Argument(help="Task ID (can be partial)")],
    path: Annotated[str, typer.Argument(help="Path to the artifact file")],
    artifact_type: Annotated[
        ArtifactTypeChoice | None, typer.Option("--type", help="Artifact type")
    ] = None,
):
    """Link an artifact to a task."""
    project_root = get_project_context()
    conn = get_db()
    full_id = resolve_task_id(conn, task_id)

    if artifact_type:
        type_enum = ArtifactType(artifact_type.value)
    else:
        type_enum = infer_artifact_type(path, base_path=project_root)

    artifact = create_artifact(conn, full_id, path, type_enum)
    typer.echo(f"Added artifact [{artifact.id[:8]}] {path} ({type_enum.value})")


@artifact_app.command("list")
def artifact_list_cmd(
    task_id: Annotated[str, typer.Argument(help="Task ID (can be partial)")],
):
    """List artifacts for a task."""
    conn = get_db()
    full_id = resolve_task_id(conn, task_id)

    artifacts = list_artifacts(conn, full_id)

    if not artifacts:
        typer.echo("No artifacts found.")
        return

    for a in artifacts:
        typer.echo(f"[{a.id[:8]}] {a.path} ({a.type.value})")


# Assessment commands
@app.command()
def assess(
    task_id: Annotated[str, typer.Argument(help="Task ID (can be partial)")],
    passed: Annotated[bool, typer.Option("--passed", help="Mark as passed")] = False,
    failed: Annotated[bool, typer.Option("--failed", help="Mark as failed")] = False,
    score: Annotated[float | None, typer.Option(help="Numeric score (0-10)")] = None,
    feedback: Annotated[str | None, typer.Option(help="Assessment feedback")] = None,
):
    """Record an assessment for a task."""
    if passed and failed:
        typer.echo("Error: Cannot specify both --passed and --failed", err=True)
        raise typer.Exit(1)

    conn = get_db()
    full_id = resolve_task_id(conn, task_id)

    passed_value = True if passed else (False if failed else None)

    assessment = create_assessment(
        conn, full_id, passed=passed_value, score=score, feedback=feedback
    )
    status_str = (
        "passed"
        if passed_value
        else ("failed" if passed_value is False else "recorded")
    )
    typer.echo(f"Assessment {status_str} [{assessment.id[:8]}]")


@app.command()
def history(
    task_id: Annotated[str, typer.Argument(help="Task ID (can be partial)")],
):
    """Show assessment history for a task."""
    conn = get_db()
    full_id = resolve_task_id(conn, task_id)

    task = get_task(conn, full_id)
    if task is None:
        typer.echo(f"Error: Task not found: {task_id}", err=True)
        raise typer.Exit(1)

    assessments = list_assessments(conn, full_id)

    if not assessments:
        typer.echo("No assessments found.")
        return

    typer.echo(f"Assessment history for [{task.id[:8]}] {task.title}")
    typer.echo("-" * 40)

    for a in assessments:
        passed_str = (
            "PASSED" if a.passed else ("FAILED" if a.passed is False else "N/A")
        )
        score_str = f"score={a.score}" if a.score is not None else ""
        typer.echo(
            f"[{a.created_at.strftime('%Y-%m-%d %H:%M')}] {passed_str} {score_str}"
        )
        if a.feedback:
            typer.echo(f"  Feedback: {a.feedback}")


# Convenience commands
@app.command()
def due(
    days: Annotated[
        int, typer.Option(help="Days to look ahead (default: 0 = today)")
    ] = 0,
):
    """Show tasks due soon."""
    conn = get_db()

    due_dt = datetime.now().replace(hour=23, minute=59, second=59) + timedelta(
        days=days
    )
    tasks = list_tasks(conn, status=TaskStatus.PENDING, due_before=due_dt, limit=50)

    if not tasks:
        typer.echo("No tasks due.")
        return

    typer.echo(f"Tasks due by {due_dt.strftime('%Y-%m-%d')}:")
    for t in tasks:
        due_str = t.due_date.strftime("%Y-%m-%d") if t.due_date else "no due date"
        typer.echo(f"  [{t.id[:8]}] {t.title} ({t.type.value}, due {due_str})")


@app.command()
def search(
    query: Annotated[str, typer.Argument(help="Search query")],
):
    """Search tasks by title and description."""
    conn = get_db()

    tasks = search_tasks(conn, query)

    if not tasks:
        typer.echo("No tasks found.")
        return

    for t in tasks:
        typer.echo(f"[{t.id[:8]}] {t.title} ({t.type.value}, {t.status.value})")


@app.command()
def mcp():
    """Start the MCP server."""
    from sensei.mcp import run_server

    run_server()


def main():
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
