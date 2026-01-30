# smartem-workspace

[![PyPI version](https://img.shields.io/pypi/v/smartem-workspace)](https://pypi.org/project/smartem-workspace/)
[![Python Versions](https://img.shields.io/pypi/pyversions/smartem-workspace.svg)](https://pypi.org/project/smartem-workspace/)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![CI](https://github.com/DiamondLightSource/smartem-devtools/actions/workflows/release-smartem-workspace.yml/badge.svg)](https://github.com/DiamondLightSource/smartem-devtools/actions/workflows/release-smartem-workspace.yml)

CLI tool to automate SmartEM multi-repo workspace setup.

## Installation

```bash
# Run directly with uvx (recommended)
uvx smartem-workspace init

# Or install globally
uv tool install smartem-workspace
```

## Usage

### Global options

```
--no-color          Disable colored output
--plain             Plain mode: no color, no interactive prompts
```

### Initialize a new workspace

```bash
# Interactive setup in current directory
smartem-workspace init

# Specify target directory
smartem-workspace init --path ~/dev/smartem

# Use a preset (skip repo selection)
smartem-workspace init --preset smartem-core

# Non-interactive with preset
smartem-workspace init --preset full --no-interactive
```

### Available presets

| Preset | Description |
|--------|-------------|
| `smartem-core` | Core SmartEM repos (decisions, frontend, devtools) |
| `full` | All 30+ repos including ARIA reference |
| `aria-reference` | ARIA ecosystem repos for reference |
| `minimal` | Just smartem-devtools (workspace setup only) |

### Verify workspace setup

```bash
# Check all configuration
smartem-workspace check

# Check specific scope
smartem-workspace check --scope claude
smartem-workspace check --scope repos
smartem-workspace check --scope serena

# Auto-repair fixable issues (broken symlinks, missing dirs)
smartem-workspace check --fix
```

### Sync repositories

```bash
# Pull latest from all cloned repos
smartem-workspace sync

# Preview what would be pulled
smartem-workspace sync --dry-run
```

Sync skips repos with uncommitted changes or not on main/master branch.

### Other commands

```bash
# Show workspace status (alias for check)
smartem-workspace status

# Set up Claude Code integration (after init without --with-claude)
smartem-workspace claude setup

# Add a single repo (not yet implemented)
smartem-workspace add DiamondLightSource/smartem-frontend
```

### Init options

```
--path PATH         Target directory (default: current directory)
--preset NAME       Use preset: smartem-core, full, aria-reference, minimal
--no-interactive    Skip prompts, use preset only
--git-ssh           Force SSH URLs for all repos
--git-https         Force HTTPS URLs (skip auto-detection)
--with-claude       Enable Claude Code integration setup
--skip-serena       Skip Serena MCP setup
--skip-dev-requirements  Skip developer requirements check
```

**Git URL auto-detection:** By default, the CLI automatically detects if you have SSH authentication configured for GitHub. If SSH works, repos are cloned via SSH (enabling push); otherwise HTTPS is used (read-only). Use `--git-ssh` or `--git-https` to override.

### Check options

```
--scope SCOPE       Check scope: dev-requirements, claude, repos, serena, or all (default: all)
--fix               Attempt to fix issues (recreate symlinks, dirs)
--offline           Use bundled config instead of fetching from GitHub
```

### Sync options

```
--dry-run, -n       Show what would be done without making changes
```

## What it sets up

1. **Repository clones** - Organized by organization (DiamondLightSource, FragmentScreen, GitlabAriaPHP)
2. **Claude Code configuration** (with `--with-claude`) - Skills, settings, permissions
3. **Serena MCP server** - Semantic code navigation
4. **Workspace structure** - tmp/, testdata/ directories

## Documentation

- **User Guide**: [Setup SmartEM Workspace](https://diamondlightsource.github.io/smartem-devtools/how-to/setup-smartem-workspace.html)
- **Developer Guide**: [Contributing to smartem-workspace](https://diamondlightsource.github.io/smartem-devtools/explanations/smartem-workspace-developer-guide.html)
- **PyPI Setup**: [Publishing to PyPI](https://diamondlightsource.github.io/smartem-devtools/how-to/publish-smartem-workspace-to-pypi.html)
- **API Documentation**: [SmartEM Devtools Docs](https://diamondlightsource.github.io/smartem-devtools/)

## Development

```bash
cd packages/smartem-workspace

# Install dev dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Run linter
uv run ruff check .

# Build package
uv build
```

See [Developer Guide](../../docs/explanations/smartem-workspace-developer-guide.md) for detailed development instructions.

## Releasing

Releases are published to PyPI via GitHub Actions using [Trusted Publishers](https://docs.pypi.org/trusted-publishers/).

```bash
# 1. Update version in pyproject.toml
# 2. Commit the change
git commit -am "chore: release smartem-workspace vX.Y.Z"

# 3. Create and push a version tag
git tag smartem-workspace-vX.Y.Z
git push origin main --tags
```

The CI workflow runs tests, builds the package, and publishes to PyPI automatically on tag push.

## Links

- **PyPI**: https://pypi.org/project/smartem-workspace/
- **Repository**: https://github.com/DiamondLightSource/smartem-devtools
- **Issues**: https://github.com/DiamondLightSource/smartem-devtools/issues
- **Changelog**: [GitHub Releases](https://github.com/DiamondLightSource/smartem-devtools/releases?q=smartem-workspace)

## License

Apache-2.0
