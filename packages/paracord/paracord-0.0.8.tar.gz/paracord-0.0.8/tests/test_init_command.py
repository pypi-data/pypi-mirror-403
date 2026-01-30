"""Tests for paracord init command."""

import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

from paracord.cli import app


runner = CliRunner()


class TestInitCommand:
    """Tests for the init command."""

    def test_init_fails_when_directory_exists(self, tmp_path: Path) -> None:
        """Should fail when target directory already exists."""
        # Create the directory that we'll try to init into
        existing_dir = tmp_path / "existing-project"
        existing_dir.mkdir()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Create the directory in the isolated filesystem
            Path("existing-project").mkdir()

            result = runner.invoke(app, ["init", "existing-project"])

            assert result.exit_code == 1
            assert "already exists" in result.output

    @patch("paracord.commands.init.run_copier_copy")
    @patch("paracord.commands.init.register_project_sync")
    def test_init_with_project_name_calls_copier(
        self,
        mock_register: MagicMock,
        mock_copier: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Should call copier with project name."""
        mock_copier.return_value = True

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(app, ["init", "my-project"])

            mock_copier.assert_called_once()
            call_kwargs = mock_copier.call_args
            assert call_kwargs[1]["project_name"] == "my-project"

    @patch("paracord.commands.init.run_copier_copy")
    @patch("paracord.commands.init.register_project_sync")
    def test_init_success_shows_next_steps(
        self,
        mock_register: MagicMock,
        mock_copier: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Should show next steps on successful init."""
        mock_copier.return_value = True

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(app, ["init", "my-project"])

            assert result.exit_code == 0
            assert "successfully" in result.output.lower()
            assert "cd my-project" in result.output
            assert "uv sync" in result.output

    @patch("paracord.commands.init.run_copier_copy")
    @patch("paracord.commands.init.register_project_sync")
    def test_init_failure_exits_with_error(
        self,
        mock_register: MagicMock,
        mock_copier: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Should exit with error when copier fails."""
        mock_copier.return_value = False

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(app, ["init", "my-project"])

            assert result.exit_code == 1
            assert "failed" in result.output.lower()

    @patch("paracord.commands.init.run_copier_copy")
    @patch("paracord.commands.init.register_project_sync")
    def test_init_with_custom_template(
        self,
        mock_register: MagicMock,
        mock_copier: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Should pass custom template to copier."""
        mock_copier.return_value = True

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                app, ["init", "my-project", "--template", "gh:custom/template"]
            )

            mock_copier.assert_called_once()
            call_kwargs = mock_copier.call_args
            assert call_kwargs[1]["template"] == "gh:custom/template"


class TestInitGitChecks:
    """Tests for git status checks in init command."""

    @patch("paracord.commands.init.run_copier_copy")
    @patch("paracord.commands.init.register_project_sync")
    @patch("paracord.commands.init.get_git_status")
    def test_init_in_current_dir_warns_no_git(
        self,
        mock_git_status: MagicMock,
        mock_register: MagicMock,
        mock_copier: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Should warn when initializing in non-git directory."""
        from paracord.utils.git import GitStatus

        mock_git_status.return_value = GitStatus(
            is_git_repo=False,
            is_dirty=False,
            has_staged=False,
            has_unstaged=False,
            has_untracked=False,
        )
        mock_copier.return_value = True

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(app, ["init"])

            assert "not a git repository" in result.output.lower()

    @patch("paracord.commands.init.run_copier_copy")
    @patch("paracord.commands.init.register_project_sync")
    @patch("paracord.commands.init.get_git_status")
    def test_init_in_dirty_repo_prompts_user(
        self,
        mock_git_status: MagicMock,
        mock_register: MagicMock,
        mock_copier: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Should prompt when initializing in dirty git repo."""
        from paracord.utils.git import GitStatus

        mock_git_status.return_value = GitStatus(
            is_git_repo=True,
            is_dirty=True,
            has_staged=False,
            has_unstaged=True,
            has_untracked=False,
        )
        mock_copier.return_value = True

        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Answer 'y' to continue
            result = runner.invoke(app, ["init"], input="y\n")

            assert "uncommitted changes" in result.output.lower()

    @patch("paracord.commands.init.run_copier_copy")
    @patch("paracord.commands.init.register_project_sync")
    @patch("paracord.commands.init.get_git_status")
    def test_init_in_dirty_repo_can_cancel(
        self,
        mock_git_status: MagicMock,
        mock_register: MagicMock,
        mock_copier: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Should cancel when user declines in dirty repo."""
        from paracord.utils.git import GitStatus

        mock_git_status.return_value = GitStatus(
            is_git_repo=True,
            is_dirty=True,
            has_staged=True,
            has_unstaged=False,
            has_untracked=False,
        )

        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Answer 'n' to cancel
            result = runner.invoke(app, ["init"], input="n\n")

            assert result.exit_code == 0
            assert "cancelled" in result.output.lower()
            mock_copier.assert_not_called()

    @patch("paracord.commands.init.run_copier_copy")
    @patch("paracord.commands.init.register_project_sync")
    def test_init_with_project_name_skips_git_check(
        self,
        mock_register: MagicMock,
        mock_copier: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Should not check git status when creating new directory."""
        mock_copier.return_value = True

        with runner.isolated_filesystem(temp_dir=tmp_path):
            # When a project name is given, git check is skipped for current dir
            result = runner.invoke(app, ["init", "new-project"])

            # Should succeed without git prompts
            assert result.exit_code == 0
            assert "uncommitted changes" not in result.output.lower()
