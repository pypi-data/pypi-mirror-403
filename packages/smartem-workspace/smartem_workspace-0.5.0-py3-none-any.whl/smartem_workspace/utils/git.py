"""Git utility functions."""

import subprocess
from pathlib import Path


def check_git_available() -> bool:
    """Check if git is available in PATH."""
    try:
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def run_git_command(
    args: list[str],
    cwd: Path | None = None,
    timeout: int = 120,
) -> tuple[int, str, str]:
    """
    Run a git command and return the result.

    Args:
        args: Git command arguments (without 'git' prefix)
        cwd: Working directory for the command
        timeout: Timeout in seconds

    Returns:
        Tuple of (return_code, stdout, stderr)
    """
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except FileNotFoundError:
        return -1, "", "Git not found"


def get_current_branch(repo_path: Path) -> str | None:
    """Get the current branch name of a repository."""
    returncode, stdout, _ = run_git_command(
        ["branch", "--show-current"],
        cwd=repo_path,
    )
    if returncode == 0:
        return stdout.strip()
    return None


def has_uncommitted_changes(repo_path: Path) -> bool:
    """Check if a repository has uncommitted changes."""
    returncode, stdout, _ = run_git_command(
        ["status", "--porcelain"],
        cwd=repo_path,
    )
    if returncode == 0:
        return bool(stdout.strip())
    return False


def fetch_remote(repo_path: Path, remote: str = "origin") -> bool:
    """
    Fetch latest changes from remote.

    Returns:
        True if successful
    """
    returncode, _, _ = run_git_command(
        ["fetch", remote],
        cwd=repo_path,
        timeout=60,
    )
    return returncode == 0


def get_commits_behind(repo_path: Path, remote: str = "origin") -> int:
    """
    Get the number of commits the local branch is behind the remote.

    Returns:
        Number of commits behind, or 0 if up to date or on error
    """
    branch = get_current_branch(repo_path)
    if not branch:
        return 0

    returncode, stdout, _ = run_git_command(
        ["rev-list", "--count", f"HEAD..{remote}/{branch}"],
        cwd=repo_path,
    )
    if returncode == 0:
        try:
            return int(stdout.strip())
        except ValueError:
            return 0
    return 0


def get_commits_ahead(repo_path: Path, remote: str = "origin") -> int:
    """
    Get the number of commits the local branch is ahead of the remote.

    Returns:
        Number of commits ahead, or 0 if up to date or on error
    """
    branch = get_current_branch(repo_path)
    if not branch:
        return 0

    returncode, stdout, _ = run_git_command(
        ["rev-list", "--count", f"{remote}/{branch}..HEAD"],
        cwd=repo_path,
    )
    if returncode == 0:
        try:
            return int(stdout.strip())
        except ValueError:
            return 0
    return 0


def has_remote(repo_path: Path, remote: str = "origin") -> bool:
    """Check if a repository has the specified remote configured."""
    returncode, stdout, _ = run_git_command(
        ["remote"],
        cwd=repo_path,
    )
    if returncode == 0:
        return remote in stdout.split()
    return False


_ssh_auth_cache: dict[str, bool] = {}


def check_github_ssh_auth() -> bool:
    """Test if SSH authentication to GitHub works.

    GitHub's SSH test returns exit code 1 on successful authentication
    (with message "successfully authenticated"), and exit code 255 or
    timeout if SSH is not configured.

    Results are cached to avoid repeated SSH connection attempts.
    """
    if "github" in _ssh_auth_cache:
        return _ssh_auth_cache["github"]

    try:
        result = subprocess.run(
            ["ssh", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", "git@github.com"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # GitHub returns exit code 1 on successful auth with specific message
        success = "successfully authenticated" in result.stderr.lower()
        _ssh_auth_cache["github"] = success
        return success
    except (subprocess.TimeoutExpired, FileNotFoundError):
        _ssh_auth_cache["github"] = False
        return False


def check_gitlab_ssh_auth() -> bool:
    """Test if SSH authentication to GitLab works.

    Similar to GitHub, GitLab returns a welcome message on successful auth.
    Results are cached.
    """
    if "gitlab" in _ssh_auth_cache:
        return _ssh_auth_cache["gitlab"]

    try:
        result = subprocess.run(
            ["ssh", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", "git@gitlab.com"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # GitLab returns exit code 0 on successful auth
        success = result.returncode == 0 or "welcome to gitlab" in result.stderr.lower()
        _ssh_auth_cache["gitlab"] = success
        return success
    except (subprocess.TimeoutExpired, FileNotFoundError):
        _ssh_auth_cache["gitlab"] = False
        return False


def clear_ssh_auth_cache() -> None:
    """Clear the SSH authentication cache (mainly for testing)."""
    _ssh_auth_cache.clear()
