"""CLI commands for dbt-unity-lineage (V2)."""

from __future__ import annotations

import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskID, TextColumn
from rich.table import Table

from . import __version__
from .config import Config, find_config_file, load_config
from .errors import (
    EXIT_ERROR,
    categorize_api_error,
)
from .mapping import infer_system_type_from_url
from .profiles import DatabricksConnection, get_databricks_connection
from .scanner import (
    Exposure,
    ScanResult,
    SourceTable,
    get_missing_source_systems,
    scan_config,
)
from .unity_catalog import UnityCatalogClient

GITHUB_RAW_BASE = "https://raw.githubusercontent.com/dbt-conceptual/dbt-unity-lineage"

console = Console()
error_console = Console(stderr=True)


def fetch_claude_context() -> str:
    """Fetch CLAUDE.md from GitHub for the current version.

    Tries the version tag first, falls back to main branch.

    Returns:
        The CLAUDE.md content.

    Raises:
        SystemExit: If the content cannot be fetched.
    """
    urls = [
        f"{GITHUB_RAW_BASE}/v{__version__}/CLAUDE.md",
        f"{GITHUB_RAW_BASE}/main/CLAUDE.md",
    ]

    for url in urls:
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                return response.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                continue  # Try next URL
            error_console.print(f"[red]Error fetching CLAUDE.md: HTTP {e.code}[/red]")
            sys.exit(1)
        except urllib.error.URLError as e:
            error_console.print(f"[red]Error fetching CLAUDE.md: {e.reason}[/red]")
            error_console.print("[dim]Check your network connection.[/dim]")
            sys.exit(1)

    # All URLs failed with 404
    error_console.print("[red]Error: CLAUDE.md not found on GitHub.[/red]")
    error_console.print(f"[dim]Tried: {', '.join(urls)}[/dim]")
    sys.exit(1)


class Context:
    """CLI context object."""

    def __init__(self) -> None:
        self.verbose: bool = False
        self.quiet: bool = False
        self.config: Optional[Config] = None
        self.connection: Optional[DatabricksConnection] = None
        self.client: Optional[UnityCatalogClient] = None
        self.project_dir: Optional[Path] = None


pass_context = click.make_pass_decorator(Context, ensure=True)


@click.group(invoke_without_command=True)
@click.option(
    "--project-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Path to dbt project directory",
)
@click.option(
    "--profiles-dir",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    help="Path to profiles directory",
)
@click.option("--profile", help="Profile to use")
@click.option("--target", help="Target to use")
@click.option("-v", "--verbose", is_flag=True, help="Verbose output")
@click.option("-q", "--quiet", is_flag=True, help="Minimal output")
@click.option(
    "--claude",
    "show_claude",
    is_flag=True,
    is_eager=True,
    expose_value=True,
    help="Output Claude AI context for this version",
)
@click.version_option(version=__version__)
@click.pass_context
def main(
    click_ctx: click.Context,
    project_dir: Optional[Path],
    profiles_dir: Optional[Path],
    profile: Optional[str],
    target: Optional[str],
    verbose: bool,
    quiet: bool,
    show_claude: bool,
) -> None:
    """Push dbt lineage to Databricks Unity Catalog.

    Scans dbt source and exposure definitions from configured folders
    and pushes external lineage to Unity Catalog.
    """
    # Handle --claude flag early and exit
    if show_claude:
        content = fetch_claude_context()
        click.echo(content)
        click_ctx.exit(0)

    # If no subcommand is invoked, show help
    if click_ctx.invoked_subcommand is None:
        click.echo(click_ctx.get_help())
        click_ctx.exit(0)

    # Get or create our custom context
    ctx = click_ctx.ensure_object(Context)
    ctx.verbose = verbose
    ctx.quiet = quiet
    ctx.project_dir = project_dir

    # Find and load config
    config_path = find_config_file(project_dir)

    if config_path and config_path.exists():
        try:
            ctx.config = load_config(config_path)
            if verbose:
                console.print(f"[dim]Loaded config from {config_path}[/dim]")
        except Exception as e:
            error_console.print(f"[red]Error loading config: {e}[/red]")
            sys.exit(EXIT_ERROR)
    else:
        if verbose:
            console.print("[dim]No config file found[/dim]")

    # Get Databricks connection (optional - not all commands need it)
    try:
        ctx.connection = get_databricks_connection(
            profiles_dir=profiles_dir,
            profile_name=profile,
            target_name=target,
            project_dir=project_dir,
        )
        ctx.client = UnityCatalogClient(ctx.connection)
        if verbose:
            console.print(f"[dim]Connected to {ctx.connection.host}[/dim]")
    except FileNotFoundError:
        if verbose:
            console.print("[dim]No profiles.yml found, connection not established[/dim]")
    except Exception as e:
        if verbose:
            error_console.print(f"[yellow]Warning: Could not establish connection: {e}[/yellow]")


