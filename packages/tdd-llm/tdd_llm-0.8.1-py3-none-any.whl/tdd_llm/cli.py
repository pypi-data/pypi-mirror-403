"""CLI interface for tdd-llm."""

import functools
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Annotated

import click
import typer
from rich import print as rprint
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskID, TextColumn
from rich.table import Table

from . import __version__
from .config import (
    Config,
    CoverageThresholds,
    JiraConfig,
    get_available_backends,
    get_available_languages,
    get_global_config_path,
    get_project_config_path,
    is_first_run,
)
from .deployer import deploy
from .updater import UpdateResult, get_local_manifest, update_templates

app = typer.Typer(
    name="tdd-llm",
    help="Deploy TDD workflow templates for Claude and Gemini AI assistants.",
    no_args_is_help=True,
)
console = Console()


# ============================================================================
# Helper functions for template updates
# ============================================================================


@contextmanager
def _update_progress(quiet: bool) -> Iterator[Callable[[int, int, str], None]]:
    """Context manager to handle the progress bar for template updates."""
    if quiet:

        def noop_callback(*args, **kwargs):
            pass

        yield noop_callback
        return

    progress: Progress | None = None
    task_id: TaskID | None = None

    def progress_callback(current: int, total: int, filename: str):
        nonlocal progress, task_id
        if progress is None:
            progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("{task.completed}/{task.total}"),
            )
            progress.start()
            task_id = progress.add_task("Downloading", total=total)
        if task_id is not None:
            progress.update(task_id, completed=current)

    try:
        yield progress_callback
    finally:
        if progress:
            progress.stop()


def _display_update_result(result: UpdateResult) -> None:
    """Display the result of an update operation and exit on error."""
    if result.status == "up_to_date":
        rprint(f"[green]Already up to date[/green] (version {result.version})")
    elif result.status == "updated":
        rprint("\n[green]Templates updated![/green]")
        if result.previous_version:
            rprint(f"  Version: {result.previous_version} -> {result.version}")
        else:
            rprint(f"  Version: {result.version}")
        if result.files_updated:
            rprint(f"  Files updated: {len(result.files_updated)}")
        if result.files_unchanged:
            rprint(f"  Files unchanged: {len(result.files_unchanged)}")
    elif result.status == "error":
        rprint("\n[red]Update failed[/red]")
        for error in result.errors:
            rprint(f"  [red]Error:[/red] {error}")
        raise typer.Exit(1)


# ============================================================================
# Setup wizard
# ============================================================================


def run_setup_wizard() -> Config | None:
    """Run interactive setup wizard for first-time configuration.

    Returns:
        Config instance if setup completed, None if cancelled.
    """
    rprint("\n[bold cyan]Welcome to tdd-llm![/bold cyan]")
    rprint("This appears to be your first time running tdd-llm.")
    rprint("Let's set up your global configuration.\n")

    if not typer.confirm("Would you like to configure tdd-llm now?", default=True):
        rprint("[yellow]Setup skipped.[/yellow] You can run 'tdd-llm setup' later.\n")
        return None

    rprint()

    # Language selection
    available_langs = get_available_languages()
    if available_langs:
        rprint(f"[bold]Available languages:[/bold] {', '.join(available_langs)}")
        default_lang = "python" if "python" in available_langs else available_langs[0]
    else:
        default_lang = "python"

    language = typer.prompt(
        "Default programming language",
        default=default_lang,
    )

    # Backend selection
    available_backends = get_available_backends()
    if available_backends:
        rprint("\n[bold]Available backends:[/bold]")
        rprint("  - files: Local files (docs/epics/, docs/state.json)")
        rprint("  - jira: Jira via REST API (requires API token)")

    backend = typer.prompt(
        "\nDefault backend",
        default="files",
        type=click.Choice(["files", "jira"], case_sensitive=False),
    )

    # Jira configuration (if jira backend selected)
    jira_config = JiraConfig()
    if backend == "jira":
        rprint("\n[bold cyan]Jira Configuration[/bold cyan]")
        rprint("[dim]Configure your Jira connection. API token should be set via[/dim]")
        rprint("[dim]the JIRA_API_TOKEN environment variable.[/dim]\n")

        jira_base_url = typer.prompt(
            "Jira base URL",
            default="https://company.atlassian.net",
        )

        jira_email = typer.prompt(
            "Jira email",
            default="",
        )

        jira_project_key = typer.prompt(
            "Default project key",
            default="PROJ",
        )

        jira_config = JiraConfig(
            base_url=jira_base_url,
            email=jira_email,
            project_key=jira_project_key,
        )

        rprint("\n[yellow]Note:[/yellow] Set the JIRA_API_TOKEN environment variable")
        rprint("Generate a token at: https://id.atlassian.com/manage-profile/security/api-tokens")

    # Target selection
    rprint("\n[bold]Deployment targets:[/bold]")
    rprint("  - project: Deploy to .claude/ and .gemini/ in project directory")
    rprint("  - user: Deploy to user-level config directories")

    target = typer.prompt(
        "\nDefault deployment target",
        default="project",
        type=click.Choice(["project", "user"], case_sensitive=False),
    )

    # Platforms selection
    rprint("\n[bold]Available platforms:[/bold] claude, gemini")
    platforms_input = typer.prompt(
        "Platforms to deploy (comma-separated)",
        default="claude,gemini",
    )
    platforms = [p.strip().lower() for p in platforms_input.split(",")]

    # Coverage thresholds
    rprint("\n[bold]Coverage thresholds[/bold]")
    coverage_line = typer.prompt(
        "Line coverage threshold (%)",
        default=80,
        type=int,
    )
    coverage_line = max(0, min(100, coverage_line))

    coverage_branch = typer.prompt(
        "Branch coverage threshold (%)",
        default=70,
        type=int,
    )
    coverage_branch = max(0, min(100, coverage_branch))

    # Create and save config
    config = Config(
        default_target=target,  # type: ignore
        default_language=language,
        default_backend=backend,  # type: ignore
        platforms=platforms,
        coverage=CoverageThresholds(line=coverage_line, branch=coverage_branch),
        jira=jira_config,
    )

    saved_path = config.save(project=False)

    rprint(f"\n[green]Configuration saved to:[/green] {saved_path}")
    rprint()

    # Show summary
    table = Table(title="Global Configuration")
    table.add_column("Setting", style="bold")
    table.add_column("Value", style="cyan")

    table.add_row("Default target", config.default_target)
    table.add_row("Default language", config.default_language)
    table.add_row("Default backend", config.default_backend)
    table.add_row("Platforms", ", ".join(config.platforms))
    table.add_row("Coverage (line)", f"{config.coverage.line}%")
    table.add_row("Coverage (branch)", f"{config.coverage.branch}%")

    if config.default_backend == "jira" and config.jira.base_url:
        table.add_row("Jira URL", config.jira.base_url)
        table.add_row("Jira email", config.jira.email or "[dim]not set[/dim]")
        table.add_row("Jira project", config.jira.project_key or "[dim]not set[/dim]")

    console.print(table)
    rprint()

    return config


