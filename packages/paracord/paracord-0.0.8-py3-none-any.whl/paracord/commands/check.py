"""paracord check command - Check for template updates."""

import typer

from paracord.core.context import require_project_context
from paracord.core.copier import check_for_updates, PARACORD_TEMPLATE
from paracord.utils.console import (
    console,
    print_header,
    print_success,
    print_info,
    print_warning,
    create_spinner,
)


def check() -> None:
    """Check for template updates without applying them.

    Compares your project's template version against the latest
    available version and shows if updates are available.
    """
    # Ensure we're in a Paracord project
    context = require_project_context()

    print_header("Paracord Check", f"Project: {context.project_name}")

    # Show current template info
    if context.template_source:
        print_info(f"Template: [path]{context.template_source}[/path]")
    else:
        print_info(f"Template: [path]{PARACORD_TEMPLATE}[/path]")

    if context.template_commit:
        print_info(f"Current version: [dim]{context.template_commit[:8]}[/dim]")
    else:
        print_warning("Could not determine current template version.")
        print_info("Run [command]paracord update[/command] to sync with the latest template.")
        return

    console.print()

    # Check for updates
    with create_spinner("Checking for updates...") as progress:
        progress.add_task("Checking...", total=None)
        template = context.template_source or PARACORD_TEMPLATE
        updates_available, latest_version = check_for_updates(
            context.template_commit,
            template,
        )

    if updates_available:
        console.print()
        print_warning("Updates available!")
        if latest_version:
            print_info(f"Latest version: [dim]{latest_version}[/dim]")
        console.print()
        print_info("Run [command]paracord update[/command] to apply updates.")
    else:
        console.print()
        print_success("Your project is up to date!")
