"""Tests for paracord update command."""

import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from typer.testing import CliRunner

from paracord.cli import app


runner = CliRunner()


class TestUpdateCommand:
    """Tests for the update command."""

    def test_update_fails_outside_project(self, tmp_path: Path) -> None:
        """Should fail when not in a Paracord project."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(app, ["update"])

            assert result.exit_code == 1
            assert "not in a paracord project" in result.output.lower()

    @patch("paracord.commands.update.run_copier_update")
    @patch("paracord.commands.update.check_git_status_with_suggestions")
    def test_update_in_project_calls_copier(
        self,
        mock_git_check: MagicMock,
        mock_copier: MagicMock,
        paracord_project: Path,
    ) -> None:
        """Should call copier update in a valid project."""
        from paracord.utils.git import GitStatus

        mock_git_check.return_value = (
            GitStatus(
                is_git_repo=True,
                is_dirty=False,
                has_staged=False,
                has_unstaged=False,
                has_untracked=False,
            ),
            [],
        )
        mock_copier.return_value = True

        # Change to project directory and run
        original_cwd = os.getcwd()
        try:
            os.chdir(paracord_project)
            # Answer 'y' to proceed with update
            result = runner.invoke(app, ["update"], input="y\n")

            mock_copier.assert_called_once()
        finally:
            os.chdir(original_cwd)

    @patch("paracord.commands.update.run_copier_update")
    @patch("paracord.commands.update.check_git_status_with_suggestions")
    def test_update_shows_template_info(
        self,
        mock_git_check: MagicMock,
        mock_copier: MagicMock,
        paracord_project: Path,
    ) -> None:
        """Should display template source and version."""
        from paracord.utils.git import GitStatus

        mock_git_check.return_value = (
            GitStatus(
                is_git_repo=True,
                is_dirty=False,
                has_staged=False,
                has_unstaged=False,
                has_untracked=False,
            ),
            [],
        )
        mock_copier.return_value = True

        original_cwd = os.getcwd()
        try:
            os.chdir(paracord_project)
            result = runner.invoke(app, ["update"], input="y\n")

            assert "gh:paracord-run/dash" in result.output
            assert "abc12345" in result.output
        finally:
            os.chdir(original_cwd)

    @patch("paracord.commands.update.run_copier_update")
    @patch("paracord.commands.update.check_git_status_with_suggestions")
    def test_update_can_be_cancelled(
        self,
        mock_git_check: MagicMock,
        mock_copier: MagicMock,
        paracord_project: Path,
    ) -> None:
        """Should allow cancelling the update."""
        from paracord.utils.git import GitStatus

        mock_git_check.return_value = (
            GitStatus(
                is_git_repo=True,
                is_dirty=False,
                has_staged=False,
                has_unstaged=False,
                has_untracked=False,
            ),
            [],
        )

        original_cwd = os.getcwd()
        try:
            os.chdir(paracord_project)
            # Answer 'n' to cancel
            result = runner.invoke(app, ["update"], input="n\n")

            assert result.exit_code == 0
            assert "cancelled" in result.output.lower()
            mock_copier.assert_not_called()
        finally:
            os.chdir(original_cwd)

    @patch("paracord.commands.update.run_copier_update")
    @patch("paracord.commands.update.check_git_status_with_suggestions")
    def test_update_failure_shows_error(
        self,
        mock_git_check: MagicMock,
        mock_copier: MagicMock,
        paracord_project: Path,
    ) -> None:
        """Should show error when copier update fails."""
        from paracord.utils.git import GitStatus

        mock_git_check.return_value = (
            GitStatus(
                is_git_repo=True,
                is_dirty=False,
                has_staged=False,
                has_unstaged=False,
                has_untracked=False,
            ),
            [],
        )
        mock_copier.return_value = False

        original_cwd = os.getcwd()
        try:
            os.chdir(paracord_project)
            result = runner.invoke(app, ["update"], input="y\n")

            assert result.exit_code == 1
            assert "failed" in result.output.lower()
        finally:
            os.chdir(original_cwd)


class TestUpdateGitChecks:
    """Tests for git status checks in update command."""

    @patch("paracord.commands.update.run_copier_update")
    @patch("paracord.commands.update.check_git_status_with_suggestions")
    def test_update_warns_no_git(
        self,
        mock_git_check: MagicMock,
        mock_copier: MagicMock,
        paracord_project: Path,
    ) -> None:
        """Should warn when updating in non-git directory."""
        from paracord.utils.git import GitStatus

        mock_git_check.return_value = (
            GitStatus(
                is_git_repo=False,
                is_dirty=False,
                has_staged=False,
                has_unstaged=False,
                has_untracked=False,
            ),
            ["Consider running git init"],
        )
        mock_copier.return_value = True

        original_cwd = os.getcwd()
        try:
            os.chdir(paracord_project)
            # Answer 'y' to continue without git, then 'y' to proceed
            result = runner.invoke(app, ["update"], input="y\ny\n")

            assert "not a git repository" in result.output.lower()
        finally:
            os.chdir(original_cwd)

    @patch("paracord.commands.update.run_copier_update")
    @patch("paracord.commands.update.check_git_status_with_suggestions")
    def test_update_can_cancel_without_git(
        self,
        mock_git_check: MagicMock,
        mock_copier: MagicMock,
        paracord_project: Path,
    ) -> None:
        """Should allow cancelling when no git repo."""
        from paracord.utils.git import GitStatus

        mock_git_check.return_value = (
            GitStatus(
                is_git_repo=False,
                is_dirty=False,
                has_staged=False,
                has_unstaged=False,
                has_untracked=False,
            ),
            [],
        )

        original_cwd = os.getcwd()
        try:
            os.chdir(paracord_project)
            # Answer 'n' to cancel due to no git
            result = runner.invoke(app, ["update"], input="n\n")

            assert result.exit_code == 0
            assert "cancelled" in result.output.lower()
            mock_copier.assert_not_called()
        finally:
            os.chdir(original_cwd)

    @patch("paracord.commands.update.run_copier_update")
    @patch("paracord.commands.update.check_git_status_with_suggestions")
    def test_update_warns_dirty_repo(
        self,
        mock_git_check: MagicMock,
        mock_copier: MagicMock,
        paracord_project: Path,
    ) -> None:
        """Should warn when updating with uncommitted changes."""
        from paracord.utils.git import GitStatus

        mock_git_check.return_value = (
            GitStatus(
                is_git_repo=True,
                is_dirty=True,
                has_staged=True,
                has_unstaged=False,
                has_untracked=False,
            ),
            ["You have staged changes. Consider committing."],
        )
        mock_copier.return_value = True

        original_cwd = os.getcwd()
        try:
            os.chdir(paracord_project)
            # Answer 'y' to continue with dirty repo, then 'y' to proceed
            result = runner.invoke(app, ["update"], input="y\ny\n")

            assert "uncommitted changes" in result.output.lower()
        finally:
            os.chdir(original_cwd)

    @patch("paracord.commands.update.run_copier_update")
    @patch("paracord.commands.update.check_git_status_with_suggestions")
    def test_update_can_cancel_dirty_repo(
        self,
        mock_git_check: MagicMock,
        mock_copier: MagicMock,
        paracord_project: Path,
    ) -> None:
        """Should allow cancelling when repo is dirty."""
        from paracord.utils.git import GitStatus

        mock_git_check.return_value = (
            GitStatus(
                is_git_repo=True,
                is_dirty=True,
                has_staged=False,
                has_unstaged=True,
                has_untracked=True,
            ),
            ["You have unstaged changes."],
        )

        original_cwd = os.getcwd()
        try:
            os.chdir(paracord_project)
            # Answer 'n' to cancel due to dirty repo
            result = runner.invoke(app, ["update"], input="n\n")

            assert result.exit_code == 0
            assert "cancelled" in result.output.lower()
            mock_copier.assert_not_called()
        finally:
            os.chdir(original_cwd)

    @patch("paracord.commands.update.run_copier_update")
    @patch("paracord.commands.update.check_git_status_with_suggestions")
    def test_update_shows_suggestions(
        self,
        mock_git_check: MagicMock,
        mock_copier: MagicMock,
        paracord_project: Path,
    ) -> None:
        """Should display git suggestions to user."""
        from paracord.utils.git import GitStatus

        mock_git_check.return_value = (
            GitStatus(
                is_git_repo=True,
                is_dirty=True,
                has_staged=False,
                has_unstaged=True,
                has_untracked=False,
            ),
            ["You have unstaged changes. Consider committing or stashing."],
        )
        mock_copier.return_value = True

        original_cwd = os.getcwd()
        try:
            os.chdir(paracord_project)
            result = runner.invoke(app, ["update"], input="y\ny\n")

            # Check that suggestions are shown
            assert "unstaged changes" in result.output.lower()
        finally:
            os.chdir(original_cwd)


class TestUpdateOptions:
    """Tests for update command options."""

    @patch("paracord.commands.update.run_copier_update")
    @patch("paracord.commands.update.check_git_status_with_suggestions")
    def test_update_skip_answered_default(
        self,
        mock_git_check: MagicMock,
        mock_copier: MagicMock,
        paracord_project: Path,
    ) -> None:
        """Should pass skip_answered=True by default."""
        from paracord.utils.git import GitStatus

        mock_git_check.return_value = (
            GitStatus(
                is_git_repo=True,
                is_dirty=False,
                has_staged=False,
                has_unstaged=False,
                has_untracked=False,
            ),
            [],
        )
        mock_copier.return_value = True

        original_cwd = os.getcwd()
        try:
            os.chdir(paracord_project)
            result = runner.invoke(app, ["update"], input="y\n")

            call_kwargs = mock_copier.call_args[1]
            assert call_kwargs["skip_answered"] is True
        finally:
            os.chdir(original_cwd)

    @patch("paracord.commands.update.run_copier_update")
    @patch("paracord.commands.update.check_git_status_with_suggestions")
    def test_update_no_skip_answered(
        self,
        mock_git_check: MagicMock,
        mock_copier: MagicMock,
        paracord_project: Path,
    ) -> None:
        """Should pass skip_answered=False when specified."""
        from paracord.utils.git import GitStatus

        mock_git_check.return_value = (
            GitStatus(
                is_git_repo=True,
                is_dirty=False,
                has_staged=False,
                has_unstaged=False,
                has_untracked=False,
            ),
            [],
        )
        mock_copier.return_value = True

        original_cwd = os.getcwd()
        try:
            os.chdir(paracord_project)
            result = runner.invoke(app, ["update", "--no-skip-answered"], input="y\n")

            call_kwargs = mock_copier.call_args[1]
            assert call_kwargs["skip_answered"] is False
        finally:
            os.chdir(original_cwd)

    @patch("paracord.commands.update.run_copier_update")
    @patch("paracord.commands.update.check_git_status_with_suggestions")
    def test_update_conflict_option(
        self,
        mock_git_check: MagicMock,
        mock_copier: MagicMock,
        paracord_project: Path,
    ) -> None:
        """Should pass conflict strategy to copier."""
        from paracord.utils.git import GitStatus

        mock_git_check.return_value = (
            GitStatus(
                is_git_repo=True,
                is_dirty=False,
                has_staged=False,
                has_unstaged=False,
                has_untracked=False,
            ),
            [],
        )
        mock_copier.return_value = True

        original_cwd = os.getcwd()
        try:
            os.chdir(paracord_project)
            result = runner.invoke(app, ["update", "--conflict", "ours"], input="y\n")

            call_kwargs = mock_copier.call_args[1]
            assert call_kwargs["conflict"] == "ours"
        finally:
            os.chdir(original_cwd)
