"""Unified sync commands for Paracord projects."""

import hashlib
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Annotated

import typer
import yaml
from rich.table import Table

from paracord.core.ports import write_env_file, PortSet, DJANGO_BASE_PORT, POSTGRES_BASE_PORT, REDIS_BASE_PORT
from paracord.core.project_registry import get_project, update_project, register_project, is_project_registered
from paracord.utils.config import (
    get_paracord_config,
    get_copier_answers,
    write_paracord_config,
    PYPROJECT_FILE,
    COPIER_ANSWERS_FILE,
)
from paracord.utils.console import (
    console,
    print_header,
    print_success,
    print_error,
    print_warning,
    print_info,
)
from paracord.core.api import ParacordClient, AuthenticationError

sync_app = typer.Typer(
    name="sync",
    help="Sync project configuration, dependencies, and knowledge base.",
    invoke_without_command=True,
)

# Knowledge base subcommand group
kb_app = typer.Typer(
    name="kb",
    help="Sync knowledge base with local markdown files.",
    no_args_is_help=True,
)
sync_app.add_typer(kb_app, name="kb")

SYNC_STATE_FILE = ".paracord-sync.yaml"


def migrate_from_copier_answers(project_path: Path) -> PortSet | None:
    """Migrate port configuration from .copier-answers.yml to pyproject.toml.

    For legacy projects created before the CLI stored ports in pyproject.toml.

    Args:
        project_path: Path to the project directory

    Returns:
        PortSet if migration successful, None otherwise
    """
    copier_answers = get_copier_answers(project_path)
    if not copier_answers:
        return None

    # Extract ports from copier answers
    django_port = copier_answers.get("django_port")
    postgres_port = copier_answers.get("postgres_port")
    redis_port = copier_answers.get("redis_port")

    if django_port is None:
        return None

    # Handle port values that might be strings
    try:
        django_port = int(django_port)
        postgres_port = int(postgres_port) if postgres_port else None
        redis_port = int(redis_port) if redis_port else None
    except (ValueError, TypeError):
        return None

    # Calculate slot and fill in missing ports
    slot = django_port - DJANGO_BASE_PORT
    port_set = PortSet(
        django_port=django_port,
        postgres_port=postgres_port or (POSTGRES_BASE_PORT + slot),
        redis_port=redis_port or (REDIS_BASE_PORT + slot),
        slot=slot,
    )

    # Write to pyproject.toml
    write_paracord_config(project_path, {
        "django_port": port_set.django_port,
        "postgres_port": port_set.postgres_port,
        "redis_port": port_set.redis_port,
    })

    return port_set


def sync_env_to_file(project_path: Path) -> bool:
    """Sync pyproject.toml [tool.paracord] to .env.paracord file.

    Args:
        project_path: Path to the project directory

    Returns:
        True if successful, False otherwise
    """
    config = get_paracord_config(project_path)

    if not config:
        print_warning(f"No \\[tool.paracord] section found in {PYPROJECT_FILE}")
        return False

    django_port = config.get("django_port")
    if django_port is None:
        print_warning("No django_port configured in [tool.paracord]")
        return False

    # Calculate slot and fill in missing ports
    slot = django_port - DJANGO_BASE_PORT
    postgres_port = config.get("postgres_port", POSTGRES_BASE_PORT + slot)
    redis_port = config.get("redis_port", REDIS_BASE_PORT + slot)

    port_set = PortSet(
        django_port=django_port,
        postgres_port=postgres_port,
        redis_port=redis_port,
        slot=slot,
    )

    write_env_file(project_path, port_set)
    return True


def sync_registry(project_path: Path) -> bool:
    """Sync pyproject.toml ports to the project registry.

    Args:
        project_path: Path to the project directory

    Returns:
        True if successful, False otherwise
    """
    config = get_paracord_config(project_path)

    if not config:
        return False

    django_port = config.get("django_port")
    postgres_port = config.get("postgres_port")
    redis_port = config.get("redis_port")

    if django_port is None:
        return False

    # Update registry if project exists
    project = get_project(project_path)
    if project:
        update_project(
            project_path,
            port=django_port,
            postgres_port=postgres_port,
            redis_port=redis_port,
        )
        return True

    return False


