"""Project registry for console - manages registered projects in ~/.paracord/config."""

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from paracord.auth.config import (
    get_config,
    save_config,
    ProjectInfo,
    CloudflareConfig,
)


def _normalize_path(path: str | Path) -> str:
    """Normalize a path to its true filesystem case.

    On case-insensitive filesystems (macOS), Path.resolve() preserves the
    input case rather than returning the actual filesystem case. This can
    cause duplicate entries when the same path is accessed with different
    casing.

    Args:
        path: Path to normalize

    Returns:
        Canonical path string with true filesystem case
    """
    resolved = Path(path).resolve()

    # On macOS, get the true case by walking through path components
    if sys.platform == "darwin":
        parts = resolved.parts
        true_path = Path(parts[0])  # Root "/"

        for part in parts[1:]:
            # Check if this component exists in the parent directory
            try:
                entries = os.listdir(true_path)
                # Find the entry with matching case-insensitive name
                for entry in entries:
                    if entry.lower() == part.lower():
                        true_path = true_path / entry
                        break
                else:
                    # Component not found, use original
                    true_path = true_path / part
            except OSError:
                # Can't list directory, use original
                true_path = true_path / part

        return str(true_path)

    return str(resolved)


def register_project(
    path: str | Path,
    name: str,
    port: int,
    postgres_port: int | None = None,
    redis_port: int | None = None,
    template_source: str | None = None,
    cloudflare_subdomain: str | None = None,
) -> ProjectInfo:
    """Register a project with the console.

    Args:
        path: Path to the project directory
        name: Display name for the project
        port: Port the project runs on (Django port)
        postgres_port: Postgres port for the project
        redis_port: Redis port for the project
        template_source: Template source (e.g., "gh:paracord-run/dash")
        cloudflare_subdomain: Subdomain for Cloudflare tunnel

    Returns:
        The created ProjectInfo
    """
    config = get_config()

    if "projects" not in config:
        config["projects"] = {}

    path_str = _normalize_path(path)

    # Clean up any case-variant duplicates on macOS
    if sys.platform == "darwin":
        path_lower = path_str.lower()
        keys_to_remove = [
            key for key in config["projects"]
            if key.lower() == path_lower and key != path_str
        ]
        for key in keys_to_remove:
            del config["projects"][key]

    project: ProjectInfo = {
        "name": name,
        "port": port,
        "registered_at": datetime.now(timezone.utc).isoformat(),
    }

    if postgres_port is not None:
        project["postgres_port"] = postgres_port

    if redis_port is not None:
        project["redis_port"] = redis_port

    if template_source:
        project["template_source"] = template_source

    if cloudflare_subdomain:
        project["cloudflare"] = {"subdomain": cloudflare_subdomain}

    config["projects"][path_str] = project
    save_config(config)

    return project


def _find_project_key(config: dict, path_str: str) -> str | None:
    """Find the actual key for a project in the registry.

    Handles case-insensitive matching on macOS for legacy entries.

    Args:
        config: The config dict
        path_str: Normalized path string to search for

    Returns:
        The actual key in the registry, or None if not found
    """
    projects = config.get("projects", {})

    # Try exact match first
    if path_str in projects:
        return path_str

    # On macOS, try case-insensitive match for legacy entries
    if sys.platform == "darwin":
        path_lower = path_str.lower()
        for key in projects:
            if key.lower() == path_lower:
                return key

    return None


def get_project(path: str | Path) -> ProjectInfo | None:
    """Get a project by its path.

    Args:
        path: Path to the project directory

    Returns:
        ProjectInfo if found, None otherwise
    """
    config = get_config()
    path_str = _normalize_path(path)
    key = _find_project_key(config, path_str)
    if key:
        return config["projects"][key]
    return None


def list_projects() -> dict[str, ProjectInfo]:
    """List all registered projects.

    Returns:
        Dict mapping path -> ProjectInfo
    """
    config = get_config()
    return config.get("projects", {})


def remove_project(path: str | Path) -> bool:
    """Remove a project from the registry.

    Args:
        path: Path to the project directory

    Returns:
        True if project was removed, False if it wasn't registered
    """
    config = get_config()
    path_str = _normalize_path(path)
    key = _find_project_key(config, path_str)

    if key:
        del config["projects"][key]
        save_config(config)
        return True

    return False


def update_project(
    path: str | Path,
    name: str | None = None,
    port: int | None = None,
    postgres_port: int | None = None,
    redis_port: int | None = None,
    cloudflare_subdomain: str | None = None,
) -> ProjectInfo | None:
    """Update a project's configuration.

    Args:
        path: Path to the project directory
        name: New display name (optional)
        port: New Django port (optional)
        postgres_port: New Postgres port (optional)
        redis_port: New Redis port (optional)
        cloudflare_subdomain: New Cloudflare subdomain (optional)

    Returns:
        Updated ProjectInfo if found, None otherwise
    """
    config = get_config()
    path_str = _normalize_path(path)
    key = _find_project_key(config, path_str)

    if not key:
        return None

    project = config["projects"][key]

    if name is not None:
        project["name"] = name

    if port is not None:
        project["port"] = port

    if postgres_port is not None:
        project["postgres_port"] = postgres_port

    if redis_port is not None:
        project["redis_port"] = redis_port

    if cloudflare_subdomain is not None:
        if "cloudflare" not in project:
            project["cloudflare"] = {}
        project["cloudflare"]["subdomain"] = cloudflare_subdomain

    # If the key has wrong case, migrate to correct case
    if key != path_str:
        del config["projects"][key]
        config["projects"][path_str] = project
    else:
        config["projects"][path_str] = project

    save_config(config)

    return project


def is_project_registered(path: str | Path) -> bool:
    """Check if a path is registered as a project.

    Args:
        path: Path to check

    Returns:
        True if registered, False otherwise
    """
    return get_project(path) is not None
