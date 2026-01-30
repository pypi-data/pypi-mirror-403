"""Tests for database operations."""

from datetime import datetime, timedelta

from sensei.db import (
    complete_task,
    create_artifact,
    create_assessment,
    create_task,
    get_task,
    get_task_detail,
    infer_artifact_type,
    list_artifacts,
    list_assessments,
    list_tasks,
    search_tasks,
    slugify,
    update_task,
)
from sensei.models import ArtifactType, TaskStatus, TaskType


class TestSlugify:
    def test_basic(self):
        assert slugify("Hello World") == "hello-world"

    def test_special_chars(self):
        assert slugify("Hello, World!") == "hello-world"

    def test_multiple_spaces(self):
        assert slugify("hello   world") == "hello-world"

    def test_max_length(self):
        long_text = "a" * 100
        assert len(slugify(long_text)) == 50

    def test_strips_leading_trailing(self):
        assert slugify("---hello---") == "hello"


class TestTaskCRUD:
    def test_create_task(self, tmp_db):
        task = create_task(tmp_db, title="Test Task", task_type=TaskType.LEARNING)
        assert task.id
        assert task.title == "Test Task"
        assert task.type == TaskType.LEARNING
        assert task.status == TaskStatus.PENDING

    def test_get_task(self, tmp_db):
        created = create_task(tmp_db, title="Test Task", task_type=TaskType.LEARNING)
        retrieved = get_task(tmp_db, created.id)
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.title == created.title

    def test_get_nonexistent_task(self, tmp_db):
        result = get_task(tmp_db, "nonexistent-id")
        assert result is None

    def test_list_tasks(self, tmp_db):
        create_task(tmp_db, title="Task 1", task_type=TaskType.LEARNING)
        create_task(tmp_db, title="Task 2", task_type=TaskType.IMPLEMENTATION)
        create_task(tmp_db, title="Task 3", task_type=TaskType.SRS)

        tasks = list_tasks(tmp_db)
        assert len(tasks) == 3

    def test_list_tasks_by_status(self, tmp_db):
        task = create_task(tmp_db, title="Task 1", task_type=TaskType.LEARNING)
        create_task(tmp_db, title="Task 2", task_type=TaskType.LEARNING)
        complete_task(tmp_db, task.id)

        pending = list_tasks(tmp_db, status=TaskStatus.PENDING)
        assert len(pending) == 1

        completed = list_tasks(tmp_db, status=TaskStatus.COMPLETED)
        assert len(completed) == 1

    def test_list_tasks_by_type(self, tmp_db):
        create_task(tmp_db, title="Task 1", task_type=TaskType.LEARNING)
        create_task(tmp_db, title="Task 2", task_type=TaskType.SRS)

        learning = list_tasks(tmp_db, task_type=TaskType.LEARNING)
        assert len(learning) == 1
        assert learning[0].type == TaskType.LEARNING

    def test_list_tasks_by_due_date(self, tmp_db):
        yesterday = datetime.now() - timedelta(days=1)
        tomorrow = datetime.now() + timedelta(days=1)

        create_task(
            tmp_db, title="Due Yesterday", task_type=TaskType.SRS, due_date=yesterday
        )
        create_task(
            tmp_db, title="Due Tomorrow", task_type=TaskType.SRS, due_date=tomorrow
        )

        today = datetime.now()
        due_now = list_tasks(tmp_db, due_before=today)
        assert len(due_now) == 1
        assert due_now[0].title == "Due Yesterday"

    def test_update_task_status(self, tmp_db):
        task = create_task(tmp_db, title="Test Task", task_type=TaskType.LEARNING)
        updated = update_task(tmp_db, task.id, status=TaskStatus.ACTIVE)

        assert updated is not None
        assert updated.status == TaskStatus.ACTIVE

    def test_update_task_due_date(self, tmp_db):
        task = create_task(tmp_db, title="Test Task", task_type=TaskType.LEARNING)
        new_due = datetime.now() + timedelta(days=7)
        updated = update_task(tmp_db, task.id, due_date=new_due)

        assert updated is not None
        assert updated.due_date is not None

    def test_complete_task(self, tmp_db):
        task = create_task(tmp_db, title="Test Task", task_type=TaskType.LEARNING)
        completed = complete_task(tmp_db, task.id)

        assert completed is not None
        assert completed.status == TaskStatus.COMPLETED
        assert completed.completed_at is not None

    def test_create_task_with_parent(self, tmp_db):
        parent = create_task(tmp_db, title="Parent Task", task_type=TaskType.LEARNING)
        child = create_task(
            tmp_db, title="Child Task", task_type=TaskType.LEARNING, parent_id=parent.id
        )

        assert child.parent_id == parent.id


