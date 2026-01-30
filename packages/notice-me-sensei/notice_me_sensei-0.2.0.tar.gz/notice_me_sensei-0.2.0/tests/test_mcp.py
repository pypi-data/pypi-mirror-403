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
    _task_bulk_create,
    _task_bulk_update,
    _task_complete,
    _task_create,
    _task_delete,
    _task_get,
    _task_list,
    _task_move,
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

    def test_create_with_path_creates_directory(self, mcp_project):
        result = _task_create(
            title="Learn Attention",
            type="learning",
            path="topics/attention",
        )
        assert result["path"] == "topics/attention"
        assert (mcp_project / "topics" / "attention").is_dir()

    def test_create_with_nested_path(self, mcp_project):
        _task_create(
            title="Deep Topic",
            type="learning",
            path="topics/ml/transformers/attention",
        )
        assert (mcp_project / "topics" / "ml" / "transformers" / "attention").is_dir()


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

    def test_update_path_creates_directory(self, mcp_project):
        task = _task_create(title="Learn Python", type="learning")
        result = _task_update(id=task["id"][:8], path="topics/python")

        assert result["path"] == "topics/python"
        assert (mcp_project / "topics" / "python").is_dir()


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


class TestTaskUpdateExtended:
    def test_update_title(self, mcp_project):
        task = _task_create(title="Learn Python", type="learning")
        result = _task_update(id=task["id"][:8], title="Master Python")

        assert result["title"] == "Master Python"

    def test_update_parent_id(self, mcp_project):
        parent = _task_create(title="Phase 1", type="learning")
        child = _task_create(title="Week 1", type="learning")

        result = _task_update(id=child["id"][:8], parent_id=parent["id"][:8])
        assert result["parent_id"] == parent["id"]

    def test_clear_parent_id(self, mcp_project):
        parent = _task_create(title="Phase 1", type="learning")
        child = _task_create(title="Week 1", type="learning", parent_id=parent["id"])

        # Clear parent by passing empty string
        result = _task_update(id=child["id"][:8], parent_id="")
        assert result["parent_id"] is None

    def test_add_blocked_by(self, mcp_project):
        task1 = _task_create(title="Task 1", type="learning")
        task2 = _task_create(title="Task 2", type="learning")

        result = _task_update(id=task2["id"][:8], add_blocked_by=[task1["id"][:8]])

        assert task1["id"] in result["blocked_by"]
        assert task2["id"] in _task_get(task1["id"][:8])["blocks"]

    def test_remove_blocked_by(self, mcp_project):
        task1 = _task_create(title="Task 1", type="learning")
        task2 = _task_create(title="Task 2", type="learning")

        _task_update(id=task2["id"][:8], add_blocked_by=[task1["id"][:8]])
        result = _task_update(id=task2["id"][:8], remove_blocked_by=[task1["id"][:8]])

        assert task1["id"] not in result["blocked_by"]


class TestTaskDelete:
    def test_delete_single_task(self, mcp_project):
        task = _task_create(title="Learn Python", type="learning")
        result = _task_delete(id=task["id"][:8])

        assert result["deleted"] == 1
        with pytest.raises(ValueError, match="not found"):
            _task_get(id=task["id"][:8])

    def test_delete_task_with_children_fails(self, mcp_project):
        parent = _task_create(title="Phase 1", type="learning")
        _task_create(title="Week 1", type="learning", parent_id=parent["id"])

        with pytest.raises(ValueError, match="children"):
            _task_delete(id=parent["id"][:8])

    def test_delete_cascade(self, mcp_project):
        parent = _task_create(title="Phase 1", type="learning")
        child = _task_create(title="Week 1", type="learning", parent_id=parent["id"])
        grandchild = _task_create(title="Day 1", type="learning", parent_id=child["id"])

        result = _task_delete(id=parent["id"][:8], cascade=True)

        assert result["deleted"] == 3
        with pytest.raises(ValueError, match="not found"):
            _task_get(id=parent["id"][:8])
        with pytest.raises(ValueError, match="not found"):
            _task_get(id=child["id"][:8])
        with pytest.raises(ValueError, match="not found"):
            _task_get(id=grandchild["id"][:8])


class TestTaskListExtended:
    def test_list_by_path_prefix(self, mcp_project):
        _task_create(title="Task 1", type="learning", path="topics/python/basics")
        _task_create(title="Task 2", type="learning", path="topics/python/advanced")
        _task_create(title="Task 3", type="learning", path="topics/javascript")

        result = _task_list(path_prefix="topics/python")
        assert len(result) == 2

        result = _task_list(path_prefix="topics/javascript")
        assert len(result) == 1


