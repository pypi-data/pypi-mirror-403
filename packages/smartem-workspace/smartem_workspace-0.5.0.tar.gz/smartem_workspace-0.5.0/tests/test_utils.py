"""Tests for utility functions."""

from pathlib import Path

from smartem_workspace.utils.git import check_git_available
from smartem_workspace.utils.paths import ensure_directory, resolve_workspace_path


class TestGitUtils:
    """Tests for git utility functions."""

    def test_git_available(self) -> None:
        """Git should be available on the system."""
        assert check_git_available() is True


class TestPathUtils:
    """Tests for path utility functions."""

    def test_resolve_workspace_path_none(self) -> None:
        """None should resolve to current directory."""
        result = resolve_workspace_path(None)
        assert result == Path.cwd().resolve()

    def test_resolve_workspace_path_string(self) -> None:
        """String path should be resolved."""
        result = resolve_workspace_path("/tmp")
        assert result == Path("/tmp")

    def test_resolve_workspace_path_expands_tilde(self) -> None:
        """Tilde should be expanded."""
        result = resolve_workspace_path("~/test")
        assert "~" not in str(result)

    def test_ensure_directory(self, tmp_path: Path) -> None:
        """ensure_directory should create missing directories."""
        test_dir = tmp_path / "a" / "b" / "c"
        assert not test_dir.exists()

        result = ensure_directory(test_dir)

        assert test_dir.exists()
        assert test_dir.is_dir()
        assert result == test_dir

    def test_ensure_directory_existing(self, tmp_path: Path) -> None:
        """ensure_directory should not fail on existing directory."""
        test_dir = tmp_path / "existing"
        test_dir.mkdir()

        result = ensure_directory(test_dir)

        assert test_dir.exists()
        assert result == test_dir