# =============================================================================
# init command
# =============================================================================

CONFIG_TEMPLATE = """\
# dbt-unity-lineage configuration
# https://github.com/dbt-conceptual/dbt-unity-lineage
version: 1

project:
  name: my_project                    # Used for tagging objects in Unity Catalog

configuration:
  # Validation rules (optional, all default to false)
  # Supports ENV vars: ${REQUIRE_OWNER:-false}
  validation:
    require_owner: false
    require_description: false
    require_source_system: false

  # Define layers and folders to scan for sources/exposures
  layers:
    bronze:
      sources:
        folders:
          - models/bronze/erp
          # - models/bronze/crm

    # silver:
    #   sources:
    #     folders:
    #       - models/silver/shared

    gold:
      exposures:
        folders:
          - models/gold/dashboards
          # - models/gold/reports

# Define upstream source systems (optional)
# Sources reference these via meta.uc_source tag
# Uncomment and configure as needed:
# source_systems:
#   erp:
  #   system_type: SAP                 # Required - see docs for valid types
  #   description: SAP ECC Production
  #   owner: data-team@example.com
  #   table_lineage: true              # Optional - enable table-level lineage
  #   meta_columns:                    # Columns to exclude from lineage
  #     - _loaded_at
  #     - _batch_id

  # crm:
  #   system_type: Salesforce
  #   description: Salesforce CRM
"""


@main.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default="models/lineage/unity_lineage.yml",
    help="Output file path",
)
@click.option("--force", "-f", is_flag=True, help="Overwrite existing file")
def init(output: Path, force: bool) -> None:
    """Create a unity_lineage.yml config file."""
    if output.exists() and not force:
        error_console.print(f"[red]Error: {output} already exists. Use --force to overwrite.[/red]")
        sys.exit(1)

    # Create parent directories if needed
    output.parent.mkdir(parents=True, exist_ok=True)

    output.write_text(CONFIG_TEMPLATE)
    console.print(f"[green]Created {output}[/green]")
    console.print("[dim]Edit the file to configure your layers and source systems, then run:[/dim]")
    console.print("[dim]  dbt-unity-lineage validate[/dim]")
    console.print("[dim]  dbt-unity-lineage scan[/dim]")


# =============================================================================
# validate command
# =============================================================================


