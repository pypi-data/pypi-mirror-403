"""CLI commands for smartem-workspace."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from smartem_workspace import __version__
from smartem_workspace.commands.check import (
    CheckScope,
    apply_fixes,
    print_report,
    run_checks,
    run_dev_requirements_checks,
)
from smartem_workspace.commands.claude import setup as claude_setup_fn
from smartem_workspace.commands.sync import print_sync_results, sync_all_repos
from smartem_workspace.config.loader import load_claude_code_config, load_config
from smartem_workspace.setup.bootstrap import bootstrap_workspace
from smartem_workspace.utils.paths import find_workspace_root

app = typer.Typer(
    name="smartem-workspace",
    help="CLI tool to automate SmartEM multi-repo workspace setup",
    no_args_is_help=True,
)

claude_app = typer.Typer(
    name="claude",
    help="Claude Code integration commands",
    no_args_is_help=True,
)
app.add_typer(claude_app, name="claude")

console = Console()


class CliState:
    """Global CLI state for color and interactivity settings."""

    no_color: bool = False
    plain: bool = False


cli_state = CliState()


def get_console() -> Console:
    """Get a console instance respecting global color settings."""
    if cli_state.no_color or cli_state.plain:
        return Console(color_system=None)
    return console


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"smartem-workspace {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-V",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit",
        ),
    ] = False,
    no_color: Annotated[
        bool,
        typer.Option("--no-color", help="Disable colored output"),
    ] = False,
    plain: Annotated[
        bool,
        typer.Option("--plain", help="Plain mode: no color, no interactive prompts"),
    ] = False,
) -> None:
    """SmartEM workspace CLI tool."""
    cli_state.no_color = no_color
    cli_state.plain = plain


@app.command()
def init(
    path: Annotated[
        Path | None,
        typer.Option("--path", "-p", help="Target directory for workspace"),
    ] = None,
    preset: Annotated[
        str | None,
        typer.Option("--preset", help="Use preset: smartem-core, full, aria-reference, minimal"),
    ] = None,
    interactive: Annotated[
        bool,
        typer.Option("--interactive/--no-interactive", help="Enable/disable interactive prompts"),
    ] = True,
    git_ssh: Annotated[
        bool,
        typer.Option("--git-ssh", help="Force SSH URLs for all repos"),
    ] = False,
    git_https: Annotated[
        bool,
        typer.Option("--git-https", help="Force HTTPS URLs (skip auto-detection)"),
    ] = False,
    with_claude: Annotated[
        bool,
        typer.Option("--with-claude", help="Enable Claude Code integration setup"),
    ] = False,
    skip_serena: Annotated[
        bool,
        typer.Option("--skip-serena", help="Skip Serena MCP setup"),
    ] = False,
    skip_dev_requirements: Annotated[
        bool,
        typer.Option("--skip-dev-requirements", help="Skip developer requirements check"),
    ] = False,
) -> None:
    """Initialize a new SmartEM workspace."""
    out = get_console()
    out.print("[bold blue]SmartEM Workspace Setup[/bold blue]")

    effective_interactive = interactive and not cli_state.plain

    if not skip_dev_requirements:
        dev_reqs_report = run_dev_requirements_checks()
        print_report(dev_reqs_report)
        if dev_reqs_report.has_errors:
            out.print("\n[red]Developer requirements check failed. Fix the errors above before continuing.[/red]")
            raise typer.Exit(1)
        out.print()

    workspace_path = path or Path.cwd()
    out.print(f"Target: {workspace_path.absolute()}")

    config = load_config()
    if config is None:
        out.print("[red]Failed to load configuration[/red]")
        raise typer.Exit(1)

    skip_claude = not with_claude
    claude_config = None
    if with_claude:
        claude_config = load_claude_code_config()
        if claude_config is None:
            out.print("[red]Failed to load Claude Code configuration[/red]")
            raise typer.Exit(1)

    # Determine use_ssh: True=force SSH, False=force HTTPS, None=auto-detect
    use_ssh: bool | None = None
    if git_ssh and git_https:
        out.print("[red]Cannot specify both --git-ssh and --git-https[/red]")
        raise typer.Exit(1)
    elif git_ssh:
        use_ssh = True
    elif git_https:
        use_ssh = False

    bootstrap_workspace(
        config=config,
        workspace_path=workspace_path,
        preset=preset,
        interactive=effective_interactive,
        use_ssh=use_ssh,
        skip_claude=skip_claude,
        skip_serena=skip_serena,
        claude_config=claude_config,
    )


@app.command()
def check(
    scope: Annotated[
        str | None,
        typer.Option("--scope", "-s", help="Check scope: dev-requirements, claude, repos, serena, or all"),
    ] = None,
    fix: Annotated[
        bool,
        typer.Option("--fix", help="Attempt to fix issues"),
    ] = False,
    path: Annotated[
        Path | None,
        typer.Option("--path", "-p", help="Workspace path (auto-detected if not specified)"),
    ] = None,
    offline: Annotated[
        bool,
        typer.Option("--offline", help="Use bundled config instead of fetching from GitHub"),
    ] = False,
) -> None:
    """Verify workspace setup and optionally repair issues."""
    out = get_console()
    check_scope = CheckScope.ALL
    if scope:
        try:
            check_scope = CheckScope(scope.lower())
        except ValueError:
            out.print(f"[red]Invalid scope: {scope}. Use: dev-requirements, claude, repos, serena, or all[/red]")
            raise typer.Exit(1) from None

    if check_scope == CheckScope.DEV_REQUIREMENTS:
        out.print("[bold]Checking developer requirements...[/bold]")
        reports = run_checks(None, None, check_scope)
    else:
        workspace_path = path or find_workspace_root()
        if workspace_path is None:
            out.print("[red]Could not find workspace root. Run from within a workspace or specify --path.[/red]")
            raise typer.Exit(1)

        config = load_config(offline=offline)
        if config is None:
            out.print("[red]Failed to load configuration[/red]")
            raise typer.Exit(1)

        claude_config = None
        if check_scope in (CheckScope.ALL, CheckScope.CLAUDE):
            claude_config = load_claude_code_config(offline=offline)

        out.print(f"[bold]Checking workspace at {workspace_path}...[/bold]")
        reports = run_checks(workspace_path, config, check_scope, claude_config)

    for report in reports:
        print_report(report)

    total_errors = sum(r.has_errors for r in reports)
    total_warnings = sum(r.has_warnings for r in reports)
    total_fixable = sum(r.fixable_count for r in reports)

    out.print()
    if total_errors or total_warnings:
        parts = []
        if total_errors:
            parts.append(f"[red]{total_errors} error(s)[/red]")
        if total_warnings:
            parts.append(f"[yellow]{total_warnings} warning(s)[/yellow]")
        out.print(f"Summary: {', '.join(parts)}")

        if fix and total_fixable and check_scope != CheckScope.DEV_REQUIREMENTS:
            out.print("\n[bold]Applying fixes...[/bold]")
            fixed, failed = apply_fixes(workspace_path, reports)
            out.print(f"\nFixed {fixed} issue(s), {failed} failed")
            if failed:
                raise typer.Exit(1)
        elif total_fixable and not fix and check_scope != CheckScope.DEV_REQUIREMENTS:
            out.print(f"\n[dim]{total_fixable} issue(s) can be fixed with --fix[/dim]")
            raise typer.Exit(1)
        elif total_errors:
            raise typer.Exit(1)
    else:
        out.print("[green]All checks passed![/green]")


@app.command()
def sync(
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", "-n", help="Show what would be done without making changes"),
    ] = False,
    git_ssh: Annotated[
        bool,
        typer.Option("--git-ssh", help="Force SSH URLs for cloning (default: auto-detect)"),
    ] = False,
    git_https: Annotated[
        bool,
        typer.Option("--git-https", help="Force HTTPS URLs for cloning (default: auto-detect)"),
    ] = False,
    path: Annotated[
        Path | None,
        typer.Option("--path", "-p", help="Workspace path (auto-detected if not specified)"),
    ] = None,
) -> None:
    """Sync workspace: clone missing repos and pull updates for existing ones."""
    out = get_console()
    workspace_path = path or find_workspace_root()
    if workspace_path is None:
        out.print("[red]Could not find workspace root. Run from within a workspace or specify --path.[/red]")
        raise typer.Exit(1)

    config = load_config()
    if config is None:
        out.print("[red]Failed to load configuration[/red]")
        raise typer.Exit(1)

    if git_ssh and git_https:
        out.print("[red]Cannot specify both --git-ssh and --git-https[/red]")
        raise typer.Exit(1)

    use_ssh: bool | None = True if git_ssh else (False if git_https else None)

    out.print("[bold blue]SmartEM Workspace Sync[/bold blue]")
    out.print(f"Workspace: {workspace_path}")

    results = sync_all_repos(workspace_path, config, out, dry_run=dry_run, use_ssh=use_ssh)
    print_sync_results(results, out)

    errors = sum(1 for r in results if r.status == "error")
    if errors:
        raise typer.Exit(1)

    if dry_run:
        would_update = sum(1 for r in results if r.status == "dry-run")
        if would_update:
            out.print("\n[dim]Run without --dry-run to apply changes[/dim]")


@app.command()
def status(
    path: Annotated[
        Path | None,
        typer.Option("--path", "-p", help="Workspace path"),
    ] = None,
    offline: Annotated[
        bool,
        typer.Option("--offline", help="Use bundled config instead of fetching from GitHub"),
    ] = False,
) -> None:
    """Show workspace status (alias for check --scope all)."""
    out = get_console()
    workspace_path = path or find_workspace_root()
    if workspace_path is None:
        out.print("[red]Could not find workspace root.[/red]")
        raise typer.Exit(1)

    config = load_config(offline=offline)
    if config is None:
        out.print("[red]Failed to load configuration[/red]")
        raise typer.Exit(1)

    claude_config = load_claude_code_config(offline=offline)

    out.print(f"[bold]Workspace Status: {workspace_path}[/bold]")
    reports = run_checks(workspace_path, config, CheckScope.ALL, claude_config)

    for report in reports:
        print_report(report)


@app.command()
def add(
    repo: Annotated[str, typer.Argument(help="Repository to add (e.g., DiamondLightSource/smartem-frontend)")],
) -> None:
    """Add a single repository to the workspace."""
    out = get_console()
    out.print(f"[yellow]Not implemented yet: {repo}[/yellow]")
    raise typer.Exit(1)


@claude_app.command("setup")
def claude_setup(
    path: Annotated[
        Path | None,
        typer.Option("--path", "-p", help="Workspace path (auto-detected if not specified)"),
    ] = None,
    offline: Annotated[
        bool,
        typer.Option("--offline", help="Use bundled config instead of fetching from GitHub"),
    ] = False,
) -> None:
    """Set up Claude Code integration in the workspace."""
    claude_setup_fn(path=path, offline=offline)


if __name__ == "__main__":
    app()