@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context):
    """Check for first run and offer setup wizard."""
    # Skip wizard for certain commands
    if ctx.invoked_subcommand in ("setup", "version"):
        return

    # Check if this is first run
    if is_first_run():
        run_setup_wizard()


def _setup_cmd(
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Re-run setup even if config exists"),
    ] = False,
):
    """Run interactive setup wizard to create global configuration."""
    if not is_first_run() and not force:
        rprint("[yellow]Global configuration already exists.[/yellow]")
        rprint(f"Location: {get_global_config_path()}")
        rprint("\nUse --force to re-run setup and overwrite.")
        raise typer.Exit(0)

    run_setup_wizard()


app.command(name="setup")(_setup_cmd)


@app.command()
def version():
    """Show version information."""
    rprint(f"[bold]tdd-llm[/bold] version {__version__}")


def _deploy_cmd(
    lang: Annotated[
        str,
        typer.Option("--lang", "-l", help="Programming language for placeholders"),
    ] = "",
    backend: Annotated[
        str,
        typer.Option("--backend", "-b", help="Backend for epics/stories (files or jira)"),
    ] = "",
    target: Annotated[
        str,
        typer.Option("--target", "-t", help="Deployment target (project or user)"),
    ] = "",
    platforms: Annotated[
        list[str] | None,
        typer.Option("--platform", "-p", help="Platforms to deploy (claude, gemini)"),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", "-n", help="Show what would be done without doing it"),
    ] = False,
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Overwrite existing files"),
    ] = False,
    no_cache: Annotated[
        bool,
        typer.Option("--no-cache", help="Use package templates, ignore cached updates"),
    ] = False,
    update: Annotated[
        bool,
        typer.Option(
            "--update",
            "-u",
            help="Update templates from GitHub before deploying. Use with --force to re-download.",
        ),
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option("--quiet", "-q", help="Suppress update progress output (only with --update)"),
    ] = False,
):
    """Deploy TDD templates to .claude and .gemini directories.

    Use --update --force to update templates from GitHub then deploy with overwrite.
    """
    config = Config.load()

    # If --update is specified, run update first
    if update:
        rprint("\n[bold]Step 1: Updating templates from GitHub...[/bold]\n")

        with _update_progress(quiet) as progress_callback:
            update_result = update_templates(force=force, progress_callback=progress_callback)

        _display_update_result(update_result)

        rprint("\n[bold]Step 2: Deploying TDD templates[/bold]")
        # Force no_cache=False when using --update since we just updated the cache
        no_cache = False

    # Use config defaults if not specified
    effective_lang = lang or config.default_language
    effective_backend = backend or config.default_backend
    effective_target = target or config.default_target
    effective_platforms = platforms or config.platforms

    # Validate language
    available_langs = get_available_languages()
    if available_langs and effective_lang not in available_langs:
        rprint(f"[red]Error:[/red] Unknown language '{effective_lang}'")
        rprint(f"Available: {', '.join(available_langs)}")
        raise typer.Exit(1)

    # Validate backend
    available_backends = get_available_backends()
    if available_backends and effective_backend not in available_backends:
        rprint(f"[red]Error:[/red] Unknown backend '{effective_backend}'")
        rprint(f"Available: {', '.join(available_backends)}")
        raise typer.Exit(1)

    # Validate target
    if effective_target not in ("project", "user"):
        rprint("[red]Error:[/red] Target must be 'project' or 'user'")
        raise typer.Exit(1)

    # Show what we're doing
    rprint("\n[bold]Deploying TDD templates[/bold]")
    rprint(f"  Target: [cyan]{effective_target}[/cyan]")
    rprint(f"  Language: [cyan]{effective_lang}[/cyan]")
    rprint(f"  Backend: [cyan]{effective_backend}[/cyan]")
    rprint(f"  Platforms: [cyan]{', '.join(effective_platforms)}[/cyan]")

    # Show template source
    if no_cache:
        rprint("  Templates: [dim]package (--no-cache)[/dim]")
    else:
        local_manifest = get_local_manifest()
        if local_manifest:
            rprint(f"  Templates: [green]cache v{local_manifest.version}[/green]")
        else:
            rprint("  Templates: [dim]package (no cache)[/dim]")

    if dry_run:
        rprint("  [yellow](dry run - no files will be written)[/yellow]")

    rprint()

    # Do the deployment
    result = deploy(
        target=effective_target,  # type: ignore
        lang=effective_lang,
        backend=effective_backend,
        platforms=effective_platforms,
        dry_run=dry_run,
        force=force,
        config=config,
        no_cache=no_cache,
    )

    # Show results
    if result.files_created:
        rprint(f"[green]Created {len(result.files_created)} files[/green]")
        for f in result.files_created[:10]:
            rprint(f"  - {f}")
        if len(result.files_created) > 10:
            rprint(f"  ... and {len(result.files_created) - 10} more")

    if result.files_converted:
        rprint(f"[blue]Converted {len(result.files_converted)} files to TOML[/blue]")

    if result.placeholders_replaced:
        unique_placeholders = set(result.placeholders_replaced)
        rprint(f"[cyan]Replaced {len(unique_placeholders)} placeholders[/cyan]")
        for p in sorted(unique_placeholders):
            rprint(f"  - {{{{{p}}}}}")

    if result.skipped:
        rprint(f"[yellow]Skipped {len(result.skipped)} existing files[/yellow]")
        rprint("  (use --force to overwrite)")

    if result.errors:
        rprint("[red]Errors:[/red]")
        for e in result.errors:
            rprint(f"  - {e}")
        raise typer.Exit(1)

    if result.success:
        rprint("\n[green]Done![/green]")
    else:
        raise typer.Exit(1)


