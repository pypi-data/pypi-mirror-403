"""Rich-based interactive prompts for repo selection."""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from smartem_workspace.config.schema import Organization, ReposConfig, Repository

console = Console()


def select_preset(config: ReposConfig) -> str | None:
    """
    Prompt user to select a preset or custom selection.

    Returns:
        Preset name or None for custom selection
    """
    console.print()
    console.print("[bold]Available presets:[/bold]")

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Option", style="cyan", width=6)
    table.add_column("Preset", style="green")
    table.add_column("Description")
    table.add_column("Repos", justify="right")

    preset_names = list(config.presets.keys())
    for i, name in enumerate(preset_names, 1):
        preset = config.presets[name]
        repo_count = len(preset.repos) if preset.repos != ["*"] else "all"
        table.add_row(str(i), name, preset.description, str(repo_count))

    table.add_row(str(len(preset_names) + 1), "custom", "Select repos interactively", "-")

    console.print(table)
    console.print()

    choice = Prompt.ask(
        "Select option",
        choices=[str(i) for i in range(1, len(preset_names) + 2)],
        default="1",
    )

    choice_idx = int(choice) - 1
    if choice_idx < len(preset_names):
        return preset_names[choice_idx]
    return None


def select_repos(config: ReposConfig) -> list[tuple[Organization, Repository]]:
    """
    Interactively select repositories, grouped by organization.

    Returns:
        List of (organization, repository) tuples
    """
    selected: list[tuple[Organization, Repository]] = []

    for org in config.organizations:
        console.print()
        console.print(Panel(f"[bold]{org.displayName}[/bold] ({org.url})", style="blue"))

        table = Table(show_header=True, header_style="bold")
        table.add_column("#", style="cyan", width=4)
        table.add_column("Repository", style="green")
        table.add_column("Description")
        table.add_column("Tags")
        table.add_column("Ownership")

        for i, repo in enumerate(org.repos, 1):
            tags = ", ".join(repo.tags) if repo.tags else "-"
            ownership = repo.ownership or "full"
            table.add_row(str(i), repo.name, repo.description, tags, ownership)

        console.print(table)

        if Confirm.ask(f"Include repos from {org.displayName}?", default=True):
            repo_input = Prompt.ask(
                "Enter repo numbers (comma-separated) or 'all'",
                default="all",
            )

            if repo_input.lower() == "all":
                for repo in org.repos:
                    selected.append((org, repo))
            else:
                try:
                    indices = [int(x.strip()) - 1 for x in repo_input.split(",")]
                    for idx in indices:
                        if 0 <= idx < len(org.repos):
                            selected.append((org, org.repos[idx]))
                except ValueError:
                    console.print("[yellow]Invalid input, skipping organization[/yellow]")

    return selected


def confirm(message: str, default: bool = True) -> bool:
    """Simple confirmation prompt."""
    return Confirm.ask(message, default=default)


def display_selection_summary(repos: list[tuple[Organization, Repository]]) -> None:
    """Display a summary of selected repositories."""
    if not repos:
        console.print("[yellow]No repositories selected[/yellow]")
        return

    console.print()
    console.print("[bold]Selected repositories:[/bold]")

    by_org: dict[str, list[Repository]] = {}
    for org, repo in repos:
        if org.name not in by_org:
            by_org[org.name] = []
        by_org[org.name].append(repo)

    for org_name, org_repos in by_org.items():
        console.print(f"  [cyan]{org_name}[/cyan]: {len(org_repos)} repos")
        for repo in org_repos:
            console.print(f"    - {repo.name}")

    console.print()
    console.print(f"[bold]Total: {len(repos)} repositories[/bold]")
