"""Main Typer application entry point for Paracord CLI."""

import typer

from paracord import __version__, __app_name__
from paracord.commands.bug import bug
from paracord.commands.init import init
from paracord.commands.run import run
from paracord.commands.update import update
from paracord.commands.check import check
from paracord.commands.component import component_app
from paracord.utils.console import console, print_warning
from paracord.utils.version_check import check_for_updates


app = typer.Typer(
    name=__app_name__,
    help="A modern CLI tool for Paracord projects.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"{__app_name__} version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version", "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """Paracord CLI - A unified developer experience for Paracord projects.

    Wraps copier, uv, and rav into a single, modern CLI tool.
    """
    latest = check_for_updates()
    if latest:
        print_warning(
            f"A new version of paracord is available: {latest} (current: {__version__})\n"
            f"  Update with: [command]uv tool upgrade paracord[/command]"
        )


# Register commands
app.command(name="bug", help="Report a bug to GitHub.")(bug)
app.command(name="init", help="Create a new Paracord project from the template.")(init)
app.command(name="run", help="Run a rav task in the current project.")(run)
app.command(name="update", help="Update the project from the upstream template.")(update)
app.command(name="check", help="Check for template updates without applying them.")(check)

# Register component command group with alias
app.add_typer(component_app, name="component")
app.add_typer(component_app, name="comp", hidden=True)  # shorthand alias


if __name__ == "__main__":
    app()