class TestTaskMove:
    def test_move_to_new_parent(self, mcp_project):
        parent1 = _task_create(title="Phase 1", type="learning")
        parent2 = _task_create(title="Phase 2", type="learning")
        child = _task_create(title="Week 1", type="learning", parent_id=parent1["id"])

        result = _task_move(id=child["id"][:8], new_parent_id=parent2["id"][:8])

        assert result["moved"] >= 1
        updated = _task_get(id=child["id"][:8])
        assert updated["parent_id"] == parent2["id"]

    def test_move_to_root(self, mcp_project):
        parent = _task_create(title="Phase 1", type="learning")
        child = _task_create(title="Week 1", type="learning", parent_id=parent["id"])

        result = _task_move(id=child["id"][:8], new_parent_id="")

        assert result["moved"] >= 1
        updated = _task_get(id=child["id"][:8])
        assert updated["parent_id"] is None

    def test_move_with_path_rebase(self, mcp_project):
        task = _task_create(title="Week 1", type="learning", path="topics/phase1/week1")
        child = _task_create(
            title="Day 1", type="learning", path="topics/phase1/week1/day1"
        )

        _task_move(
            id=task["id"][:8],
            new_parent_id=None,
            new_path="topics/phase2/week1",
        )

        updated_task = _task_get(id=task["id"][:8])
        assert updated_task["path"] == "topics/phase2/week1"

        # Child path should also be rebased
        updated_child = _task_get(id=child["id"][:8])
        assert updated_child["path"] == "topics/phase2/week1/day1"


class TestTaskBulkCreate:
    def test_bulk_create_simple(self, mcp_project):
        result = _task_bulk_create(
            tasks=[
                {"title": "Task 1", "type": "learning"},
                {"title": "Task 2", "type": "implementation"},
            ]
        )

        assert result["created"] == 2
        assert len(result["task_ids"]) == 2

    def test_bulk_create_with_base_path(self, mcp_project):
        result = _task_bulk_create(
            base_path="topics/phase1",
            tasks=[
                {"title": "Task 1", "type": "learning", "path": "week1"},
                {"title": "Task 2", "type": "learning"},
            ],
        )

        task1 = _task_get(result["task_ids"][0][:8])
        assert task1["path"] == "topics/phase1/week1"

        task2 = _task_get(result["task_ids"][1][:8])
        assert task2["path"] == "topics/phase1"

    def test_bulk_create_with_relative_dates(self, mcp_project):
        result = _task_bulk_create(
            base_due_date="2026-02-01",
            tasks=[
                {"title": "Task 1", "type": "learning", "due_date": "+7d"},
                {"title": "Task 2", "type": "learning", "due_date": "+14d"},
            ],
        )

        task1 = _task_get(result["task_ids"][0][:8])
        assert "2026-02-08" in task1["due_date"]

        task2 = _task_get(result["task_ids"][1][:8])
        assert "2026-02-15" in task2["due_date"]

    def test_bulk_create_with_children(self, mcp_project):
        result = _task_bulk_create(
            tasks=[
                {
                    "title": "Parent",
                    "type": "learning",
                    "children": [
                        {"title": "Child 1", "type": "learning"},
                        {"title": "Child 2", "type": "implementation"},
                    ],
                }
            ]
        )

        assert result["created"] == 3

        # Get parent and children
        parent = _task_get(result["task_ids"][0][:8])
        child1 = _task_get(result["task_ids"][1][:8])
        child2 = _task_get(result["task_ids"][2][:8])

        assert child1["parent_id"] == parent["id"]
        assert child2["parent_id"] == parent["id"]

    def test_bulk_create_with_parent_ref(self, mcp_project):
        result = _task_bulk_create(
            tasks=[
                {"title": "Phase 1", "type": "learning"},
                {"title": "Week 1", "type": "learning", "parent_ref": 0},
            ]
        )

        phase = _task_get(result["task_ids"][0][:8])
        week = _task_get(result["task_ids"][1][:8])

        assert week["parent_id"] == phase["id"]


