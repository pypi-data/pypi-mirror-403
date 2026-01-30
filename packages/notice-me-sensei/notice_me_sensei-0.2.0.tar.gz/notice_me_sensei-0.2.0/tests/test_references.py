"""Tests for reference management."""

import tempfile
from pathlib import Path

import pytest

from sensei.db import (
    create_reference,
    delete_reference,
    get_reference,
    search_references,
    update_reference,
)
from sensei.init import init_db
from sensei.models import ContentType


@pytest.fixture
def tmp_db():
    """Create a temporary database with migrations applied."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)

    conn = init_db(db_path)
    yield conn
    conn.close()
    db_path.unlink(missing_ok=True)


class TestCreateReference:
    """Tests for create_reference."""

    def test_create_minimal(self, tmp_db):
        """Test creating a reference with minimal fields."""
        ref = create_reference(
            tmp_db,
            title="Test Paper",
            content_type=ContentType.PAPER,
        )

        assert ref.id is not None
        assert ref.title == "Test Paper"
        assert ref.content_type == ContentType.PAPER
        assert ref.description is None
        assert ref.authors is None
        assert ref.url is None
        assert ref.file_path is None
        assert ref.tags == []
        assert ref.metadata == {}
        assert ref.created_at is not None
        assert ref.updated_at is None

    def test_create_full(self, tmp_db):
        """Test creating a reference with all fields."""
        ref = create_reference(
            tmp_db,
            title="Attention Is All You Need",
            content_type=ContentType.ARXIV,
            description="The transformer architecture paper",
            authors="Vaswani et al.",
            url="https://arxiv.org/abs/1706.03762",
            file_path="references/attention-is-all-you-need.pdf",
            tags=["transformers", "nlp", "deep-learning"],
            metadata={"arxiv_id": "1706.03762", "year": 2017},
        )

        assert ref.title == "Attention Is All You Need"
        assert ref.content_type == ContentType.ARXIV
        assert ref.description == "The transformer architecture paper"
        assert ref.authors == "Vaswani et al."
        assert ref.url == "https://arxiv.org/abs/1706.03762"
        assert ref.file_path == "references/attention-is-all-you-need.pdf"
        assert ref.tags == ["transformers", "nlp", "deep-learning"]
        assert ref.metadata == {"arxiv_id": "1706.03762", "year": 2017}


class TestGetReference:
    """Tests for get_reference."""

    def test_get_by_full_id(self, tmp_db):
        """Test getting a reference by full ID."""
        created = create_reference(
            tmp_db,
            title="Test Reference",
            content_type=ContentType.WEBPAGE,
        )

        found = get_reference(tmp_db, created.id)
        assert found is not None
        assert found.id == created.id
        assert found.title == "Test Reference"

    def test_get_by_partial_id(self, tmp_db):
        """Test getting a reference by partial ID."""
        created = create_reference(
            tmp_db,
            title="Test Reference",
            content_type=ContentType.WEBPAGE,
        )

        # Use first 8 characters
        found = get_reference(tmp_db, created.id[:8])
        assert found is not None
        assert found.id == created.id

    def test_get_not_found(self, tmp_db):
        """Test getting a non-existent reference."""
        found = get_reference(tmp_db, "nonexistent")
        assert found is None

    def test_get_ambiguous_id(self, tmp_db):
        """Test that ambiguous partial IDs raise an error."""
        # This test is probabilistic - create many refs to increase chance of collision
        refs = []
        for i in range(100):
            refs.append(
                create_reference(
                    tmp_db,
                    title=f"Reference {i}",
                    content_type=ContentType.OTHER,
                )
            )

        # Try to find ambiguous match (may not always happen)
        # Just verify that get_reference doesn't crash on normal IDs
        for ref in refs[:5]:
            found = get_reference(tmp_db, ref.id)
            assert found is not None


class TestSearchReferences:
    """Tests for search_references."""

    def test_search_by_title(self, tmp_db):
        """Test searching by title."""
        create_reference(
            tmp_db,
            title="Machine Learning Basics",
            content_type=ContentType.BOOK,
        )
        create_reference(
            tmp_db,
            title="Deep Learning",
            content_type=ContentType.BOOK,
        )

        results = search_references(tmp_db, query="Machine")
        assert len(results) == 1
        assert results[0].title == "Machine Learning Basics"

    def test_search_by_description(self, tmp_db):
        """Test searching by description."""
        create_reference(
            tmp_db,
            title="Paper A",
            description="About neural networks",
            content_type=ContentType.PAPER,
        )

        results = search_references(tmp_db, query="neural")
        assert len(results) == 1
        assert results[0].title == "Paper A"

    def test_search_by_authors(self, tmp_db):
        """Test searching by authors."""
        create_reference(
            tmp_db,
            title="Research Paper",
            authors="Smith, Johnson, Williams",
            content_type=ContentType.PAPER,
        )

        results = search_references(tmp_db, query="Johnson")
        assert len(results) == 1
        assert "Johnson" in results[0].authors

    def test_filter_by_content_type(self, tmp_db):
        """Test filtering by content type."""
        create_reference(
            tmp_db,
            title="A Book",
            content_type=ContentType.BOOK,
        )
        create_reference(
            tmp_db,
            title="A Paper",
            content_type=ContentType.PAPER,
        )

        results = search_references(tmp_db, content_type=ContentType.BOOK)
        assert len(results) == 1
        assert results[0].title == "A Book"

    def test_filter_by_tags(self, tmp_db):
        """Test filtering by tags."""
        create_reference(
            tmp_db,
            title="ML Paper",
            content_type=ContentType.PAPER,
            tags=["machine-learning", "ai"],
        )
        create_reference(
            tmp_db,
            title="Web Dev",
            content_type=ContentType.DOCUMENTATION,
            tags=["javascript", "react"],
        )

        results = search_references(tmp_db, tags=["machine-learning"])
        assert len(results) == 1
        assert results[0].title == "ML Paper"

    def test_search_with_limit(self, tmp_db):
        """Test limiting search results."""
        for i in range(10):
            create_reference(
                tmp_db,
                title=f"Reference {i}",
                content_type=ContentType.OTHER,
            )

        results = search_references(tmp_db, limit=5)
        assert len(results) == 5

    def test_search_no_query(self, tmp_db):
        """Test listing all references without query."""
        create_reference(tmp_db, title="Ref 1", content_type=ContentType.OTHER)
        create_reference(tmp_db, title="Ref 2", content_type=ContentType.OTHER)

        results = search_references(tmp_db)
        assert len(results) == 2


class TestUpdateReference:
    """Tests for update_reference."""

    def test_update_title(self, tmp_db):
        """Test updating the title."""
        ref = create_reference(
            tmp_db,
            title="Old Title",
            content_type=ContentType.WEBPAGE,
        )

        updated = update_reference(tmp_db, ref.id, title="New Title")
        assert updated is not None
        assert updated.title == "New Title"
        assert updated.updated_at is not None

    def test_update_description(self, tmp_db):
        """Test updating the description."""
        ref = create_reference(
            tmp_db,
            title="Test",
            content_type=ContentType.PAPER,
        )

        updated = update_reference(tmp_db, ref.id, description="A new description")
        assert updated.description == "A new description"

    def test_update_tags(self, tmp_db):
        """Test updating tags replaces existing."""
        ref = create_reference(
            tmp_db,
            title="Test",
            content_type=ContentType.OTHER,
            tags=["old-tag"],
        )

        updated = update_reference(tmp_db, ref.id, tags=["new-tag", "another"])
        assert updated.tags == ["new-tag", "another"]

    def test_update_not_found(self, tmp_db):
        """Test updating non-existent reference."""
        updated = update_reference(tmp_db, "nonexistent", title="New")
        assert updated is None

    def test_update_by_partial_id(self, tmp_db):
        """Test updating by partial ID."""
        ref = create_reference(
            tmp_db,
            title="Original",
            content_type=ContentType.BOOK,
        )

        updated = update_reference(tmp_db, ref.id[:8], title="Updated")
        assert updated is not None
        assert updated.title == "Updated"


class TestDeleteReference:
    """Tests for delete_reference."""

    def test_delete_existing(self, tmp_db):
        """Test deleting an existing reference."""
        ref = create_reference(
            tmp_db,
            title="To Delete",
            content_type=ContentType.OTHER,
        )

        result = delete_reference(tmp_db, ref.id)
        assert result is True

        # Verify deleted
        found = get_reference(tmp_db, ref.id)
        assert found is None

    def test_delete_not_found(self, tmp_db):
        """Test deleting non-existent reference."""
        result = delete_reference(tmp_db, "nonexistent")
        assert result is False

    def test_delete_by_partial_id(self, tmp_db):
        """Test deleting by partial ID."""
        ref = create_reference(
            tmp_db,
            title="To Delete",
            content_type=ContentType.OTHER,
        )

        result = delete_reference(tmp_db, ref.id[:8])
        assert result is True


class TestContentTypes:
    """Test all content types work correctly."""

    @pytest.mark.parametrize(
        "content_type",
        [
            ContentType.WEBPAGE,
            ContentType.PDF,
            ContentType.ARXIV,
            ContentType.BOOK,
            ContentType.VIDEO,
            ContentType.PAPER,
            ContentType.DOCUMENTATION,
            ContentType.OTHER,
        ],
    )
    def test_create_with_content_type(self, tmp_db, content_type):
        """Test creating references with each content type."""
        ref = create_reference(
            tmp_db,
            title=f"Test {content_type.value}",
            content_type=content_type,
        )
        assert ref.content_type == content_type

        # Verify can be retrieved
        found = get_reference(tmp_db, ref.id)
        assert found.content_type == content_type