app.command(name="deploy")(_deploy_cmd)


def _list_cmd():
    """List available languages and backends."""
    # Languages table
    langs = get_available_languages()
    lang_table = Table(title="Available Languages")
    lang_table.add_column("Language", style="cyan")

    if langs:
        for lang in langs:
            lang_table.add_row(lang)
    else:
        lang_table.add_row("[dim]No languages configured[/dim]")

    console.print(lang_table)
    console.print()

    # Backends table
    backends = get_available_backends()
    backend_table = Table(title="Available Backends")
    backend_table.add_column("Backend", style="cyan")
    backend_table.add_column("Description")

    if backends:
        descriptions = {
            "files": "Local files (docs/epics/, docs/state.json)",
            "jira": "Jira via REST API",
        }
        for backend in backends:
            backend_table.add_row(backend, descriptions.get(backend, ""))
    else:
        backend_table.add_row("[dim]No backends configured[/dim]", "")

    console.print(backend_table)


app.command(name="list")(_list_cmd)


def _init_cmd(
    lang: Annotated[
        str,
        typer.Option("--lang", "-l", help="Default language for this project"),
    ] = "",
    backend: Annotated[
        str,
        typer.Option("--backend", "-b", help="Default backend for this project"),
    ] = "",
    coverage_line: Annotated[
        int | None,
        typer.Option("--coverage-line", help="Line coverage threshold (%)"),
    ] = None,
    coverage_branch: Annotated[
        int | None,
        typer.Option("--coverage-branch", help="Branch coverage threshold (%)"),
    ] = None,
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Overwrite existing project config"),
    ] = False,
):
    """Initialize project-level configuration (.tdd-llm.yaml)."""
    project_config_path = get_project_config_path()

    if project_config_path.exists() and not force:
        rprint(f"[yellow]Project config already exists:[/yellow] {project_config_path}")
        rprint("Use --force to overwrite")
        raise typer.Exit(1)

    # Start with global config as base
    global_config = Config.load(include_project=False)

    # Create project config with specified or inherited values
    config = Config(
        default_language=lang or global_config.default_language,
        default_backend=backend or global_config.default_backend,  # type: ignore
        default_target="project",
        platforms=global_config.platforms,
        coverage=global_config.coverage,
    )

    # Override coverage if specified
    if coverage_line is not None:
        if not 0 <= coverage_line <= 100:
            rprint("[red]Error:[/red] Coverage must be between 0 and 100")
            raise typer.Exit(1)
        config.coverage.line = coverage_line

    if coverage_branch is not None:
        if not 0 <= coverage_branch <= 100:
            rprint("[red]Error:[/red] Coverage must be between 0 and 100")
            raise typer.Exit(1)
        config.coverage.branch = coverage_branch

    saved_path = config.save(project=True)
    rprint(f"[green]Created project config:[/green] {saved_path}")
    rprint()

    # Show what was created
    table = Table(title="Project Configuration")
    table.add_column("Setting", style="bold")
    table.add_column("Value", style="cyan")

    table.add_row("Language", config.default_language)
    table.add_row("Backend", config.default_backend)
    table.add_row("Coverage (line)", f"{config.coverage.line}%")
    table.add_row("Coverage (branch)", f"{config.coverage.branch}%")

    console.print(table)


app.command(name="init")(_init_cmd)