@main.command()
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "md"]),
    default="table",
    help="Output format",
)
@pass_context
def validate(ctx: Context, output_format: str) -> None:
    """Validate configuration and project alignment."""
    if ctx.config is None:
        error_console.print("[red]Error: No config file found.[/red]")
        error_console.print("[dim]Run 'dbt-unity-lineage init' to create one.[/dim]")
        sys.exit(EXIT_ERROR)

    errors: list[str] = []
    warnings: list[str] = []

    # Validate config structure
    if not ctx.config.configuration.layers:
        errors.append("No layers defined in configuration.layers")

    # Check folders exist
    base_dir = ctx.project_dir or Path.cwd()
    for layer_name, layer in ctx.config.configuration.layers.items():
        for folder in layer.source_folders:
            folder_path = base_dir / folder
            if not folder_path.exists():
                warnings.append(f"Source folder does not exist: {folder} (layer: {layer_name})")

        for folder in layer.exposure_folders:
            folder_path = base_dir / folder
            if not folder_path.exists():
                warnings.append(f"Exposure folder does not exist: {folder} (layer: {layer_name})")

    # Scan and check for missing source systems
    scan_result = scan_config(ctx.config, ctx.project_dir)
    errors.extend(scan_result.errors)
    warnings.extend(scan_result.warnings)

    missing = get_missing_source_systems(scan_result, ctx.config)
    if missing:
        if ctx.config.configuration.validation.require_source_system:
            for uc_source, tables in missing.items():
                table_names = ", ".join(t.qualified_name for t in tables[:3])
                if len(tables) > 3:
                    table_names += f" (+{len(tables) - 3} more)"
                errors.append(
                    f"Source system '{uc_source}' not defined "
                    f"(referenced by: {table_names})"
                )
        else:
            for uc_source, tables in missing.items():
                warnings.append(
                    f"Source system '{uc_source}' not defined "
                    f"(referenced by {len(tables)} sources)"
                )

    # Check validation rules
    validation = ctx.config.configuration.validation
    for table in scan_result.all_source_tables:
        if validation.require_description and not table.description:
            errors.append(f"Source {table.qualified_name} missing description")
        if validation.require_source_system and not table.uc_source:
            errors.append(f"Source {table.qualified_name} missing meta.uc_source")

    # Output results
    if output_format == "json":
        import json

        result = {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "sources_found": scan_result.source_count,
            "exposures_found": scan_result.exposure_count,
        }
        click.echo(json.dumps(result, indent=2))
    elif output_format == "md":
        console.print("## Validation Results\n")
        if errors:
            console.print("### Errors")
            for error in errors:
                console.print(f"- :x: {error}")
            console.print()
        if warnings:
            console.print("### Warnings")
            for warning in warnings:
                console.print(f"- :warning: {warning}")
            console.print()
        if not errors and not warnings:
            console.print(":white_check_mark: Configuration is valid\n")
        console.print(f"**Sources found:** {scan_result.source_count}")
        console.print(f"**Exposures found:** {scan_result.exposure_count}")
    else:
        # Table format
        if errors:
            console.print("[bold red]Errors:[/bold red]")
            for error in errors:
                console.print(f"  [red]✗[/red] {error}")
        if warnings:
            console.print("[bold yellow]Warnings:[/bold yellow]")
            for warning in warnings:
                console.print(f"  [yellow]![/yellow] {warning}")
        if not errors and not warnings:
            console.print("[green]✓ Configuration is valid[/green]")

        console.print(f"\n[dim]Sources found: {scan_result.source_count}[/dim]")
        console.print(f"[dim]Exposures found: {scan_result.exposure_count}[/dim]")

    if errors:
        sys.exit(EXIT_ERROR)


# =============================================================================
# scan command
# =============================================================================


@main.command()
@click.option("--select", "select_pattern", help="Select folders to scan (e.g., 'bronze/*')")
@click.option(
    "--type",
    "scan_type",
    type=click.Choice(["source", "exposure"]),
    help="Filter by type",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "md"]),
    default="table",
    help="Output format",
)
@pass_context
def scan(
    ctx: Context,
    select_pattern: Optional[str],
    scan_type: Optional[str],
    output_format: str,
) -> None:
    """Scan configured folders for sources and exposures."""
    if ctx.config is None:
        error_console.print("[red]Error: No config file found.[/red]")
        error_console.print("[dim]Run 'dbt-unity-lineage init' to create one.[/dim]")
        sys.exit(EXIT_ERROR)

    # Determine scan type
    type_filter = "all"
    if scan_type == "source":
        type_filter = "sources"
    elif scan_type == "exposure":
        type_filter = "exposures"

    # Scan folders
    result = scan_config(ctx.config, ctx.project_dir, select_pattern, type_filter)

    # Output results
    if output_format == "json":
        import json

        data = {
            "sources": [
                {
                    "name": s.name,
                    "tables": [
                        {
                            "name": t.name,
                            "qualified_name": t.qualified_name,
                            "uc_source": t.uc_source,
                            "description": t.description,
                            "layer": t.layer,
                            "folder": t.folder,
                        }
                        for t in s.tables
                    ],
                }
                for s in result.sources
            ],
            "exposures": [
                {
                    "name": e.name,
                    "type": e.type,
                    "url": e.url,
                    "layer": e.layer,
                    "folder": e.folder,
                }
                for e in result.exposures
            ],
            "errors": result.errors,
            "warnings": result.warnings,
        }
        click.echo(json.dumps(data, indent=2))

    elif output_format == "md":
        _output_scan_markdown(result)

    else:
        _output_scan_table(result)

    if result.errors:
        sys.exit(EXIT_ERROR)


