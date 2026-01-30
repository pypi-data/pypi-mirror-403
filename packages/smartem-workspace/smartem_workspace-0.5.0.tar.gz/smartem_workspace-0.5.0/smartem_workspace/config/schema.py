"""Pydantic models for workspace configuration."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RepoUrls(BaseModel):
    """Repository clone URLs."""

    https: str
    ssh: str


class Repository(BaseModel):
    """Repository definition."""

    name: str
    description: str
    urls: RepoUrls
    tags: list[str] = Field(default_factory=list)
    ownership: Literal["full", "reference-only"] | None = None
    required: bool = False


class Organization(BaseModel):
    """Organization containing repositories."""

    model_config = ConfigDict(populate_by_name=True)

    name: str
    displayName: str = Field(alias="displayName")
    url: str
    provider: Literal["github", "gitlab"]
    localDir: str | None = Field(default=None, alias="localDir")
    repos: list[Repository]


class Preset(BaseModel):
    """Preset repository selection."""

    description: str
    repos: list[str]


class ExternalLinks(BaseModel):
    """External documentation and project links."""

    model_config = ConfigDict(populate_by_name=True)

    docs: str
    projectBoard: str = Field(alias="projectBoard")


class SkillDefinition(BaseModel):
    """Claude Code skill definition."""

    name: str
    path: str


class DefaultPermissions(BaseModel):
    """Default Claude Code permissions."""

    allow: list[str]


class ClaudeConfig(BaseModel):
    """Claude Code configuration."""

    model_config = ConfigDict(populate_by_name=True)

    skills: list[SkillDefinition]
    defaultPermissions: DefaultPermissions = Field(alias="defaultPermissions")


class SerenaConfig(BaseModel):
    """Serena MCP server configuration."""

    model_config = ConfigDict(populate_by_name=True)

    languages: list[str]
    encoding: str = "utf-8"
    ignoreAllFilesInGitignore: bool = Field(default=True, alias="ignoreAllFilesInGitignore")
    projectName: str = Field(alias="projectName")


class McpServerConfig(BaseModel):
    """MCP server command configuration."""

    command: str
    args: list[str]


class McpConfig(BaseModel):
    """MCP servers configuration."""

    serena: McpServerConfig


class ClaudeCodeConfig(BaseModel):
    """Claude Code integration configuration (from claude-code-config.json)."""

    model_config = ConfigDict(populate_by_name=True)

    version: str = "1.0.0"
    description: str = ""
    claudeConfig: ClaudeConfig = Field(alias="claudeConfig")
    serenaConfig: SerenaConfig = Field(alias="serenaConfig")
    mcpConfig: McpConfig = Field(alias="mcpConfig")


class ReposConfig(BaseModel):
    """Repository configuration schema (from repos.json)."""

    model_config = ConfigDict(populate_by_name=True)

    version: str = "1.0.0"
    links: ExternalLinks
    presets: dict[str, Preset]
    organizations: list[Organization]

    def get_preset(self, name: str) -> Preset | None:
        """Get a preset by name."""
        return self.presets.get(name)

    def get_organization(self, name: str) -> Organization | None:
        """Get an organization by name."""
        for org in self.organizations:
            if org.name == name:
                return org
        return None

    def get_all_repos(self) -> list[tuple[Organization, Repository]]:
        """Get all repositories with their organizations."""
        result = []
        for org in self.organizations:
            for repo in org.repos:
                result.append((org, repo))
        return result

    def resolve_preset(self, preset_name: str) -> list[tuple[Organization, Repository]]:
        """Resolve a preset to a list of (org, repo) tuples."""
        preset = self.get_preset(preset_name)
        if not preset:
            return []

        result = []
        for pattern in preset.repos:
            if pattern == "*":
                return self.get_all_repos()

            if "/" in pattern:
                org_name, repo_pattern = pattern.split("/", 1)
                org = self.get_organization(org_name)
                if not org:
                    continue

                if repo_pattern == "*":
                    for repo in org.repos:
                        result.append((org, repo))
                else:
                    for repo in org.repos:
                        if repo.name == repo_pattern:
                            result.append((org, repo))
                            break

        return result
