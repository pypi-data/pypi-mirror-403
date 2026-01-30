"""Remote component registry fetching for Paracord CLI."""

import base64
import json
import subprocess
from dataclasses import dataclass, field
from typing import Any

import yaml

from paracord.core.components import ComponentInfo


COMPONENT_LIBRARY_REPO = "gh:paracord-run/library"
COMPONENT_LIBRARY_OWNER = "paracord-run"
COMPONENT_LIBRARY_NAME = "library"


@dataclass
class ComponentRegistry:
    """Registry of available components."""

    version: str
    components: dict[str, ComponentInfo] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ComponentRegistry":
        """Create a ComponentRegistry from a dictionary."""
        components = {}
        for name, component_data in data.get("components", {}).items():
            components[name] = ComponentInfo(
                name=name,
                description=component_data.get("description", ""),
                version=component_data.get("version", "1.0.0"),
                tags=component_data.get("tags", []),
                requires=component_data.get("requires", []),
                conflicts=component_data.get("conflicts", []),
            )

        return cls(
            version=data.get("version", "1.0"),
            components=components,
        )


def fetch_registry() -> ComponentRegistry | None:
    """Fetch registry.yaml from the component-library repo.

    Uses gh CLI to fetch from GitHub API, which works with private repos.

    Returns:
        ComponentRegistry if successful, None otherwise
    """
    try:
        # Use gh api to fetch the registry file (works with private repos)
        result = subprocess.run(
            [
                "gh", "api",
                f"repos/{COMPONENT_LIBRARY_OWNER}/{COMPONENT_LIBRARY_NAME}/contents/registry.yaml",
                "--jq", ".content",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )

        # GitHub API returns base64-encoded content
        content = base64.b64decode(result.stdout.strip()).decode("utf-8")
        data = yaml.safe_load(content)
        if data:
            return ComponentRegistry.from_dict(data)

    except subprocess.TimeoutExpired:
        pass
    except subprocess.CalledProcessError:
        pass
    except yaml.YAMLError:
        pass
    except Exception:
        pass

    return None


def get_component_source(component_name: str) -> str:
    """Resolve a component name to its copier template path.

    Args:
        component_name: Name of the component

    Returns:
        Full copier source path for the component
    """
    return f"{COMPONENT_LIBRARY_REPO}/{component_name}"


def get_component_commit(component_name: str) -> str | None:
    """Get the latest commit hash for a component.

    Uses gh CLI to fetch from GitHub API, which works with private repos.

    Args:
        component_name: Name of the component

    Returns:
        Short commit hash or None if unable to determine
    """
    try:
        # Use gh api to get the latest commit (works with private repos)
        result = subprocess.run(
            [
                "gh", "api",
                f"repos/{COMPONENT_LIBRARY_OWNER}/{COMPONENT_LIBRARY_NAME}/commits/main",
                "--jq", ".sha",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )

        if result.stdout:
            return result.stdout.strip()[:8]  # Return short hash

    except Exception:
        pass

    return None
