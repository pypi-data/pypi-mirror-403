"""Auto-update functionality for kubepath.

Checks GitHub for updates on app startup and silently updates via git pull.
"""

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from kubepath import __version__


@dataclass
class UpdateResult:
    """Result of an update check/operation."""

    checked: bool  # Whether check was performed
    update_available: bool  # Whether update was found
    updated: bool  # Whether update was applied
    local_version: str
    remote_version: Optional[str] = None
    message: str = ""
    error: Optional[str] = None


def get_local_version() -> str:
    """Get the current local version.

    Returns:
        Version string from kubepath.__version__
    """
    return __version__


def get_repo_root() -> Optional[Path]:
    """Get the root directory of the git repository.

    Returns:
        Path to repo root, or None if not in a git repo.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return Path(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    return None


def is_git_available() -> bool:
    """Check if git is installed and available.

    Returns:
        True if git command is available.
    """
    return shutil.which("git") is not None


def is_git_repo() -> bool:
    """Check if current directory is inside a git repository.

    Returns:
        True if in a git repo.
    """
    return get_repo_root() is not None


def get_latest_remote_version(repo_root: Path) -> Optional[str]:
    """Fetch and get the latest version tag from remote.

    This performs a `git fetch --tags` and then gets the latest tag.

    Args:
        repo_root: Path to the repository root.

    Returns:
        Latest version string (without 'v' prefix), or None on failure.
    """
    try:
        # Fetch latest tags from remote
        fetch_result = subprocess.run(
            ["git", "fetch", "--tags", "--quiet"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if fetch_result.returncode != 0:
            return None

        # Get the latest tag (sorted by version)
        # Using describe to get the most recent tag reachable from origin/main
        tag_result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0", "origin/main"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=10,
        )

        if tag_result.returncode == 0:
            tag = tag_result.stdout.strip()
            # Remove 'v' prefix if present (e.g., "v0.1.1" -> "0.1.1")
            if tag.startswith("v"):
                tag = tag[1:]
            return tag

    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    return None


def compare_versions(local: str, remote: str) -> int:
    """Compare two semantic version strings.

    Args:
        local: Local version string (e.g., "0.1.0")
        remote: Remote version string (e.g., "0.1.1")

    Returns:
        -1 if local < remote (update available)
         0 if local == remote (up to date)
         1 if local > remote (local is newer)
    """

    def parse_version(v: str) -> tuple:
        """Parse version string to tuple of integers."""
        parts = v.split(".")
        return tuple(int(p) for p in parts[:3])  # Only compare major.minor.patch

    try:
        local_tuple = parse_version(local)
        remote_tuple = parse_version(remote)

        if local_tuple < remote_tuple:
            return -1
        elif local_tuple > remote_tuple:
            return 1
        return 0
    except (ValueError, IndexError):
        # If parsing fails, assume no update needed
        return 0


def perform_git_pull(repo_root: Path) -> tuple[bool, str]:
    """Perform git pull to update the repository.

    Args:
        repo_root: Path to the repository root.

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        result = subprocess.run(
            ["git", "pull", "--quiet"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            return True, "Update successful"
        else:
            # Check for common issues
            stderr = result.stderr.lower()
            if "uncommitted changes" in stderr or "local changes" in stderr:
                return False, "Local changes would be overwritten"
            elif "conflict" in stderr:
                return False, "Merge conflict detected"
            else:
                return False, f"Git pull failed: {result.stderr.strip()}"

    except subprocess.TimeoutExpired:
        return False, "Update timed out"
    except FileNotFoundError:
        return False, "Git not found"
    except OSError as e:
        return False, f"OS error: {e}"


def check_and_update() -> UpdateResult:
    """Check for updates and apply them if available.

    This is the main entry point for the auto-update feature.
    It performs the following steps:
    1. Check if git is available
    2. Check if we're in a git repository
    3. Fetch latest tags from remote
    4. Compare versions
    5. Run git pull if update available

    Returns:
        UpdateResult with details of the operation.
    """
    local_version = get_local_version()

    # Check prerequisites
    if not is_git_available():
        return UpdateResult(
            checked=False,
            update_available=False,
            updated=False,
            local_version=local_version,
            error="Git not available",
        )

    repo_root = get_repo_root()
    if repo_root is None:
        return UpdateResult(
            checked=False,
            update_available=False,
            updated=False,
            local_version=local_version,
            error="Not a git repository",
        )

    # Get remote version
    remote_version = get_latest_remote_version(repo_root)
    if remote_version is None:
        return UpdateResult(
            checked=False,
            update_available=False,
            updated=False,
            local_version=local_version,
            error="Could not fetch remote version",
        )

    # Compare versions
    comparison = compare_versions(local_version, remote_version)

    if comparison >= 0:
        # Already up to date or local is newer
        return UpdateResult(
            checked=True,
            update_available=False,
            updated=False,
            local_version=local_version,
            remote_version=remote_version,
            message="Already up to date",
        )

    # Update available - perform git pull
    success, message = perform_git_pull(repo_root)

    return UpdateResult(
        checked=True,
        update_available=True,
        updated=success,
        local_version=local_version,
        remote_version=remote_version,
        message=message,
        error=None if success else message,
    )


def should_check_for_updates() -> bool:
    """Determine if we should check for updates.

    Respects environment variables to skip updates in certain environments.

    Returns:
        True if update check should proceed.
    """
    # Skip if explicitly disabled
    if os.environ.get("KUBEPATH_NO_UPDATE", "0") == "1":
        return False

    # Skip in CI environments
    if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
        return False

    return True
