"""Update checker for EntelligenceAI CLI."""

from __future__ import annotations

import json
import time
from pathlib import Path

import requests


PACKAGE_NAME = "entelligence-cli"
PYPI_URL = f"https://pypi.org/pypi/{PACKAGE_NAME}/json"
CHECK_INTERVAL_SECONDS = 24 * 60 * 60  # Check once per day


def get_cache_file() -> Path:
    """Get the path to the update check cache file."""
    cache_dir = Path.home() / ".entelligence"
    cache_dir.mkdir(exist_ok=True)
    return cache_dir / "update_cache.json"


def load_cache() -> dict:
    """Load the update check cache."""
    cache_file = get_cache_file()
    if cache_file.exists():
        try:
            with open(cache_file) as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            pass
    return {}


def save_cache(data: dict) -> None:
    """Save the update check cache."""
    cache_file = get_cache_file()
    try:
        with open(cache_file, "w") as f:
            json.dump(data, f)
    except OSError:
        pass  # Silently fail - don't break CLI for cache issues


def parse_version(version_str: str) -> tuple[int, ...]:
    """Parse a version string into a tuple of integers for comparison.

    Handles versions like '0.1.3', '1.0.0', '2.0.0a1' (strips non-numeric suffixes).
    """
    # Strip any pre-release suffixes (a, b, rc, etc.)
    clean_version = ""
    for char in version_str:
        if char.isdigit() or char == ".":
            clean_version += char
        else:
            break

    # Remove trailing dots
    clean_version = clean_version.rstrip(".")

    try:
        return tuple(int(part) for part in clean_version.split("."))
    except ValueError:
        return (0,)


def compare_versions(current: str, latest: str) -> bool:
    """Return True if latest > current."""
    return parse_version(latest) > parse_version(current)


def fetch_latest_version():
    """Fetch the latest version from PyPI.

    Returns the latest version string, or None if the check fails.
    """
    try:
        response = requests.get(PYPI_URL, timeout=3)
        if response.status_code == 200:
            data = response.json()
            return data.get("info", {}).get("version")
    except (requests.RequestException, json.JSONDecodeError, KeyError):
        pass
    return None


def check_for_updates(current_version: str, force: bool = False):
    """Check if a new version is available.

    Args:
        current_version: The currently installed version.
        force: If True, bypass the cache and check immediately.

    Returns:
        A dict with 'current', 'latest', and 'update_command' if an update is available.
        None if no update is available or the check failed.
    """
    cache = load_cache()
    now = time.time()

    # Check if we should skip (checked recently)
    if not force:
        last_check = cache.get("last_check", 0)
        if now - last_check < CHECK_INTERVAL_SECONDS:
            # Use cached result if available
            cached_latest = cache.get("latest_version")
            if cached_latest and compare_versions(current_version, cached_latest):
                return {
                    "current": current_version,
                    "latest": cached_latest,
                    "update_command": f"uv tool upgrade {PACKAGE_NAME}",
                }
            return None

    # Fetch latest version from PyPI
    latest_version = fetch_latest_version()

    # Update cache
    cache["last_check"] = now
    if latest_version:
        cache["latest_version"] = latest_version
    save_cache(cache)

    # Compare versions
    if latest_version and compare_versions(current_version, latest_version):
        return {
            "current": current_version,
            "latest": latest_version,
            "update_command": f"uv tool upgrade {PACKAGE_NAME}",
        }

    return None


def get_update_message(update_info: dict) -> str:
    """Format an update notification message.

    Args:
        update_info: Dict with 'current', 'latest', and 'update_command'.

    Returns:
        A formatted string to display to the user.
    """
    return (
        f"\n⚠️  Update available: {update_info['current']} → {update_info['latest']}\n"
        f"   Run: {update_info['update_command']}\n"
    )
