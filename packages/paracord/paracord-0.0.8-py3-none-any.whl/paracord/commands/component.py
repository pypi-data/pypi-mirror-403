"""paracord component command - Manage optional components."""

from pathlib import Path
from typing import Annotated

import typer
from rich.table import Table

from paracord.core.components import (
    get_applied_components,
    save_applied_component,
    check_component_conflicts,
    check_component_dependencies,
    create_applied_component,
)
from paracord.core.component_installer import install_component
from paracord.core.context import require_project_context
from paracord.core.registry import (
    fetch_registry,
    get_component_source,
    get_component_commit,
    COMPONENT_LIBRARY_REPO,
)
from paracord.utils.console import (
    console,
    print_header,
    print_success,
    print_error,
    print_info,
    print_warning,
    create_spinner,
)
from paracord.utils.git import check_git_status_with_suggestions


component_app = typer.Typer(
    name="component",
    help="Manage optional components for your Paracord project.",
    no_args_is_help=True,
)


@component_app.command(name="list")
def list_components() -> None:
    """List available components from the registry.

    Fetches the component registry and displays all available
    components that can be added to your project.
    """
    print_header("Available Components", "From paracord-run/library")

    with create_spinner("Fetching component registry...") as progress:
        progress.add_task("Fetching...", total=None)
        registry = fetch_registry()

    if not registry:
        print_error("Failed to fetch component registry.")
        print_info("Check your internet connection and try again.")
        raise typer.Exit(1)

    if not registry.components:
        print_info("No components available in the registry.")
        return

    console.print()

    # Create a table of components
    table = Table(border_style="cyan")
    table.add_column("Component", style="command")
    table.add_column("Version", style="dim")
    table.add_column("Description")
    table.add_column("Tags", style="dim")

    for name, component in sorted(registry.components.items()):
        tags = ", ".join(component.tags) if component.tags else "-"
        table.add_row(name, component.version, component.description, tags)

    console.print(table)
    console.print()
    print_info("Run [command]paracord component add <name>[/command] to add a component.")


@component_app.command(name="add")
def add_component(
    component_name: Annotated[
        str,
        typer.Argument(help="Name of the component to add."),
    ],
) -> None:
    """Add a component to the current project.

    Downloads and applies a component from the component library
    to your project. Components are layered on top of your existing
    project files.
    """
    # Ensure we're in a Paracord project
    context = require_project_context()

    print_header("Add Component", f"Adding: {component_name}")

    # Fetch registry to get component info
    with create_spinner("Fetching component info...") as progress:
        progress.add_task("Fetching...", total=None)
        registry = fetch_registry()

    if not registry:
        print_error("Failed to fetch component registry.")
        raise typer.Exit(1)

    if component_name not in registry.components:
        print_error(f"Component '{component_name}' not found in registry.")
        print_info("Run [command]paracord component list[/command] to see available components.")
        raise typer.Exit(1)

    component_info = registry.components[component_name]
    print_info(f"Component: {component_info.description}")
    print_info(f"Version: {component_info.version}")

    # Check if already applied
    applied = get_applied_components(context.path)
    if component_name in applied:
        print_warning(f"Component '{component_name}' is already applied to this project.")
        print_info("Run [command]paracord component update {component_name}[/command] to update it.")
        raise typer.Exit(1)

    # Check for conflicts
    conflicts = check_component_conflicts(context.path, component_info)
    if conflicts:
        print_error(f"Component '{component_name}' conflicts with: {', '.join(conflicts)}")
        print_info("Remove the conflicting components before adding this one.")
        raise typer.Exit(1)

    # Check for missing dependencies
    missing = check_component_dependencies(context.path, component_info)
    if missing:
        print_error(f"Component '{component_name}' requires: {', '.join(missing)}")
        print_info("Add the required components first.")
        raise typer.Exit(1)

    # Check git status
    console.print()
    git_status, suggestions = check_git_status_with_suggestions(
        context.path, "adding component"
    )

    if git_status.is_dirty:
        print_warning("You have uncommitted changes in your repository.")
        console.print()
        for suggestion in suggestions:
            console.print(f"  [dim]•[/dim] {suggestion}")
        console.print()
        if not typer.confirm("Continue with uncommitted changes?", default=False):
            print_info("Cancelled. Commit or stash your changes and try again.")
            raise typer.Exit(0)

    console.print()

    # Confirm before proceeding
    if not typer.confirm(f"Add component '{component_name}'?"):
        print_info("Cancelled.")
        raise typer.Exit(0)

    # Install component files
    with create_spinner("Installing component files...") as progress:
        progress.add_task("Installing...", total=None)
        success, manifest, written_paths = install_component(
            component_name=component_name,
            destination=context.path,
        )

    if not success:
        print_error("Failed to apply component.")
        raise typer.Exit(1)

    console.print()

    # Show installed files
    print_info(f"Installed {len(written_paths)} files:")
    for path in written_paths[:10]:  # Show first 10
        rel_path = path.relative_to(context.path)
        console.print(f"  [dim]•[/dim] {rel_path}")
    if len(written_paths) > 10:
        console.print(f"  [dim]... and {len(written_paths) - 10} more[/dim]")

    # Get commit hash and save applied component
    source = get_component_source(component_name)
    commit = get_component_commit(component_name) or "unknown"
    applied_component = create_applied_component(
        name=component_name,
        version=component_info.version,
        commit=commit,
        source=source,
    )
    save_applied_component(context.path, applied_component)

    console.print()
    print_success(f"Component '{component_name}' added successfully!")

    # Show post-install instructions if any
    if manifest and manifest.post_install:
        console.print()
        print_info("Post-install steps:")
        for step in manifest.post_install:
            console.print(f"  [dim]•[/dim] {step}")

    console.print()
    print_info("Review the changes and commit when ready.")


