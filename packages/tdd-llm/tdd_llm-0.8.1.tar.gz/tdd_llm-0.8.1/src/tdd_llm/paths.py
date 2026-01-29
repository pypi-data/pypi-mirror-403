"""Cross-platform path utilities."""

import os
import sys
from pathlib import Path


def get_config_dir() -> Path:
    """Get the user config directory for tdd-llm.

    Returns:
        - Windows: %APPDATA%/tdd-llm
        - Linux/macOS: ~/.config/tdd-llm
    """
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))

    return base / "tdd-llm"


def get_user_claude_dir() -> Path:
    """Get the user-level .claude directory.

    Returns:
        - Windows: %USERPROFILE%/.claude
        - Linux/macOS: ~/.claude
    """
    return Path.home() / ".claude"


def get_user_gemini_dir() -> Path:
    """Get the user-level .gemini directory.

    Returns:
        - Windows: %USERPROFILE%/.gemini
        - Linux/macOS: ~/.gemini
    """
    return Path.home() / ".gemini"


def get_project_claude_dir(project_path: Path | None = None) -> Path:
    """Get the project-level .claude directory.

    Args:
        project_path: Project root path. Defaults to current directory.

    Returns:
        Path to .claude directory in project root.
    """
    base = project_path or Path.cwd()
    return base / ".claude"


def get_project_gemini_dir(project_path: Path | None = None) -> Path:
    """Get the project-level .gemini directory.

    Args:
        project_path: Project root path. Defaults to current directory.

    Returns:
        Path to .gemini directory in project root.
    """
    base = project_path or Path.cwd()
    return base / ".gemini"


def get_templates_dir() -> Path:
    """Get the bundled templates directory.

    Returns:
        Path to templates directory within the package.
    """
    return Path(__file__).parent / "templates"


def get_base_templates_dir() -> Path:
    """Get the base templates directory (containing commands structure)."""
    return get_templates_dir()


def get_placeholders_dir() -> Path:
    """Get the placeholders directory."""
    return get_templates_dir() / "placeholders"


def get_lang_placeholders_dir(lang: str) -> Path:
    """Get the placeholders directory for a specific language."""
    return get_placeholders_dir() / "langs" / lang


def get_backend_placeholders_dir(backend: str) -> Path:
    """Get the placeholders directory for a specific backend."""
    return get_placeholders_dir() / "backends" / backend


def get_templates_cache_dir() -> Path:
    """Get the cached templates directory (from update command).

    Templates are stored alongside the config for simplicity.

    Returns:
        Path to templates cache directory within config dir.
    """
    return get_config_dir() / "templates"


def get_cached_base_templates_dir() -> Path:
    """Get cached base templates directory."""
    return get_templates_cache_dir()


def get_cached_placeholders_dir() -> Path:
    """Get cached placeholders directory."""
    return get_templates_cache_dir() / "placeholders"


def get_cached_lang_placeholders_dir(lang: str) -> Path:
    """Get the cached placeholders directory for a specific language."""
    return get_cached_placeholders_dir() / "langs" / lang


def get_cached_backend_placeholders_dir(backend: str) -> Path:
    """Get the cached placeholders directory for a specific backend."""
    return get_cached_placeholders_dir() / "backends" / backend
