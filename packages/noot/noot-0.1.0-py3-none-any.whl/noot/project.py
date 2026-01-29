"""Project root discovery utilities."""

import os
from pathlib import Path

# Module-level cache for project root, populated at import time.
# This allows tests running in tmp_path to still find the original project root.
_cached_project_root: Path | None = None


class ProjectRootNotFoundError(Exception):
    """Raised when no project root can be found."""

    def __init__(self, start_dir: Path):
        self.start_dir = start_dir
        super().__init__(
            f"Could not find project root (no .git directory) "
            f"starting from {start_dir}.\n"
            "Either:\n"
            "  1. Run from within a git repository, or\n"
            "  2. Set NOOT_PROJECT_ROOT environment variable"
        )


def _discover_project_root(start_dir: Path) -> Path:
    """
    Walk up from start_dir to find .git directory.

    Args:
        start_dir: Directory to start searching from.

    Returns:
        Path to the project root directory.

    Raises:
        ProjectRootNotFoundError: If no .git directory is found.
    """
    current = start_dir.resolve()

    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent

    # Check root directory as well
    if (current / ".git").exists():
        return current

    raise ProjectRootNotFoundError(start_dir)


def find_project_root(start_dir: Path | None = None) -> Path:
    """
    Find the project root by walking up from start_dir to find .git directory.

    Resolution order (when start_dir is None):
        1. Cached project root (discovered at import time)
        2. NOOT_PROJECT_ROOT environment variable
        3. Walk up from cwd to find .git

    When called with no arguments, returns the cached project root that was
    discovered at import time. This allows code running from temporary
    directories (e.g., pytest tmp_path) to still find the original project.

    Args:
        start_dir: Directory to start searching from. If None, uses the
            cached project root or NOOT_PROJECT_ROOT env var.

    Returns:
        Path to the project root directory.

    Raises:
        ProjectRootNotFoundError: If no .git directory is found and
            NOOT_PROJECT_ROOT is not set.
    """
    global _cached_project_root

    # If no start_dir specified and we have a cached value, return it
    if start_dir is None and _cached_project_root is not None:
        return _cached_project_root

    # Check for explicit env var override
    if start_dir is None:
        env_root = os.environ.get("NOOT_PROJECT_ROOT")
        if env_root:
            return Path(env_root)

    # Discover from specified dir or current cwd
    search_dir = start_dir if start_dir is not None else Path.cwd()
    result = _discover_project_root(search_dir)

    # Cache the result if we used default start_dir and cache is empty
    if start_dir is None and _cached_project_root is None:
        _cached_project_root = result

    return result


def _init_project_root() -> None:
    """
    Initialize project root cache at import time.

    This captures the cwd before any test fixtures change it.
    Does not raise if project root cannot be found - that error
    is deferred until find_project_root() is actually called.
    """
    global _cached_project_root

    # Check env var first
    env_root = os.environ.get("NOOT_PROJECT_ROOT")
    if env_root:
        _cached_project_root = Path(env_root)
        return

    # Try to discover from cwd, but don't fail if not found.
    # This allows commands like `noot init` to run outside a git repo.
    try:
        _cached_project_root = _discover_project_root(Path.cwd())
    except ProjectRootNotFoundError:
        pass  # Will raise when find_project_root() is called


_init_project_root()
