"""Component installer for Paracord CLI.

Installs components from the paracord-run/library repo using gh api.
"""

import base64
import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

import yaml

from paracord.core.registry import COMPONENT_LIBRARY_OWNER, COMPONENT_LIBRARY_NAME


# Paths that should be copied (component mirrors project structure)
# Files under these prefixes are copied as-is
ALLOWED_PATHS = [
    "backend/src/",
    "frontend/src/",
]


@dataclass
class ComponentFile:
    """A file from a component."""

    path: str  # Path within component (e.g., "backend/cloud_storage/apps.py")
    content: bytes
    dest_path: str  # Destination path in project


@dataclass
class ComponentManifest:
    """Parsed component.yaml manifest."""

    name: str
    version: str
    description: str
    requires: list[str]
    backend_dependencies: list[str]
    frontend_dependencies: dict[str, str]
    post_install: list[str]

    @classmethod
    def from_dict(cls, data: dict) -> "ComponentManifest":
        """Create a ComponentManifest from a dictionary."""
        backend = data.get("backend", {})
        frontend = data.get("frontend", {})

        return cls(
            name=data.get("name", ""),
            version=data.get("version", "0.0.0"),
            description=data.get("description", ""),
            requires=data.get("requires", []),
            backend_dependencies=backend.get("dependencies", []),
            frontend_dependencies=frontend.get("dependencies", {}),
            post_install=data.get("post_install", []),
        )


def _gh_api(endpoint: str) -> dict | list | None:
    """Make a GitHub API request using gh cli.

    Args:
        endpoint: API endpoint (without /repos/ prefix)

    Returns:
        Parsed JSON response or None on error
    """
    try:
        result = subprocess.run(
            ["gh", "api", endpoint],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )
        return json.loads(result.stdout)
    except Exception:
        return None


def _get_file_content(path: str) -> bytes | None:
    """Fetch file content from the library repo.

    Args:
        path: File path within the repo

    Returns:
        File content as bytes or None on error
    """
    endpoint = f"repos/{COMPONENT_LIBRARY_OWNER}/{COMPONENT_LIBRARY_NAME}/contents/{path}"
    data = _gh_api(endpoint)

    if data and isinstance(data, dict) and "content" in data:
        # GitHub API returns base64-encoded content
        return base64.b64decode(data["content"])

    return None


def _list_directory(path: str) -> list[dict] | None:
    """List files in a directory in the library repo.

    Args:
        path: Directory path within the repo

    Returns:
        List of file/directory info dicts or None on error
    """
    endpoint = f"repos/{COMPONENT_LIBRARY_OWNER}/{COMPONENT_LIBRARY_NAME}/contents/{path}"
    data = _gh_api(endpoint)

    if data and isinstance(data, list):
        return data

    return None


def _map_destination_path(component_path: str) -> str | None:
    """Map a component file path to a destination path.

    Components mirror the project structure, so paths are copied as-is
    if they match an allowed prefix.

    Args:
        component_path: Path within the component (e.g., "backend/src/cloud_storage/apps.py")

    Returns:
        Destination path in project or None if file should be skipped
    """
    for allowed_prefix in ALLOWED_PATHS:
        if component_path.startswith(allowed_prefix):
            return component_path  # Identity mapping

    # Skip files that don't match any allowed path (like component.yaml, README.md)
    return None


def _collect_files_recursive(base_path: str, current_path: str = "") -> list[tuple[str, str]]:
    """Recursively collect all files from a directory.

    Args:
        base_path: Base path in the repo (e.g., "components/cloud_storage")
        current_path: Current subdirectory being processed

    Returns:
        List of (full_repo_path, relative_component_path) tuples
    """
    files = []
    full_path = f"{base_path}/{current_path}".rstrip("/")
    contents = _list_directory(full_path)

    if not contents:
        return files

    for item in contents:
        item_name = item.get("name", "")
        item_type = item.get("type", "")
        item_path = f"{current_path}/{item_name}".lstrip("/")

        if item_type == "file":
            files.append((f"{base_path}/{item_path}", item_path))
        elif item_type == "dir":
            files.extend(_collect_files_recursive(base_path, item_path))

    return files


def fetch_component_manifest(component_name: str) -> ComponentManifest | None:
    """Fetch and parse a component's manifest.

    Args:
        component_name: Name of the component

    Returns:
        ComponentManifest or None on error
    """
    path = f"components/{component_name}/component.yaml"
    content = _get_file_content(path)

    if content:
        try:
            data = yaml.safe_load(content.decode("utf-8"))
            return ComponentManifest.from_dict(data)
        except Exception:
            pass

    return None


def fetch_component_files(component_name: str) -> list[ComponentFile]:
    """Fetch all files for a component.

    Args:
        component_name: Name of the component

    Returns:
        List of ComponentFile objects
    """
    base_path = f"components/{component_name}"
    all_files = _collect_files_recursive(base_path)
    component_files = []

    for repo_path, component_path in all_files:
        # Skip metadata files
        if component_path in ("component.yaml", "README.md"):
            continue

        # Map to destination path
        dest_path = _map_destination_path(component_path)
        if not dest_path:
            continue

        # Fetch content (use `is not None` to allow empty files like __init__.py)
        content = _get_file_content(repo_path)
        if content is not None:
            component_files.append(
                ComponentFile(
                    path=component_path,
                    content=content,
                    dest_path=dest_path,
                )
            )

    return component_files


def install_component_files(
    files: list[ComponentFile],
    destination: Path,
    dry_run: bool = False,
) -> list[Path]:
    """Install component files to a destination directory.

    Args:
        files: List of ComponentFile objects to install
        destination: Destination directory (project root)
        dry_run: If True, don't actually write files

    Returns:
        List of paths that were written
    """
    written_paths = []

    for file in files:
        dest_path = destination / file.dest_path

        if not dry_run:
            # Create parent directories
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            dest_path.write_bytes(file.content)

        written_paths.append(dest_path)

    return written_paths


def install_component(
    component_name: str,
    destination: Path,
    dry_run: bool = False,
) -> tuple[bool, ComponentManifest | None, list[Path]]:
    """Install a component to a destination directory.

    Args:
        component_name: Name of the component to install
        destination: Destination directory (project root)
        dry_run: If True, don't actually write files

    Returns:
        Tuple of (success, manifest, written_paths)
    """
    # Fetch manifest
    manifest = fetch_component_manifest(component_name)
    if not manifest:
        return False, None, []

    # Fetch files
    files = fetch_component_files(component_name)
    if not files:
        return False, manifest, []

    # Install files
    written_paths = install_component_files(files, destination, dry_run)

    return True, manifest, written_paths