class TestTaskBulkUpdate:
    def test_bulk_update_status(self, mcp_project):
        _task_create(title="Task 1", type="learning", path="topics/phase1")
        _task_create(title="Task 2", type="learning", path="topics/phase1")
        _task_create(title="Task 3", type="learning", path="topics/phase2")

        result = _task_bulk_update(
            filter={"path_prefix": "topics/phase1"},
            updates={"status": "active"},
        )

        assert result["updated"] == 2

        # Verify status changed
        active_tasks = _task_list(status="active")
        assert len(active_tasks) == 2

    def test_bulk_update_path_replace(self, mcp_project):
        _task_create(title="Task 1", type="learning", path="topics/old/sub1")
        _task_create(title="Task 2", type="learning", path="topics/old/sub2")

        result = _task_bulk_update(
            filter={"path_prefix": "topics/old"},
            updates={"path_replace": {"old": "topics/old", "new": "topics/new"}},
        )

        assert result["updated"] == 2

        # Verify paths changed
        tasks = _task_list(path_prefix="topics/new")
        assert len(tasks) == 2

    def test_bulk_update_due_date_shift(self, mcp_project):
        task1 = _task_create(title="Task 1", type="learning", due_date="2026-02-01")
        _task_create(title="Task 2", type="learning", due_date="2026-02-15")

        result = _task_bulk_update(
            filter={"ids": [task1["id"]]},
            updates={"due_date_shift": "+7d"},
        )

        assert result["updated"] == 1

        updated = _task_get(task1["id"][:8])
        assert "2026-02-08" in updated["due_date"]

    def test_bulk_update_negative_date_shift(self, mcp_project):
        task = _task_create(title="Task 1", type="learning", due_date="2026-02-15")

        result = _task_bulk_update(
            filter={"ids": [task["id"]]},
            updates={"due_date_shift": "-7d"},
        )

        assert result["updated"] == 1
        updated = _task_get(task["id"][:8])
        assert "2026-02-08" in updated["due_date"]

    def test_bulk_update_weeks_shift(self, mcp_project):
        task = _task_create(title="Task 1", type="learning", due_date="2026-02-01")

        result = _task_bulk_update(
            filter={"ids": [task["id"]]},
            updates={"due_date_shift": "+2w"},
        )

        assert result["updated"] == 1
        updated = _task_get(task["id"][:8])
        assert "2026-02-15" in updated["due_date"]

    def test_bulk_update_months_shift(self, mcp_project):
        task = _task_create(title="Task 1", type="learning", due_date="2026-02-01")

        result = _task_bulk_update(
            filter={"ids": [task["id"]]},
            updates={"due_date_shift": "+1m"},
        )

        assert result["updated"] == 1
        updated = _task_get(task["id"][:8])
        # +1m = +30 days = 2026-03-03
        assert "2026-03-03" in updated["due_date"]

    def test_bulk_update_filter_by_parent_id(self, mcp_project):
        parent = _task_create(title="Parent", type="learning")
        child1 = _task_create(title="Child 1", type="learning", parent_id=parent["id"])
        child2 = _task_create(title="Child 2", type="learning", parent_id=parent["id"])
        _task_create(title="Other", type="learning")

        result = _task_bulk_update(
            filter={"parent_id": parent["id"][:8]},
            updates={"status": "active"},
        )

        assert result["updated"] == 2
        assert _task_get(child1["id"][:8])["status"] == "active"
        assert _task_get(child2["id"][:8])["status"] == "active"

    def test_bulk_update_filter_by_status(self, mcp_project):
        task1 = _task_create(title="Task 1", type="learning")
        task2 = _task_create(title="Task 2", type="learning")
        _task_update(id=task1["id"][:8], status="active")

        result = _task_bulk_update(
            filter={"status": "active"},
            updates={"status": "completed"},
        )

        assert result["updated"] == 1
        assert _task_get(task1["id"][:8])["status"] == "completed"
        assert _task_get(task2["id"][:8])["status"] == "pending"

    def test_bulk_update_empty_filter_raises(self, mcp_project):
        _task_create(title="Task 1", type="learning")

        with pytest.raises(ValueError, match="At least one filter required"):
            _task_bulk_update(filter={}, updates={"status": "active"})


class TestTaskListBlocked:
    def test_list_blocked_true(self, mcp_project):
        blocker = _task_create(title="Blocker", type="learning")
        blocked = _task_create(title="Blocked", type="learning")
        _task_create(title="Unblocked", type="learning")  # Not blocked

        _task_update(id=blocked["id"][:8], add_blocked_by=[blocker["id"][:8]])

        result = _task_list(blocked=True)
        assert len(result) == 1
        assert result[0]["id"] == blocked["id"]

    def test_list_blocked_false(self, mcp_project):
        blocker = _task_create(title="Blocker", type="learning")
        blocked = _task_create(title="Blocked", type="learning")
        unblocked = _task_create(title="Unblocked", type="learning")

        _task_update(id=blocked["id"][:8], add_blocked_by=[blocker["id"][:8]])

        result = _task_list(blocked=False)
        ids = [t["id"] for t in result]
        assert blocker["id"] in ids
        assert unblocked["id"] in ids
        assert blocked["id"] not in ids

    def test_blocked_resolved_when_blocker_completed(self, mcp_project):
        blocker = _task_create(title="Blocker", type="learning")
        blocked = _task_create(title="Blocked", type="learning")

        _task_update(id=blocked["id"][:8], add_blocked_by=[blocker["id"][:8]])

        # Initially blocked
        assert len(_task_list(blocked=True)) == 1

        # Complete the blocker
        _task_complete(id=blocker["id"][:8])

        # Now unblocked
        assert len(_task_list(blocked=True)) == 0
        unblocked_tasks = _task_list(blocked=False)
        ids = [t["id"] for t in unblocked_tasks]
        assert blocked["id"] in ids


