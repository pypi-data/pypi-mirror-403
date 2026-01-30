"""Main bootstrap orchestration for workspace setup."""

from pathlib import Path

from rich.console import Console

from smartem_workspace.config.schema import ClaudeCodeConfig, Organization, ReposConfig, Repository
from smartem_workspace.interactive.prompts import (
    confirm,
    display_selection_summary,
    select_preset,
    select_repos,
)
from smartem_workspace.setup.claude import setup_claude_config
from smartem_workspace.setup.repos import clone_repos
from smartem_workspace.setup.serena import setup_serena_config
from smartem_workspace.setup.workspace import display_next_steps, setup_workspace_structure

console = Console()


def ensure_devtools_in_selection(
    repos: list[tuple[Organization, Repository]],
    config: ReposConfig,
) -> list[tuple[Organization, Repository]]:
    """Ensure smartem-devtools is in the selection (required)."""
    has_devtools = any(org.name == "DiamondLightSource" and repo.name == "smartem-devtools" for org, repo in repos)

    if not has_devtools:
        dls_org = config.get_organization("DiamondLightSource")
        if dls_org:
            for repo in dls_org.repos:
                if repo.name == "smartem-devtools":
                    repos.insert(0, (dls_org, repo))
                    console.print("[dim]Added smartem-devtools (required)[/dim]")
                    break

    return repos


def bootstrap_workspace(
    config: ReposConfig,
    workspace_path: Path,
    preset: str | None = None,
    interactive: bool = True,
    use_ssh: bool | None = None,
    skip_claude: bool = False,
    skip_serena: bool = False,
    claude_config: ClaudeCodeConfig | None = None,
) -> bool:
    """
    Main bootstrap function to set up a SmartEM workspace.

    Args:
        config: Loaded workspace configuration
        workspace_path: Target directory for workspace
        preset: Preset name (if provided, skips repo selection)
        interactive: Enable interactive prompts
        use_ssh: True=force SSH, False=force HTTPS, None=auto-detect for GitHub
        skip_claude: Skip Claude Code setup
        skip_serena: Skip Serena MCP setup
        claude_config: Claude Code configuration (required if skip_claude is False)

    Returns:
        True if setup completed successfully
    """
    console.print()
    console.print(f"[bold]Workspace path:[/bold] {workspace_path.absolute()}")

    workspace_path.mkdir(parents=True, exist_ok=True)

    selected_repos: list[tuple[Organization, Repository]] = []

    if preset:
        selected_repos = config.resolve_preset(preset)
        if not selected_repos:
            console.print(f"[red]Unknown preset: {preset}[/red]")
            console.print(f"Available presets: {', '.join(config.presets.keys())}")
            return False
        console.print(f"[dim]Using preset: {preset}[/dim]")
    elif interactive:
        preset_choice = select_preset(config)
        selected_repos = config.resolve_preset(preset_choice) if preset_choice else select_repos(config)
    else:
        console.print("[red]No preset specified and interactive mode disabled[/red]")
        return False

    selected_repos = ensure_devtools_in_selection(selected_repos, config)

    display_selection_summary(selected_repos)

    if interactive and not confirm("Proceed with setup?"):
        console.print("[yellow]Setup cancelled[/yellow]")
        return False

    if not setup_workspace_structure(workspace_path):
        console.print("[red]Failed to create workspace structure[/red]")
        return False

    success, failed = clone_repos(
        repos=selected_repos,
        workspace_path=workspace_path,
        use_ssh=use_ssh,
        devtools_first=True,
    )

    console.print()
    console.print(f"[bold]Clone results:[/bold] {success} succeeded, {failed} failed")

    if failed > 0 and interactive and not confirm("Some repos failed to clone. Continue with setup?"):
        return False

    if not skip_claude and claude_config:
        setup_claude_config(claude_config, workspace_path)

    if not skip_serena:
        project_name = workspace_path.name or "smartem-workspace"
        setup_serena_config(config, workspace_path, project_name)

    display_next_steps(workspace_path)

    return True
