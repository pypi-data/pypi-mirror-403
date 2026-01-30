"""Workspace verification and repair command."""

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from importlib import resources
from pathlib import Path
from typing import Literal

import httpx
from rich.console import Console

from smartem_workspace.config.schema import ClaudeCodeConfig, ReposConfig
from smartem_workspace.setup.repos import get_local_dir

console = Console()

DEV_REQUIREMENTS_URL = (
    "https://raw.githubusercontent.com/DiamondLightSource/smartem-devtools/main/core/dev-requirements.json"
)


class CheckScope(str, Enum):
    ALL = "all"
    CLAUDE = "claude"
    REPOS = "repos"
    SERENA = "serena"
    DEV_REQUIREMENTS = "dev-requirements"


@dataclass
class CheckResult:
    name: str
    status: Literal["ok", "warning", "error"]
    message: str
    fixable: bool = False
    fix_data: dict = field(default_factory=dict)


@dataclass
class CheckReport:
    scope: str
    results: list[CheckResult]

    @property
    def has_errors(self) -> bool:
        return any(r.status == "error" for r in self.results)

    @property
    def has_warnings(self) -> bool:
        return any(r.status == "warning" for r in self.results)

    @property
    def fixable_count(self) -> int:
        return sum(1 for r in self.results if r.fixable)


def _load_dev_requirements() -> dict | None:
    """Load dev-requirements.json from network or bundled fallback."""
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(DEV_REQUIREMENTS_URL)
            response.raise_for_status()
            return response.json()
    except (httpx.HTTPError, json.JSONDecodeError):
        pass

    try:
        config_path = resources.files("smartem_workspace.config").joinpath("dev-requirements.json")
        with resources.as_file(config_path) as path:
            if path.exists():
                return json.loads(path.read_text())
    except Exception:
        pass

    return None


def _parse_version(version_str: str) -> tuple[int, ...] | None:
    """Extract version numbers from a version string."""
    match = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", version_str)
    if match:
        parts = [int(p) for p in match.groups() if p is not None]
        return tuple(parts)
    return None


def _compare_versions(actual: str, min_version: str) -> bool:
    """Check if actual version meets minimum requirement."""
    actual_parts = _parse_version(actual)
    min_parts = _parse_version(min_version)

    if not actual_parts or not min_parts:
        return True

    for a, m in zip(actual_parts, min_parts, strict=False):
        if a > m:
            return True
        if a < m:
            return False
    return len(actual_parts) >= len(min_parts)