class TestTaskGetDependencies:
    def test_get_shows_blocks(self, mcp_project):
        blocker = _task_create(title="Blocker", type="learning")
        blocked1 = _task_create(title="Blocked 1", type="learning")
        blocked2 = _task_create(title="Blocked 2", type="learning")

        _task_update(id=blocked1["id"][:8], add_blocked_by=[blocker["id"][:8]])
        _task_update(id=blocked2["id"][:8], add_blocked_by=[blocker["id"][:8]])

        result = _task_get(blocker["id"][:8])
        assert blocked1["id"] in result["blocks"]
        assert blocked2["id"] in result["blocks"]


class TestBulkCreateExtended:
    def test_bulk_create_weeks_relative_date(self, mcp_project):
        result = _task_bulk_create(
            base_due_date="2026-02-01",
            tasks=[{"title": "Task 1", "type": "learning", "due_date": "+2w"}],
        )

        task = _task_get(result["task_ids"][0][:8])
        assert "2026-02-15" in task["due_date"]

    def test_bulk_create_months_relative_date(self, mcp_project):
        result = _task_bulk_create(
            base_due_date="2026-02-01",
            tasks=[{"title": "Task 1", "type": "learning", "due_date": "+1m"}],
        )

        task = _task_get(result["task_ids"][0][:8])
        # +1m = +30 days = 2026-03-03
        assert "2026-03-03" in task["due_date"]

    def test_bulk_create_today_base_date(self, mcp_project):
        from datetime import datetime, timedelta

        result = _task_bulk_create(
            base_due_date="today",
            tasks=[{"title": "Task 1", "type": "learning", "due_date": "+7d"}],
        )

        task = _task_get(result["task_ids"][0][:8])
        expected = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        assert expected in task["due_date"]

    def test_bulk_create_missing_title_raises(self, mcp_project):
        with pytest.raises(ValueError, match="missing required"):
            _task_bulk_create(tasks=[{"type": "learning"}])

    def test_bulk_create_missing_type_raises(self, mcp_project):
        with pytest.raises(ValueError, match="missing required"):
            _task_bulk_create(tasks=[{"title": "Task"}])

    def test_bulk_create_invalid_parent_ref_raises(self, mcp_project):
        with pytest.raises(ValueError, match="parent_ref"):
            _task_bulk_create(
                tasks=[
                    {"title": "Task 1", "type": "learning", "parent_ref": 5},
                ]
            )


class TestDeleteCleanup:
    def test_delete_removes_artifacts(self, mcp_project):
        task = _task_create(title="Task", type="learning")
        _artifact_add(task_id=task["id"][:8], path="notes.md")

        # Verify artifact exists
        assert len(_artifact_list(task["id"][:8])) == 1

        _task_delete(id=task["id"][:8])

        # Task is gone, can't list artifacts for it
        with pytest.raises(ValueError, match="not found"):
            _artifact_list(task["id"][:8])

    def test_delete_removes_assessments(self, mcp_project):
        task = _task_create(title="Task", type="srs")
        _assessment_record(task_id=task["id"][:8], passed=True)

        # Verify assessment exists
        assert len(_assessment_history(task["id"][:8])) == 1

        _task_delete(id=task["id"][:8])

        # Task is gone, can't get assessments for it
        with pytest.raises(ValueError, match="not found"):
            _assessment_history(task["id"][:8])

    def test_delete_removes_dependencies(self, mcp_project):
        blocker = _task_create(title="Blocker", type="learning")
        blocked = _task_create(title="Blocked", type="learning")

        _task_update(id=blocked["id"][:8], add_blocked_by=[blocker["id"][:8]])

        # Verify dependency exists
        assert blocker["id"] in _task_get(blocked["id"][:8])["blocked_by"]

        # Delete blocker
        _task_delete(id=blocker["id"][:8])

        # Dependency should be cleaned up
        assert _task_get(blocked["id"][:8])["blocked_by"] == []
