"""Claude Code setup command."""

from pathlib import Path

import typer
from rich.console import Console

from smartem_workspace.config.loader import load_claude_code_config
from smartem_workspace.setup.claude import setup_claude_config
from smartem_workspace.utils.paths import find_workspace_root

console = Console()


def setup(
    path: Path | None = None,
    offline: bool = False,
) -> bool:
    """
    Set up Claude Code integration in the workspace.

    Args:
        path: Workspace path (auto-detected if not specified)
        offline: Use bundled config instead of fetching from GitHub

    Returns:
        True if successful
    """
    workspace_path = path or find_workspace_root()
    if workspace_path is None:
        console.print("[red]Could not find workspace root. Run from within a workspace or specify --path.[/red]")
        raise typer.Exit(1)

    claude_config = load_claude_code_config(offline=offline)
    if claude_config is None:
        console.print("[red]Failed to load Claude Code configuration[/red]")
        raise typer.Exit(1)

    console.print("[bold blue]Claude Code Setup[/bold blue]")
    console.print(f"Workspace: {workspace_path}")

    return setup_claude_config(claude_config, workspace_path)
