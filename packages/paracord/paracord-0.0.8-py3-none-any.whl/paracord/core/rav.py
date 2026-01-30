"""Rav task discovery and execution for Paracord CLI."""

import subprocess
from pathlib import Path

from paracord.utils.config import get_rav_config
from paracord.utils.console import print_error, print_info


def get_available_tasks(project_path: Path) -> dict[str, str]:
    """Get available rav tasks from rav.yaml.

    Args:
        project_path: Path to the project

    Returns:
        Dictionary of task_name -> description
    """
    rav_config = get_rav_config(project_path)

    if not rav_config:
        return {}

    tasks = {}

    # Rav config structure: scripts section contains the tasks
    scripts = rav_config.get("scripts", {})

    for name, value in scripts.items():
        if isinstance(value, str):
            # Simple command
            tasks[name] = value[:50] + "..." if len(value) > 50 else value
        elif isinstance(value, dict):
            # Task with metadata
            description = value.get("help", value.get("run", ""))
            if isinstance(description, str):
                tasks[name] = description[:50] + "..." if len(description) > 50 else description
            else:
                tasks[name] = ""

    return tasks


def run_task(project_path: Path, task_name: str) -> bool:
    """Run a rav task using uv.

    Args:
        project_path: Path to the project
        task_name: Name of the task to run

    Returns:
        True if successful, False otherwise
    """
    cmd = ["uv", "run", "rav", "run", task_name]

    print_info(f"Running: [command]{' '.join(cmd)}[/command]")

    try:
        result = subprocess.run(cmd, cwd=project_path, check=False)
        return result.returncode == 0
    except FileNotFoundError:
        print_error("uv or rav is not installed.")
        print_error("Install uv: [command]curl -LsSf https://astral.sh/uv/install.sh | sh[/command]")
        return False
    except Exception as e:
        print_error(f"Failed to run task: {e}")
        return False


def list_tasks(project_path: Path) -> bool:
    """List available rav tasks using rav directly.

    Args:
        project_path: Path to the project

    Returns:
        True if successful, False otherwise
    """
    cmd = ["uv", "run", "rav"]

    try:
        result = subprocess.run(cmd, cwd=project_path, check=False)
        return result.returncode == 0
    except FileNotFoundError:
        print_error("uv or rav is not installed.")
        return False
    except Exception as e:
        print_error(f"Failed to list tasks: {e}")
        return False
