"""Tests for project initialization."""

import tempfile
from pathlib import Path

from sensei.init import find_project_root, is_sensei_project


class TestInitProject:
    def test_creates_directories(self, tmp_project):
        assert (tmp_project / ".claude" / "skills" / "sensei").is_dir()
        assert (tmp_project / "topics").is_dir()
        assert (tmp_project / "practice").is_dir()

    def test_creates_skill_file(self, tmp_project):
        skill_file = tmp_project / ".claude" / "skills" / "sensei" / "SKILL.md"
        assert skill_file.exists()
        content = skill_file.read_text()
        assert "sensei" in content
        assert "Learning Coach" in content

    def test_creates_settings(self, tmp_project):
        settings_file = tmp_project / ".claude" / "settings.local.json"
        assert settings_file.exists()
        content = settings_file.read_text()
        assert "mcpServers" in content
        assert "sensei" in content

    def test_creates_claude_md(self, tmp_project):
        claude_md = tmp_project / "CLAUDE.md"
        assert claude_md.exists()
        content = claude_md.read_text()
        assert "Study Project" in content

    def test_creates_database(self, tmp_project):
        db_file = tmp_project / "sensei.db"
        assert db_file.exists()


class TestIsSenseiProject:
    def test_is_project(self, tmp_project):
        assert is_sensei_project(tmp_project) is True

    def test_not_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            assert is_sensei_project(Path(tmpdir)) is False


class TestFindProjectRoot:
    def test_finds_root(self, tmp_project):
        # Create a subdirectory
        subdir = tmp_project / "topics" / "deep" / "nested"
        subdir.mkdir(parents=True)

        import os

        original = os.getcwd()
        try:
            os.chdir(subdir)
            root = find_project_root()
            assert root == tmp_project
        finally:
            os.chdir(original)

    def test_no_project(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            import os

            original = os.getcwd()
            try:
                os.chdir(tmpdir)
                root = find_project_root()
                assert root is None
            finally:
                os.chdir(original)
