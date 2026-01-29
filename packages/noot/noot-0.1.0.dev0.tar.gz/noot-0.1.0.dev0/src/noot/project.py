"""Project root discovery utilities."""

from pathlib import Path


class ProjectRootNotFoundError(Exception):
    """Raised when no project root can be found."""

    def __init__(self, start_dir: Path):
        self.start_dir = start_dir
        super().__init__(
            f"Could not find project root (no .git directory) starting from {start_dir}"
        )


def find_project_root(start_dir: Path | None = None) -> Path:
    """
    Find the project root by walking up from start_dir to find .git directory.

    Args:
        start_dir: Directory to start searching from. Defaults to cwd.

    Returns:
        Path to the project root directory.

    Raises:
        ProjectRootNotFoundError: If no .git directory is found.
    """
    if start_dir is None:
        start_dir = Path.cwd()

    current = start_dir.resolve()

    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent

    # Check root directory as well
    if (current / ".git").exists():
        return current

    raise ProjectRootNotFoundError(start_dir)