@sync_app.callback(invoke_without_command=True)
def sync_default(
    ctx: typer.Context,
    path: Annotated[
        Path,
        typer.Option("--path", "-p", help="Project directory"),
    ] = Path("."),
) -> None:
    """Run full project sync (env, registry, uv, rav)."""
    if ctx.invoked_subcommand is not None:
        return

    print_header("Paracord Sync")

    project_path = path.resolve()

    # Check if this is a paracord project
    pyproject = project_path / PYPROJECT_FILE
    if not pyproject.exists():
        print_error(f"No {PYPROJECT_FILE} found in {project_path}")
        raise typer.Exit(1)

    # Check if [tool.paracord] exists, if not try to migrate from .copier-answers.yml
    config = get_paracord_config(project_path)
    migrated_port_set = None
    if not config or "django_port" not in config:
        copier_answers_path = project_path / COPIER_ANSWERS_FILE
        if copier_answers_path.exists():
            print_info("No [tool.paracord] found, migrating from .copier-answers.yml...")
            migrated_port_set = migrate_from_copier_answers(project_path)
            if migrated_port_set:
                print_success(
                    f"Migrated ports: Django={migrated_port_set.django_port}, "
                    f"Postgres={migrated_port_set.postgres_port}, Redis={migrated_port_set.redis_port}"
                )
            else:
                print_warning("Could not migrate ports from .copier-answers.yml")

    # 1. Sync env file
    print_info("Syncing .env.paracord...")
    if sync_env_to_file(project_path):
        print_success("Generated .env.paracord")
    else:
        print_warning("Skipped .env.paracord (no port config)")

    # 2. Sync registry - register if not already registered
    if not is_project_registered(project_path):
        config = get_paracord_config(project_path)
        if config and "django_port" in config:
            copier_answers = get_copier_answers(project_path)
            project_name = copier_answers.get("project_name") or project_path.name
            template_source = copier_answers.get("_src_path")

            print_info("Registering project...")
            try:
                register_project(
                    path=project_path,
                    name=project_name,
                    port=config["django_port"],
                    postgres_port=config.get("postgres_port"),
                    redis_port=config.get("redis_port"),
                    template_source=template_source,
                )
                print_success("Registered project")
            except Exception as e:
                print_warning(f"Could not register project: {e}")
    else:
        print_info("Syncing project registry...")
        if sync_registry(project_path):
            print_success("Updated project registry")
        else:
            print_info("Registry update skipped")

    # 3. Run uv sync if uv.lock exists or pyproject.toml has dependencies
    uv_lock = project_path / "uv.lock"
    if uv_lock.exists() or pyproject.exists():
        print_info("Running uv sync...")
        try:
            result = subprocess.run(
                ["uv", "sync"],
                cwd=project_path,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                print_success("uv sync complete")
            else:
                print_warning(f"uv sync failed: {result.stderr.strip()}")
        except FileNotFoundError:
            print_warning("uv not found, skipping dependency sync")

    # 4. Run rav sync if rav.yaml exists
    rav_yaml = project_path / "rav.yaml"
    if rav_yaml.exists():
        print_info("Running rav run sync (if available)...")
        try:
            result = subprocess.run(
                ["rav", "run", "sync"],
                cwd=project_path,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                print_success("rav sync complete")
            else:
                # rav sync might not exist, that's ok
                pass
        except FileNotFoundError:
            pass  # rav not installed, skip

    console.print()
    print_success("Sync complete!")


@sync_app.command(name="env")
def sync_env(
    path: Annotated[
        Path,
        typer.Option("--path", "-p", help="Project directory"),
    ] = Path("."),
) -> None:
    """Regenerate .env.paracord from pyproject.toml."""
    print_header("Sync Env")

    project_path = path.resolve()

    if not (project_path / PYPROJECT_FILE).exists():
        print_error(f"No {PYPROJECT_FILE} found in {project_path}")
        raise typer.Exit(1)

    if sync_env_to_file(project_path):
        print_success("Generated .env.paracord")
    else:
        print_error("Failed to generate .env.paracord")
        raise typer.Exit(1)


# --- Knowledge Base Commands (moved under kb subcommand) ---


def get_sync_state(path: Path) -> dict:
    """Load sync state from directory."""
    state_file = path / SYNC_STATE_FILE
    if state_file.exists():
        with open(state_file) as f:
            return yaml.safe_load(f) or {}
    return {"files": {}, "last_sync": None, "organization_id": None}


def save_sync_state(path: Path, state: dict) -> None:
    """Save sync state to directory."""
    state_file = path / SYNC_STATE_FILE
    with open(state_file, "w") as f:
        yaml.safe_dump(state, f)


def file_hash(content: str) -> str:
    """Get hash of file content."""
    return hashlib.sha256(content.encode()).hexdigest()[:12]


@kb_app.command(name="pull")
def kb_pull(
    path: Annotated[
        Path,
        typer.Option("--path", "-p", help="Directory to sync to"),
    ] = Path("./knowledge"),
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Overwrite local changes"),
    ] = False,
) -> None:
    """Download knowledge base as markdown files."""
    print_header("Sync KB Pull")

    try:
        client = ParacordClient()
    except AuthenticationError as e:
        print_error(str(e))
        raise typer.Exit(1)

    # Create directory if needed
    path.mkdir(parents=True, exist_ok=True)

    # Fetch articles from API
    console.print("[info]Fetching articles...[/info]")
    response = client.get(f"/api/knowledge/org/{client.org_id}/articles/")

    if response.status_code != 200:
        print_error(f"Failed to fetch articles: {response.status_code}")
        if response.status_code == 401:
            print_info("Your token may have expired. Run 'paracord auth login' to re-authenticate.")
        raise typer.Exit(1)

    articles = response.json()
    state = get_sync_state(path)
    state["organization_id"] = client.org_id

    created = 0
    updated = 0
    skipped = 0

    for article in articles:
        article_path = path / f"{article['path']}.md"
        article_path.parent.mkdir(parents=True, exist_ok=True)

        content = article.get("content", "")
        remote_hash = file_hash(content)

        # Check if file exists and has local changes
        if article_path.exists() and not force:
            local_content = article_path.read_text()
            local_hash = file_hash(local_content)
            stored_hash = state.get("files", {}).get(article["path"], {}).get(
                "local_hash"
            )

            if local_hash != stored_hash and local_hash != remote_hash:
                console.print(
                    f"[warning]Skipping {article['path']} (local changes)[/warning]"
                )
                skipped += 1
                continue

        # Write file
        existed = article_path.exists()
        article_path.write_text(content)

        # Update state
        state.setdefault("files", {})[article["path"]] = {
            "local_hash": remote_hash,
            "remote_updated_at": article.get("updated_at"),
        }

        if existed:
            updated += 1
        else:
            created += 1

    state["last_sync"] = datetime.utcnow().isoformat()
    save_sync_state(path, state)

    print_success(f"Pull complete: {created} created, {updated} updated, {skipped} skipped")


@kb_app.command(name="push")
def kb_push(
    path: Annotated[
        Path,
        typer.Option("--path", "-p", help="Directory to sync from"),
    ] = Path("./knowledge"),
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", "-n", help="Show what would be pushed"),
    ] = False,
) -> None:
    """Upload local markdown changes to knowledge base."""
    print_header("Sync KB Push")

    try:
        client = ParacordClient()
    except AuthenticationError as e:
        print_error(str(e))
        raise typer.Exit(1)

    if not path.exists():
        print_error(f"Directory not found: {path}")
        raise typer.Exit(1)

    state = get_sync_state(path)

    # Find all markdown files
    changes = []
    for md_file in path.rglob("*.md"):
        if md_file.name == SYNC_STATE_FILE:
            continue

        relative_path = md_file.relative_to(path)
        article_path = str(relative_path.with_suffix(""))

        content = md_file.read_text()
        current_hash = file_hash(content)
        stored_hash = state.get("files", {}).get(article_path, {}).get("local_hash")

        if current_hash != stored_hash:
            changes.append(
                {
                    "path": article_path,
                    "content": content,
                    "hash": current_hash,
                    "is_new": stored_hash is None,
                }
            )

    if not changes:
        print_info("No changes to push")
        return

    # Show changes
    table = Table(title="Changes to Push")
    table.add_column("Status")
    table.add_column("Path")

    for change in changes:
        status = "[green]NEW[/green]" if change["is_new"] else "[yellow]MODIFIED[/yellow]"
        table.add_row(status, change["path"])

    console.print(table)

    if dry_run:
        print_info("Dry run - no changes made")
        return

    # Push changes
    pushed = 0
    for change in changes:
        if change["is_new"]:
            response = client.post(
                f"/api/knowledge/org/{client.org_id}/articles/",
                json={"path": change["path"], "content": change["content"]},
            )
        else:
            response = client.patch(
                f"/api/knowledge/org/{client.org_id}/articles/{change['path']}/",
                json={"content": change["content"]},
            )

        if response.status_code in (200, 201):
            state.setdefault("files", {})[change["path"]] = {
                "local_hash": change["hash"],
                "remote_updated_at": datetime.utcnow().isoformat(),
            }
            pushed += 1
        else:
            print_error(f"Failed to push {change['path']}: {response.status_code}")

    state["last_sync"] = datetime.utcnow().isoformat()
    save_sync_state(path, state)

    print_success(f"Pushed {pushed} changes")