def _output_scan_table(result: ScanResult) -> None:
    """Output scan results as a rich table."""
    if result.all_source_tables:
        table = Table(title="Sources")
        table.add_column("Source", style="cyan")
        table.add_column("Table", style="cyan")
        table.add_column("UC Source", style="green")
        table.add_column("Layer")
        table.add_column("Folder", style="dim")

        for source_table in result.all_source_tables:
            table.add_row(
                source_table.source_name,
                source_table.name,
                source_table.uc_source or "-",
                source_table.layer or "-",
                source_table.folder or "-",
            )
        console.print(table)
        console.print()

    if result.exposures:
        table = Table(title="Exposures")
        table.add_column("Name", style="cyan")
        table.add_column("Type")
        table.add_column("URL", style="blue")
        table.add_column("Layer")
        table.add_column("Folder", style="dim")

        for exposure in result.exposures:
            if exposure.url and len(exposure.url) > 50:
                url_display = exposure.url[:50] + "..."
            else:
                url_display = exposure.url or "-"
            table.add_row(
                exposure.name,
                exposure.type,
                url_display,
                exposure.layer or "-",
                exposure.folder or "-",
            )
        console.print(table)
        console.print()

    if result.warnings:
        console.print("[yellow]Warnings:[/yellow]")
        for warning in result.warnings:
            console.print(f"  [yellow]![/yellow] {warning}")

    total = f"{result.source_count} sources, {result.exposure_count} exposures"
    console.print(f"[dim]Total: {total}[/dim]")


def _output_scan_markdown(result: ScanResult) -> None:
    """Output scan results as markdown."""
    console.print("## Scan Results\n")

    if result.all_source_tables:
        console.print("### Sources\n")
        console.print("| Source | Table | UC Source | Layer |")
        console.print("|--------|-------|-----------|-------|")
        for t in result.all_source_tables:
            uc_src = t.uc_source or "-"
            layer = t.layer or "-"
            console.print(f"| {t.source_name} | {t.name} | {uc_src} | {layer} |")
        console.print()

    if result.exposures:
        console.print("### Exposures\n")
        console.print("| Name | Type | URL | Layer |")
        console.print("|------|------|-----|-------|")
        for e in result.exposures:
            url = e.url or "-"
            console.print(f"| {e.name} | {e.type} | {url} | {e.layer or '-'} |")
        console.print()

    console.print(f"**Total:** {result.source_count} sources, {result.exposure_count} exposures")


# =============================================================================
# sync command
# =============================================================================


@main.command()
@click.option("--select", "select_pattern", help="Select folders to sync")
@click.option(
    "--type",
    "scan_type",
    type=click.Choice(["source", "exposure"]),
    help="Filter by type",
)
@click.option("--dry-run", is_flag=True, help="Show what would change")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "md"]),
    default="table",
    help="Output format",
)
@pass_context
def sync(
    ctx: Context,
    select_pattern: Optional[str],
    scan_type: Optional[str],
    dry_run: bool,
    output_format: str,
) -> None:
    """Sync source definitions with source_systems configuration.

    Discovers uc_source references in sources that are not defined
    in source_systems and creates placeholder entries.
    """
    if ctx.config is None:
        error_console.print("[red]Error: No config file found.[/red]")
        sys.exit(EXIT_ERROR)

    # Determine scan type
    type_filter = "sources" if scan_type == "source" else "all"

    # Scan folders
    result = scan_config(ctx.config, ctx.project_dir, select_pattern, type_filter)

    # Find missing source systems
    missing = get_missing_source_systems(result, ctx.config)

    if not missing:
        if not ctx.quiet:
            console.print("[green]All source systems are defined.[/green]")
        return

    # Output what would be added
    if output_format == "json":
        import json

        data = {
            "dry_run": dry_run,
            "missing_source_systems": {
                key: [t.qualified_name for t in tables] for key, tables in missing.items()
            },
        }
        click.echo(json.dumps(data, indent=2))
    else:
        if dry_run:
            console.print("[bold]Dry run - would add the following source_systems:[/bold]")
        else:
            console.print("[bold]Missing source_systems to add:[/bold]")

        for uc_source, tables in missing.items():
            console.print(f"\n  [cyan]{uc_source}:[/cyan]")
            console.print("    system_type: <UNKNOWN>  # Set the correct type")
            console.print(f"    # Referenced by: {', '.join(t.qualified_name for t in tables[:3])}")
            if len(tables) > 3:
                console.print(f"    # ... and {len(tables) - 3} more")

    if not dry_run:
        note = "Note: Add these entries to your unity_lineage.yml manually."
        console.print(f"\n[yellow]{note}[/yellow]")
        console.print("[dim]Automatic config updates are not supported yet.[/dim]")