def _config_cmd(
    show: Annotated[
        bool,
        typer.Option("--show", "-s", help="Show current configuration"),
    ] = False,
    project: Annotated[
        bool,
        typer.Option("--project", "-p", help="Modify project config instead of global"),
    ] = False,
    set_lang: Annotated[
        str | None,
        typer.Option("--set-lang", help="Set default language"),
    ] = None,
    set_backend: Annotated[
        str | None,
        typer.Option("--set-backend", help="Set default backend"),
    ] = None,
    set_target: Annotated[
        str | None,
        typer.Option("--set-target", help="Set default target (project or user)"),
    ] = None,
    set_coverage_line: Annotated[
        int | None,
        typer.Option("--set-coverage-line", help="Set line coverage threshold (%)"),
    ] = None,
    set_coverage_branch: Annotated[
        int | None,
        typer.Option("--set-coverage-branch", help="Set branch coverage threshold (%)"),
    ] = None,
):
    """Show or modify configuration."""
    config = Config.load()
    modified = False

    if set_lang:
        config.default_language = set_lang
        modified = True
        rprint(f"Set default language to: [cyan]{set_lang}[/cyan]")

    if set_backend:
        if set_backend not in ("files", "jira"):
            rprint("[red]Error:[/red] Backend must be 'files' or 'jira'")
            raise typer.Exit(1)
        config.default_backend = set_backend  # type: ignore
        modified = True
        rprint(f"Set default backend to: [cyan]{set_backend}[/cyan]")

        # If switching to jira, prompt for Jira configuration
        if set_backend == "jira" and not config.jira.base_url:
            rprint("\n[bold cyan]Jira Configuration[/bold cyan]")
            rprint("[dim]Configure your Jira connection. API token should be set via[/dim]")
            rprint("[dim]the JIRA_API_TOKEN environment variable.[/dim]\n")

            jira_base_url = typer.prompt(
                "Jira base URL",
                default=config.jira.base_url or "https://company.atlassian.net",
            )

            jira_email = typer.prompt(
                "Jira email",
                default=config.jira.email or "",
            )

            jira_project_key = typer.prompt(
                "Default project key",
                default=config.jira.project_key or "PROJ",
            )

            config.jira = JiraConfig(
                base_url=jira_base_url,
                email=jira_email,
                project_key=jira_project_key,
                fields=config.jira.fields,
                status_map=config.jira.status_map,
            )

            rprint("\n[yellow]Note:[/yellow] Set the JIRA_API_TOKEN environment variable")
            rprint(
                "Generate a token at: https://id.atlassian.com/manage-profile/security/api-tokens"
            )

    if set_target:
        if set_target not in ("project", "user"):
            rprint("[red]Error:[/red] Target must be 'project' or 'user'")
            raise typer.Exit(1)
        config.default_target = set_target  # type: ignore
        modified = True
        rprint(f"Set default target to: [cyan]{set_target}[/cyan]")

    if set_coverage_line is not None:
        if not 0 <= set_coverage_line <= 100:
            rprint("[red]Error:[/red] Coverage must be between 0 and 100")
            raise typer.Exit(1)
        config.coverage.line = set_coverage_line
        modified = True
        rprint(f"Set line coverage threshold to: [cyan]{set_coverage_line}%[/cyan]")

    if set_coverage_branch is not None:
        if not 0 <= set_coverage_branch <= 100:
            rprint("[red]Error:[/red] Coverage must be between 0 and 100")
            raise typer.Exit(1)
        config.coverage.branch = set_coverage_branch
        modified = True
        rprint(f"Set branch coverage threshold to: [cyan]{set_coverage_branch}%[/cyan]")

    if modified:
        saved_path = config.save(project=project)
        scope = "project" if project else "global"
        rprint(f"\n[green]Configuration saved to {scope} config:[/green] {saved_path}")

    if show or not modified:
        # Show effective configuration
        table = Table(title="Effective Configuration (merged)")
        table.add_column("Setting", style="bold")
        table.add_column("Value", style="cyan")

        table.add_row("Default target", config.default_target)
        table.add_row("Default language", config.default_language)
        table.add_row("Default backend", config.default_backend)
        table.add_row("Platforms", ", ".join(config.platforms))
        table.add_row("Coverage (line)", f"{config.coverage.line}%")
        table.add_row("Coverage (branch)", f"{config.coverage.branch}%")

        console.print(table)
        console.print()

        # Show config sources
        source_table = Table(title="Configuration Sources")
        source_table.add_column("Level", style="bold")
        source_table.add_column("Path")
        source_table.add_column("Status", style="dim")

        global_path = get_global_config_path()
        global_status = "[green]exists[/green]" if global_path.exists() else "[dim]not found[/dim]"
        source_table.add_row("Global", str(global_path), global_status)

        project_path = get_project_config_path()
        project_status = (
            "[green]exists[/green]" if project_path.exists() else "[dim]not found[/dim]"
        )
        source_table.add_row("Project", str(project_path), project_status)

        console.print(source_table)

        if project_path.exists():
            rprint("\n[dim]Project config overrides global config[/dim]")


app.command(name="config")(_config_cmd)


def _update_cmd(
    force: Annotated[
        bool,
        typer.Option("--force", "-f", help="Force re-download all templates"),
    ] = False,
    quiet: Annotated[
        bool,
        typer.Option("--quiet", "-q", help="Suppress progress output"),
    ] = False,
):
    """Update templates from GitHub repository.

    Fetches the latest templates from the tdd-llm-workflow repository
    and caches them locally. Cached templates are used by deploy command.
    """
    if not quiet:
        rprint("\n[bold]Updating templates from GitHub...[/bold]\n")

    with _update_progress(quiet) as progress_callback:
        result = update_templates(force=force, progress_callback=progress_callback)

    _display_update_result(result)


app.command(name="update")(_update_cmd)


# ============================================================================
# Migrate command
# ============================================================================


def _migrate_cmd(
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", "-n", help="Show what would be done without creating issues"),
    ] = False,
    output: Annotated[
        str | None,
        typer.Option(
            "--output", "-o", help="Path for mapping file (default: docs/jira-mapping.json)"
        ),
    ] = None,
):
    """Migrate epics and tasks from files backend to Jira.

    Reads epics from docs/epics/*.md and creates corresponding
    epics and stories in Jira. Generates a mapping file with
    local IDs to Jira keys.

    Requires Jira to be configured (tdd-llm config --set-backend jira).
    """
    from pathlib import Path

    from .migrate import FilesToJiraMigrator

    config = Config.load()

    # Check Jira is configured (config or stored OAuth credentials)
    from .backends.jira.auth import JiraAuthManager

    auth_manager = JiraAuthManager(config.jira)
    if not config.jira.is_configured() and not auth_manager.is_oauth_available():
        rprint("[red]Error:[/red] Jira is not configured.")
        rprint("Run: tdd-llm jira login")
        raise typer.Exit(1)

    if dry_run:
        rprint("[yellow]Dry run mode - no issues will be created[/yellow]\n")

    migrator = FilesToJiraMigrator(
        jira_config=config.jira,
        dry_run=dry_run,
    )

    # Progress display
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
        console=console,
    ) as progress:
        task_id = progress.add_task("Migrating...", total=100)

        def update_progress(current: int, total: int, message: str):
            progress.update(task_id, completed=current, total=total, description=message)

        result = migrator.migrate(progress_callback=update_progress)

    # Show results
    rprint()
    if result.success:
        rprint("[green]Migration completed![/green]")
    else:
        rprint("[red]Migration failed![/red]")

    # Stats table
    table = Table(title="Migration Results")
    table.add_column("Item", style="bold")
    table.add_column("Count", style="cyan")

    table.add_row("Epics created", str(result.epics_created))
    table.add_row("Tasks created", str(result.tasks_created))
    if result.epics_updated:
        table.add_row("Epics updated", str(result.epics_updated))
    if result.tasks_updated:
        table.add_row("Tasks updated", str(result.tasks_updated))
    if result.epics_skipped:
        table.add_row("Epics skipped", str(result.epics_skipped))
    if result.tasks_skipped:
        table.add_row("Tasks skipped", str(result.tasks_skipped))

    console.print(table)

    # Show errors
    if result.errors:
        rprint("\n[red]Errors:[/red]")
        for error in result.errors:
            rprint(f"  - {error}")

    # Save and show mapping
    if result.mapping and not dry_run:
        output_path = Path(output) if output else None
        mapping_path = migrator.save_mapping(result.mapping, output_path)
        rprint(f"\n[green]Mapping saved to:[/green] {mapping_path}")

        # Show mapping preview
        rprint("\n[bold]ID Mapping:[/bold]")
        for local_id, jira_key in list(result.mapping.items())[:10]:
            rprint(f"  {local_id} → {jira_key}")
        if len(result.mapping) > 10:
            rprint(f"  ... and {len(result.mapping) - 10} more")

    elif result.mapping and dry_run:
        rprint("\n[bold]Would create mapping:[/bold]")
        for local_id, jira_key in list(result.mapping.items())[:10]:
            rprint(f"  {local_id} → {jira_key}")

    if not result.success:
        raise typer.Exit(1)


