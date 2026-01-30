"""Tests for configuration loading and schema."""

import json
from pathlib import Path

from smartem_workspace.config.schema import ReposConfig


def get_bundled_config_path() -> Path:
    """Get path to the bundled repos.json."""
    return Path(__file__).parent.parent / "smartem_workspace" / "config" / "repos.json"


class TestReposConfig:
    """Tests for ReposConfig schema."""

    def test_bundled_config_exists(self) -> None:
        """Bundled config file should exist."""
        config_path = get_bundled_config_path()
        assert config_path.exists(), f"Bundled config not found at {config_path}"

    def test_bundled_config_valid_json(self) -> None:
        """Bundled config should be valid JSON."""
        config_path = get_bundled_config_path()
        with open(config_path) as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_bundled_config_validates(self) -> None:
        """Bundled config should pass Pydantic validation."""
        config_path = get_bundled_config_path()
        with open(config_path) as f:
            data = json.load(f)
        config = ReposConfig.model_validate(data)
        assert config.version == "1.0.0"

    def test_config_has_organizations(self) -> None:
        """Config should have organizations defined."""
        config_path = get_bundled_config_path()
        with open(config_path) as f:
            data = json.load(f)
        config = ReposConfig.model_validate(data)
        assert len(config.organizations) > 0

    def test_config_has_presets(self) -> None:
        """Config should have presets defined."""
        config_path = get_bundled_config_path()
        with open(config_path) as f:
            data = json.load(f)
        config = ReposConfig.model_validate(data)
        assert "smartem-core" in config.presets
        assert "full" in config.presets
        assert "minimal" in config.presets

    def test_resolve_smartem_core_preset(self) -> None:
        """smartem-core preset should resolve to expected repos."""
        config_path = get_bundled_config_path()
        with open(config_path) as f:
            data = json.load(f)
        config = ReposConfig.model_validate(data)

        repos = config.resolve_preset("smartem-core")
        repo_names = [repo.name for _, repo in repos]

        assert "smartem-decisions" in repo_names
        assert "smartem-frontend" in repo_names
        assert "smartem-devtools" in repo_names

    def test_resolve_minimal_preset(self) -> None:
        """minimal preset should resolve to just smartem-devtools."""
        config_path = get_bundled_config_path()
        with open(config_path) as f:
            data = json.load(f)
        config = ReposConfig.model_validate(data)

        repos = config.resolve_preset("minimal")
        assert len(repos) == 1
        assert repos[0][1].name == "smartem-devtools"

    def test_get_organization(self) -> None:
        """Should be able to get organization by name."""
        config_path = get_bundled_config_path()
        with open(config_path) as f:
            data = json.load(f)
        config = ReposConfig.model_validate(data)

        dls = config.get_organization("DiamondLightSource")
        assert dls is not None
        assert dls.provider == "github"

        aria = config.get_organization("aria-php")
        assert aria is not None
        assert aria.provider == "gitlab"

    def test_unknown_organization_returns_none(self) -> None:
        """Unknown organization should return None."""
        config_path = get_bundled_config_path()
        with open(config_path) as f:
            data = json.load(f)
        config = ReposConfig.model_validate(data)

        assert config.get_organization("NonExistent") is None

    def test_unknown_preset_returns_empty(self) -> None:
        """Unknown preset should return empty list."""
        config_path = get_bundled_config_path()
        with open(config_path) as f:
            data = json.load(f)
        config = ReposConfig.model_validate(data)

        repos = config.resolve_preset("nonexistent")
        assert repos == []
