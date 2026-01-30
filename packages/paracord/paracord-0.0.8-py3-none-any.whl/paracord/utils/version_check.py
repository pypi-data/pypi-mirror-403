"""Periodic version check for Paracord CLI."""

import json
import time
from pathlib import Path

import httpx

from paracord import __version__

PYPI_URL = "https://pypi.org/pypi/paracord/json"
CACHE_DIR = Path.home() / ".cache" / "paracord"
CACHE_FILE = CACHE_DIR / "version_check.json"
CHECK_INTERVAL = 86400  # 24 hours in seconds


def _parse_version(version: str) -> tuple[int, ...]:
    """Parse version string into tuple for comparison."""
    return tuple(int(x) for x in version.split("."))


def _is_newer(latest: str, current: str) -> bool:
    """Check if latest version is newer than current."""
    try:
        return _parse_version(latest) > _parse_version(current)
    except (ValueError, AttributeError):
        return False


def _read_cache() -> dict:
    """Read the version check cache file."""
    try:
        if CACHE_FILE.exists():
            return json.loads(CACHE_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        pass
    return {}


def _write_cache(data: dict) -> None:
    """Write to the version check cache file."""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(data))
    except OSError:
        pass


def _fetch_latest_version() -> str | None:
    """Fetch the latest version from PyPI."""
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(PYPI_URL)
            response.raise_for_status()
            data = response.json()
            return data.get("info", {}).get("version")
    except (httpx.HTTPError, json.JSONDecodeError, KeyError):
        return None


def check_for_updates() -> str | None:
    """Check for updates periodically.

    Returns the latest version string if an update is available,
    None otherwise. Fails gracefully on any error.
    """
    try:
        cache = _read_cache()
        now = time.time()
        last_check = cache.get("last_check", 0)

        # Return cached result if checked recently
        if now - last_check < CHECK_INTERVAL:
            latest = cache.get("latest_version")
            if latest and _is_newer(latest, __version__):
                return latest
            return None

        # Fetch latest version from PyPI
        latest = _fetch_latest_version()

        # Update cache
        _write_cache({
            "last_check": now,
            "latest_version": latest,
        })

        if latest and _is_newer(latest, __version__):
            return latest

        return None
    except Exception:
        # Fail gracefully on any unexpected error
        return None
