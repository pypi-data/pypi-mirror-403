"""Configuration file handling for Paracord CLI."""

from pathlib import Path
from typing import Any

import yaml


COPIER_ANSWERS_FILE = ".copier-answers.yml"
RAV_CONFIG_FILE = "rav.yaml"
PARACORD_COMPONENTS_FILE = ".paracord-components.yml"


def load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file and return its contents."""
    if not path.exists():
        return {}

    with open(path, "r") as f:
        return yaml.safe_load(f) or {}


def save_yaml(path: Path, data: dict[str, Any]) -> None:
    """Save data to a YAML file."""
    with open(path, "w") as f:
        yaml.safe_dump(data, f, default_flow_style=False)


def get_copier_answers(project_path: Path) -> dict[str, Any]:
    """Get copier answers from a project directory."""
    answers_path = project_path / COPIER_ANSWERS_FILE
    return load_yaml(answers_path)


def get_rav_config(project_path: Path) -> dict[str, Any]:
    """Get rav configuration from a project directory."""
    rav_path = project_path / RAV_CONFIG_FILE
    return load_yaml(rav_path)


def get_template_info(copier_answers: dict[str, Any]) -> tuple[str | None, str | None]:
    """Extract template source and commit from copier answers.

    Returns:
        Tuple of (template_source, commit_hash)
    """
    template = copier_answers.get("_src_path")
    commit = copier_answers.get("_commit")
    return template, commit
