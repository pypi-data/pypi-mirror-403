"""Project detection and context for Paracord CLI."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from paracord.utils.config import (
    COPIER_ANSWERS_FILE,
    RAV_CONFIG_FILE,
    get_copier_answers,
    get_rav_config,
    get_template_info,
)


@dataclass
class ProjectContext:
    """Context information for a Paracord project."""

    path: Path
    is_paracord_project: bool
    has_copier_answers: bool
    has_rav_config: bool
    template_source: str | None = None
    template_commit: str | None = None
    project_name: str | None = None
    copier_answers: dict[str, Any] | None = None
    rav_config: dict[str, Any] | None = None


def find_project_root(start_path: Path | None = None) -> Path | None:
    """Find the project root by looking for indicator files.

    Walks up the directory tree from start_path looking for
    .copier-answers.yml or rav.yaml files.

    Args:
        start_path: Starting directory (defaults to cwd)

    Returns:
        Path to project root, or None if not found
    """
    if start_path is None:
        start_path = Path.cwd()

    current = start_path.resolve()

    while current != current.parent:
        if (current / COPIER_ANSWERS_FILE).exists():
            return current
        if (current / RAV_CONFIG_FILE).exists():
            return current
        current = current.parent

    return None


def get_project_context(path: Path | None = None) -> ProjectContext:
    """Get the project context for the given path.

    Args:
        path: Path to check (defaults to cwd)

    Returns:
        ProjectContext with project information
    """
    if path is None:
        path = Path.cwd()

    path = path.resolve()

    # Check for indicator files
    copier_answers_path = path / COPIER_ANSWERS_FILE
    rav_config_path = path / RAV_CONFIG_FILE

    has_copier = copier_answers_path.exists()
    has_rav = rav_config_path.exists()

    # Determine if this is a Paracord project
    is_paracord = has_copier  # Primary indicator

    # Load configuration if available
    copier_answers = get_copier_answers(path) if has_copier else None
    rav_config = get_rav_config(path) if has_rav else None

    # Extract template info
    template_source = None
    template_commit = None
    if copier_answers:
        template_source, template_commit = get_template_info(copier_answers)

    # Try to determine project name
    project_name = path.name
    if copier_answers and "project_name" in copier_answers:
        project_name = copier_answers["project_name"]

    return ProjectContext(
        path=path,
        is_paracord_project=is_paracord,
        has_copier_answers=has_copier,
        has_rav_config=has_rav,
        template_source=template_source,
        template_commit=template_commit,
        project_name=project_name,
        copier_answers=copier_answers,
        rav_config=rav_config,
    )


def require_project_context(path: Path | None = None) -> ProjectContext:
    """Get project context, raising an error if not in a Paracord project.

    Args:
        path: Path to check (defaults to cwd)

    Returns:
        ProjectContext for a valid Paracord project

    Raises:
        SystemExit: If not in a Paracord project
    """
    from paracord.utils.console import print_error

    # First try the given path
    if path:
        context = get_project_context(path)
        if context.is_paracord_project:
            return context

    # Try to find project root
    project_root = find_project_root(path)
    if project_root:
        return get_project_context(project_root)

    print_error("Not in a Paracord project directory.")
    print_error(
        "Run [command]paracord init[/command] to create a new project, "
        "or navigate to an existing Paracord project."
    )
    raise SystemExit(1)