# =============================================================================
# status command
# =============================================================================


@main.command()
@click.option("--select", "select_pattern", help="Filter by folder")
@click.option(
    "--type",
    "scan_type",
    type=click.Choice(["source", "exposure"]),
    help="Filter by type",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "md"]),
    default="table",
    help="Output format",
)
@pass_context
def status(
    ctx: Context,
    select_pattern: Optional[str],
    scan_type: Optional[str],
    output_format: str,
) -> None:
    """Show current state - local definitions vs Unity Catalog."""
    if ctx.config is None:
        error_console.print("[red]Error: No config file found.[/red]")
        sys.exit(EXIT_ERROR)

    if ctx.client is None:
        error_console.print("[red]Error: No Databricks connection. Check your profiles.yml.[/red]")
        sys.exit(EXIT_ERROR)

    # Determine scan type
    type_filter = "all"
    if scan_type == "source":
        type_filter = "sources"
    elif scan_type == "exposure":
        type_filter = "exposures"

    # Scan local definitions
    local_result = scan_config(ctx.config, ctx.project_dir, select_pattern, type_filter)

    # Get remote state
    try:
        remote_objects = ctx.client.list_external_metadata(ctx.config.project_name)
    except Exception as e:
        categorized = categorize_api_error(e)
        error_console.print(f"[red]Error querying Unity Catalog: {categorized.message}[/red]")
        if categorized.resolution:
            error_console.print(f"[dim]Resolution: {categorized.resolution}[/dim]")
        sys.exit(EXIT_ERROR)

    # Compare local vs remote
    local_source_names = {t.qualified_name for t in local_result.all_source_tables}
    local_exposure_names = {e.name for e in local_result.exposures}
    remote_names = {obj.name for obj in remote_objects}

    # Categorize
    new_sources = [
        t for t in local_result.all_source_tables
        if t.qualified_name not in remote_names
    ]
    new_exposures = [
        e for e in local_result.exposures if e.name not in remote_names
    ]
    orphaned = [
        name for name in remote_names
        if name not in local_source_names and name not in local_exposure_names
    ]
    in_sync_count = len(remote_names) - len(orphaned)

    # Output
    if output_format == "json":
        import json

        data = {
            "local_sources": list(local_source_names),
            "local_exposures": list(local_exposure_names),
            "remote_objects": list(remote_names),
            "new": [t.qualified_name for t in new_sources] + [e.name for e in new_exposures],
            "orphaned": orphaned,
            "in_sync": in_sync_count,
        }
        click.echo(json.dumps(data, indent=2))

    elif output_format == "md":
        console.print("## dbt-unity-lineage Status\n")

        if new_sources or new_exposures:
            console.print("### New (to be created)")
            for t in new_sources:
                console.print(f"- 🆕 Source: `{t.qualified_name}`")
            for e in new_exposures:
                console.print(f"- 🆕 Exposure: `{e.name}`")
            console.print()

        if orphaned:
            console.print("### Orphaned (to be removed)")
            for name in orphaned:
                console.print(f"- 🗑️ `{name}`")
            console.print()

        console.print(f"**In sync:** {in_sync_count} objects")
        console.print(f"**New:** {len(new_sources) + len(new_exposures)} objects")
        console.print(f"**Orphaned:** {len(orphaned)} objects")

    else:
        # Table format
        if new_sources or new_exposures:
            console.print("[bold]New (to be created):[/bold]")
            for t in new_sources:
                console.print(f"  [green]🆕[/green] Source: {t.qualified_name}")
            for e in new_exposures:
                console.print(f"  [green]🆕[/green] Exposure: {e.name}")

        if orphaned:
            console.print("\n[bold]Orphaned (to be removed):[/bold]")
            for name in orphaned:
                console.print(f"  [red]🗑️[/red] {name}")

        if not new_sources and not new_exposures and not orphaned:
            console.print("[green]✓ Everything is in sync[/green]")
        else:
            new_count = len(new_sources) + len(new_exposures)
            summary = f"In sync: {in_sync_count} | New: {new_count} | Orphaned: {len(orphaned)}"
            console.print(f"\n[dim]{summary}[/dim]")