@kb_app.command(name="status")
def kb_status(
    path: Annotated[
        Path,
        typer.Option("--path", "-p", help="Directory to check"),
    ] = Path("./knowledge"),
) -> None:
    """Show knowledge base sync status."""
    print_header("Sync KB Status")

    if not path.exists():
        print_warning(f"Directory not found: {path}")
        print_info("Run 'paracord sync kb pull' to download knowledge base")
        return

    state = get_sync_state(path)

    if not state.get("organization_id"):
        print_warning("Not synced yet")
        print_info("Run 'paracord sync kb pull' to initialize")
        return

    console.print(f"[info]Organization:[/info] {state['organization_id']}")
    console.print(f"[info]Last sync:[/info] {state.get('last_sync', 'never')}")

    # Check for local changes
    local_changes = []
    for md_file in path.rglob("*.md"):
        if md_file.name == SYNC_STATE_FILE:
            continue

        relative_path = md_file.relative_to(path)
        article_path = str(relative_path.with_suffix(""))

        content = md_file.read_text()
        current_hash = file_hash(content)
        stored_hash = state.get("files", {}).get(article_path, {}).get("local_hash")

        if current_hash != stored_hash:
            is_new = stored_hash is None
            local_changes.append((article_path, "new" if is_new else "modified"))

    if local_changes:
        console.print(f"\n[warning]Local changes ({len(local_changes)}):[/warning]")
        for path_str, change_type in local_changes:
            status = "[green]new[/green]" if change_type == "new" else "[yellow]modified[/yellow]"
            console.print(f"  {status} {path_str}")
        console.print("\nRun 'paracord sync kb push' to upload changes")
    else:
        print_success("No local changes")
