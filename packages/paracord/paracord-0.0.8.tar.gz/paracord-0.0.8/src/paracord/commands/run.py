"""paracord run command - Run rav tasks."""

from typing import Annotated, Optional

import typer

from paracord.core.context import require_project_context
from paracord.core.rav import get_available_tasks, run_task, list_tasks
from paracord.utils.console import (
    print_header,
    print_success,
    print_error,
    print_info,
    print_task_table,
)


def run(
    task: Annotated[
        Optional[str],
        typer.Argument(
            help="Name of the task to run. If omitted, lists available tasks.",
        ),
    ] = None,
) -> None:
    """Run a rav task in the current project.

    If no task is specified, lists all available tasks from rav.yaml.
    Tasks are executed using 'uv run rav run <task>'.
    """
    # Ensure we're in a Paracord project
    context = require_project_context()

    if not context.has_rav_config:
        print_error("No rav.yaml found in this project.")
        print_info("This project may not have any configured tasks.")
        raise typer.Exit(1)

    if task is None:
        # List available tasks
        print_header("Available Tasks", f"Project: {context.project_name}")

        tasks = get_available_tasks(context.path)
        if tasks:
            print_task_table(tasks)
        else:
            # Fall back to rav's own listing
            list_tasks(context.path)

        print_info("Run a task with: [command]paracord run <task>[/command]")
    else:
        # Run the specified task
        print_header(f"Running: {task}", f"Project: {context.project_name}")

        success = run_task(context.path, task)

        if success:
            print_success(f"Task '{task}' completed successfully.")
        else:
            print_error(f"Task '{task}' failed.")
            raise typer.Exit(1)