# =============================================================================
# push command
# =============================================================================


@main.command()
@click.option("--select", "select_pattern", help="Select folders to push")
@click.option(
    "--type",
    "scan_type",
    type=click.Choice(["source", "exposure"]),
    help="Filter by type",
)
@click.option("--dry-run", is_flag=True, help="Show what would be pushed")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "md"]),
    default="table",
    help="Output format",
)
@pass_context
def push(
    ctx: Context,
    select_pattern: Optional[str],
    scan_type: Optional[str],
    dry_run: bool,
    output_format: str,
) -> None:
    """Push lineage to Unity Catalog.

    Behavior:
    1. Identifies all project objects in UC (by system tags)
    2. Removes them (scoped to selection if --select used)
    3. Pushes fresh from local definitions
    """
    if ctx.config is None:
        error_console.print("[red]Error: No config file found.[/red]")
        sys.exit(EXIT_ERROR)

    if ctx.client is None:
        error_console.print("[red]Error: No Databricks connection. Check your profiles.yml.[/red]")
        sys.exit(EXIT_ERROR)

    # Determine scan type
    type_filter = "all"
    if scan_type == "source":
        type_filter = "sources"
    elif scan_type == "exposure":
        type_filter = "exposures"

    # Scan local definitions
    local_result = scan_config(ctx.config, ctx.project_dir, select_pattern, type_filter)

    if local_result.errors:
        for error in local_result.errors:
            error_console.print(f"[red]Error: {error}[/red]")
        sys.exit(EXIT_ERROR)

    if not ctx.quiet:
        if dry_run:
            console.print("[bold]Dry run mode - no changes will be made[/bold]")
        src_count = local_result.source_count
        exp_count = local_result.exposure_count
        console.print(f"Found {src_count} sources and {exp_count} exposures")

    # Get current remote state
    try:
        remote_objects = ctx.client.list_external_metadata(ctx.config.project_name)
    except Exception as e:
        categorized = categorize_api_error(e)
        error_console.print(f"[red]Error querying Unity Catalog: {categorized.message}[/red]")
        sys.exit(EXIT_ERROR)

    # Calculate actions
    local_names = {t.qualified_name for t in local_result.all_source_tables}
    local_names.update(e.name for e in local_result.exposures)
    remote_names = {obj.name for obj in remote_objects}

    to_create = local_names - remote_names
    to_delete = remote_names - local_names
    to_update = local_names & remote_names

    if dry_run:
        _output_push_dry_run(to_create, to_update, to_delete, output_format)
        return

    # Execute push
    errors: list[str] = []
    created = 0
    updated = 0
    deleted = 0

    total_ops = len(to_delete) + len(to_create) + len(to_update)

    if not ctx.quiet and sys.stdout.isatty() and total_ops > 0:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
            transient=True,
        ) as progress:
            task: TaskID = progress.add_task("Pushing...", total=total_ops)

            # Delete orphaned objects
            for name in to_delete:
                progress.update(task, description=f"Deleting {name}")
                try:
                    ctx.client.delete_external_metadata(name)
                    deleted += 1
                except Exception as e:
                    errors.append(f"Failed to delete {name}: {e}")
                progress.advance(task)

            # Create/update objects
            for table in local_result.all_source_tables:
                name = table.qualified_name
                progress.update(task, description=f"Pushing {name}")
                try:
                    _push_source(ctx, table)
                    if name in to_create:
                        created += 1
                    else:
                        updated += 1
                except Exception as e:
                    errors.append(f"Failed to push {name}: {e}")
                progress.advance(task)

            for exposure in local_result.exposures:
                progress.update(task, description=f"Pushing {exposure.name}")
                try:
                    _push_exposure(ctx, exposure)
                    if exposure.name in to_create:
                        created += 1
                    else:
                        updated += 1
                except Exception as e:
                    errors.append(f"Failed to push {exposure.name}: {e}")
                progress.advance(task)
    else:
        # Non-interactive mode
        for name in to_delete:
            try:
                ctx.client.delete_external_metadata(name)
                deleted += 1
            except Exception as e:
                errors.append(f"Failed to delete {name}: {e}")

        for table in local_result.all_source_tables:
            try:
                _push_source(ctx, table)
                if table.qualified_name in to_create:
                    created += 1
                else:
                    updated += 1
            except Exception as e:
                errors.append(f"Failed to push {table.qualified_name}: {e}")

        for exposure in local_result.exposures:
            try:
                _push_exposure(ctx, exposure)
                if exposure.name in to_create:
                    created += 1
                else:
                    updated += 1
            except Exception as e:
                errors.append(f"Failed to push {exposure.name}: {e}")

    # Output results
    if not ctx.quiet:
        console.print(f"\n[green]Created: {created}[/green]")
        console.print(f"[blue]Updated: {updated}[/blue]")
        console.print(f"[yellow]Deleted: {deleted}[/yellow]")

    if errors:
        console.print(f"\n[red]Errors: {len(errors)}[/red]")
        for error in errors:
            error_console.print(f"  [red]✗[/red] {error}")
        sys.exit(EXIT_ERROR)


