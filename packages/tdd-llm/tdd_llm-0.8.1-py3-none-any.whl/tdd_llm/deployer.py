"""Deployment logic for tdd-llm templates."""

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from . import converter, placeholder
from .config import Config
from .paths import (
    get_base_templates_dir,
    get_cached_base_templates_dir,
    get_project_claude_dir,
    get_project_gemini_dir,
    get_user_claude_dir,
    get_user_gemini_dir,
)


@dataclass
class DeploymentResult:
    """Result of a deployment operation."""

    success: bool = True
    files_created: list[str] = field(default_factory=list)
    files_converted: list[str] = field(default_factory=list)
    placeholders_replaced: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


def get_target_dirs(
    target: Literal["project", "user"],
    platforms: list[str],
    project_path: Path | None = None,
) -> dict[str, Path]:
    """Get target directories for each platform.

    Args:
        target: "project" or "user" level deployment.
        platforms: List of platforms ("claude", "gemini").
        project_path: Project root for project-level deployment.

    Returns:
        Dict mapping platform names to target directories.
    """
    dirs = {}

    if target == "user":
        if "claude" in platforms:
            dirs["claude"] = get_user_claude_dir()
        if "gemini" in platforms:
            dirs["gemini"] = get_user_gemini_dir()
    else:
        if "claude" in platforms:
            dirs["claude"] = get_project_claude_dir(project_path)
        if "gemini" in platforms:
            dirs["gemini"] = get_project_gemini_dir(project_path)

    return dirs


def deploy(
    target: Literal["project", "user"] = "project",
    lang: str = "python",
    backend: str = "files",
    platforms: list[str] | None = None,
    project_path: Path | None = None,
    dry_run: bool = False,
    force: bool = False,
    config: Config | None = None,
    no_cache: bool = False,
) -> DeploymentResult:
    """Deploy TDD templates to target directories.

    Args:
        target: "project" or "user" level deployment.
        lang: Language for placeholder replacement.
        backend: Backend for placeholder replacement ("files" or "jira").
        platforms: Platforms to deploy to. Defaults to ["claude", "gemini"].
        project_path: Project root for project-level deployment.
        dry_run: If True, don't actually write files.
        force: If True, overwrite existing files.
        config: Config instance for config-based placeholders.
        no_cache: If True, use package templates ignoring cached updates.

    Returns:
        DeploymentResult with details of what was done.
    """
    if platforms is None:
        platforms = ["claude", "gemini"]

    if config is None:
        config = Config.load()

    result = DeploymentResult()

    # Use cached templates if available, otherwise fall back to package
    cached_base_dir = get_cached_base_templates_dir()
    package_base_dir = get_base_templates_dir()

    if no_cache or not cached_base_dir.exists():
        base_dir = package_base_dir
    else:
        base_dir = cached_base_dir

    target_dirs = get_target_dirs(target, platforms, project_path)

    # Get source commands directory
    source_commands = base_dir / "commands"
    if not source_commands.exists():
        result.success = False
        result.errors.append(f"Commands templates not found: {source_commands}")
        return result

    # Deploy to each platform
    for platform, target_dir in target_dirs.items():
        platform_result = _deploy_to_platform(
            source_commands,
            target_dir / "commands",
            platform,
            lang,
            backend,
            dry_run,
            force,
            config,
            no_cache,
        )

        result.files_created.extend(platform_result.files_created)
        result.files_converted.extend(platform_result.files_converted)
        result.placeholders_replaced.extend(platform_result.placeholders_replaced)
        result.errors.extend(platform_result.errors)
        result.skipped.extend(platform_result.skipped)

        if not platform_result.success:
            result.success = False

    return result


def _deploy_to_platform(
    source_dir: Path,
    target_dir: Path,
    platform: str,
    lang: str,
    backend: str,
    dry_run: bool,
    force: bool,
    config: Config,
    no_cache: bool,
) -> DeploymentResult:
    """Deploy to a single platform.

    Args:
        source_dir: Source commands directory.
        target_dir: Target commands directory (.claude/commands or .gemini/commands).
        platform: Platform name ("claude" or "gemini").
        lang: Language for placeholders.
        backend: Backend for placeholders.
        dry_run: Don't write files.
        force: Overwrite existing.
        config: Config instance for config-based placeholders.
        no_cache: If True, use package placeholders only.

    Returns:
        DeploymentResult for this platform.
    """
    result = DeploymentResult()
    is_gemini = platform == "gemini"

    # Walk through source directory
    for source_file in source_dir.rglob("*"):
        if not source_file.is_file():
            continue

        # Calculate relative path and target path
        rel_path = source_file.relative_to(source_dir)
        target_file = target_dir / rel_path

        # For Gemini, convert .md to .toml
        if is_gemini and source_file.suffix == ".md":
            target_file = target_file.with_suffix(".toml")

        # Check if target exists
        if target_file.exists() and not force:
            result.skipped.append(str(target_file))
            continue

        if dry_run:
            result.files_created.append(str(target_file))
            if is_gemini and source_file.suffix == ".md":
                result.files_converted.append(str(target_file))
            continue

        # Read and process content
        content = source_file.read_text(encoding="utf-8")

        # Replace placeholders
        processed = placeholder.replace_placeholders(
            content, lang, backend, config, no_cache=no_cache, platform=platform
        )
        found_placeholders = placeholder.find_placeholders(content)
        remaining_placeholders = placeholder.find_placeholders(processed)
        replaced = found_placeholders - remaining_placeholders
        result.placeholders_replaced.extend(replaced)

        # Convert to TOML for Gemini
        if is_gemini and source_file.suffix == ".md":
            processed = converter.md_to_toml(processed)
            result.files_converted.append(str(target_file))

        # Write file
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(processed, encoding="utf-8")
        result.files_created.append(str(target_file))

    return result


def backup_existing(target_dir: Path) -> Path | None:
    """Create a backup of existing directory.

    Args:
        target_dir: Directory to backup.

    Returns:
        Path to backup directory, or None if nothing to backup.
    """
    if not target_dir.exists():
        return None

    backup_dir = target_dir.with_name(f"{target_dir.name}.backup")

    # Remove old backup if exists
    if backup_dir.exists():
        shutil.rmtree(backup_dir)

    shutil.copytree(target_dir, backup_dir)
    return backup_dir
