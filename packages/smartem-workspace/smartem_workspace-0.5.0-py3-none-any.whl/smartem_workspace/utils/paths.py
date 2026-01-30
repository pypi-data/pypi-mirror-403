"""Path utility functions."""

from pathlib import Path


def resolve_workspace_path(path: Path | str | None = None) -> Path:
    """
    Resolve and validate the workspace path.

    Args:
        path: Target path (defaults to current directory)

    Returns:
        Resolved absolute path
    """
    if path is None:
        return Path.cwd().resolve()

    resolved = Path(path).expanduser().resolve()
    return resolved


def ensure_directory(path: Path) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path

    Returns:
        The path (for chaining)
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def is_git_repository(path: Path) -> bool:
    """Check if a path is a git repository."""
    return (path / ".git").exists()


def find_workspace_root(start_path: Path | None = None) -> Path | None:
    """
    Find the workspace root by looking for marker files.

    Looks for .mcp.json or CLAUDE.md as workspace indicators.

    Args:
        start_path: Starting directory (defaults to cwd)

    Returns:
        Workspace root path or None if not found
    """
    path = start_path or Path.cwd()
    path = path.resolve()

    markers = [".mcp.json", "CLAUDE.md", ".serena"]

    while path != path.parent:
        for marker in markers:
            if (path / marker).exists():
                return path
        path = path.parent

    return None