def check_tool(tool: dict) -> CheckResult:
    """Check a tool prerequisite from JSON definition."""
    name = tool["name"]
    command = tool["command"]
    version_args = tool.get("versionArgs", ["--version"])
    required = tool.get("required", False)
    min_version = tool.get("minVersion")
    alternatives = tool.get("alternatives", [])

    commands_to_try = [command] + alternatives
    found_command = None
    version_output = None

    for cmd in commands_to_try:
        cmd_path = shutil.which(cmd)
        if cmd_path:
            found_command = cmd
            try:
                result = subprocess.run(
                    [cmd] + version_args,
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    version_output = result.stdout.strip() or result.stderr.strip()
                    break
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue

    if not found_command:
        status = "error" if required else "warning"
        return CheckResult(name, status, "Not found in PATH")

    if version_output:
        display_version = version_output.split("\n")[0][:60]

        if min_version:
            if _compare_versions(version_output, min_version):
                return CheckResult(name, "ok", display_version)
            status = "error" if required else "warning"
            return CheckResult(name, status, f"{display_version} (requires {min_version}+)")

        return CheckResult(name, "ok", display_version)

    return CheckResult(name, "ok", f"Found: {found_command}")


def check_network(network_config: dict) -> CheckResult:
    """Check network connectivity based on JSON definition."""
    url = network_config.get("checkUrl", "https://github.com")
    timeout = network_config.get("timeout", 5)
    required = network_config.get("required", False)

    try:
        with httpx.Client(timeout=float(timeout)) as client:
            response = client.head(url)
            if response.status_code < 400:
                return CheckResult("Network", "ok", f"{url} reachable")
            status = "error" if required else "warning"
            return CheckResult("Network", status, f"{url} returned {response.status_code}")
    except httpx.RequestError:
        status = "error" if required else "warning"
        return CheckResult("Network", status, f"Cannot reach {url}")


def run_dev_requirements_checks() -> CheckReport:
    """Run all developer requirements checks from dev-requirements.json."""
    config = _load_dev_requirements()
    results = []

    if config is None:
        results.append(CheckResult("dev-requirements.json", "error", "Failed to load configuration"))
        return CheckReport("dev-requirements", results)

    for tool in config.get("tools", []):
        results.append(check_tool(tool))

    if "network" in config:
        results.append(check_network(config["network"]))

    return CheckReport("dev-requirements", results)


def check_devtools_present(workspace_path: Path) -> CheckResult:
    devtools_path = workspace_path / "repos" / "DiamondLightSource" / "smartem-devtools"
    if devtools_path.exists() and (devtools_path / ".git").exists():
        return CheckResult("smartem-devtools", "ok", "Present and valid")
    if devtools_path.exists():
        return CheckResult("smartem-devtools", "error", "Directory exists but not a git repo")
    return CheckResult(
        "smartem-devtools",
        "error",
        "Not cloned (required for configuration)",
        fixable=False,
    )


def check_symlink(link_path: Path, expected_target: Path, name: str) -> CheckResult:
    if not link_path.exists() and not link_path.is_symlink():
        return CheckResult(
            name,
            "warning",
            "Missing",
            fixable=True,
            fix_data={"link": str(link_path), "target": str(expected_target)},
        )

    if link_path.is_symlink():
        actual_target = link_path.resolve()
        if actual_target == expected_target.resolve():
            return CheckResult(name, "ok", "Valid symlink")
        return CheckResult(
            name,
            "warning",
            "Points to wrong target",
            fixable=True,
            fix_data={"link": str(link_path), "target": str(expected_target)},
        )

    if link_path.is_file():
        return CheckResult(name, "ok", "Present as file (acceptable)")

    return CheckResult(name, "warning", "Unexpected state", fixable=False)


def check_file_exists(file_path: Path, name: str) -> CheckResult:
    if file_path.exists():
        return CheckResult(name, "ok", "Present")
    return CheckResult(name, "warning", f"Missing: {file_path.name}", fixable=False)


def check_json_valid(file_path: Path, name: str) -> CheckResult:
    if not file_path.exists():
        return CheckResult(name, "warning", "File missing", fixable=False)
    try:
        json.loads(file_path.read_text())
        return CheckResult(name, "ok", "Valid JSON")
    except json.JSONDecodeError as e:
        return CheckResult(name, "error", f"Invalid JSON: {e}")


def run_claude_checks(workspace_path: Path, claude_config: ClaudeCodeConfig) -> CheckReport:
    """Check Claude Code integration setup."""
    results = []
    devtools_path = workspace_path / "repos" / "DiamondLightSource" / "smartem-devtools"

    results.append(check_devtools_present(workspace_path))

    claude_config_link = workspace_path / "claude-config"
    claude_config_target = devtools_path / "claude-code"
    results.append(check_symlink(claude_config_link, claude_config_target, "claude-config symlink"))

    claude_md_link = workspace_path / "CLAUDE.md"
    claude_md_target = devtools_path / "claude-code" / "CLAUDE.md"
    results.append(check_symlink(claude_md_link, claude_md_target, "CLAUDE.md"))

    skills_dir = workspace_path / ".claude" / "skills"
    if not skills_dir.exists():
        results.append(
            CheckResult(
                ".claude/skills directory",
                "warning",
                "Missing",
                fixable=True,
                fix_data={"mkdir": str(skills_dir)},
            )
        )
    else:
        results.append(CheckResult(".claude/skills directory", "ok", "Present"))

    for skill in claude_config.claudeConfig.skills:
        skill_link = skills_dir / skill.name
        skill_target = devtools_path / skill.path
        results.append(check_symlink(skill_link, skill_target, f"skill: {skill.name}"))

    settings_path = workspace_path / ".claude" / "settings.local.json"
    if settings_path.exists():
        results.append(check_json_valid(settings_path, "settings.local.json"))
    else:
        results.append(CheckResult("settings.local.json", "warning", "Missing (not auto-fixable)", fixable=False))

    return CheckReport("claude", results)


def run_serena_checks(workspace_path: Path) -> CheckReport:
    results = []

    serena_dir = workspace_path / ".serena"
    if serena_dir.exists():
        results.append(CheckResult(".serena directory", "ok", "Present"))
    else:
        results.append(CheckResult(".serena directory", "warning", "Missing", fixable=False))

    project_yml = workspace_path / ".serena" / "project.yml"
    results.append(check_file_exists(project_yml, ".serena/project.yml"))

    mcp_json = workspace_path / ".mcp.json"
    if mcp_json.exists():
        results.append(check_json_valid(mcp_json, ".mcp.json"))
    else:
        results.append(CheckResult(".mcp.json", "warning", "Missing", fixable=False))

    return CheckReport("serena", results)


def run_repos_checks(workspace_path: Path, config: ReposConfig) -> CheckReport:
    results = []
    repos_dir = workspace_path / "repos"

    if not repos_dir.exists():
        results.append(CheckResult("repos directory", "error", "Missing"))
        return CheckReport("repos", results)

    results.append(CheckResult("repos directory", "ok", "Present"))

    for org in config.organizations:
        local_dir = get_local_dir(org)
        org_dir = repos_dir / local_dir

        for repo in org.repos:
            repo_path = org_dir / repo.name
            full_name = f"{org.name}/{repo.name}"

            if not repo_path.exists():
                results.append(CheckResult(full_name, "warning", "Not cloned", fixable=False))
                continue

            if not (repo_path / ".git").exists():
                results.append(CheckResult(full_name, "error", "Not a git repository"))
                continue

            results.append(CheckResult(full_name, "ok", "Cloned"))

    return CheckReport("repos", results)


def run_checks(
    workspace_path: Path | None,
    config: ReposConfig | None,
    scope: CheckScope = CheckScope.ALL,
    claude_config: ClaudeCodeConfig | None = None,
) -> list[CheckReport]:
    reports = []

    if scope in (CheckScope.ALL, CheckScope.DEV_REQUIREMENTS):
        reports.append(run_dev_requirements_checks())

    if scope in (CheckScope.ALL, CheckScope.CLAUDE) and workspace_path and claude_config:
        reports.append(run_claude_checks(workspace_path, claude_config))

    if scope in (CheckScope.ALL, CheckScope.SERENA) and workspace_path:
        reports.append(run_serena_checks(workspace_path))

    if scope in (CheckScope.ALL, CheckScope.REPOS) and workspace_path and config:
        reports.append(run_repos_checks(workspace_path, config))

    return reports


def apply_fixes(workspace_path: Path, reports: list[CheckReport]) -> tuple[int, int]:
    fixed = 0
    failed = 0

    for report in reports:
        for result in report.results:
            if not result.fixable or result.status == "ok":
                continue

            fix_data = result.fix_data

            if "mkdir" in fix_data:
                try:
                    Path(fix_data["mkdir"]).mkdir(parents=True, exist_ok=True)
                    console.print(f"  [green]Created directory: {fix_data['mkdir']}[/green]")
                    fixed += 1
                except OSError as e:
                    console.print(f"  [red]Failed to create directory: {e}[/red]")
                    failed += 1

            elif "link" in fix_data and "target" in fix_data:
                link_path = Path(fix_data["link"])
                target_path = Path(fix_data["target"])

                try:
                    if link_path.is_symlink():
                        link_path.unlink()

                    link_path.parent.mkdir(parents=True, exist_ok=True)

                    if target_path.exists():
                        os.symlink(str(target_path.resolve()), str(link_path))
                        console.print(f"  [green]Created symlink: {link_path.name}[/green]")
                        fixed += 1
                    else:
                        console.print(f"  [yellow]Target does not exist: {target_path}[/yellow]")
                        failed += 1
                except OSError as e:
                    console.print(f"  [red]Failed to create symlink: {e}[/red]")
                    failed += 1

    return fixed, failed


def print_report(report: CheckReport) -> None:
    title = report.scope.replace("-", " ").title()
    console.print(f"\n[bold]{title}:[/bold]")

    for result in report.results:
        if result.status == "ok":
            icon = "[green]\u2713[/green]"
        elif result.status == "warning":
            icon = "[yellow]![/yellow]"
        else:
            icon = "[red]\u2717[/red]"

        fixable_note = " [dim](fixable)[/dim]" if result.fixable and result.status != "ok" else ""
        console.print(f"  {icon} {result.name}: {result.message}{fixable_note}")
