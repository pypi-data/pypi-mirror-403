"""Tests for paths module."""

import os
from pathlib import Path
from unittest import mock

from tdd_llm.paths import (
    get_backend_placeholders_dir,
    get_base_templates_dir,
    get_config_dir,
    get_lang_placeholders_dir,
    get_placeholders_dir,
    get_project_claude_dir,
    get_project_gemini_dir,
    get_templates_dir,
    get_user_claude_dir,
    get_user_gemini_dir,
)


class TestGetConfigDir:
    """Tests for get_config_dir function."""

    def test_returns_path(self):
        """Test that get_config_dir returns a Path object."""
        result = get_config_dir()
        assert isinstance(result, Path)

    def test_ends_with_tdd_llm(self):
        """Test that config dir ends with tdd-llm."""
        result = get_config_dir()
        assert result.name == "tdd-llm"

    @mock.patch("sys.platform", "win32")
    @mock.patch.dict(os.environ, {"APPDATA": "C:\\Users\\Test\\AppData\\Roaming"})
    def test_windows_uses_appdata(self):
        """Test Windows uses APPDATA environment variable."""
        result = get_config_dir()
        assert "AppData" in str(result) or "tdd-llm" in str(result)

    @mock.patch("sys.platform", "linux")
    @mock.patch.dict(os.environ, {"XDG_CONFIG_HOME": "/home/test/.config"}, clear=False)
    def test_linux_uses_xdg_config(self):
        """Test Linux uses XDG_CONFIG_HOME when set."""
        # Force reimport to pick up mocked platform
        import importlib

        from tdd_llm import paths
        importlib.reload(paths)

        result = paths.get_config_dir()
        # Should end with tdd-llm regardless of platform
        assert result.name == "tdd-llm"


class TestGetUserClaudeDir:
    """Tests for get_user_claude_dir function."""

    def test_returns_path(self):
        """Test that get_user_claude_dir returns a Path object."""
        result = get_user_claude_dir()
        assert isinstance(result, Path)

    def test_ends_with_claude(self):
        """Test that user claude dir ends with .claude."""
        result = get_user_claude_dir()
        assert result.name == ".claude"

    def test_is_in_home_directory(self):
        """Test that user claude dir is in home directory."""
        result = get_user_claude_dir()
        assert result.parent == Path.home()


class TestGetUserGeminiDir:
    """Tests for get_user_gemini_dir function."""

    def test_returns_path(self):
        """Test that get_user_gemini_dir returns a Path object."""
        result = get_user_gemini_dir()
        assert isinstance(result, Path)

    def test_ends_with_gemini(self):
        """Test that user gemini dir ends with .gemini."""
        result = get_user_gemini_dir()
        assert result.name == ".gemini"

    def test_is_in_home_directory(self):
        """Test that user gemini dir is in home directory."""
        result = get_user_gemini_dir()
        assert result.parent == Path.home()


class TestGetProjectClaudeDir:
    """Tests for get_project_claude_dir function."""

    def test_returns_path(self):
        """Test that get_project_claude_dir returns a Path object."""
        result = get_project_claude_dir()
        assert isinstance(result, Path)

    def test_ends_with_claude(self):
        """Test that project claude dir ends with .claude."""
        result = get_project_claude_dir()
        assert result.name == ".claude"

    def test_default_uses_cwd(self):
        """Test that default uses current working directory."""
        result = get_project_claude_dir()
        assert result.parent == Path.cwd()

    def test_custom_project_path(self, temp_dir):
        """Test with custom project path."""
        result = get_project_claude_dir(temp_dir)
        assert result == temp_dir / ".claude"


class TestGetProjectGeminiDir:
    """Tests for get_project_gemini_dir function."""

    def test_returns_path(self):
        """Test that get_project_gemini_dir returns a Path object."""
        result = get_project_gemini_dir()
        assert isinstance(result, Path)

    def test_ends_with_gemini(self):
        """Test that project gemini dir ends with .gemini."""
        result = get_project_gemini_dir()
        assert result.name == ".gemini"

    def test_default_uses_cwd(self):
        """Test that default uses current working directory."""
        result = get_project_gemini_dir()
        assert result.parent == Path.cwd()

    def test_custom_project_path(self, temp_dir):
        """Test with custom project path."""
        result = get_project_gemini_dir(temp_dir)
        assert result == temp_dir / ".gemini"