app.command(name="migrate")(_migrate_cmd)


# ============================================================================
# Backend commands - for AI assistants to interact with state backends
# ============================================================================

backend_app = typer.Typer(
    name="backend",
    help="Backend operations for TDD workflow state management.",
    no_args_is_help=True,
)


def _get_backend():
    """Get the configured backend instance."""
    from .backends import get_backend

    config = Config.load()
    return get_backend(config)


def _format_json(obj) -> str:
    """Format object as JSON for output."""
    import json
    from dataclasses import asdict, is_dataclass

    def serialize(o):
        if is_dataclass(o):
            return asdict(o)
        if isinstance(o, list):
            return [serialize(i) for i in o]
        return o

    return json.dumps(serialize(obj), indent=2)


def _format_status(state) -> None:
    """Format workflow state as a readable status display."""
    from rich.table import Table

    # Status icons (ASCII-compatible for Windows)
    status_icons = {
        "completed": "[green]\\[x][/green]",
        "in_progress": "[yellow]\\[~][/yellow]",
        "not_started": "[dim]\\[ ][/dim]",
    }

    # Phase display
    phase_display = {
        "analyze": "[cyan]analyze[/cyan]",
        "test": "[magenta]test[/magenta]",
        "dev": "[blue]dev[/blue]",
        "docs": "[yellow]docs[/yellow]",
        "review": "[green]review[/green]",
        "done": "[green]done[/green]",
    }

    # Collect all epics data in a single iteration
    epics_list = list(state.epics)
    total_tasks, completed_tasks, completed_epics = 0, 0, 0
    for e in epics_list:
        total_tasks += len(e.tasks)
        completed_tasks += e.completed_count
        if e.status == "completed":
            completed_epics += 1

    # Project progress summary
    console.print("\n[bold]Project Progress[/bold]")
    console.print(f"  Epics: {completed_epics}/{len(epics_list)} completed")
    console.print(f"  Tasks: {completed_tasks}/{total_tasks} completed")

    # All epics overview
    if epics_list:
        console.print("\n[bold]Epics[/bold]")
        for epic in epics_list:
            icon = status_icons.get(epic.status, "?")
            is_current = state.current_epic and epic.id == state.current_epic.id
            marker = " [cyan]<< current[/cyan]" if is_current else ""
            console.print(f"  {icon} [bold]{epic.id}[/bold] {epic.name} ({epic.progress}){marker}")

    # Current epic details with stories
    if state.current_epic:
        console.print(
            f"\n[bold]Current Epic: {state.current_epic.id}[/bold] {state.current_epic.name}"
        )

        if state.current_epic.tasks:
            table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
            table.add_column("", width=3)
            table.add_column("ID", style="bold")
            table.add_column("Story")
            table.add_column("Phase")

            for task in state.current_epic.tasks:
                icon = status_icons.get(task.status, "?")
                is_current_task = state.current_task and task.id == state.current_task.id
                task_marker = " [cyan]<<[/cyan]" if is_current_task else ""
                phase = phase_display.get(task.phase, "[dim]-[/dim]")
                title_display = f"{task.title}{task_marker}"
                table.add_row(icon, task.id, title_display, phase)

            console.print(table)
        else:
            console.print("  [dim]No stories[/dim]")

    # Current task info
    if state.current_task:
        phase_str = phase_display.get(state.current_task.phase, "[dim]none[/dim]")
        console.print(
            f"\n[bold]Current Task:[/bold] {state.current_task.id} - {state.current_task.title}"
        )
        console.print(f"  Phase: {phase_str}")

    console.print()


@backend_app.command(name="get-task")
def backend_get_task(
    task_id: Annotated[str, typer.Argument(help="Task ID (e.g., T1 or PROJ-1234)")],
):
    """Get task details from the configured backend.

    Returns JSON with task information including title, description, status,
    and acceptance criteria.
    """
    try:
        backend = _get_backend()
        task = backend.get_task(task_id)
        print(_format_json(task))
    except KeyError as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@backend_app.command(name="get-epic")
def backend_get_epic(
    epic_id: Annotated[str, typer.Argument(help="Epic ID (e.g., E1 or PROJ-100)")],
):
    """Get epic details with all tasks from the configured backend.

    Returns JSON with epic information including name, description, status,
    and all tasks.
    """
    try:
        backend = _get_backend()
        epic = backend.get_epic(epic_id)
        print(_format_json(epic))
    except KeyError as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@backend_app.command(name="status")
def backend_status(
    json_output: Annotated[
        bool,
        typer.Option("--json", "-j", help="Output raw JSON instead of formatted display"),
    ] = False,
):
    """Show project progress and workflow state.

    Displays:
    - Project progress (epics and tasks completed)
    - All epics with their status and progress
    - Current epic's stories with status and phase
    - Current task being worked on
    """
    try:
        backend = _get_backend()
        state = backend.get_state()
        if json_output:
            print(_format_json(state))
        else:
            _format_status(state)
    except Exception as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@backend_app.command(name="update-status")
def backend_update_status(
    task_id: Annotated[str, typer.Argument(help="Task ID to update")],
    status: Annotated[
        str,
        typer.Argument(
            help="New status (not_started, in_progress, completed, or Jira status name)"
        ),
    ],
):
    """Update a task's status in the configured backend.

    For Jira backend, you can use either TDD status names (not_started,
    in_progress, completed) or Jira status names (To Do, In Progress, Done).
    """
    try:
        backend = _get_backend()
        backend.update_task_status(task_id, status)
        rprint(f"[green]Updated {task_id} status to {status}[/green]")
    except KeyError as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@backend_app.command(name="set-phase")