def _push_source(ctx: Context, table: SourceTable) -> None:
    """Push a source table to Unity Catalog."""
    assert ctx.client is not None
    assert ctx.config is not None

    # Get source system config if available
    source_system = None
    if table.uc_source:
        source_system = ctx.config.source_systems.get(table.uc_source)

    # Build metadata
    system_type = "CUSTOM"
    if source_system:
        system_type = source_system.system_type

    properties = {
        "dbt_unity_lineage_managed": "true",
        "dbt_unity_lineage_project": ctx.config.project_name,
        "dbt_source": table.qualified_name,
    }

    if source_system and source_system.meta:
        properties.update({str(k): str(v) for k, v in source_system.meta.items()})

    from .unity_catalog import ExternalMetadata

    metadata = ExternalMetadata(
        name=table.qualified_name,
        system_type=system_type,
        entity_type="table",
        description=table.description or (source_system.description if source_system else None),
        url=source_system.url if source_system else None,
        owner=source_system.owner if source_system else None,
        properties=properties,
    )

    # Check if exists
    try:
        existing = ctx.client.get_external_metadata(table.qualified_name)
        if existing:
            ctx.client.update_external_metadata(metadata)
        else:
            ctx.client.create_external_metadata(metadata)
    except Exception:
        ctx.client.create_external_metadata(metadata)


def _push_exposure(ctx: Context, exposure: Exposure) -> None:
    """Push an exposure to Unity Catalog."""
    assert ctx.client is not None
    assert ctx.config is not None

    # Infer system type from URL
    system_type = exposure.uc_system_type
    if not system_type and exposure.url:
        system_type = infer_system_type_from_url(exposure.url)
    if not system_type:
        system_type = "CUSTOM"

    # Map exposure type to entity type
    entity_type_map = {
        "dashboard": "dashboard",
        "notebook": "notebook",
        "analysis": "dashboard",
        "ml": "model",
        "application": "application",
    }
    entity_type = entity_type_map.get(exposure.type.lower(), "dashboard")

    properties = {
        "dbt_unity_lineage_managed": "true",
        "dbt_unity_lineage_project": ctx.config.project_name,
        "dbt_exposure": exposure.name,
        "exposure_type": exposure.type,
    }

    from .unity_catalog import ExternalMetadata

    metadata = ExternalMetadata(
        name=exposure.name,
        system_type=system_type,
        entity_type=entity_type,
        description=exposure.description,
        url=exposure.url,
        owner=exposure.owner.email if exposure.owner else None,
        properties=properties,
    )

    # Check if exists
    try:
        existing = ctx.client.get_external_metadata(exposure.name)
        if existing:
            ctx.client.update_external_metadata(metadata)
        else:
            ctx.client.create_external_metadata(metadata)
    except Exception:
        ctx.client.create_external_metadata(metadata)


