"""Tests for paracord.utils.git module."""

from pathlib import Path

import pytest

from paracord.utils.git import (
    GitStatus,
    is_git_repo,
    is_git_dirty,
    get_git_status,
    check_git_status_with_suggestions,
)


class TestIsGitRepo:
    """Tests for is_git_repo function."""

    def test_returns_true_for_git_repo(self, git_repo: Path) -> None:
        """Should return True for a valid git repository."""
        assert is_git_repo(git_repo) is True

    def test_returns_false_for_non_git_directory(self, temp_dir: Path) -> None:
        """Should return False for a directory without git."""
        assert is_git_repo(temp_dir) is False

    def test_returns_false_for_nonexistent_directory(self, tmp_path: Path) -> None:
        """Should return False for a directory that doesn't exist."""
        nonexistent = tmp_path / "does-not-exist"
        assert is_git_repo(nonexistent) is False

    def test_works_with_none_uses_cwd(self) -> None:
        """Should use current working directory when path is None."""
        # This test runs from the paracord-cli repo which is a git repo
        result = is_git_repo(None)
        assert isinstance(result, bool)


class TestIsGitDirty:
    """Tests for is_git_dirty function."""

    def test_returns_false_for_clean_repo(self, git_repo: Path) -> None:
        """Should return False for a clean git repository."""
        assert is_git_dirty(git_repo) is False

    def test_returns_true_for_dirty_repo(self, dirty_git_repo: Path) -> None:
        """Should return True when there are untracked files."""
        assert is_git_dirty(dirty_git_repo) is True

    def test_returns_true_for_staged_changes(self, staged_git_repo: Path) -> None:
        """Should return True when there are staged changes."""
        assert is_git_dirty(staged_git_repo) is True

    def test_returns_false_for_non_git_directory(self, temp_dir: Path) -> None:
        """Should return False for a non-git directory."""
        assert is_git_dirty(temp_dir) is False


class TestGetGitStatus:
    """Tests for get_git_status function."""

    def test_non_git_directory(self, temp_dir: Path) -> None:
        """Should return status showing not a git repo."""
        status = get_git_status(temp_dir)

        assert status.is_git_repo is False
        assert status.is_dirty is False
        assert status.has_staged is False
        assert status.has_unstaged is False
        assert status.has_untracked is False

    def test_clean_git_repo(self, git_repo: Path) -> None:
        """Should return clean status for a fresh git repo."""
        status = get_git_status(git_repo)

        assert status.is_git_repo is True
        assert status.is_dirty is False
        assert status.has_staged is False
        assert status.has_unstaged is False
        assert status.has_untracked is False

    def test_repo_with_untracked_files(self, dirty_git_repo: Path) -> None:
        """Should detect untracked files."""
        status = get_git_status(dirty_git_repo)

        assert status.is_git_repo is True
        assert status.is_dirty is True
        assert status.has_staged is False
        assert status.has_unstaged is False
        assert status.has_untracked is True

    def test_repo_with_staged_files(self, staged_git_repo: Path) -> None:
        """Should detect staged files."""
        status = get_git_status(staged_git_repo)

        assert status.is_git_repo is True
        assert status.is_dirty is True
        assert status.has_staged is True
        assert status.has_unstaged is False
        assert status.has_untracked is False

    def test_repo_with_mixed_changes(self, mixed_git_repo: Path) -> None:
        """Should detect all types of changes."""
        status = get_git_status(mixed_git_repo)

        assert status.is_git_repo is True
        assert status.is_dirty is True
        assert status.has_staged is True
        assert status.has_unstaged is True
        assert status.has_untracked is True


class TestGitStatusHasChanges:
    """Tests for GitStatus.has_changes property."""

    def test_no_changes(self) -> None:
        """Should return False when no changes."""
        status = GitStatus(
            is_git_repo=True,
            is_dirty=False,
            has_staged=False,
            has_unstaged=False,
            has_untracked=False,
        )
        assert status.has_changes is False

    def test_has_staged(self) -> None:
        """Should return True when has staged changes."""
        status = GitStatus(
            is_git_repo=True,
            is_dirty=True,
            has_staged=True,
            has_unstaged=False,
            has_untracked=False,
        )
        assert status.has_changes is True

    def test_has_unstaged(self) -> None:
        """Should return True when has unstaged changes."""
        status = GitStatus(
            is_git_repo=True,
            is_dirty=True,
            has_staged=False,
            has_unstaged=True,
            has_untracked=False,
        )
        assert status.has_changes is True

    def test_has_untracked(self) -> None:
        """Should return True when has untracked files."""
        status = GitStatus(
            is_git_repo=True,
            is_dirty=True,
            has_staged=False,
            has_unstaged=False,
            has_untracked=True,
        )
        assert status.has_changes is True


class TestCheckGitStatusWithSuggestions:
    """Tests for check_git_status_with_suggestions function."""

    def test_non_git_repo_suggests_git_init(self, temp_dir: Path) -> None:
        """Should suggest git init for non-git directories."""
        status, suggestions = check_git_status_with_suggestions(temp_dir, "updating")

        assert status.is_git_repo is False
        assert len(suggestions) == 1
        assert "git init" in suggestions[0]
        assert "updating" in suggestions[0]

    def test_clean_repo_no_suggestions(self, git_repo: Path) -> None:
        """Should return no suggestions for a clean repo."""
        status, suggestions = check_git_status_with_suggestions(git_repo, "updating")

        assert status.is_git_repo is True
        assert status.is_dirty is False
        assert len(suggestions) == 0

    def test_staged_changes_suggests_commit(self, staged_git_repo: Path) -> None:
        """Should suggest committing staged changes."""
        status, suggestions = check_git_status_with_suggestions(staged_git_repo, "updating")

        assert status.has_staged is True
        assert len(suggestions) >= 1
        assert any("staged changes" in s.lower() for s in suggestions)
        assert any("commit" in s.lower() for s in suggestions)

    def test_unstaged_changes_suggests_commit_or_stash(self, mixed_git_repo: Path) -> None:
        """Should suggest committing or stashing unstaged changes."""
        status, suggestions = check_git_status_with_suggestions(mixed_git_repo, "updating")

        assert status.has_unstaged is True
        assert len(suggestions) >= 1
        assert any("stash" in s.lower() for s in suggestions)

    def test_untracked_only_suggests_add_and_commit(self, dirty_git_repo: Path) -> None:
        """Should suggest adding and committing untracked files."""
        status, suggestions = check_git_status_with_suggestions(dirty_git_repo, "updating")

        assert status.has_untracked is True
        assert status.has_staged is False
        assert status.has_unstaged is False
        assert len(suggestions) >= 1
        assert any("untracked" in s.lower() for s in suggestions)

    def test_operation_name_in_suggestion(self, temp_dir: Path) -> None:
        """Should include the operation name in suggestions."""
        _, suggestions = check_git_status_with_suggestions(temp_dir, "deploying to production")

        assert any("deploying to production" in s for s in suggestions)