def backend_set_phase(
    task_id: Annotated[str, typer.Argument(help="Task ID")],
    phase: Annotated[
        str,
        typer.Argument(help="TDD phase (analyze, test, dev, docs, review)"),
    ],
):
    """Set the TDD phase for a task.

    For Jira backend, this adds a label like 'tdd:test' to the issue.
    For files backend, this updates .tdd-state.local.json.
    """
    valid_phases = ["analyze", "test", "dev", "docs", "review"]
    if phase not in valid_phases:
        rprint(f"[red]Error:[/red] Invalid phase '{phase}'")
        rprint(f"Valid phases: {', '.join(valid_phases)}")
        raise typer.Exit(1)

    try:
        backend = _get_backend()
        backend.set_phase(task_id, phase)
        rprint(f"[green]Set {task_id} phase to {phase}[/green]")
    except Exception as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@backend_app.command(name="set-current")
def backend_set_current(
    epic_id: Annotated[str, typer.Argument(help="Epic ID")],
    task_id: Annotated[str | None, typer.Argument(help="Task ID (optional)")] = None,
):
    """Set the current active task.

    This updates the local session state to track which task is being worked on.
    """
    try:
        backend = _get_backend()
        backend.set_current_task(epic_id, task_id)
        if task_id:
            rprint(f"[green]Set current task to {epic_id}/{task_id}[/green]")
        else:
            rprint(f"[green]Set current epic to {epic_id}[/green]")
    except Exception as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@backend_app.command(name="next-task")
def backend_next_task(
    epic_id: Annotated[str, typer.Argument(help="Epic ID")],
):
    """Get the next incomplete task in an epic.

    Returns JSON with the next task to work on, or an error if all tasks
    are completed.
    """
    try:
        backend = _get_backend()
        task = backend.get_next_task(epic_id)
        if task:
            print(_format_json(task))
        else:
            rprint("[yellow]All tasks in epic are completed.[/yellow]")
    except KeyError as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@backend_app.command(name="add-comment")
