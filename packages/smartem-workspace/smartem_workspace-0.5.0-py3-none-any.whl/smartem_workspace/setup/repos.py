"""Repository cloning operations."""

import subprocess
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from smartem_workspace.config.schema import Organization, Repository
from smartem_workspace.utils.git import check_github_ssh_auth

console = Console()


def get_repo_url(repo: Repository, org: Organization, use_ssh: bool | None, github_ssh_ok: bool | None = None) -> str:
    """Get the clone URL based on preference or auto-detection.

    Args:
        repo: Repository to get URL for
        org: Organization the repo belongs to
        use_ssh: True=force SSH, False=force HTTPS, None=auto-detect
        github_ssh_ok: Cached result of GitHub SSH check (for auto-detect)

    Returns:
        Clone URL (SSH or HTTPS)
    """
    # Explicit override
    if use_ssh is True:
        return repo.urls.ssh
    if use_ssh is False:
        return repo.urls.https

    # Auto-detect mode
    if org.provider == "github" and github_ssh_ok:
        return repo.urls.ssh

    # Default to HTTPS (GitLab or GitHub without SSH)
    return repo.urls.https


def get_local_dir(org: Organization) -> str:
    """Get the local directory name for an organization."""
    return org.localDir if org.localDir else org.name


def clone_repo(
    repo: Repository,
    org: Organization,
    repos_dir: Path,
    use_ssh: bool | None = None,
    github_ssh_ok: bool | None = None,
) -> bool:
    """
    Clone a single repository.

    Args:
        repo: Repository to clone
        org: Organization the repo belongs to
        repos_dir: Directory to clone into
        use_ssh: True=force SSH, False=force HTTPS, None=auto-detect
        github_ssh_ok: Cached result of GitHub SSH check

    Returns:
        True if successful or already exists, False on error
    """
    org_dir = repos_dir / get_local_dir(org)
    org_dir.mkdir(parents=True, exist_ok=True)

    repo_path = org_dir / repo.name

    if repo_path.exists():
        console.print(f"  [dim]Skipping {repo.name} (already exists)[/dim]")
        return True

    url = get_repo_url(repo, org, use_ssh, github_ssh_ok)

    try:
        result = subprocess.run(
            ["git", "clone", url, str(repo_path)],
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            console.print(f"  [red]Failed to clone {repo.name}: {result.stderr}[/red]")
            return False
        console.print(f"  [green]Cloned {repo.name}[/green]")
        return True
    except subprocess.TimeoutExpired:
        console.print(f"  [red]Timeout cloning {repo.name}[/red]")
        return False
    except FileNotFoundError:
        console.print("[red]Git not found. Please install git and try again.[/red]")
        return False


def clone_repos(
    repos: list[tuple[Organization, Repository]],
    workspace_path: Path,
    use_ssh: bool | None = None,
    devtools_first: bool = True,
) -> tuple[int, int]:
    """
    Clone multiple repositories.

    Args:
        repos: List of (org, repo) tuples to clone
        workspace_path: Root workspace directory
        use_ssh: True=force SSH, False=force HTTPS, None=auto-detect for GitHub
        devtools_first: Clone smartem-devtools first (required for config)

    Returns:
        Tuple of (success_count, failure_count)
    """
    repos_dir = workspace_path / "repos"
    repos_dir.mkdir(parents=True, exist_ok=True)

    # Check SSH auth once at start for auto-detect mode
    github_ssh_ok: bool | None = None
    has_github_repos = any(org.provider == "github" for org, _ in repos)

    if use_ssh is None and has_github_repos:
        console.print()
        console.print("[dim]Checking GitHub SSH authentication...[/dim]")
        github_ssh_ok = check_github_ssh_auth()
        if github_ssh_ok:
            console.print("[green]SSH authentication successful - using SSH for GitHub repos[/green]")
        else:
            console.print("[yellow]SSH not configured for GitHub - using HTTPS (anonymous/read-only)[/yellow]")
            console.print(
                "[dim]To enable push access, configure SSH keys: https://docs.github.com/en/authentication/connecting-to-github-with-ssh[/dim]"
            )
    elif use_ssh is True:
        console.print()
        console.print("[dim]Using SSH URLs (--git-ssh)[/dim]")
    elif use_ssh is False:
        console.print()
        console.print("[dim]Using HTTPS URLs (--git-https)[/dim]")

    success = 0
    failed = 0

    if devtools_first:
        devtools = None
        remaining = []
        for org, repo in repos:
            if org.name == "DiamondLightSource" and repo.name == "smartem-devtools":
                devtools = (org, repo)
            else:
                remaining.append((org, repo))

        if devtools:
            console.print()
            console.print("[bold]Cloning smartem-devtools (required)...[/bold]")
            org, repo = devtools
            if clone_repo(repo, org, repos_dir, use_ssh, github_ssh_ok):
                success += 1
            else:
                failed += 1
                console.print("[red]Failed to clone smartem-devtools. Cannot continue.[/red]")
                return success, failed + len(remaining)

            repos = remaining

    console.print()
    console.print("[bold]Cloning repositories...[/bold]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Cloning...", total=len(repos))

        for org, repo in repos:
            progress.update(task, description=f"Cloning {org.name}/{repo.name}...")
            if clone_repo(repo, org, repos_dir, use_ssh, github_ssh_ok):
                success += 1
            else:
                failed += 1
            progress.advance(task)

    return success, failed


def pull_repo(repo_path: Path) -> bool:
    """
    Pull latest changes for a repository.

    Returns:
        True if successful, False on error
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "pull", "--ff-only"],
            capture_output=True,
            text=True,
            timeout=120,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def get_repo_status(repo_path: Path) -> dict | None:
    """
    Get status information for a repository.

    Returns:
        Dict with status info or None if not a git repo
    """
    if not (repo_path / ".git").exists():
        return None

    try:
        branch_result = subprocess.run(
            ["git", "-C", str(repo_path), "branch", "--show-current"],
            capture_output=True,
            text=True,
        )
        branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"

        status_result = subprocess.run(
            ["git", "-C", str(repo_path), "status", "--porcelain"],
            capture_output=True,
            text=True,
        )
        has_changes = bool(status_result.stdout.strip())

        return {
            "branch": branch,
            "has_changes": has_changes,
            "path": str(repo_path),
        }
    except Exception:
        return None
