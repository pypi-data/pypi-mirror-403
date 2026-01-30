"""paracord bug command - Report bugs to GitHub."""

import subprocess
from typing import Annotated

import typer

from paracord import __version__
from paracord.utils.console import print_success, print_error, print_info


CLI_REPO = "paracord-co/paracord-cli"
LIBRARY_REPO = "paracord-run/library"


def bug(
    description: Annotated[
        str,
        typer.Argument(help="Brief description of the bug."),
    ],
    library: Annotated[
        bool,
        typer.Option("--library", "-l", help="Report bug for the component library instead of CLI."),
    ] = False,
) -> None:
    """Report a bug to GitHub.

    Opens a new GitHub issue with the bug description.
    Use --library to report bugs with components.
    """
    repo = LIBRARY_REPO if library else CLI_REPO
    repo_name = "component library" if library else "CLI"

    print_info(f"Opening bug report for {repo_name}...")

    # Build issue body
    body_parts = [description]
    if not library:
        body_parts.append(f"\n\n---\nCLI Version: {__version__}")

    body = "\n".join(body_parts)

    try:
        result = subprocess.run(
            [
                "gh", "issue", "create",
                "--repo", repo,
                "--title", description[:80],
                "--body", body,
                "--label", "bug",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )

        # gh issue create outputs the URL on success
        issue_url = result.stdout.strip()
        print_success(f"Bug reported: {issue_url}")

    except subprocess.CalledProcessError as e:
        if "label" in e.stderr.lower():
            # Try without label if it doesn't exist
            try:
                result = subprocess.run(
                    [
                        "gh", "issue", "create",
                        "--repo", repo,
                        "--title", description[:80],
                        "--body", body,
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=30,
                )
                issue_url = result.stdout.strip()
                print_success(f"Bug reported: {issue_url}")
            except subprocess.CalledProcessError as e2:
                print_error(f"Failed to create issue: {e2.stderr}")
                raise typer.Exit(1)
        else:
            print_error(f"Failed to create issue: {e.stderr}")
            raise typer.Exit(1)
    except subprocess.TimeoutExpired:
        print_error("Request timed out.")
        raise typer.Exit(1)
    except FileNotFoundError:
        print_error("GitHub CLI (gh) not found. Install it from https://cli.github.com")
        raise typer.Exit(1)
