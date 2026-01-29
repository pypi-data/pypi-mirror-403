"""Configuration management for tdd-llm."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import yaml

from .paths import get_config_dir

# Project-level config filename
PROJECT_CONFIG_NAME = ".tdd-llm.yaml"

# Status aliases mapping common English/French status names to TDD status names
# Used by JiraConfig.get_jira_status() to normalize LLM input
_STATUS_ALIASES = {
    # English aliases
    "to do": "not_started",
    "open": "not_started",
    "backlog": "not_started",
    "in progress": "in_progress",
    "in review": "in_progress",
    "done": "completed",
    "closed": "completed",
    "resolved": "completed",
    # French aliases
    "à faire": "not_started",
    "a faire": "not_started",
    "ouvert": "not_started",
    "en cours": "in_progress",
    "en cours de revue": "in_progress",
    "en attente": "in_progress",
    "terminé": "completed",
    "termine": "completed",
    "fermé": "completed",
    "ferme": "completed",
    "résolu": "completed",
    "resolu": "completed",
}


@dataclass
class CoverageThresholds:
    """Coverage threshold configuration."""

    line: int = 80
    branch: int = 70

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {"line": self.line, "branch": self.branch}


@dataclass
class JiraFieldMappings:
    """Mapping of Jira custom fields to TDD concepts."""

    acceptance_criteria: str | None = None
    """Custom field ID for acceptance criteria (e.g., 'customfield_10001').
    If None, uses the issue description."""

    epic_link: str = "parent"
    """Field for epic-task relationship.
    Jira Cloud uses 'parent', Server may use 'customfield_*'."""

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        result = {}
        if self.acceptance_criteria:
            result["acceptance_criteria"] = self.acceptance_criteria
        if self.epic_link != "parent":
            result["epic_link"] = self.epic_link
        return result


@dataclass
class JiraConfig:
    """Jira backend configuration."""

    base_url: str = ""
    """Jira instance URL (e.g., 'https://company.atlassian.net')."""

    email: str = ""
    """User email for API authentication."""

    project_key: str = ""
    """Default Jira project key (e.g., 'PROJ')."""

    epic_issue_type: str = "Epic"
    """Issue type name for epics."""

    task_issue_types: list[str] = field(default_factory=lambda: ["Story", "Task"])
    """Issue type names considered as tasks."""

    fields: JiraFieldMappings = field(default_factory=JiraFieldMappings)
    """Custom field mappings."""

    status_map: dict[str, str] = field(default_factory=dict)
    """Map Jira status names to TDD status ('not_started', 'in_progress', 'completed').

    Example for French Jira:
        status_map = {"À faire": "not_started", "En cours": "in_progress", "Terminé": "completed"}
    """

    oauth_client_id: str = ""
    """OAuth 2.0 client ID from Atlassian Developer Console."""

    @property
    def api_token(self) -> str:
        """Get API token from environment variable.

        Returns:
            API token from JIRA_API_TOKEN env var, or empty string if not set.
        """
        return os.environ.get("JIRA_API_TOKEN", "")

    @property
    def effective_oauth_client_id(self) -> str:
        """Get OAuth client ID with env var override."""
        return os.environ.get("JIRA_OAUTH_CLIENT_ID", self.oauth_client_id)

    @property
    def effective_oauth_client_secret(self) -> str:
        """Get OAuth client secret from env var (never stored in config)."""
        return os.environ.get("JIRA_OAUTH_CLIENT_SECRET", "")

    @property
    def effective_base_url(self) -> str:
        """Get base URL with env var override."""
        return os.environ.get("JIRA_BASE_URL", self.base_url)

    @property
    def effective_email(self) -> str:
        """Get email with env var override."""
        return os.environ.get("JIRA_EMAIL", self.email)

    @property
    def effective_project_key(self) -> str:
        """Get project key with env var override."""
        return os.environ.get("JIRA_PROJECT_KEY", self.project_key)

    def is_oauth_configured(self) -> bool:
        """Check if OAuth credentials are configured."""
        return bool(self.effective_oauth_client_id and self.effective_oauth_client_secret)

    def is_configured(self) -> bool:
        """Check if Jira is properly configured (any auth method)."""
        # OAuth: need client_id and client_secret (tokens checked separately)
        if self.is_oauth_configured():
            return True
        # API Token: need base_url, email, api_token
        return bool(self.effective_base_url and self.effective_email and self.api_token)

    def get_tdd_status(self, jira_status: str) -> str:
        """Map Jira status to TDD status.

        Args:
            jira_status: Jira status name (e.g., 'To Do', 'In Progress', 'Done').

        Returns:
            TDD status: 'not_started', 'in_progress', or 'completed'.
        """
        if self.status_map:
            # Try exact match first
            if jira_status in self.status_map:
                return self.status_map[jira_status]
            # Try case-insensitive match
            jira_lower = jira_status.lower()
            return next(
                (value for key, value in self.status_map.items() if key.lower() == jira_lower),
                "not_started",
            )

        # Default mapping
        jira_lower = jira_status.lower()
        if "done" in jira_lower or "closed" in jira_lower or "resolved" in jira_lower:
            return "completed"
        if "progress" in jira_lower or "review" in jira_lower:
            return "in_progress"
        return "not_started"

    def get_jira_status(self, tdd_status: str) -> str:
        """Map TDD status to Jira status name.

        Args:
            tdd_status: TDD status ('not_started', 'in_progress', 'completed')
                       or common aliases like 'In Progress', 'En cours', etc.

        Returns:
            Jira status name (e.g., 'To Do', 'In Progress', 'Done').
        """
        # Normalize input: check if it's a known alias (uses module-level _STATUS_ALIASES)
        normalized = _STATUS_ALIASES.get(tdd_status.lower(), tdd_status)

        # If we have a status_map, invert it to find the first Jira status
        # that maps to the given TDD status
        if self.status_map:
            for jira_status, mapped_tdd_status in self.status_map.items():
                if mapped_tdd_status == normalized:
                    return jira_status

        # Default mapping
        default_map = {
            "not_started": "To Do",
            "in_progress": "In Progress",
            "completed": "Done",
        }
        return default_map.get(normalized, tdd_status)

    def get_jira_statuses_for_tdd(self, tdd_status: str) -> list[str]:
        """Get all Jira statuses that map to a TDD status.

        Args:
            tdd_status: TDD status ('not_started', 'in_progress', 'completed').

        Returns:
            List of Jira status names.
        """
        statuses = []

        if self.status_map:
            for jira_status, mapped_tdd_status in self.status_map.items():
                if mapped_tdd_status == tdd_status:
                    statuses.append(jira_status)

        # Add defaults if not already in the map
        default_map = {
            "not_started": ["To Do", "Open", "Backlog"],
            "in_progress": ["In Progress", "In Review"],
            "completed": ["Done", "Closed", "Resolved"],
        }
        for default_status in default_map.get(tdd_status, []):
            if default_status not in statuses:
                statuses.append(default_status)

        return statuses

    def to_dict(self) -> dict:
        """Convert to dictionary (excluding sensitive data)."""
        result: dict = {}
        if self.base_url:
            result["base_url"] = self.base_url
        if self.email:
            result["email"] = self.email
        if self.project_key:
            result["project_key"] = self.project_key
        if self.epic_issue_type != "Epic":
            result["epic_issue_type"] = self.epic_issue_type
        if self.task_issue_types != ["Story", "Task"]:
            result["task_issue_types"] = self.task_issue_types
        fields_dict = self.fields.to_dict()
        if fields_dict:
            result["fields"] = fields_dict
        if self.status_map:
            result["status_map"] = self.status_map
        if self.oauth_client_id:
            result["oauth_client_id"] = self.oauth_client_id
        return result


@dataclass
class ConfigSource:
    """Tracks where configuration was loaded from."""

    global_path: Path | None = None
    project_path: Path | None = None

    @property
    def active_path(self) -> Path | None:
        """Return the most specific config path (project > global)."""
        return self.project_path or self.global_path


@dataclass
class Config:
    """TDD-LLM configuration."""

    default_target: Literal["project", "user"] = "project"
    default_language: str = "python"
    default_backend: Literal["files", "jira"] = "files"
    platforms: list[str] = field(default_factory=lambda: ["claude", "gemini"])
    coverage: CoverageThresholds = field(default_factory=CoverageThresholds)
    jira: JiraConfig = field(default_factory=JiraConfig)
    source: ConfigSource = field(default_factory=ConfigSource)

    @classmethod
    def _load_from_file(cls, path: Path) -> dict:
        """Load raw config data from a YAML file."""
        if not path.exists():
            return {}
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    @classmethod
    def _merge_data(cls, base: dict, override: dict) -> dict:
        """Merge two config dicts, with override taking precedence."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = cls._merge_data(result[key], value)
            else:
                result[key] = value
        return result

    @classmethod
    def _from_data(cls, data: dict, source: ConfigSource) -> Config:
        """Create Config from data dict."""
        coverage_data = data.get("coverage", {})
        coverage = CoverageThresholds(
            line=coverage_data.get("line", 80),
            branch=coverage_data.get("branch", 70),
        )

        # Parse Jira config
        jira_data = data.get("jira", {})
        jira_fields_data = jira_data.get("fields", {})
        jira_fields = JiraFieldMappings(
            acceptance_criteria=jira_fields_data.get("acceptance_criteria"),
            epic_link=jira_fields_data.get("epic_link", "parent"),
        )
        jira = JiraConfig(
            base_url=jira_data.get("base_url", ""),
            email=jira_data.get("email", ""),
            project_key=jira_data.get("project_key", ""),
            epic_issue_type=jira_data.get("epic_issue_type", "Epic"),
            task_issue_types=jira_data.get("task_issue_types", ["Story", "Task"]),
            fields=jira_fields,
            status_map=jira_data.get("status_map", {}),
            oauth_client_id=jira_data.get("oauth_client_id", ""),
        )

        return cls(
            default_target=data.get("default_target", "project"),
            default_language=data.get("default_language", "python"),
            default_backend=data.get("default_backend", "files"),
            platforms=data.get("platforms", ["claude", "gemini"]),
            coverage=coverage,
            jira=jira,
            source=source,
        )

    @classmethod
    def load(
        cls,
        path: Path | None = None,
        project_path: Path | None = None,
        include_project: bool = True,
    ) -> Config:
        """Load configuration from YAML files.

        Loads global config first, then merges project config on top.
        Project config values override global config values.

        Args:
            path: Path to global config file. Defaults to user config directory.
            project_path: Project root to look for .tdd-llm.yaml. Defaults to cwd.
            include_project: If True, also load project-level config.

        Returns:
            Config instance with merged values.
        """
        global_path = path or get_config_dir() / "config.yaml"
        source = ConfigSource()

        # Load global config
        global_data = cls._load_from_file(global_path)
        if global_path.exists():
            source.global_path = global_path

        # Load project config if requested
        project_data = {}
        if include_project:
            proj_root = project_path or Path.cwd()
            proj_config_path = proj_root / PROJECT_CONFIG_NAME
            project_data = cls._load_from_file(proj_config_path)
            if proj_config_path.exists():
                source.project_path = proj_config_path

        # Merge: project overrides global
        merged_data = cls._merge_data(global_data, project_data)

        return cls._from_data(merged_data, source)

    def save(self, path: Path | None = None, project: bool = False) -> Path:
        """Save configuration to YAML file.

        Args:
            path: Path to config file. If None, uses default location.
            project: If True, save to project config (.tdd-llm.yaml in cwd).
                    If False, save to global config.

        Returns:
            Path where config was saved.
        """
        if path:
            config_path = path
        elif project:
            config_path = Path.cwd() / PROJECT_CONFIG_NAME
        else:
            config_path = get_config_dir() / "config.yaml"

        config_path.parent.mkdir(parents=True, exist_ok=True)

        data: dict = {
            "default_target": self.default_target,
            "default_language": self.default_language,
            "default_backend": self.default_backend,
            "platforms": self.platforms,
            "coverage": self.coverage.to_dict(),
        }

        # Only include jira config if it has values
        jira_dict = self.jira.to_dict()
        if jira_dict:
            data["jira"] = jira_dict

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True)

        return config_path

    def to_dict(self) -> dict:
        """Convert config to dictionary."""
        result = {
            "default_target": self.default_target,
            "default_language": self.default_language,
            "default_backend": self.default_backend,
            "platforms": self.platforms,
            "coverage": self.coverage.to_dict(),
        }

        jira_dict = self.jira.to_dict()
        if jira_dict:
            result["jira"] = jira_dict

        return result


