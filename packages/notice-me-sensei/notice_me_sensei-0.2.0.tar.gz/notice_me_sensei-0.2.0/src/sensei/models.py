"""Pydantic models for Sensei."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TaskType(str, Enum):
    """Types of study tasks."""

    LEARNING = "learning"
    IMPLEMENTATION = "implementation"
    SRS = "srs"
    TEST = "test"
    REVIEW = "review"


class TaskStatus(str, Enum):
    """Task status values."""

    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class ArtifactType(str, Enum):
    """Types of artifacts that can be linked to tasks."""

    NOTE = "note"
    CODE = "code"
    NOTEBOOK = "notebook"
    PDF = "pdf"
    TEST_HARNESS = "test_harness"
    OTHER = "other"


class ContentType(str, Enum):
    """Types of reference content."""

    WEBPAGE = "webpage"
    PDF = "pdf"
    ARXIV = "arxiv"
    BOOK = "book"
    VIDEO = "video"
    PAPER = "paper"
    DOCUMENTATION = "documentation"
    OTHER = "other"


class SRSMetadata(BaseModel):
    """SRS scheduling metadata."""

    interval_days: int = 1
    ease_factor: float = 2.5
    repetition_count: int = 0


class Task(BaseModel):
    """A study task."""

    id: str
    parent_id: str | None = None
    type: TaskType
    title: str
    description: str | None = None
    status: TaskStatus = TaskStatus.PENDING
    path: str | None = None
    due_date: datetime | None = None
    created_at: datetime
    completed_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Artifact(BaseModel):
    """A file linked to a task."""

    id: str
    task_id: str
    path: str
    type: ArtifactType
    created_at: datetime


class Assessment(BaseModel):
    """An assessment record for a task."""

    id: str
    task_id: str
    score: float | None = None
    passed: bool | None = None
    feedback: str | None = None
    created_at: datetime


class TaskDetail(Task):
    """Task with related artifacts and assessments."""

    artifacts: list[Artifact] = Field(default_factory=list)
    assessments: list[Assessment] = Field(default_factory=list)


class Reference(BaseModel):
    """A study material reference (paper, book, webpage, etc.)."""

    id: str
    title: str
    description: str | None = None
    authors: str | None = None
    url: str | None = None
    file_path: str | None = None
    content_type: ContentType
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime | None = None
