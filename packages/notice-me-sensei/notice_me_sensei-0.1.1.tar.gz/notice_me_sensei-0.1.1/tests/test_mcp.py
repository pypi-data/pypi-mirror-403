"""Tests for MCP tools (using internal functions)."""

import os
import tempfile
from pathlib import Path

import pytest

from sensei.init import init_project
from sensei.mcp import (
    _artifact_add,
    _artifact_list,
    _assessment_history,
    _assessment_record,
    _search,
    _task_complete,
    _task_create,
    _task_get,
    _task_list,
    _task_schedule_next,
    _task_update,
)


@pytest.fixture
def mcp_project():
    """Create a temp project for MCP testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)
        init_project(project_path)
        original = os.getcwd()
        os.chdir(project_path)
        yield project_path
        os.chdir(original)


class TestTaskCreate:
    def test_create_learning_task(self, mcp_project):
        result = _task_create(title="Learn Python", type="learning")
        assert result["title"] == "Learn Python"
        assert result["type"] == "learning"
        assert result["status"] == "pending"

    def test_create_srs_task(self, mcp_project):
        result = _task_create(title="Quiz: Python", type="srs")
        assert result["type"] == "srs"
        assert result["due_date"] is not None
        assert result["metadata"]["interval_days"] == 1

    def test_create_with_description(self, mcp_project):
        result = _task_create(
            title="Learn Python",
            type="learning",
            description="Study Python basics",
        )
        assert result["description"] == "Study Python basics"


class TestTaskList:
    def test_list_empty(self, mcp_project):
        result = _task_list()
        assert result == []

    def test_list_tasks(self, mcp_project):
        _task_create(title="Task 1", type="learning")
        _task_create(title="Task 2", type="implementation")

        result = _task_list()
        assert len(result) == 2

    def test_list_by_status(self, mcp_project):
        task = _task_create(title="Task 1", type="learning")
        _task_create(title="Task 2", type="learning")
        _task_complete(id=task["id"][:8])

        pending = _task_list(status="pending")
        assert len(pending) == 1

        completed = _task_list(status="completed")
        assert len(completed) == 1


class TestTaskGet:
    def test_get_task(self, mcp_project):
        created = _task_create(title="Learn Python", type="learning")
        result = _task_get(id=created["id"][:8])

        assert result["title"] == "Learn Python"
        assert "artifacts" in result
        assert "assessments" in result

    def test_get_nonexistent(self, mcp_project):
        with pytest.raises(ValueError, match="not found"):
            _task_get(id="nonexistent")


class TestTaskUpdate:
    def test_update_status(self, mcp_project):
        task = _task_create(title="Learn Python", type="learning")
        result = _task_update(id=task["id"][:8], status="active")

        assert result["status"] == "active"

    def test_update_description(self, mcp_project):
        task = _task_create(title="Learn Python", type="learning")
        result = _task_update(id=task["id"][:8], description="New description")

        assert result["description"] == "New description"


class TestTaskComplete:
    def test_complete_task(self, mcp_project):
        task = _task_create(title="Learn Python", type="learning")
        result = _task_complete(id=task["id"][:8])

        assert result["status"] == "completed"
        assert result["completed_at"] is not None


class TestTaskScheduleNext:
    def test_schedule_with_days(self, mcp_project):
        task = _task_create(title="Quiz: Python", type="srs")
        result = _task_schedule_next(task_id=task["id"][:8], days=3)

        assert result["title"] == "Quiz: Python"
        assert result["type"] == "srs"

    def test_schedule_with_assessment(self, mcp_project):
        task = _task_create(title="Quiz: Python", type="srs")
        _assessment_record(task_id=task["id"][:8], passed=True)

        result = _task_schedule_next(task_id=task["id"][:8])
        assert result["type"] == "srs"


class TestArtifacts:
    def test_add_artifact(self, mcp_project):
        task = _task_create(title="Learn Python", type="learning")
        result = _artifact_add(task_id=task["id"][:8], path="notes.md")

        assert result["path"] == "notes.md"
        assert result["type"] == "note"

    def test_list_artifacts(self, mcp_project):
        task = _task_create(title="Learn Python", type="learning")
        _artifact_add(task_id=task["id"][:8], path="notes.md")
        _artifact_add(task_id=task["id"][:8], path="code.py")

        result = _artifact_list(task_id=task["id"][:8])
        assert len(result) == 2


class TestAssessments:
    def test_record_assessment(self, mcp_project):
        task = _task_create(title="Quiz", type="srs")
        result = _assessment_record(
            task_id=task["id"][:8],
            passed=True,
            score=8.5,
            feedback="Well done!",
        )

        assert result["passed"] is True
        assert result["score"] == 8.5
        assert result["feedback"] == "Well done!"

    def test_assessment_history(self, mcp_project):
        task = _task_create(title="Quiz", type="srs")
        _assessment_record(task_id=task["id"][:8], passed=True)
        _assessment_record(task_id=task["id"][:8], passed=False)

        result = _assessment_history(task_id=task["id"][:8])
        assert len(result) == 2


class TestSearch:
    def test_search_by_title(self, mcp_project):
        _task_create(title="Learn Python", type="learning")
        _task_create(title="Learn JavaScript", type="learning")

        result = _search(query="Python")
        assert len(result) == 1
        assert result[0]["title"] == "Learn Python"
