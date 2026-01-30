"""Copier wrapper utilities for Paracord CLI."""

import subprocess
from pathlib import Path

from paracord.utils.console import console, print_error, print_info, create_spinner


PARACORD_TEMPLATE = "gh:paracord-run/dash"


def run_copier_copy(
    template: str = PARACORD_TEMPLATE,
    destination: Path | None = None,
    project_name: str | None = None,
) -> bool:
    """Run copier copy to create a new project.

    Args:
        template: Template source (defaults to paracord-run/dash)
        destination: Destination directory
        project_name: Name for the new project

    Returns:
        True if successful, False otherwise
    """
    cmd = ["copier", "copy", template]

    if destination:
        cmd.append(str(destination))
    elif project_name:
        cmd.append(project_name)
    else:
        cmd.append(".")

    print_info(f"Running: [command]{' '.join(cmd)}[/command]")

    try:
        # Run copier interactively (it needs user input for prompts)
        result = subprocess.run(cmd, check=False)
        return result.returncode == 0
    except FileNotFoundError:
        print_error("Copier is not installed. Install it with: [command]uv pip install copier[/command]")
        return False
    except Exception as e:
        print_error(f"Failed to run copier: {e}")
        return False


def run_copier_update(
    project_path: Path,
    skip_answered: bool = True,
    conflict: str = "inline",
) -> bool:
    """Run copier update to update an existing project.

    Args:
        project_path: Path to the project to update
        skip_answered: Skip questions that have already been answered
        conflict: How to handle conflicts (inline, ours, theirs)

    Returns:
        True if successful, False otherwise
    """
    cmd = ["copier", "update"]

    if skip_answered:
        cmd.append("--skip-answered")

    cmd.extend(["--conflict", conflict])

    print_info(f"Running: [command]{' '.join(cmd)}[/command]")

    try:
        result = subprocess.run(cmd, cwd=project_path, check=False)
        return result.returncode == 0
    except FileNotFoundError:
        print_error("Copier is not installed. Install it with: [command]uv pip install copier[/command]")
        return False
    except Exception as e:
        print_error(f"Failed to run copier update: {e}")
        return False


def get_template_version(template: str = PARACORD_TEMPLATE) -> str | None:
    """Get the latest version/commit of the template.

    Args:
        template: Template source

    Returns:
        Version string or None if unable to determine
    """
    # For GitHub templates, we can use git ls-remote
    if template.startswith("gh:"):
        repo = template[3:]  # Remove "gh:" prefix
        try:
            result = subprocess.run(
                ["git", "ls-remote", f"https://github.com/{repo}.git", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            # Output format: "<commit>\tHEAD"
            if result.stdout:
                return result.stdout.split()[0][:8]  # Return short hash
        except Exception:
            pass

    return None


def check_for_updates(current_commit: str | None, template: str = PARACORD_TEMPLATE) -> tuple[bool, str | None]:
    """Check if updates are available for the template.

    Args:
        current_commit: Current template commit
        template: Template source

    Returns:
        Tuple of (updates_available, latest_version)
    """
    latest = get_template_version(template)

    if not latest or not current_commit:
        return False, latest

    # Compare commits (simple string comparison for now)
    updates_available = latest != current_commit[:8] if current_commit else True

    return updates_available, latest
