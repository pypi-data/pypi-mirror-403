"""Shared fixtures for Paracord CLI tests."""

import subprocess
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Provide a clean temporary directory."""
    return tmp_path


@pytest.fixture
def git_repo(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary git repository with an initial commit."""
    repo_path = tmp_path / "repo"
    repo_path.mkdir()

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=repo_path, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_path,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_path,
        capture_output=True,
        check=True,
    )

    # Create initial file and commit
    (repo_path / "README.md").write_text("# Test Project\n")
    subprocess.run(["git", "add", "."], cwd=repo_path, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_path,
        capture_output=True,
        check=True,
    )

    yield repo_path


@pytest.fixture
def dirty_git_repo(git_repo: Path) -> Path:
    """Create a git repository with uncommitted changes."""
    # Create an unstaged file
    (git_repo / "unstaged.txt").write_text("unstaged content\n")

    return git_repo


@pytest.fixture
def staged_git_repo(git_repo: Path) -> Path:
    """Create a git repository with staged changes."""
    # Create and stage a file
    (git_repo / "staged.txt").write_text("staged content\n")
    subprocess.run(["git", "add", "staged.txt"], cwd=git_repo, capture_output=True, check=True)

    return git_repo


@pytest.fixture
def mixed_git_repo(git_repo: Path) -> Path:
    """Create a git repository with staged, unstaged, and untracked files."""
    # Staged file
    (git_repo / "staged.txt").write_text("staged content\n")
    subprocess.run(["git", "add", "staged.txt"], cwd=git_repo, capture_output=True, check=True)

    # Modify existing tracked file (unstaged)
    (git_repo / "README.md").write_text("# Modified\n")

    # Untracked file
    (git_repo / "untracked.txt").write_text("untracked content\n")

    return git_repo


@pytest.fixture
def paracord_project(tmp_path: Path) -> Path:
    """Create a minimal Paracord project structure."""
    project_path = tmp_path / "test-project"
    project_path.mkdir()

    # Create .copier-answers.yml
    copier_answers = project_path / ".copier-answers.yml"
    copier_answers.write_text(
        """_src_path: gh:paracord-run/dash
_commit: abc12345
project_name: test-project
"""
    )

    # Create rav.yaml
    rav_config = project_path / "rav.yaml"
    rav_config.write_text(
        """scripts:
  dev:
    help: Run development server
    run: echo "dev"
  test:
    help: Run tests
    run: pytest
"""
    )

    return project_path


@pytest.fixture
def paracord_git_project(paracord_project: Path) -> Path:
    """Create a Paracord project that is also a git repository."""
    # Initialize git repo
    subprocess.run(["git", "init"], cwd=paracord_project, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=paracord_project,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=paracord_project,
        capture_output=True,
        check=True,
    )
    subprocess.run(["git", "add", "."], cwd=paracord_project, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=paracord_project,
        capture_output=True,
        check=True,
    )

    return paracord_project