@component_app.command(name="status")
def status() -> None:
    """Show components applied to the current project.

    Displays all components that have been added to the project
    along with their versions and when they were applied.
    """
    # Ensure we're in a Paracord project
    context = require_project_context()

    print_header("Component Status", f"Project: {context.project_name}")

    applied = get_applied_components(context.path)

    if not applied:
        print_info("No components have been added to this project.")
        print_info("Run [command]paracord component list[/command] to see available components.")
        return

    console.print()

    # Create a table of applied components
    table = Table(border_style="cyan")
    table.add_column("Component", style="command")
    table.add_column("Version", style="dim")
    table.add_column("Commit", style="dim")
    table.add_column("Applied", style="dim")

    for name, component in sorted(applied.items()):
        # Format the timestamp nicely
        applied_at = component.applied_at
        if applied_at.endswith("Z"):
            applied_at = applied_at[:-1].replace("T", " ")[:16]

        table.add_row(
            name,
            component.version,
            component.commit[:8] if len(component.commit) >= 8 else component.commit,
            applied_at,
        )

    console.print(table)


@component_app.command(name="check")
def check_updates() -> None:
    """Check for updates to applied components.

    Compares the versions of applied components against the
    registry to see if updates are available.
    """
    # Ensure we're in a Paracord project
    context = require_project_context()

    print_header("Check Component Updates", f"Project: {context.project_name}")

    applied = get_applied_components(context.path)

    if not applied:
        print_info("No components have been added to this project.")
        return

    # Fetch registry
    with create_spinner("Fetching component registry...") as progress:
        progress.add_task("Fetching...", total=None)
        registry = fetch_registry()

    if not registry:
        print_error("Failed to fetch component registry.")
        raise typer.Exit(1)

    console.print()

    updates_available = False
    for name, applied_component in sorted(applied.items()):
        if name in registry.components:
            registry_component = registry.components[name]
            if registry_component.version != applied_component.version:
                print_warning(
                    f"[command]{name}[/command]: "
                    f"{applied_component.version} -> {registry_component.version}"
                )
                updates_available = True
            else:
                print_success(f"[command]{name}[/command]: up to date ({applied_component.version})")
        else:
            print_warning(f"[command]{name}[/command]: not found in registry (orphaned)")

    console.print()
    if updates_available:
        print_info(
            "Run [command]paracord component update <name>[/command] to update a component."
        )
    else:
        print_success("All components are up to date!")


@component_app.command(name="update")
def update_component(
    component_name: Annotated[
        str,
        typer.Argument(help="Name of the component to update."),
    ],
) -> None:
    """Update a specific component to the latest version.

    Re-applies the component from the component library to pull
    in the latest changes.
    """
    # Ensure we're in a Paracord project
    context = require_project_context()

    print_header("Update Component", f"Updating: {component_name}")

    # Check if component is applied
    applied = get_applied_components(context.path)
    if component_name not in applied:
        print_error(f"Component '{component_name}' is not applied to this project.")
        print_info("Run [command]paracord component status[/command] to see applied components.")
        raise typer.Exit(1)

    applied_component = applied[component_name]
    print_info(f"Current version: {applied_component.version}")

    # Fetch registry
    with create_spinner("Fetching component info...") as progress:
        progress.add_task("Fetching...", total=None)
        registry = fetch_registry()

    if not registry:
        print_error("Failed to fetch component registry.")
        raise typer.Exit(1)

    if component_name not in registry.components:
        print_warning(f"Component '{component_name}' not found in registry.")
        print_info("The component may have been removed. You can still re-apply it from the source.")

    component_info = registry.components.get(component_name)
    if component_info:
        print_info(f"Latest version: {component_info.version}")

    # Check git status
    console.print()
    git_status, suggestions = check_git_status_with_suggestions(
        context.path, "updating component"
    )

    if git_status.is_dirty:
        print_warning("You have uncommitted changes in your repository.")
        console.print()
        for suggestion in suggestions:
            console.print(f"  [dim]•[/dim] {suggestion}")
        console.print()
        if not typer.confirm("Continue with uncommitted changes?", default=False):
            print_info("Cancelled. Commit or stash your changes and try again.")
            raise typer.Exit(0)

    console.print()

    # Confirm before proceeding
    if not typer.confirm(f"Update component '{component_name}'?"):
        print_info("Cancelled.")
        raise typer.Exit(0)

    # Install component files
    with create_spinner("Installing component files...") as progress:
        progress.add_task("Installing...", total=None)
        success, manifest, written_paths = install_component(
            component_name=component_name,
            destination=context.path,
        )

    if not success:
        print_error("Failed to update component.")
        raise typer.Exit(1)

    console.print()

    # Show installed files
    print_info(f"Updated {len(written_paths)} files:")
    for path in written_paths[:10]:  # Show first 10
        rel_path = path.relative_to(context.path)
        console.print(f"  [dim]•[/dim] {rel_path}")
    if len(written_paths) > 10:
        console.print(f"  [dim]... and {len(written_paths) - 10} more[/dim]")

    # Update the applied component record
    source = get_component_source(component_name)
    commit = get_component_commit(component_name) or "unknown"
    version = component_info.version if component_info else applied_component.version
    updated_component = create_applied_component(
        name=component_name,
        version=version,
        commit=commit,
        source=source,
    )
    save_applied_component(context.path, updated_component)

    console.print()
    print_success(f"Component '{component_name}' updated successfully!")

    # Show post-install instructions if any
    if manifest and manifest.post_install:
        console.print()
        print_info("Post-install steps:")
        for step in manifest.post_install:
            console.print(f"  [dim]•[/dim] {step}")

    console.print()
    print_info("Review the changes and commit when ready.")
