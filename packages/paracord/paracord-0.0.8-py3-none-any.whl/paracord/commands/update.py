"""paracord update command - Update project from template."""

from typing import Annotated

import typer

from paracord.core.context import require_project_context
from paracord.core.copier import run_copier_update
from paracord.utils.console import (
    console,
    print_header,
    print_success,
    print_error,
    print_info,
    print_warning,
)
from paracord.utils.git import check_git_status_with_suggestions


def update(
    skip_answered: Annotated[
        bool,
        typer.Option(
            "--skip-answered/--no-skip-answered",
            help="Skip questions that have already been answered.",
        ),
    ] = True,
    conflict: Annotated[
        str,
        typer.Option(
            "--conflict", "-c",
            help="How to handle conflicts: inline, ours, theirs.",
        ),
    ] = "inline",
) -> None:
    """Update the current project from the upstream template.

    This runs 'copier update' to pull in changes from the paracord-run/dash
    template. Your answers to previous questions are preserved by default.

    Conflicts are marked inline by default, allowing you to review and
    resolve them manually.
    """
    # Ensure we're in a Paracord project
    context = require_project_context()

    print_header("Paracord Update", f"Updating: {context.project_name}")

    # Show current template info
    if context.template_source:
        print_info(f"Template: [path]{context.template_source}[/path]")
    if context.template_commit:
        print_info(f"Current version: [dim]{context.template_commit[:8]}[/dim]")

    # Check git status and provide suggestions
    console.print()
    git_status, suggestions = check_git_status_with_suggestions(
        context.path, "updating from template"
    )

    if not git_status.is_git_repo:
        print_warning(
            "This directory is not a git repository. It's strongly recommended "
            "to initialize git before updating to track changes."
        )
        console.print()
        console.print("  [dim]To initialize git:[/dim]")
        console.print("    [command]git init && git add . && git commit -m 'Initial commit'[/command]")
        console.print()
        if not typer.confirm("Continue without git?", default=False):
            print_info("Update cancelled. Initialize git and try again.")
            raise typer.Exit(0)
    elif git_status.is_dirty:
        print_warning("You have uncommitted changes in your repository.")
        console.print()
        for suggestion in suggestions:
            console.print(f"  [dim]•[/dim] {suggestion}")
        console.print()
        if not typer.confirm("Continue with uncommitted changes?", default=False):
            print_info("Update cancelled. Commit or stash your changes and try again.")
            raise typer.Exit(0)

    console.print()
    print_warning(
        "This will update your project from the upstream template. "
        "Make sure to review changes and resolve any conflicts."
    )
    console.print()

    # Confirm before proceeding
    if not typer.confirm("Proceed with update?"):
        print_info("Update cancelled.")
        raise typer.Exit(0)

    console.print()

    # Run copier update
    success = run_copier_update(
        project_path=context.path,
        skip_answered=skip_answered,
        conflict=conflict,
    )

    if success:
        console.print()
        print_success("Project updated successfully!")
        print_info(
            "Review any conflict markers in your files and commit the changes."
        )
    else:
        print_error("Update failed. Check the output above for details.")
        raise typer.Exit(1)