def get_project_config_path(project_path: Path | None = None) -> Path:
    """Get the project config file path.

    Args:
        project_path: Project root. Defaults to cwd.

    Returns:
        Path to project config file (may not exist).
    """
    return (project_path or Path.cwd()) / PROJECT_CONFIG_NAME


def get_global_config_path() -> Path:
    """Get the global config file path.

    Returns:
        Path to global config file (may not exist).
    """
    return get_config_dir() / "config.yaml"


def is_first_run() -> bool:
    """Check if this is the first run (no global config exists).

    Returns:
        True if global config does not exist.
    """
    return not get_global_config_path().exists()


def get_available_languages() -> list[str]:
    """Get list of available language placeholders.

    Returns:
        List of language names with placeholder directories.
    """
    from .paths import get_placeholders_dir

    langs_dir = get_placeholders_dir() / "langs"
    if not langs_dir.exists():
        return []

    return sorted([d.name for d in langs_dir.iterdir() if d.is_dir()])


def get_available_backends() -> list[str]:
    """Get list of available backend placeholders.

    Returns:
        List of backend names with placeholder directories.
    """
    from .paths import get_placeholders_dir

    backends_dir = get_placeholders_dir() / "backends"
    if not backends_dir.exists():
        return []

    return sorted([d.name for d in backends_dir.iterdir() if d.is_dir()])
