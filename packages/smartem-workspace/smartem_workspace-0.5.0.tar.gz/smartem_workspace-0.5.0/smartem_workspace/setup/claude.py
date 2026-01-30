"""Claude Code configuration setup."""

import json
import os
from pathlib import Path

from rich.console import Console

from smartem_workspace.config.schema import ClaudeCodeConfig

console = Console()


def setup_claude_config(
    config: ClaudeCodeConfig,
    workspace_path: Path,
) -> bool:
    """
    Set up Claude Code configuration.

    Creates:
    - claude-config/ symlink to smartem-devtools/claude-code
    - .claude/skills/ symlinks to skills
    - .claude/settings.local.json

    Returns:
        True if successful
    """
    console.print()
    console.print("[bold]Setting up Claude Code configuration...[/bold]")

    devtools_path = workspace_path / "repos" / "DiamondLightSource" / "smartem-devtools"
    if not devtools_path.exists():
        console.print("[red]smartem-devtools not found. Clone it first.[/red]")
        return False

    claude_config_source = devtools_path / "claude-code"
    if not claude_config_source.exists():
        console.print(f"[yellow]claude-code directory not found in {devtools_path}[/yellow]")

    claude_config_link = workspace_path / "claude-config"
    if not claude_config_link.exists() and claude_config_source.exists():
        try:
            os.symlink(str(claude_config_source.resolve()), str(claude_config_link))
            console.print(f"  [green]Created symlink: claude-config -> {claude_config_source}[/green]")
        except OSError as e:
            console.print(f"  [yellow]Could not create claude-config symlink: {e}[/yellow]")

    claude_dir = workspace_path / ".claude"
    claude_dir.mkdir(parents=True, exist_ok=True)

    skills_dir = claude_dir / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)

    for skill in config.claudeConfig.skills:
        skill_source = devtools_path / skill.path
        skill_link = skills_dir / skill.name

        if skill_link.exists():
            console.print(f"  [dim]Skill {skill.name} already linked[/dim]")
            continue

        if skill_source.exists():
            try:
                os.symlink(str(skill_source.resolve()), str(skill_link))
                console.print(f"  [green]Linked skill: {skill.name}[/green]")
            except OSError as e:
                console.print(f"  [yellow]Could not link skill {skill.name}: {e}[/yellow]")
        else:
            console.print(f"  [dim]Skill source not found: {skill_source}[/dim]")

    settings_path = claude_dir / "settings.local.json"
    if not settings_path.exists():
        settings = {
            "permissions": config.claudeConfig.defaultPermissions.model_dump(),
        }
        settings_path.write_text(json.dumps(settings, indent=2))
        console.print(f"  [green]Created {settings_path.name}[/green]")
    else:
        console.print(f"  [dim]{settings_path.name} already exists[/dim]")

    claude_md_source = devtools_path / "claude-code" / "CLAUDE.md"
    claude_md_target = workspace_path / "CLAUDE.md"

    if claude_md_source.exists() and not claude_md_target.exists():
        try:
            os.symlink(str(claude_md_source.resolve()), str(claude_md_target))
            console.print("  [green]Created symlink: CLAUDE.md[/green]")
        except OSError as e:
            console.print(f"  [yellow]Could not create CLAUDE.md symlink: {e}[/yellow]")
    elif claude_md_target.exists():
        console.print("  [dim]CLAUDE.md already exists[/dim]")

    console.print("[green]Claude Code configuration complete[/green]")
    return True