class TestGetTemplatesDir:
    """Tests for get_templates_dir function."""

    def test_returns_path(self):
        """Test that get_templates_dir returns a Path object."""
        result = get_templates_dir()
        assert isinstance(result, Path)

    def test_ends_with_templates(self):
        """Test that templates dir ends with templates."""
        result = get_templates_dir()
        assert result.name == "templates"

    def test_directory_exists(self):
        """Test that templates directory exists."""
        result = get_templates_dir()
        assert result.exists()

    def test_is_in_package(self):
        """Test that templates dir is within the package."""
        result = get_templates_dir()
        assert "tdd_llm" in str(result)


class TestGetBaseTemplatesDir:
    """Tests for get_base_templates_dir function."""

    def test_returns_path(self):
        """Test that get_base_templates_dir returns a Path object."""
        result = get_base_templates_dir()
        assert isinstance(result, Path)

    def test_ends_with_templates(self):
        """Test that base templates dir ends with templates."""
        result = get_base_templates_dir()
        assert result.name == "templates"

    def test_equals_templates_dir(self):
        """Test that base templates dir equals templates directory."""
        result = get_base_templates_dir()
        assert result == get_templates_dir()

    def test_directory_exists(self):
        """Test that base templates directory exists."""
        result = get_base_templates_dir()
        assert result.exists()


class TestGetPlaceholdersDir:
    """Tests for get_placeholders_dir function."""

    def test_returns_path(self):
        """Test that get_placeholders_dir returns a Path object."""
        result = get_placeholders_dir()
        assert isinstance(result, Path)

    def test_ends_with_placeholders(self):
        """Test that placeholders dir ends with placeholders."""
        result = get_placeholders_dir()
        assert result.name == "placeholders"

    def test_is_under_templates(self):
        """Test that placeholders is under templates directory."""
        result = get_placeholders_dir()
        assert result.parent == get_templates_dir()

    def test_directory_exists(self):
        """Test that placeholders directory exists."""
        result = get_placeholders_dir()
        assert result.exists()


class TestGetLangPlaceholdersDir:
    """Tests for get_lang_placeholders_dir function."""

    def test_returns_path(self):
        """Test that get_lang_placeholders_dir returns a Path object."""
        result = get_lang_placeholders_dir("python")
        assert isinstance(result, Path)

    def test_ends_with_lang_name(self):
        """Test that path ends with language name."""
        result = get_lang_placeholders_dir("python")
        assert result.name == "python"

    def test_is_under_langs(self):
        """Test that language dir is under langs directory."""
        result = get_lang_placeholders_dir("python")
        assert result.parent.name == "langs"

    def test_python_directory_exists(self):
        """Test that python placeholders directory exists."""
        result = get_lang_placeholders_dir("python")
        assert result.exists()

    def test_csharp_directory_exists(self):
        """Test that csharp placeholders directory exists."""
        result = get_lang_placeholders_dir("csharp")
        assert result.exists()

    def test_typescript_directory_exists(self):
        """Test that typescript placeholders directory exists."""
        result = get_lang_placeholders_dir("typescript")
        assert result.exists()


class TestGetBackendPlaceholdersDir:
    """Tests for get_backend_placeholders_dir function."""

    def test_returns_path(self):
        """Test that get_backend_placeholders_dir returns a Path object."""
        result = get_backend_placeholders_dir("files")
        assert isinstance(result, Path)

    def test_ends_with_backend_name(self):
        """Test that path ends with backend name."""
        result = get_backend_placeholders_dir("files")
        assert result.name == "files"

    def test_is_under_backends(self):
        """Test that backend dir is under backends directory."""
        result = get_backend_placeholders_dir("files")
        assert result.parent.name == "backends"

    def test_files_directory_exists(self):
        """Test that files backend directory exists."""
        result = get_backend_placeholders_dir("files")
        assert result.exists()

    def test_jira_directory_exists(self):
        """Test that jira backend directory exists."""
        result = get_backend_placeholders_dir("jira")
        assert result.exists()