def backend_add_comment(
    task_id: Annotated[str, typer.Argument(help="Task ID")],
    comment: Annotated[str, typer.Argument(help="Comment text")],
):
    """Add a comment to a task (Jira backend only).

    For Jira backend, adds a comment to the issue.
    For files backend, this command is a no-op.
    """
    try:
        backend = _get_backend()
        if backend.add_comment(task_id, comment):
            rprint(f"[green]Added comment to {task_id}[/green]")
        else:
            rprint("[yellow]Comments not supported for this backend.[/yellow]")
    except Exception as e:
        rprint(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


def handle_cli_errors(func):
    """Decorator to handle common CLI errors for backend commands."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (KeyError, ValueError) as e:
            rprint(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)
        except Exception as e:
            rprint(f"[red]Error:[/red] {e}")
            raise typer.Exit(1)

    return wrapper


@backend_app.command(name="list-epics")
@handle_cli_errors
def backend_list_epics(
    status: Annotated[
        str | None,
        typer.Option("--status", "-s", help="Filter by status"),
    ] = None,
):
    """List all epics in the project.

    Returns JSON array with epic details including progress.
    """
    backend = _get_backend()
    epics = backend.list_epics(status=status)
    print(_format_json(epics))


@backend_app.command(name="list-stories")
@handle_cli_errors
def backend_list_stories(
    epic_id: Annotated[str, typer.Argument(help="Epic ID to list stories from")],
    status: Annotated[
        str | None,
        typer.Option("--status", "-s", help="Filter by status"),
    ] = None,
):
    """List all stories/tasks in an epic.

    Returns JSON array with task details.
    """
    backend = _get_backend()
    epic = backend.get_epic(epic_id)
    tasks = epic.tasks

    # Filter by status if specified
    if status:
        tasks = [t for t in tasks if t.status == status]

    print(_format_json(tasks))


@backend_app.command(name="create-epic")
@handle_cli_errors
def backend_create_epic(
    name: Annotated[str, typer.Argument(help="Epic name/title")],
    description: Annotated[str, typer.Argument(help="Epic description")],
    epic_id: Annotated[
        str | None,
        typer.Option("--id", "-i", help="Epic ID (auto-generated if not provided)"),
    ] = None,
):
    """Create a new epic.

    For files backend, creates a markdown file in docs/epics/ and updates state.json.
    For Jira backend, creates an Epic issue in the configured project.

    Returns JSON with the created epic details.
    """
    backend = _get_backend()
    epic = backend.create_epic(name=name, description=description, epic_id=epic_id)
    print(_format_json(epic))
    rprint(f"\n[green]Created epic {epic.id}[/green]")


@backend_app.command(name="create-story")
@handle_cli_errors
def backend_create_story(
    epic_id: Annotated[str, typer.Argument(help="Parent epic ID")],
    title: Annotated[str, typer.Argument(help="Story/task title")],
    description: Annotated[str, typer.Argument(help="Story/task description")],
    acceptance_criteria: Annotated[
        str | None,
        typer.Option("--ac", "-a", help="Acceptance criteria"),
    ] = None,
    task_id: Annotated[
        str | None,
        typer.Option("--id", "-i", help="Task ID (auto-generated if not provided)"),
    ] = None,
):
    """Create a new story/task in an epic.

    For files backend, adds a task section to the epic's markdown file.
    For Jira backend, creates a Story issue linked to the epic.

    Returns JSON with the created task details.
    """
    backend = _get_backend()
    task = backend.create_task(
        epic_id=epic_id,
        title=title,
        description=description,
        acceptance_criteria=acceptance_criteria,
        task_id=task_id,
    )
    print(_format_json(task))
    rprint(f"\n[green]Created task {task.id} in epic {epic_id}[/green]")


# Alias: create-task -> create-story (LLMs often try this name)
backend_app.command(name="create-task")(backend_create_story)


@backend_app.command(name="update-story")
@handle_cli_errors
def backend_update_story(
    task_id: Annotated[str, typer.Argument(help="Task/story ID to update")],
    title: Annotated[
        str | None,
        typer.Option("--title", "-t", help="New title"),
    ] = None,
    description: Annotated[
        str | None,
        typer.Option("--description", "-d", help="New description"),
    ] = None,
    acceptance_criteria: Annotated[
        str | None,
        typer.Option("--ac", "-a", help="New acceptance criteria"),
    ] = None,
):
    """Update a story/task's title, description, or acceptance criteria.

    For Jira backend, updates the issue fields.
    For files backend, updates the markdown file.

    At least one of --title, --description, or --ac must be provided.
    """
    if not any([title, description, acceptance_criteria]):
        rprint("[red]Error:[/red] At least one of --title, --description, or --ac must be provided")
        raise typer.Exit(1)

    from .backends.jira.backend import JiraBackend
    from .backends.jira.client import markdown_to_adf

    backend = _get_backend()

    if isinstance(backend, JiraBackend):
        # Build Jira update payload
        fields: dict = {}
        if title:
            fields["summary"] = title
        if description:
            fields["description"] = markdown_to_adf(description)
        if acceptance_criteria:
            # Check if AC field is configured
            ac_field = backend.config.jira.field_mappings.acceptance_criteria
            if ac_field:
                fields[ac_field] = markdown_to_adf(acceptance_criteria)
            else:
                rprint("[yellow]Warning:[/yellow] AC field not configured, skipping")

        if fields:
            backend.client.update_issue(task_id, {"fields": fields})
            rprint(f"[green]Updated {task_id}[/green]")
    else:
        # Files backend - direct markdown edit
        rprint("[yellow]For files backend, edit the epic markdown file directly:[/yellow]")
        rprint("  1. Find: docs/epics/{epic_id}-*.md")
        rprint(f"  2. Locate section starting with: ## {task_id}:")
        rprint("  3. Edit title/description/acceptance criteria")
        raise typer.Exit(1)


@backend_app.command(name="get-transitions")
@handle_cli_errors
def backend_get_transitions(
    task_id: Annotated[str, typer.Argument(help="Task/story ID")],
):
    """Get available status transitions for a task.

    Shows what statuses the task can be transitioned to.
    Useful for understanding workflow constraints.

    Returns JSON array of available transitions.
    """
    from .backends.jira.backend import JiraBackend

    backend = _get_backend()

    if isinstance(backend, JiraBackend):
        transitions = backend.client.get_transitions(task_id)
        # Simplify output for LLM consumption
        result = [
            {
                "id": t["id"],
                "name": t["name"],
                "to_status": t.get("to", {}).get("name", "Unknown"),
            }
            for t in transitions
        ]
        print(_format_json(result))
    else:
        rprint("[yellow]Transitions not available for files backend[/yellow]")
        raise typer.Exit(1)


@backend_app.command(name="list-comments")
@handle_cli_errors
def backend_list_comments(
    task_id: Annotated[str, typer.Argument(help="Task/story ID")],
):
    """List all comments on a task.

    Returns JSON array of comments with author, body, and date.
    """
    from .backends.jira.backend import JiraBackend

    backend = _get_backend()

    if isinstance(backend, JiraBackend):
        comments = backend.client.get_comments(task_id)
        print(_format_json(comments))
    else:
        rprint("[yellow]Comments not available for files backend[/yellow]")
        raise typer.Exit(1)


@backend_app.command(name="update-labels")
@handle_cli_errors
def backend_update_labels(
    task_id: Annotated[str, typer.Argument(help="Task/story ID")],
    add: Annotated[
        list[str] | None,
        typer.Option("--add", "-a", help="Labels to add"),
    ] = None,
    remove: Annotated[
        list[str] | None,
        typer.Option("--remove", "-r", help="Labels to remove"),
    ] = None,
):
    """Add or remove labels from a task.

    Examples:
        tdd-llm backend update-labels PROJ-123 --add bug --add urgent
        tdd-llm backend update-labels PROJ-123 --remove wontfix
    """
    if not add and not remove:
        rprint("[red]Error:[/red] At least one of --add or --remove must be provided")
        raise typer.Exit(1)

    from .backends.jira.backend import JiraBackend

    backend = _get_backend()

    if isinstance(backend, JiraBackend):
        backend.client.update_labels(task_id, add=add, remove=remove)
        rprint(f"[green]Updated labels on {task_id}[/green]")
    else:
        rprint("[yellow]Labels not available for files backend[/yellow]")
        raise typer.Exit(1)


@backend_app.command(name="search")
@handle_cli_errors
def backend_search(
    jql: Annotated[str, typer.Argument(help="JQL query string")],
    max_results: Annotated[
        int,
        typer.Option("--max", "-m", help="Maximum results to return"),
    ] = 50,
):
    """Search for issues using JQL (Jira Query Language).

    Examples:
        tdd-llm backend search "project = PROJ AND status = 'In Progress'"
        tdd-llm backend search "assignee = currentUser() AND sprint in openSprints()"
        tdd-llm backend search "labels = bug AND created >= -7d" --max 10

    Returns JSON array of matching issues.
    """
    from .backends.jira.backend import JiraBackend

    backend = _get_backend()

    if isinstance(backend, JiraBackend):
        issues, _ = backend.client.search(jql, max_results=max_results)
        # Convert to simple dict format
        result = [
            {
                "key": issue.key,
                "summary": issue.summary,
                "status": issue.status,
                "type": issue.issue_type,
                "labels": issue.labels,
            }
            for issue in issues
        ]
        print(_format_json(result))
    else:
        rprint("[yellow]JQL search not available for files backend[/yellow]")
        raise typer.Exit(1)


app.add_typer(backend_app)


# ============================================================================
# Jira authentication commands
# ============================================================================

jira_app = typer.Typer(
    name="jira",
    help="Jira authentication and configuration.",
    no_args_is_help=True,
)


@jira_app.command(name="login")
def jira_login(
    port: Annotated[
        int,
        typer.Option("--port", "-p", help="Callback server port"),
    ] = 8089,
    no_browser: Annotated[
        bool,
        typer.Option("--no-browser", help="Don't auto-open browser"),
    ] = False,
    timeout: Annotated[
        int,
        typer.Option("--timeout", "-t", help="Authorization timeout in seconds"),
    ] = 300,
):
    """Authenticate with Jira using OAuth 2.0.

    This will:
    1. Open your browser to Atlassian authorization page
    2. Start a local server to receive the callback
    3. Exchange the authorization code for access tokens
    4. Store encrypted tokens locally

    If this is your first time, you'll be prompted for your OAuth credentials.
    Create an OAuth app at https://developer.atlassian.com/console/myapps/ first.
    """
    from .backends.jira.auth import JiraAuthManager, OAuthConfigurationError, OAuthError

    config = Config.load()
    auth_manager = JiraAuthManager(config.jira)

    # Check if we need to get credentials from user
    client_id = None
    client_secret = None

    if not auth_manager.is_oauth_available():
        rprint("\n[bold cyan]Jira OAuth Setup[/bold cyan]")
        rprint("No OAuth credentials found. Let's set them up.\n")
        rprint("First, create an OAuth app at:")
        rprint("  [cyan]https://developer.atlassian.com/console/myapps/[/cyan]\n")
        rprint("Configure your app with:")
        rprint(f"  Callback URL: [cyan]http://localhost:{port}/callback[/cyan]")
        rprint(
            "  Permissions: [dim]Jira API > read:jira-work, write:jira-work, read:jira-user[/dim]\n"
        )

        client_id = typer.prompt("OAuth Client ID")
        client_secret = typer.prompt("OAuth Client Secret", hide_input=True)

    rprint("\n[bold cyan]Jira OAuth Login[/bold cyan]")
    rprint(f"Starting callback server on port {port}...")

    if not no_browser:
        rprint("Opening browser for Atlassian authorization...")
    else:
        rprint("Browser auto-open disabled. URL will be displayed below.")

    rprint(f"\nWaiting for authorization (timeout: {timeout} seconds)...\n")

    try:
        tokens = auth_manager.login(
            port=port,
            open_browser=not no_browser,
            timeout=timeout,
            client_id=client_id,
            client_secret=client_secret,
        )
        rprint("[green]Successfully authenticated![/green]")
        rprint(f"  Site: [cyan]{tokens.site_url}[/cyan]")
        rprint(f"  Cloud ID: [dim]{tokens.cloud_id[:8]}...[/dim]")
        rprint(f"  Credentials and tokens stored in: [dim]{auth_manager.storage.config_dir}[/dim]")
    except OAuthConfigurationError as e:
        rprint(f"\n[red]Configuration error:[/red] {e}")
        raise typer.Exit(1)
    except OAuthError as e:
        rprint(f"\n[red]Login failed:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        rprint(f"\n[red]Unexpected error:[/red] {e}")
        raise typer.Exit(1)


@jira_app.command(name="logout")
def jira_logout(
    keep_credentials: Annotated[
        bool,
        typer.Option("--keep-credentials", help="Keep stored OAuth credentials"),
    ] = False,
):
    """Remove stored Jira OAuth tokens and credentials."""
    from .backends.jira.auth import TokenStorage

    storage = TokenStorage()
    tokens = storage.load_tokens()
    credentials = storage.load_credentials()

    if tokens is None and credentials is None:
        rprint("[yellow]No OAuth data stored.[/yellow]")
        raise typer.Exit(0)

    if tokens:
        rprint(f"Current authentication: [cyan]{tokens.site_url}[/cyan]")

    if keep_credentials:
        if typer.confirm("Remove OAuth tokens (keep credentials)?", default=False):
            storage.delete_tokens()
            rprint("[green]OAuth tokens removed. Credentials kept.[/green]")
        else:
            rprint("Cancelled.")
    else:
        if typer.confirm("Remove all OAuth data (tokens and credentials)?", default=False):
            storage.delete_all()
            rprint("[green]OAuth tokens and credentials removed.[/green]")
        else:
            rprint("Cancelled.")


@jira_app.command(name="status")
def jira_auth_status():
    """Show Jira authentication status."""
    from datetime import datetime

    from .backends.jira.auth import TokenStorage

    config = Config.load()
    storage = TokenStorage()

    table = Table(title="Jira Authentication Status")
    table.add_column("Setting", style="bold")
    table.add_column("Value")

    # Check stored credentials
    credentials = storage.load_credentials()
    if credentials:
        table.add_row(
            "Stored Credentials",
            "[green]yes[/green]",
        )
        client_id_display = (
            f"{credentials.client_id[:12]}..."
            if len(credentials.client_id) > 12
            else credentials.client_id
        )
        table.add_row("Client ID", client_id_display)
    else:
        # Check env var / config
        oauth_configured = config.jira.is_oauth_configured()
        table.add_row(
            "OAuth (env vars)",
            "[green]configured[/green]" if oauth_configured else "[dim]not set[/dim]",
        )

    # Check stored tokens
    tokens = storage.load_tokens()

    if tokens:
        expires = datetime.fromtimestamp(tokens.expires_at)
        is_expired = tokens.is_expired()

        table.add_row(
            "Token Status",
            "[red]expired[/red]" if is_expired else "[green]valid[/green]",
        )
        table.add_row("Expires", expires.strftime("%Y-%m-%d %H:%M:%S"))
        table.add_row("Site", tokens.site_url)
        table.add_row("Cloud ID", f"{tokens.cloud_id[:8]}...")
    else:
        table.add_row("Token Status", "[yellow]not logged in[/yellow]")

    # Check API token fallback
    table.add_row("", "")  # Separator
    table.add_row("[dim]API Token Fallback[/dim]", "")
    has_api_token = bool(config.jira.api_token)
    table.add_row(
        "API Token",
        "[green]set[/green]" if has_api_token else "[dim]not set[/dim]",
    )
    if config.jira.effective_base_url:
        table.add_row("Base URL", config.jira.effective_base_url)
    if config.jira.effective_email:
        table.add_row("Email", config.jira.effective_email)

    console.print(table)

    # Summary
    rprint()
    if tokens and not tokens.is_expired():
        rprint("[green]Ready to use Jira with OAuth.[/green]")
    elif has_api_token and config.jira.effective_base_url and config.jira.effective_email:
        rprint("[yellow]Using API token authentication (OAuth not configured or expired).[/yellow]")
    else:
        rprint("[red]Jira not configured.[/red] Run 'tdd-llm jira login' or set JIRA_API_TOKEN.")


app.add_typer(jira_app)


if __name__ == "__main__":
    app()
