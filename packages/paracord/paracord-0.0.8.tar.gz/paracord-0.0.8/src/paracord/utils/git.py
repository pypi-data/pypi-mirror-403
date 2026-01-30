"""Git utilities for Paracord CLI."""

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GitStatus:
    """Git repository status information."""

    is_git_repo: bool
    is_dirty: bool
    has_staged: bool
    has_unstaged: bool
    has_untracked: bool

    @property
    def has_changes(self) -> bool:
        """Check if there are any uncommitted changes."""
        return self.has_staged or self.has_unstaged or self.has_untracked


def is_git_repo(path: Path | None = None) -> bool:
    """Check if the given path is inside a git repository.

    Args:
        path: Directory to check. Defaults to current directory.

    Returns:
        True if inside a git repository, False otherwise.
    """
    cwd = str(path) if path else None
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0 and result.stdout.strip() == "true"
    except FileNotFoundError:
        # git not installed
        return False
    except Exception:
        return False


def is_git_dirty(path: Path | None = None) -> bool:
    """Check if the git repository has uncommitted changes.

    Args:
        path: Directory to check. Defaults to current directory.

    Returns:
        True if there are uncommitted changes, False otherwise.
    """
    cwd = str(path) if path else None
    try:
        # Check for any changes (staged, unstaged, or untracked)
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        return result.returncode == 0 and bool(result.stdout.strip())
    except Exception:
        return False


def get_git_status(path: Path | None = None) -> GitStatus:
    """Get detailed git status for a directory.

    Args:
        path: Directory to check. Defaults to current directory.

    Returns:
        GitStatus with detailed repository state.
    """
    if not is_git_repo(path):
        return GitStatus(
            is_git_repo=False,
            is_dirty=False,
            has_staged=False,
            has_unstaged=False,
            has_untracked=False,
        )

    cwd = str(path) if path else None
    has_staged = False
    has_unstaged = False
    has_untracked = False

    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if len(line) >= 2:
                    index_status = line[0]
                    worktree_status = line[1]

                    # Untracked files (both columns are ?)
                    if index_status == "?":
                        has_untracked = True
                    else:
                        # Staged changes (first column is not space or ?)
                        if index_status != " ":
                            has_staged = True
                        # Unstaged changes (second column is M, D, etc. but not space)
                        if worktree_status != " ":
                            has_unstaged = True
    except Exception:
        pass

    is_dirty = has_staged or has_unstaged or has_untracked

    return GitStatus(
        is_git_repo=True,
        is_dirty=is_dirty,
        has_staged=has_staged,
        has_unstaged=has_unstaged,
        has_untracked=has_untracked,
    )


def check_git_status_with_suggestions(
    path: Path | None = None,
    operation: str = "this operation",
) -> tuple[GitStatus, list[str]]:
    """Check git status and return suggestions based on the state.

    Args:
        path: Directory to check. Defaults to current directory.
        operation: Description of the operation for context in suggestions.

    Returns:
        Tuple of (GitStatus, list of suggestion strings).
    """
    status = get_git_status(path)
    suggestions: list[str] = []

    if not status.is_git_repo:
        suggestions.append(
            f"This directory is not a git repository. Consider running "
            f"[command]git init[/command] to track changes from {operation}."
        )
    elif status.is_dirty:
        if status.has_staged:
            suggestions.append(
                "You have staged changes. Consider committing them before "
                f"{operation}: [command]git commit -m 'your message'[/command]"
            )
        if status.has_unstaged:
            suggestions.append(
                "You have unstaged changes. Consider committing or stashing them: "
                "[command]git add . && git commit -m 'your message'[/command] or "
                "[command]git stash[/command]"
            )
        if status.has_untracked and not status.has_staged and not status.has_unstaged:
            suggestions.append(
                "You have untracked files. Consider adding and committing them: "
                "[command]git add . && git commit -m 'your message'[/command]"
            )

    return status, suggestions
