"""GitHub Discussions integration for Paracord CLI."""

import httpx
from datetime import datetime, timezone

from paracord import __version__
from paracord.utils.console import print_info


GITHUB_GRAPHQL_API = "https://api.github.com/graphql"
PARACORD_REPO_OWNER = "paracord-run"
PARACORD_REPO_NAME = "dash"


async def register_project(
    project_name: str | None = None,
    github_token: str | None = None,
) -> bool:
    """Register a new project in GitHub Discussions.

    This is a non-blocking, best-effort community registration that
    posts to the paracord-run/dash discussions to help track adoption.

    Args:
        project_name: Optional project name to include
        github_token: GitHub token for API access

    Returns:
        True if registration succeeded, False otherwise
    """
    if not github_token:
        # Try to get token from environment or gh cli
        github_token = _get_github_token()

    if not github_token:
        # No token available, silently skip
        return False

    try:
        # Create the discussion post
        timestamp = datetime.now(timezone.utc).isoformat()
        title = f"New Paracord project created"
        body = _build_registration_body(project_name, timestamp)

        # For now, we'll use a simpler approach - just log intent
        # Full GraphQL implementation would require finding the
        # correct discussion category ID first
        print_info("Community registration: skipped (token required)")
        return False

    except Exception:
        # Fail silently - this is non-critical
        return False


def _get_github_token() -> str | None:
    """Try to get a GitHub token from available sources."""
    import os
    import subprocess

    # Check environment variable
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        return token

    # Try gh cli
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except Exception:
        pass

    return None


def _build_registration_body(project_name: str | None, timestamp: str) -> str:
    """Build the registration post body."""
    lines = [
        "A new Paracord project has been created!",
        "",
        f"- **CLI Version**: {__version__}",
        f"- **Timestamp**: {timestamp}",
    ]

    if project_name:
        lines.insert(2, f"- **Project**: {project_name}")

    lines.extend([
        "",
        "---",
        "*This is an automated registration from the Paracord CLI.*",
    ])

    return "\n".join(lines)


def register_project_sync(project_name: str | None = None) -> bool:
    """Synchronous wrapper for register_project.

    Args:
        project_name: Optional project name to include

    Returns:
        True if registration succeeded, False otherwise
    """
    import asyncio

    try:
        return asyncio.run(register_project(project_name))
    except Exception:
        return False
