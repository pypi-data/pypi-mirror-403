"""Configuration loading with network-first, bundled fallback strategy."""

import json
from importlib import resources

import httpx
from rich.console import Console

from smartem_workspace.config.schema import ClaudeCodeConfig, ReposConfig

GITHUB_RAW_BASE = "https://raw.githubusercontent.com/DiamondLightSource/smartem-devtools/main/core"
REPOS_CONFIG_URL = f"{GITHUB_RAW_BASE}/repos.json"
CLAUDE_CODE_CONFIG_URL = f"{GITHUB_RAW_BASE}/claude-code-config.json"
REQUEST_TIMEOUT = 10.0

console = Console()


def _load_json_from_network(url: str) -> dict | None:
    """Attempt to load JSON config from a URL."""
    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            response = client.get(url)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        console.print(f"[dim]Network fetch failed: {e}[/dim]")
        return None
    except json.JSONDecodeError as e:
        console.print(f"[dim]Invalid JSON from network: {e}[/dim]")
        return None


def _load_json_from_bundled(filename: str) -> dict | None:
    """Load bundled fallback config by filename."""
    try:
        config_path = resources.files("smartem_workspace.config").joinpath(filename)
        with resources.as_file(config_path) as path:
            if path.exists():
                return json.loads(path.read_text())
    except Exception as e:
        console.print(f"[dim]Bundled config load failed: {e}[/dim]")

    return None


def load_config(offline: bool = False) -> ReposConfig | None:
    """
    Load workspace repository configuration.

    Strategy:
    1. If offline, use bundled config
    2. Try network (GitHub raw)
    3. Fall back to bundled config

    Args:
        offline: Skip network fetch, use bundled config

    Returns:
        ReposConfig if successful, None otherwise
    """
    config_dict: dict | None = None

    if offline:
        console.print("[dim]Using bundled config (offline mode)[/dim]")
        config_dict = _load_json_from_bundled("repos.json")
    else:
        console.print("[dim]Fetching latest config from GitHub...[/dim]")
        config_dict = _load_json_from_network(REPOS_CONFIG_URL)

        if config_dict is None:
            console.print("[dim]Using bundled fallback config[/dim]")
            config_dict = _load_json_from_bundled("repos.json")

    if config_dict is None:
        console.print("[red]Failed to load configuration from any source[/red]")
        return None

    try:
        return ReposConfig.model_validate(config_dict)
    except Exception as e:
        console.print(f"[red]Configuration validation failed: {e}[/red]")
        return None


def load_claude_code_config(offline: bool = False) -> ClaudeCodeConfig | None:
    """
    Load Claude Code integration configuration.

    Strategy:
    1. If offline, use bundled config
    2. Try network (GitHub raw)
    3. Fall back to bundled config

    Args:
        offline: Skip network fetch, use bundled config

    Returns:
        ClaudeCodeConfig if successful, None otherwise
    """
    config_dict: dict | None = None

    if offline:
        console.print("[dim]Using bundled Claude Code config (offline mode)[/dim]")
        config_dict = _load_json_from_bundled("claude-code-config.json")
    else:
        console.print("[dim]Fetching Claude Code config from GitHub...[/dim]")
        config_dict = _load_json_from_network(CLAUDE_CODE_CONFIG_URL)

        if config_dict is None:
            console.print("[dim]Using bundled fallback Claude Code config[/dim]")
            config_dict = _load_json_from_bundled("claude-code-config.json")

    if config_dict is None:
        console.print("[red]Failed to load Claude Code configuration[/red]")
        return None

    try:
        return ClaudeCodeConfig.model_validate(config_dict)
    except Exception as e:
        console.print(f"[red]Claude Code configuration validation failed: {e}[/red]")
        return None