class TestArtifacts:
    def test_create_artifact(self, tmp_db):
        task = create_task(tmp_db, title="Test Task", task_type=TaskType.LEARNING)
        artifact = create_artifact(tmp_db, task.id, "notes.md", ArtifactType.NOTE)

        assert artifact.id
        assert artifact.task_id == task.id
        assert artifact.path == "notes.md"
        assert artifact.type == ArtifactType.NOTE

    def test_list_artifacts(self, tmp_db):
        task = create_task(tmp_db, title="Test Task", task_type=TaskType.LEARNING)
        create_artifact(tmp_db, task.id, "notes.md", ArtifactType.NOTE)
        create_artifact(tmp_db, task.id, "code.py", ArtifactType.CODE)

        artifacts = list_artifacts(tmp_db, task.id)
        assert len(artifacts) == 2


class TestInferArtifactType:
    def test_markdown(self):
        assert infer_artifact_type("notes.md") == ArtifactType.NOTE

    def test_python(self):
        assert infer_artifact_type("code.py") == ArtifactType.CODE

    def test_notebook_ipynb(self):
        assert infer_artifact_type("analysis.ipynb") == ArtifactType.NOTEBOOK

    def test_pdf(self):
        assert infer_artifact_type("paper.pdf") == ArtifactType.PDF

    def test_test_file(self):
        # test_*.py pattern
        assert infer_artifact_type("test_code.py") == ArtifactType.TEST_HARNESS
        assert infer_artifact_type("test_utils.py") == ArtifactType.TEST_HARNESS

    def test_conftest(self):
        assert infer_artifact_type("conftest.py") == ArtifactType.TEST_HARNESS

    def test_non_test_with_test_in_name(self):
        # "test" in path but not test_*.py pattern
        assert infer_artifact_type("contest.py") == ArtifactType.CODE
        assert infer_artifact_type("utils_test.py") == ArtifactType.CODE

    def test_unknown(self):
        assert infer_artifact_type("file.xyz") == ArtifactType.OTHER

    def test_marimo_notebook(self, tmp_path):
        # Create a marimo notebook file
        marimo_file = tmp_path / "notebook.py"
        marimo_file.write_text("""import marimo

__generated_with = "0.19.4"
app = marimo.App(width="medium")

@app.cell
def _():
    return None
""")
        assert (
            infer_artifact_type("notebook.py", base_path=tmp_path)
            == ArtifactType.NOTEBOOK
        )

    def test_regular_python_not_marimo(self, tmp_path):
        # Create a regular Python file
        py_file = tmp_path / "script.py"
        py_file.write_text("""def hello():
    print("Hello, world!")

if __name__ == "__main__":
    hello()
""")
        assert infer_artifact_type("script.py", base_path=tmp_path) == ArtifactType.CODE


class TestAssessments:
    def test_create_assessment(self, tmp_db):
        task = create_task(tmp_db, title="Test Task", task_type=TaskType.SRS)
        assessment = create_assessment(
            tmp_db, task.id, passed=True, score=8.0, feedback="Good job!"
        )

        assert assessment.id
        assert assessment.task_id == task.id
        assert assessment.passed is True
        assert assessment.score == 8.0
        assert assessment.feedback == "Good job!"

    def test_list_assessments(self, tmp_db):
        task = create_task(tmp_db, title="Test Task", task_type=TaskType.SRS)
        create_assessment(tmp_db, task.id, passed=True)
        create_assessment(tmp_db, task.id, passed=False)

        assessments = list_assessments(tmp_db, task.id)
        assert len(assessments) == 2


class TestTaskDetail:
    def test_get_task_detail(self, tmp_db):
        task = create_task(tmp_db, title="Test Task", task_type=TaskType.LEARNING)
        create_artifact(tmp_db, task.id, "notes.md", ArtifactType.NOTE)
        create_assessment(tmp_db, task.id, passed=True)

        detail = get_task_detail(tmp_db, task.id)
        assert detail is not None
        assert len(detail.artifacts) == 1
        assert len(detail.assessments) == 1


class TestSearch:
    def test_search_by_title(self, tmp_db):
        create_task(tmp_db, title="Learn Python", task_type=TaskType.LEARNING)
        create_task(tmp_db, title="Learn JavaScript", task_type=TaskType.LEARNING)
        create_task(tmp_db, title="Implement API", task_type=TaskType.IMPLEMENTATION)

        results = search_tasks(tmp_db, "Python")
        assert len(results) == 1
        assert results[0].title == "Learn Python"

    def test_search_by_description(self, tmp_db):
        create_task(
            tmp_db,
            title="Task 1",
            task_type=TaskType.LEARNING,
            description="Learn about Python",
        )
        create_task(
            tmp_db,
            title="Task 2",
            task_type=TaskType.LEARNING,
            description="Learn about JavaScript",
        )

        results = search_tasks(tmp_db, "Python")
        assert len(results) == 1
