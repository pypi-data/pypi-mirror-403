"""paracord init command - Create a new Paracord project."""

from pathlib import Path
from typing import Annotated, Optional

import typer

from paracord.core.copier import run_copier_copy, PARACORD_TEMPLATE
from paracord.core.github import register_project_sync
from paracord.utils.console import (
    console,
    print_header,
    print_success,
    print_error,
    print_info,
    print_warning,
    print_next_steps,
)
from paracord.utils.git import get_git_status


def init(
    project_name: Annotated[
        Optional[str],
        typer.Argument(
            help="Name of the project to create. Creates a new directory with this name.",
        ),
    ] = None,
    template: Annotated[
        str,
        typer.Option(
            "--template", "-t",
            help="Template to use for the project.",
        ),
    ] = PARACORD_TEMPLATE,
) -> None:
    """Create a new Paracord project from the template.

    This command runs copier to create a new project from the
    paracord-run/dash template. You'll be prompted for project
    configuration options interactively.
    """
    print_header("Paracord Init", "Creating a new Paracord project")

    # Determine destination
    if project_name:
        destination = Path.cwd() / project_name
        if destination.exists():
            print_error(f"Directory '{project_name}' already exists.")
            raise typer.Exit(1)
        print_info(f"Creating project in: [path]{destination}[/path]")
    else:
        destination = None
        print_info("Creating project in current directory")

    # Check git status for current directory initialization
    if destination is None:
        git_status = get_git_status(Path.cwd())

        if not git_status.is_git_repo:
            console.print()
            print_warning(
                "This directory is not a git repository. Consider initializing "
                "git after project creation to track your changes."
            )
        elif git_status.is_dirty:
            console.print()
            print_warning("You have uncommitted changes in this repository.")
            if git_status.has_staged:
                console.print("  [dim]•[/dim] You have staged changes")
            if git_status.has_unstaged:
                console.print("  [dim]•[/dim] You have unstaged changes")
            if git_status.has_untracked:
                console.print("  [dim]•[/dim] You have untracked files")
            console.print()
            console.print(
                "  [dim]The template will add new files to your working directory.[/dim]"
            )
            console.print()
            if not typer.confirm("Continue with uncommitted changes?", default=True):
                print_info("Init cancelled. Commit or stash your changes and try again.")
                raise typer.Exit(0)

    # Run copier
    console.print()
    success = run_copier_copy(
        template=template,
        project_name=project_name,
    )

    if not success:
        print_error("Failed to create project.")
        raise typer.Exit(1)

    # Attempt community registration (non-blocking)
    console.print()
    print_info("Registering with Paracord community...")
    register_project_sync(project_name)

    # Success message
    console.print()
    print_success("Project created successfully!")

    # Next steps - check if we need to suggest git init
    if project_name:
        # New directory was created, check if it has git
        project_path = Path.cwd() / project_name
        suggest_git_init = not get_git_status(project_path).is_git_repo
    else:
        # Used current directory, git_status was already checked above
        suggest_git_init = not git_status.is_git_repo

    steps = []
    if project_name:
        steps.append(f"cd {project_name}")
    if suggest_git_init:
        steps.append("git init && git add . && git commit -m 'Initial commit'")
    steps.extend([
        "uv sync",
        "paracord run  # to see available tasks",
    ])
    print_next_steps(steps)
