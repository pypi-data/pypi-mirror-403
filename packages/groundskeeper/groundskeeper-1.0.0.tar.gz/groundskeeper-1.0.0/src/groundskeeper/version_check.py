"""Version check functionality for groundskeeper updates."""

import json
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from groundskeeper import __version__
from groundskeeper.constants import VERSION_CACHE_DURATION

GITHUB_RELEASES_URL = "https://api.github.com/repos/aorumbayev/groundskeeper/releases/latest"


@dataclass(slots=True)
class VersionCheckResult:
    """Result of a version check."""

    current_version: str
    latest_version: str | None
    update_available: bool
    error: str | None = None


def _get_cache_path() -> Path:
    """Get the path to the version check cache file."""
    cache_dir = Path.home() / ".cache" / "groundskeeper"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / "version_check.json"


def _read_cache() -> dict | None:
    """Read cached version check result."""
    cache_path = _get_cache_path()
    if not cache_path.exists():
        return None

    try:
        data = json.loads(cache_path.read_text())
        # Check if cache is still valid (within 24 hours)
        if time.time() - data.get("timestamp", 0) < VERSION_CACHE_DURATION:
            return data
    except (json.JSONDecodeError, OSError):
        pass

    return None


def _write_cache(latest_version: str) -> None:
    """Write version check result to cache."""
    cache_path = _get_cache_path()
    try:
        cache_path.write_text(
            json.dumps(
                {
                    "timestamp": time.time(),
                    "latest_version": latest_version,
                }
            )
        )
    except OSError:
        # Silently ignore cache write failures
        pass


def _parse_version(version: str) -> tuple[int, ...]:
    """Parse version string into comparable tuple.

    Handles versions like '1.2.3', 'v1.2.3', '1.2.3-beta'.
    """
    # Strip leading 'v' if present
    version = version.lstrip("v")
    # Take only the numeric part (before any hyphen for pre-release)
    version = version.split("-")[0]
    # Split by dots and convert to integers
    try:
        return tuple(int(part) for part in version.split("."))
    except ValueError:
        return (0,)


def _is_newer_version(latest: str, current: str) -> bool:
    """Check if latest version is newer than current version."""
    latest_tuple = _parse_version(latest)
    current_tuple = _parse_version(current)
    return latest_tuple > current_tuple


def _fetch_latest_release() -> str:
    """Fetch latest release version from GitHub API.

    Returns:
        Version tag string or raises exception on error.
    """
    request = Request(
        GITHUB_RELEASES_URL,
        headers={
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": f"groundskeeper/{__version__}",
        },
    )

    with urlopen(request, timeout=10) as response:
        data = json.loads(response.read().decode("utf-8"))
        return data.get("tag_name", "")


def check_for_updates(force_refresh: bool = False) -> VersionCheckResult:
    """Check if a newer version of groundskeeper is available.

    Args:
        force_refresh: If True, bypass cache and query GitHub API directly.

    Returns:
        VersionCheckResult containing version info and update availability.
    """
    current = __version__

    # Check cache first (unless force refresh)
    if not force_refresh:
        cached = _read_cache()
        if cached:
            latest = cached.get("latest_version", "")
            return VersionCheckResult(
                current_version=current,
                latest_version=latest,
                update_available=_is_newer_version(latest, current),
            )

    # Fetch from GitHub API
    try:
        latest = _fetch_latest_release()
        _write_cache(latest)
        return VersionCheckResult(
            current_version=current,
            latest_version=latest,
            update_available=_is_newer_version(latest, current),
        )
    except (URLError, TimeoutError, OSError) as e:
        return VersionCheckResult(
            current_version=current,
            latest_version=None,
            update_available=False,
            error=f"Network error: {e}",
        )
    except (json.JSONDecodeError, KeyError) as e:
        return VersionCheckResult(
            current_version=current,
            latest_version=None,
            update_available=False,
            error=f"Failed to parse response: {e}",
        )
