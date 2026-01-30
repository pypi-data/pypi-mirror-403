"""Tests for paracord.core.context module."""

from pathlib import Path

import pytest

from paracord.core.context import (
    ProjectContext,
    find_project_root,
    get_project_context,
    require_project_context,
)


class TestFindProjectRoot:
    """Tests for find_project_root function."""

    def test_finds_root_with_copier_answers(self, paracord_project: Path) -> None:
        """Should find project root when .copier-answers.yml exists."""
        result = find_project_root(paracord_project)
        assert result == paracord_project

    def test_finds_root_from_subdirectory(self, paracord_project: Path) -> None:
        """Should find project root when starting from a subdirectory."""
        subdir = paracord_project / "src" / "deep" / "nested"
        subdir.mkdir(parents=True)

        result = find_project_root(subdir)
        assert result == paracord_project

    def test_returns_none_for_non_project(self, temp_dir: Path) -> None:
        """Should return None when no project indicators found."""
        result = find_project_root(temp_dir)
        assert result is None

    def test_finds_root_with_rav_config_only(self, tmp_path: Path) -> None:
        """Should find project root when only rav.yaml exists."""
        project = tmp_path / "rav-only-project"
        project.mkdir()
        (project / "rav.yaml").write_text("scripts:\n  test: echo test\n")

        result = find_project_root(project)
        assert result == project


class TestGetProjectContext:
    """Tests for get_project_context function."""

    def test_paracord_project_context(self, paracord_project: Path) -> None:
        """Should correctly identify a Paracord project."""
        context = get_project_context(paracord_project)

        assert context.is_paracord_project is True
        assert context.has_copier_answers is True
        assert context.has_rav_config is True
        assert context.path == paracord_project
        assert context.template_source == "gh:paracord-run/dash"
        assert context.template_commit == "abc12345"
        assert context.project_name == "test-project"

    def test_non_project_context(self, temp_dir: Path) -> None:
        """Should return non-project context for empty directory."""
        context = get_project_context(temp_dir)

        assert context.is_paracord_project is False
        assert context.has_copier_answers is False
        assert context.has_rav_config is False
        assert context.template_source is None
        assert context.template_commit is None

    def test_copier_answers_loaded(self, paracord_project: Path) -> None:
        """Should load copier answers dict."""
        context = get_project_context(paracord_project)

        assert context.copier_answers is not None
        assert "_src_path" in context.copier_answers
        assert context.copier_answers["project_name"] == "test-project"

    def test_rav_config_loaded(self, paracord_project: Path) -> None:
        """Should load rav config dict."""
        context = get_project_context(paracord_project)

        assert context.rav_config is not None
        assert "scripts" in context.rav_config

    def test_project_name_from_directory(self, tmp_path: Path) -> None:
        """Should use directory name when project_name not in copier answers."""
        project = tmp_path / "my-project-dir"
        project.mkdir()
        (project / ".copier-answers.yml").write_text("_src_path: gh:test/template\n")

        context = get_project_context(project)
        assert context.project_name == "my-project-dir"


class TestRequireProjectContext:
    """Tests for require_project_context function."""

    def test_returns_context_for_valid_project(self, paracord_project: Path) -> None:
        """Should return context for a valid Paracord project."""
        context = require_project_context(paracord_project)

        assert context.is_paracord_project is True
        assert context.path == paracord_project

    def test_finds_root_from_subdirectory(self, paracord_project: Path) -> None:
        """Should find project root from subdirectory."""
        subdir = paracord_project / "src"
        subdir.mkdir()

        context = require_project_context(subdir)
        assert context.path == paracord_project

    def test_exits_for_non_project(self, temp_dir: Path) -> None:
        """Should raise SystemExit for non-project directory."""
        with pytest.raises(SystemExit) as exc_info:
            require_project_context(temp_dir)

        assert exc_info.value.code == 1


class TestProjectContextDataclass:
    """Tests for ProjectContext dataclass."""

    def test_default_values(self) -> None:
        """Should have sensible default values."""
        context = ProjectContext(
            path=Path("/test"),
            is_paracord_project=False,
            has_copier_answers=False,
            has_rav_config=False,
        )

        assert context.template_source is None
        assert context.template_commit is None
        assert context.project_name is None
        assert context.copier_answers is None
        assert context.rav_config is None
