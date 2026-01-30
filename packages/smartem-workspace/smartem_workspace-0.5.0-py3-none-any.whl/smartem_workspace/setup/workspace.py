"""Workspace directory structure setup."""

from pathlib import Path

from rich.console import Console

console = Console()


def setup_workspace_structure(workspace_path: Path) -> bool:
    """
    Set up the basic workspace directory structure.

    Creates:
    - repos/
    - tmp/
    - testdata/

    Returns:
        True if successful
    """
    console.print()
    console.print("[bold]Setting up workspace structure...[/bold]")

    directories = [
        "repos",
        "tmp",
        "testdata",
    ]

    for dir_name in directories:
        dir_path = workspace_path / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            console.print(f"  [green]Created {dir_name}/[/green]")
        else:
            console.print(f"  [dim]{dir_name}/ already exists[/dim]")

    console.print("[green]Workspace structure complete[/green]")
    return True


def display_next_steps(workspace_path: Path) -> None:
    """Display post-setup instructions."""
    console.print()
    console.print("[bold green]Workspace setup complete![/bold green]")
    console.print()
    console.print("[bold]Next steps:[/bold]")
    console.print(f"  1. cd {workspace_path}")
    console.print("  2. Open in your IDE (e.g., code .)")
    console.print("  3. If using Claude Code, it will auto-detect the configuration")
    console.print()
    console.print("[bold]Useful links:[/bold]")
    console.print("  - Docs: https://diamondlightsource.github.io/smartem-decisions/")
    console.print("  - Project Board: https://github.com/orgs/DiamondLightSource/projects/51/views/1")
