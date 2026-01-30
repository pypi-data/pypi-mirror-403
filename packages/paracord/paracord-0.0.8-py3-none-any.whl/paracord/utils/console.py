"""Rich console configuration for Paracord CLI."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.theme import Theme

# Custom theme for Paracord CLI
paracord_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "command": "bold magenta",
    "path": "blue underline",
})

# Global console instance
console = Console(theme=paracord_theme)
err_console = Console(stderr=True, theme=paracord_theme)


def print_header(title: str, subtitle: str | None = None) -> None:
    """Print a styled header panel."""
    content = f"[bold]{title}[/bold]"
    if subtitle:
        content += f"\n[dim]{subtitle}[/dim]"
    console.print(Panel(content, border_style="cyan"))


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[success]✓[/success] {message}")


def print_error(message: str) -> None:
    """Print an error message."""
    err_console.print(f"[error]✗[/error] {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[warning]![/warning] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[info]→[/info] {message}")


def create_spinner(message: str) -> Progress:
    """Create a spinner progress context."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    )


def print_task_table(tasks: dict[str, str]) -> None:
    """Print a table of available tasks."""
    table = Table(title="Available Tasks", border_style="cyan")
    table.add_column("Task", style="command")
    table.add_column("Description", style="dim")

    for name, description in tasks.items():
        table.add_row(name, description)

    console.print(table)


def print_diff(content: str, language: str = "diff") -> None:
    """Print syntax-highlighted diff content."""
    syntax = Syntax(content, language, theme="monokai", line_numbers=True)
    console.print(syntax)


def print_next_steps(steps: list[str]) -> None:
    """Print next steps after an operation."""
    console.print("\n[bold]Next steps:[/bold]")
    for i, step in enumerate(steps, 1):
        console.print(f"  {i}. {step}")
    console.print()
