"""Tests for config module."""

import pytest
import yaml

from tdd_llm.config import (
    PROJECT_CONFIG_NAME,
    Config,
    CoverageThresholds,
    JiraConfig,
    get_available_backends,
    get_available_languages,
    get_global_config_path,
    get_project_config_path,
    is_first_run,
)


class TestCoverageThresholds:
    """Tests for CoverageThresholds dataclass."""

    def test_default_values(self):
        """Test default coverage thresholds."""
        thresholds = CoverageThresholds()
        assert thresholds.line == 80
        assert thresholds.branch == 70

    def test_custom_values(self):
        """Test custom coverage thresholds."""
        thresholds = CoverageThresholds(line=90, branch=85)
        assert thresholds.line == 90
        assert thresholds.branch == 85

    def test_to_dict(self):
        """Test conversion to dictionary."""
        thresholds = CoverageThresholds(line=95, branch=80)
        result = thresholds.to_dict()
        assert result == {"line": 95, "branch": 80}


class TestConfig:
    """Tests for Config dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = Config()
        assert config.default_target == "project"
        assert config.default_language == "python"
        assert config.default_backend == "files"
        assert config.platforms == ["claude", "gemini"]
        assert config.coverage.line == 80
        assert config.coverage.branch == 70

    def test_custom_values(self):
        """Test custom configuration values."""
        coverage = CoverageThresholds(line=90, branch=85)
        config = Config(
            default_target="user",
            default_language="typescript",
            default_backend="jira",
            platforms=["claude"],
            coverage=coverage,
        )
        assert config.default_target == "user"
        assert config.default_language == "typescript"
        assert config.default_backend == "jira"
        assert config.platforms == ["claude"]
        assert config.coverage.line == 90
        assert config.coverage.branch == 85

    def test_load_missing_file_returns_defaults(self, temp_dir):
        """Test loading from non-existent file returns defaults."""
        config = Config.load(temp_dir / "nonexistent.yaml")
        assert config.default_target == "project"
        assert config.default_language == "python"
        assert config.coverage.line == 80

    def test_save_and_load(self, temp_config_file):
        """Test saving and loading configuration."""
        original = Config(
            default_target="user",
            default_language="csharp",
            default_backend="jira",
            coverage=CoverageThresholds(line=95, branch=90),
        )
        original.save(temp_config_file)

        loaded = Config.load(temp_config_file)
        assert loaded.default_target == "user"
        assert loaded.default_language == "csharp"
        assert loaded.default_backend == "jira"
        assert loaded.coverage.line == 95
        assert loaded.coverage.branch == 90

    def test_load_partial_config(self, temp_config_file):
        """Test loading config with missing fields uses defaults."""
        # Write partial config
        partial_data = {"default_language": "typescript"}
        with open(temp_config_file, "w") as f:
            yaml.safe_dump(partial_data, f)

        config = Config.load(temp_config_file)
        assert config.default_language == "typescript"
        assert config.default_target == "project"  # default
        assert config.coverage.line == 80  # default

    def test_load_partial_coverage(self, temp_config_file):
        """Test loading config with partial coverage uses defaults."""
        data = {
            "default_language": "python",
            "coverage": {"line": 95},  # branch missing
        }
        with open(temp_config_file, "w") as f:
            yaml.safe_dump(data, f)

        config = Config.load(temp_config_file)
        assert config.coverage.line == 95
        assert config.coverage.branch == 70  # default

    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = Config(
            default_target="user",
            default_language="python",
            coverage=CoverageThresholds(line=85, branch=75),
        )
        result = config.to_dict()

        assert result["default_target"] == "user"
        assert result["default_language"] == "python"
        assert result["coverage"] == {"line": 85, "branch": 75}


class TestProjectLevelConfig:
    """Tests for project-level configuration."""

    def test_load_merges_global_and_project(self, temp_dir):
        """Test that project config overrides global config."""
        global_config_path = temp_dir / "global" / "config.yaml"
        global_config_path.parent.mkdir(parents=True)

        # Create global config
        global_data = {
            "default_language": "python",
            "default_backend": "files",
            "coverage": {"line": 80, "branch": 70},
        }
        with open(global_config_path, "w") as f:
            yaml.safe_dump(global_data, f)

        # Create project config that overrides some values
        project_config_path = temp_dir / PROJECT_CONFIG_NAME
        project_data = {
            "default_language": "typescript",
            "coverage": {"line": 90},  # Only override line
        }
        with open(project_config_path, "w") as f:
            yaml.safe_dump(project_data, f)

        # Load merged config
        config = Config.load(path=global_config_path, project_path=temp_dir)

        # Project overrides global
        assert config.default_language == "typescript"
        assert config.coverage.line == 90

        # Global values kept where not overridden
        assert config.default_backend == "files"
        assert config.coverage.branch == 70  # Not overridden in project

    def test_load_without_project_config(self, temp_dir):
        """Test loading when no project config exists."""
        global_config_path = temp_dir / "global" / "config.yaml"
        global_config_path.parent.mkdir(parents=True)

        global_data = {"default_language": "csharp"}
        with open(global_config_path, "w") as f:
            yaml.safe_dump(global_data, f)

        config = Config.load(path=global_config_path, project_path=temp_dir)

        assert config.default_language == "csharp"
        assert config.source.global_path == global_config_path
        assert config.source.project_path is None

    def test_load_include_project_false(self, temp_dir):
        """Test loading with include_project=False ignores project config."""
        global_config_path = temp_dir / "global" / "config.yaml"
        global_config_path.parent.mkdir(parents=True)

        global_data = {"default_language": "python"}
        with open(global_config_path, "w") as f:
            yaml.safe_dump(global_data, f)

        project_config_path = temp_dir / PROJECT_CONFIG_NAME
        project_data = {"default_language": "typescript"}
        with open(project_config_path, "w") as f:
            yaml.safe_dump(project_data, f)

        # Load without project config
        config = Config.load(
            path=global_config_path,
            project_path=temp_dir,
            include_project=False,
        )

        # Should use global, not project
        assert config.default_language == "python"

    def test_save_to_project(self, temp_dir, monkeypatch):
        """Test saving config to project file."""
        monkeypatch.chdir(temp_dir)

        config = Config(default_language="typescript", coverage=CoverageThresholds(line=95))
        saved_path = config.save(project=True)

        assert saved_path == temp_dir / PROJECT_CONFIG_NAME
        assert saved_path.exists()

        # Verify content
        with open(saved_path) as f:
            data = yaml.safe_load(f)
        assert data["default_language"] == "typescript"
        assert data["coverage"]["line"] == 95

    def test_config_source_tracks_paths(self, temp_dir):
        """Test ConfigSource tracks which config files were loaded."""
        global_path = temp_dir / "global" / "config.yaml"
        global_path.parent.mkdir(parents=True)
        with open(global_path, "w") as f:
            yaml.safe_dump({"default_language": "python"}, f)

        project_path = temp_dir / PROJECT_CONFIG_NAME
        with open(project_path, "w") as f:
            yaml.safe_dump({"default_backend": "jira"}, f)

        config = Config.load(path=global_path, project_path=temp_dir)

        assert config.source.global_path == global_path
        assert config.source.project_path == project_path
        assert config.source.active_path == project_path  # Project takes precedence

    def test_deep_merge_coverage(self, temp_dir):
        """Test that nested coverage dict is properly merged."""
        global_path = temp_dir / "global" / "config.yaml"
        global_path.parent.mkdir(parents=True)
        with open(global_path, "w") as f:
            yaml.safe_dump({"coverage": {"line": 80, "branch": 70}}, f)

        project_path = temp_dir / PROJECT_CONFIG_NAME
        with open(project_path, "w") as f:
            yaml.safe_dump({"coverage": {"line": 95}}, f)  # Only override line

        config = Config.load(path=global_path, project_path=temp_dir)

        assert config.coverage.line == 95  # From project
        assert config.coverage.branch == 70  # From global


class TestConfigPathHelpers:
    """Tests for config path helper functions."""

    def test_get_project_config_path(self, temp_dir):
        """Test get_project_config_path returns correct path."""
        path = get_project_config_path(temp_dir)
        assert path == temp_dir / PROJECT_CONFIG_NAME

    def test_get_global_config_path(self):
        """Test get_global_config_path returns a path."""
        path = get_global_config_path()
        assert path.name == "config.yaml"
        assert "tdd-llm" in str(path).lower() or "tdd_llm" in str(path).lower()


class TestAvailableLangsAndBackends:
    """Tests for language and backend discovery functions."""

    def test_get_available_languages(self):
        """Test discovering available languages."""
        langs = get_available_languages()
        assert "python" in langs
        assert "csharp" in langs
        assert "typescript" in langs

    def test_get_available_backends(self):
        """Test discovering available backends."""
        backends = get_available_backends()
        assert "files" in backends
        assert "jira" in backends


class TestIsFirstRun:
    """Tests for is_first_run function."""

    def test_is_first_run_when_no_config(self, temp_dir, monkeypatch):
        """Test is_first_run returns True when no global config exists."""
        monkeypatch.setattr(
            "tdd_llm.config.get_config_dir",
            lambda: temp_dir / "nonexistent",
        )
        assert is_first_run() is True

    def test_is_first_run_when_config_exists(self, temp_dir, monkeypatch):
        """Test is_first_run returns False when global config exists."""
        config_dir = temp_dir / "config"
        config_dir.mkdir(parents=True)
        (config_dir / "config.yaml").write_text("default_language: python\n")

        monkeypatch.setattr("tdd_llm.config.get_config_dir", lambda: config_dir)
        assert is_first_run() is False


class TestJiraConfigStatusMapping:
    """Tests for JiraConfig status mapping functions."""

    def test_get_jira_status_with_tdd_status(self):
        """Test mapping TDD status to Jira status."""
        config = JiraConfig()
        assert config.get_jira_status("not_started") == "To Do"
        assert config.get_jira_status("in_progress") == "In Progress"
        assert config.get_jira_status("completed") == "Done"

    def test_get_jira_status_with_custom_status_map(self):
        """Test mapping with custom status_map configured."""
        config = JiraConfig(
            status_map={
                "À faire": "not_started",
                "En cours": "in_progress",
                "Terminé": "completed",
            }
        )
        # Should return the first Jira status that maps to the TDD status
        assert config.get_jira_status("not_started") == "À faire"
        assert config.get_jira_status("in_progress") == "En cours"
        assert config.get_jira_status("completed") == "Terminé"

    @pytest.mark.parametrize(
        "alias,expected_tdd",
        [
            # English aliases
            ("In Progress", "In Progress"),  # Maps to in_progress, then to default
            ("To Do", "To Do"),
            ("Done", "Done"),
            ("Open", "To Do"),
            ("Closed", "Done"),
            ("In Review", "In Progress"),
            # French aliases (without status_map, falls back to defaults)
            ("En cours", "In Progress"),
            ("À faire", "To Do"),
            ("Terminé", "Done"),
            ("En attente", "In Progress"),
        ],
    )
    def test_get_jira_status_normalizes_aliases_to_defaults(self, alias, expected_tdd):
        """Test that common aliases are normalized and mapped to defaults."""
        config = JiraConfig()  # No status_map
        result = config.get_jira_status(alias)
        assert result == expected_tdd

    @pytest.mark.parametrize(
        "alias,expected_jira",
        [
            # LLM sends English, but Jira is French
            ("In Progress", "En cours"),
            ("To Do", "À faire"),
            ("Done", "Terminé"),
            ("Open", "À faire"),
            ("Closed", "Terminé"),
            # LLM could also send French directly
            ("En cours", "En cours"),
            ("À faire", "À faire"),
            ("Terminé", "Terminé"),
            # TDD status names should also work
            ("in_progress", "En cours"),
            ("not_started", "À faire"),
            ("completed", "Terminé"),
        ],
    )
    def test_get_jira_status_with_french_jira(self, alias, expected_jira):
        """Test English aliases map correctly to French Jira statuses."""
        config = JiraConfig(
            status_map={
                "À faire": "not_started",
                "En cours": "in_progress",
                "Terminé": "completed",
            }
        )
        result = config.get_jira_status(alias)
        assert result == expected_jira

    def test_get_jira_status_case_insensitive(self):
        """Test that alias matching is case-insensitive."""
        config = JiraConfig()
        assert config.get_jira_status("IN PROGRESS") == "In Progress"
        assert config.get_jira_status("in progress") == "In Progress"
        assert config.get_jira_status("In Progress") == "In Progress"

    def test_get_jira_status_accents_without_accents(self):
        """Test French aliases work with or without accents."""
        config = JiraConfig(
            status_map={
                "À faire": "not_started",
                "En cours": "in_progress",
                "Terminé": "completed",
            }
        )
        # With accents
        assert config.get_jira_status("À faire") == "À faire"
        assert config.get_jira_status("Terminé") == "Terminé"
        # Without accents (should still map correctly)
        assert config.get_jira_status("a faire") == "À faire"
        assert config.get_jira_status("termine") == "Terminé"

    def test_get_jira_status_unknown_returns_original(self):
        """Test that unknown status is returned as-is."""
        config = JiraConfig()
        assert config.get_jira_status("CustomStatus") == "CustomStatus"

    def test_get_tdd_status_default_mapping(self):
        """Test default mapping from Jira to TDD status."""
        config = JiraConfig()
        assert config.get_tdd_status("To Do") == "not_started"
        assert config.get_tdd_status("In Progress") == "in_progress"
        assert config.get_tdd_status("Done") == "completed"

    def test_get_tdd_status_with_custom_map(self):
        """Test custom mapping from Jira to TDD status."""
        config = JiraConfig(
            status_map={
                "À faire": "not_started",
                "En cours": "in_progress",
                "Terminé": "completed",
            }
        )
        assert config.get_tdd_status("À faire") == "not_started"
        assert config.get_tdd_status("En cours") == "in_progress"
        assert config.get_tdd_status("Terminé") == "completed"
