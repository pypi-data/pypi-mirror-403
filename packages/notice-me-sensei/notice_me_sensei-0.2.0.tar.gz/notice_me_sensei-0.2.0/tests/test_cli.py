"""Tests for CLI commands."""

import os
import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sensei.cli import app
from sensei.db import create_task, get_connection
from sensei.init import get_db_path, init_project
from sensei.models import TaskType


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def cli_project():
    """Create a temp project and change to its directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)
        init_project(project_path)
        original = os.getcwd()
        os.chdir(project_path)
        yield project_path
        os.chdir(original)


class TestInit:
    def test_init_creates_project(self, runner):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(app, ["init", "--path", tmpdir])
            assert result.exit_code == 0
            assert "Initialized" in result.stdout
            assert (Path(tmpdir) / ".sensei" / "sensei.db").exists()

    def test_init_already_exists(self, runner, cli_project):
        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0
        assert "already initialized" in result.stdout


class TestStatus:
    def test_status_empty(self, runner, cli_project):
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0
        assert "Pending tasks:" in result.stdout

    def test_status_with_tasks(self, runner, cli_project):
        conn = get_connection(get_db_path(cli_project))
        create_task(conn, title="Test Task", task_type=TaskType.LEARNING)
        conn.close()

        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0
        assert "Pending tasks:  1" in result.stdout


class TestTaskCommands:
    def test_task_list_empty(self, runner, cli_project):
        result = runner.invoke(app, ["task", "list"])
        assert result.exit_code == 0
        assert "No tasks found" in result.stdout

    def test_task_create(self, runner, cli_project):
        result = runner.invoke(
            app, ["task", "create", "Learn Python", "--type", "learning"]
        )
        assert result.exit_code == 0
        assert "Created task" in result.stdout
        assert "Learn Python" in result.stdout

    def test_task_create_srs(self, runner, cli_project):
        result = runner.invoke(
            app, ["task", "create", "Quiz: Python basics", "--type", "srs"]
        )
        assert result.exit_code == 0
        assert "Created task" in result.stdout

    def test_task_list_with_tasks(self, runner, cli_project):
        runner.invoke(app, ["task", "create", "Task 1", "--type", "learning"])
        runner.invoke(app, ["task", "create", "Task 2", "--type", "implementation"])

        result = runner.invoke(app, ["task", "list"])
        assert result.exit_code == 0
        assert "Task 1" in result.stdout
        assert "Task 2" in result.stdout

    def test_task_list_filter_by_type(self, runner, cli_project):
        runner.invoke(app, ["task", "create", "Task 1", "--type", "learning"])
        runner.invoke(app, ["task", "create", "Task 2", "--type", "implementation"])

        result = runner.invoke(app, ["task", "list", "--type", "learning"])
        assert result.exit_code == 0
        assert "Task 1" in result.stdout
        assert "Task 2" not in result.stdout

    def test_task_show(self, runner, cli_project):
        runner.invoke(
            app,
            [
                "task",
                "create",
                "Learn Python",
                "--type",
                "learning",
                "--description",
                "Study Python basics",
            ],
        )

        # Get task ID from list
        list_result = runner.invoke(app, ["task", "list"])
        task_id = list_result.stdout.split("[")[1].split("]")[0]

        result = runner.invoke(app, ["task", "show", task_id])
        assert result.exit_code == 0
        assert "Learn Python" in result.stdout
        assert "Study Python basics" in result.stdout

    def test_task_update(self, runner, cli_project):
        runner.invoke(app, ["task", "create", "Learn Python", "--type", "learning"])

        list_result = runner.invoke(app, ["task", "list"])
        task_id = list_result.stdout.split("[")[1].split("]")[0]

        result = runner.invoke(app, ["task", "update", task_id, "--status", "active"])
        assert result.exit_code == 0
        assert "Updated" in result.stdout

    def test_task_complete(self, runner, cli_project):
        runner.invoke(app, ["task", "create", "Learn Python", "--type", "learning"])

        list_result = runner.invoke(app, ["task", "list"])
        task_id = list_result.stdout.split("[")[1].split("]")[0]

        result = runner.invoke(app, ["task", "complete", task_id])
        assert result.exit_code == 0
        assert "Completed" in result.stdout

    def test_task_schedule_next(self, runner, cli_project):
        runner.invoke(app, ["task", "create", "Quiz: Python", "--type", "srs"])

        list_result = runner.invoke(app, ["task", "list"])
        task_id = list_result.stdout.split("[")[1].split("]")[0]

        result = runner.invoke(app, ["task", "schedule-next", task_id, "--days", "3"])
        assert result.exit_code == 0
        assert "Created follow-up task" in result.stdout


class TestArtifactCommands:
    def test_artifact_add(self, runner, cli_project):
        runner.invoke(app, ["task", "create", "Learn Python", "--type", "learning"])

        list_result = runner.invoke(app, ["task", "list"])
        task_id = list_result.stdout.split("[")[1].split("]")[0]

        result = runner.invoke(app, ["artifact", "add", task_id, "notes.md"])
        assert result.exit_code == 0
        assert "Added artifact" in result.stdout
        assert "note" in result.stdout

    def test_artifact_list(self, runner, cli_project):
        runner.invoke(app, ["task", "create", "Learn Python", "--type", "learning"])

        list_result = runner.invoke(app, ["task", "list"])
        task_id = list_result.stdout.split("[")[1].split("]")[0]

        runner.invoke(app, ["artifact", "add", task_id, "notes.md"])

        result = runner.invoke(app, ["artifact", "list", task_id])
        assert result.exit_code == 0
        assert "notes.md" in result.stdout


class TestAssessmentCommands:
    def test_assess_passed(self, runner, cli_project):
        runner.invoke(app, ["task", "create", "Quiz", "--type", "srs"])

        list_result = runner.invoke(app, ["task", "list"])
        task_id = list_result.stdout.split("[")[1].split("]")[0]

        result = runner.invoke(
            app, ["assess", task_id, "--passed", "--feedback", "Good work!"]
        )
        assert result.exit_code == 0
        assert "passed" in result.stdout

    def test_assess_failed(self, runner, cli_project):
        runner.invoke(app, ["task", "create", "Quiz", "--type", "srs"])

        list_result = runner.invoke(app, ["task", "list"])
        task_id = list_result.stdout.split("[")[1].split("]")[0]

        result = runner.invoke(app, ["assess", task_id, "--failed"])
        assert result.exit_code == 0
        assert "failed" in result.stdout

    def test_history(self, runner, cli_project):
        runner.invoke(app, ["task", "create", "Quiz", "--type", "srs"])

        list_result = runner.invoke(app, ["task", "list"])
        task_id = list_result.stdout.split("[")[1].split("]")[0]

        runner.invoke(app, ["assess", task_id, "--passed"])
        runner.invoke(app, ["assess", task_id, "--failed"])

        result = runner.invoke(app, ["history", task_id])
        assert result.exit_code == 0
        assert "PASSED" in result.stdout
        assert "FAILED" in result.stdout


class TestConvenienceCommands:
    def test_due(self, runner, cli_project):
        result = runner.invoke(app, ["due"])
        assert result.exit_code == 0

    def test_search(self, runner, cli_project):
        runner.invoke(app, ["task", "create", "Learn Python", "--type", "learning"])
        runner.invoke(app, ["task", "create", "Learn JavaScript", "--type", "learning"])

        result = runner.invoke(app, ["search", "Python"])
        assert result.exit_code == 0
        assert "Python" in result.stdout
        assert "JavaScript" not in result.stdout
