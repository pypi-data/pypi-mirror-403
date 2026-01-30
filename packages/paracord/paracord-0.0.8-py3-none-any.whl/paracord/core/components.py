"""Component tracking and lifecycle management for Paracord CLI."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from paracord.utils.config import (
    PARACORD_COMPONENTS_FILE,
    load_yaml,
    save_yaml,
)


@dataclass
class ComponentInfo:
    """Metadata about an available component."""

    name: str
    description: str
    version: str
    tags: list[str] = field(default_factory=list)
    requires: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)


@dataclass
class AppliedComponent:
    """Information about a component applied to a project."""

    name: str
    version: str
    commit: str
    source: str
    applied_at: str

    @classmethod
    def from_dict(cls, name: str, data: dict[str, Any]) -> "AppliedComponent":
        """Create an AppliedComponent from a dictionary."""
        return cls(
            name=name,
            version=data.get("version", "unknown"),
            commit=data.get("commit", "unknown"),
            source=data.get("source", "unknown"),
            applied_at=data.get("applied_at", "unknown"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to a dictionary for YAML serialization."""
        return {
            "version": self.version,
            "commit": self.commit,
            "source": self.source,
            "applied_at": self.applied_at,
        }


def get_applied_components(project_path: Path) -> dict[str, AppliedComponent]:
    """Read applied components from .paracord-components.yml.

    Args:
        project_path: Path to the project directory

    Returns:
        Dictionary mapping component name to AppliedComponent
    """
    components_file = project_path / PARACORD_COMPONENTS_FILE
    data = load_yaml(components_file)

    components = {}
    for name, component_data in data.get("components", {}).items():
        components[name] = AppliedComponent.from_dict(name, component_data)

    return components


def save_applied_component(
    project_path: Path,
    component: AppliedComponent,
) -> None:
    """Record an applied component to .paracord-components.yml.

    Args:
        project_path: Path to the project directory
        component: The component that was applied
    """
    components_file = project_path / PARACORD_COMPONENTS_FILE
    data = load_yaml(components_file)

    if "components" not in data:
        data["components"] = {}

    data["components"][component.name] = component.to_dict()
    save_yaml(components_file, data)


def remove_applied_component(
    project_path: Path,
    component_name: str,
) -> bool:
    """Remove a component from .paracord-components.yml.

    Args:
        project_path: Path to the project directory
        component_name: Name of the component to remove

    Returns:
        True if component was removed, False if it wasn't found
    """
    components_file = project_path / PARACORD_COMPONENTS_FILE
    data = load_yaml(components_file)

    if "components" not in data or component_name not in data["components"]:
        return False

    del data["components"][component_name]
    save_yaml(components_file, data)
    return True


def check_component_conflicts(
    project_path: Path,
    component_info: ComponentInfo,
) -> list[str]:
    """Check if a component conflicts with already applied components.

    Args:
        project_path: Path to the project directory
        component_info: Information about the component to check

    Returns:
        List of conflicting component names
    """
    applied = get_applied_components(project_path)
    conflicts = []

    for conflict_name in component_info.conflicts:
        if conflict_name in applied:
            conflicts.append(conflict_name)

    return conflicts


def check_component_dependencies(
    project_path: Path,
    component_info: ComponentInfo,
) -> list[str]:
    """Check if required components exist for a component.

    Args:
        project_path: Path to the project directory
        component_info: Information about the component to check

    Returns:
        List of missing required component names
    """
    applied = get_applied_components(project_path)
    missing = []

    for required_name in component_info.requires:
        if required_name not in applied:
            missing.append(required_name)

    return missing


def create_applied_component(
    name: str,
    version: str,
    commit: str,
    source: str,
) -> AppliedComponent:
    """Create a new AppliedComponent with current timestamp.

    Args:
        name: Component name
        version: Component version
        commit: Git commit hash
        source: Component source path

    Returns:
        New AppliedComponent instance
    """
    return AppliedComponent(
        name=name,
        version=version,
        commit=commit,
        source=source,
        applied_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )
