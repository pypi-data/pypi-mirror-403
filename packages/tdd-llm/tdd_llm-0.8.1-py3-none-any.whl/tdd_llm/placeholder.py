"""Placeholder replacement for templates."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from .paths import (
    get_backend_placeholders_dir,
    get_cached_backend_placeholders_dir,
    get_cached_lang_placeholders_dir,
    get_lang_placeholders_dir,
)

if TYPE_CHECKING:
    from .config import Config

# Pattern to match {{PLACEHOLDER_NAME}}
PLACEHOLDER_PATTERN = re.compile(r"\{\{([A-Z_][A-Z0-9_]*)\}\}")


def find_placeholders(content: str) -> set[str]:
    """Find all placeholder names in content.

    Args:
        content: Text content to scan.

    Returns:
        Set of placeholder names (without braces).
    """
    return set(PLACEHOLDER_PATTERN.findall(content))


def get_platform_placeholder(name: str, platform: str | None) -> str | None:
    """Get placeholder value based on platform.

    Args:
        name: Placeholder name.
        platform: Platform name ("claude" or "gemini").

    Returns:
        Platform-specific placeholder content or None if not a platform placeholder.
    """
    if platform is None:
        return None

    if name == "AGENT_FILE":
        platform_files = {
            "claude": "CLAUDE.md",
            "gemini": "GEMINI.md",
        }
        return platform_files.get(platform)

    return None


def get_config_placeholder(name: str, config: Config | None) -> str | None:
    """Get placeholder value from config.

    Some placeholders are generated from config values rather than files.

    Args:
        name: Placeholder name.
        config: Config instance.

    Returns:
        Generated placeholder content or None if not a config placeholder.
    """
    if config is None:
        return None

    if name == "COVERAGE_THRESHOLDS":
        return (
            f"**Global thresholds:** Line >= {config.coverage.line}%, "
            f"Branch >= {config.coverage.branch}%, no regression vs baseline.\n\n"
            "If coverage fails: add missing tests before continuing."
        )

    return None


def load_placeholder(
    name: str,
    lang: str | None,
    backend: str | None,
    config: Config | None = None,
    no_cache: bool = False,
    platform: str | None = None,
) -> str | None:
    """Load placeholder content from config, cache, or package.

    Searches in order:
    1. Platform-based placeholder (for platform-specific values like agent file)
    2. Config-based placeholder (for configurable values like thresholds)
    3. Cached placeholder files (from tdd-llm update)
    4. Package placeholder files (bundled with package)

    Args:
        name: Placeholder name (e.g., "TESTING_FRAMEWORK").
        lang: Language name (e.g., "python").
        backend: Backend name (e.g., "jira").
        config: Config instance for config-based placeholders.
        no_cache: If True, skip cached placeholders and use package only.
        platform: Platform name ("claude" or "gemini") for platform-specific placeholders.

    Returns:
        Placeholder content or None if not found.
    """
    # Try platform-based placeholder first
    platform_value = get_platform_placeholder(name, platform)
    if platform_value is not None:
        return platform_value

    # Try config-based placeholder
    config_value = get_config_placeholder(name, config)
    if config_value is not None:
        return config_value

    # Try cached placeholder (from tdd-llm update)
    if not no_cache:
        if lang:
            cached_lang_file = get_cached_lang_placeholders_dir(lang) / f"{name}.md"
            if cached_lang_file.exists():
                return cached_lang_file.read_text(encoding="utf-8").strip()

        if backend:
            cached_backend_file = get_cached_backend_placeholders_dir(backend) / f"{name}.md"
            if cached_backend_file.exists():
                return cached_backend_file.read_text(encoding="utf-8").strip()

    # Fall back to package placeholder
    if lang:
        lang_dir = get_lang_placeholders_dir(lang)
        lang_file = lang_dir / f"{name}.md"
        if lang_file.exists():
            return lang_file.read_text(encoding="utf-8").strip()

    if backend:
        backend_dir = get_backend_placeholders_dir(backend)
        backend_file = backend_dir / f"{name}.md"
        if backend_file.exists():
            return backend_file.read_text(encoding="utf-8").strip()

    return None


def replace_placeholders(
    content: str,
    lang: str | None = None,
    backend: str | None = None,
    config: Config | None = None,
    remove_unfound: bool = True,
    no_cache: bool = False,
    platform: str | None = None,
) -> str:
    """Replace all placeholders in content.

    Args:
        content: Text content with {{PLACEHOLDER}} markers.
        lang: Language for language-specific placeholders.
        backend: Backend for backend-specific placeholders.
        config: Config instance for config-based placeholders.
        remove_unfound: If True, remove placeholders without replacements.
                       If False, leave them as-is.
        no_cache: If True, skip cached placeholders and use package only.
        platform: Platform name ("claude" or "gemini") for platform-specific placeholders.

    Returns:
        Content with placeholders replaced.
    """
    placeholders = find_placeholders(content)

    for name in placeholders:
        replacement = load_placeholder(name, lang, backend, config, no_cache, platform)

        if replacement is not None:
            content = content.replace(f"{{{{{name}}}}}", replacement)
        elif remove_unfound:
            # Remove the placeholder entirely
            content = content.replace(f"{{{{{name}}}}}", "")

    return content


def process_file(
    source: Path,
    dest: Path,
    lang: str | None = None,
    backend: str | None = None,
    config: Config | None = None,
) -> list[str]:
    """Process a single file, replacing placeholders.

    Args:
        source: Source file path.
        dest: Destination file path.
        lang: Language for placeholders.
        backend: Backend for placeholders.
        config: Config instance for config-based placeholders.

    Returns:
        List of placeholder names that were replaced.
    """
    content = source.read_text(encoding="utf-8")
    original_placeholders = find_placeholders(content)

    processed = replace_placeholders(content, lang, backend, config)

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(processed, encoding="utf-8")

    # Return which placeholders were actually replaced
    remaining = find_placeholders(processed)
    replaced = original_placeholders - remaining
    return list(replaced)


def get_all_placeholders_for_lang(lang: str) -> dict[str, str]:
    """Get all placeholder values for a language.

    Args:
        lang: Language name.

    Returns:
        Dict mapping placeholder names to their content.
    """
    lang_dir = get_lang_placeholders_dir(lang)
    if not lang_dir.exists():
        return {}

    result = {}
    for file in lang_dir.glob("*.md"):
        name = file.stem
        result[name] = file.read_text(encoding="utf-8").strip()

    return result


def get_all_placeholders_for_backend(backend: str) -> dict[str, str]:
    """Get all placeholder values for a backend.

    Args:
        backend: Backend name.

    Returns:
        Dict mapping placeholder names to their content.
    """
    backend_dir = get_backend_placeholders_dir(backend)
    if not backend_dir.exists():
        return {}

    result = {}
    for file in backend_dir.glob("*.md"):
        name = file.stem
        result[name] = file.read_text(encoding="utf-8").strip()

    return result