def _output_push_dry_run(
    to_create: set[str],
    to_update: set[str],
    to_delete: set[str],
    output_format: str,
) -> None:
    """Output dry-run results."""
    if output_format == "json":
        import json

        data = {
            "dry_run": True,
            "to_create": list(to_create),
            "to_update": list(to_update),
            "to_delete": list(to_delete),
        }
        click.echo(json.dumps(data, indent=2))

    elif output_format == "md":
        console.print("## Push Dry Run\n")
        if to_create:
            console.print("### To Create")
            for name in to_create:
                console.print(f"- 🆕 `{name}`")
        if to_update:
            console.print("### To Update")
            for name in to_update:
                console.print(f"- 🔄 `{name}`")
        if to_delete:
            console.print("### To Delete")
            for name in to_delete:
                console.print(f"- 🗑️ `{name}`")
        summary = f"{len(to_create)} create, {len(to_update)} update, {len(to_delete)} delete"
        console.print(f"\n**Summary:** {summary}")

    else:
        if to_create:
            console.print("[bold]To Create:[/bold]")
            for name in to_create:
                console.print(f"  [green]🆕[/green] {name}")
        if to_update:
            console.print("[bold]To Update:[/bold]")
            for name in to_update:
                console.print(f"  [blue]🔄[/blue] {name}")
        if to_delete:
            console.print("[bold]To Delete:[/bold]")
            for name in to_delete:
                console.print(f"  [red]🗑️[/red] {name}")

        summary = f"{len(to_create)} create, {len(to_update)} update, {len(to_delete)} delete"
        console.print(f"\n[dim]Summary: {summary}[/dim]")


# =============================================================================
# clean command
# =============================================================================


@main.command()
@click.option("--select", "select_pattern", help="Select folders to clean")
@click.option(
    "--type",
    "scan_type",
    type=click.Choice(["source", "exposure"]),
    help="Filter by type",
)
@click.option("--dry-run", is_flag=True, help="Show what would be removed")
@click.option("--force", is_flag=True, help="Skip confirmation prompt")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json", "md"]),
    default="table",
    help="Output format",
)
@pass_context
def clean(
    ctx: Context,
    select_pattern: Optional[str],
    scan_type: Optional[str],
    dry_run: bool,
    force: bool,
    output_format: str,
) -> None:
    """Remove all project objects from Unity Catalog."""
    if ctx.config is None:
        error_console.print("[red]Error: No config file found.[/red]")
        sys.exit(EXIT_ERROR)

    if ctx.client is None:
        error_console.print("[red]Error: No Databricks connection. Check your profiles.yml.[/red]")
        sys.exit(EXIT_ERROR)

    # Get remote objects for this project
    try:
        remote_objects = ctx.client.list_external_metadata(ctx.config.project_name)
    except Exception as e:
        categorized = categorize_api_error(e)
        error_console.print(f"[red]Error querying Unity Catalog: {categorized.message}[/red]")
        sys.exit(EXIT_ERROR)

    if not remote_objects:
        if not ctx.quiet:
            console.print("[green]No objects to remove.[/green]")
        return

    to_delete = [obj.name for obj in remote_objects]

    # Output
    if dry_run:
        if output_format == "json":
            import json

            click.echo(json.dumps({"dry_run": True, "to_delete": to_delete}, indent=2))
        elif output_format == "md":
            console.print("## Clean Dry Run\n")
            console.print("### Objects to Remove")
            for name in to_delete:
                console.print(f"- 🗑️ `{name}`")
            console.print(f"\n**Total:** {len(to_delete)} objects")
        else:
            console.print(f"[bold]Would remove {len(to_delete)} objects:[/bold]")
            for name in to_delete:
                console.print(f"  [red]🗑️[/red] {name}")
        return

    # Confirm unless --force
    if not force:
        console.print(f"[bold]About to remove {len(to_delete)} objects from Unity Catalog.[/bold]")
        for name in to_delete[:5]:
            console.print(f"  - {name}")
        if len(to_delete) > 5:
            console.print(f"  ... and {len(to_delete) - 5} more")

        if not click.confirm("Continue?"):
            console.print("[yellow]Cancelled.[/yellow]")
            sys.exit(2)  # User cancelled

    # Execute
    errors: list[str] = []
    deleted = 0

    for name in to_delete:
        try:
            ctx.client.delete_external_metadata(name)
            deleted += 1
            if ctx.verbose:
                console.print(f"  [green]✓[/green] Deleted {name}")
        except Exception as e:
            errors.append(f"Failed to delete {name}: {e}")

    if not ctx.quiet:
        console.print(f"\n[green]Deleted: {deleted}[/green]")

    if errors:
        console.print(f"[red]Errors: {len(errors)}[/red]")
        for error in errors:
            error_console.print(f"  [red]✗[/red] {error}")
        sys.exit(EXIT_ERROR)


if __name__ == "__main__":
    main()
