"""CLI commands for dbt-unity-lineage."""

from __future__ import annotations

import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskID, TextColumn

from . import __version__
from .config import Config, find_config_file, load_config
from .dbt_cloud import DbtCloudClient, DbtCloudConfig, DbtCloudError
from .errors import (
    EXIT_ERROR,
    EXIT_PARTIAL_FAILURE,
    EXIT_SUCCESS,
    categorize_api_error,
)
from .manifest import Manifest, find_manifest_file, load_manifest, load_manifest_from_dict
from .output import OutputFormat, format_status, print_status_rich
from .profiles import DatabricksConnection, get_databricks_connection
from .sync import StrictModeError, apply_sync_plan, build_sync_plan
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
        self.manifest: Optional[Manifest] = None
        self.connection: Optional[DatabricksConnection] = None
        self.client: Optional[UnityCatalogClient] = None


pass_context = click.make_pass_decorator(Context, ensure=True)


@click.group(invoke_without_command=True)
@click.option(
    "--config",
    "config_path",
    type=click.Path(exists=False, path_type=Path),
    help="Path to dbt_unity_lineage.yml",
)
@click.option(
    "--manifest",
    "manifest_path",
    type=click.Path(exists=False, path_type=Path),
    help="Path to manifest.json",
)
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
# dbt Cloud options
@click.option(
    "--dbt-cloud",
    is_flag=True,
    help="Fetch manifest from dbt Cloud instead of local file",
)
@click.option(
    "--dbt-cloud-account-id",
    type=int,
    envvar="DBT_CLOUD_ACCOUNT_ID",
    help="dbt Cloud account ID",
)
@click.option(
    "--dbt-cloud-token",
    envvar="DBT_CLOUD_TOKEN",
    help="dbt Cloud API token",
)
@click.option(
    "--dbt-cloud-job-id",
    type=int,
    help="dbt Cloud job ID (fetches from latest successful run)",
)
@click.option(
    "--dbt-cloud-run-id",
    type=int,
    help="dbt Cloud run ID (fetches from specific run)",
)
@click.option(
    "--dbt-cloud-host",
    envvar="DBT_CLOUD_HOST",
    help="dbt Cloud API host (default: cloud.getdbt.com)",
)
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
    config_path: Optional[Path],
    manifest_path: Optional[Path],
    project_dir: Optional[Path],
    profiles_dir: Optional[Path],
    profile: Optional[str],
    target: Optional[str],
    dbt_cloud: bool,
    dbt_cloud_account_id: Optional[int],
    dbt_cloud_token: Optional[str],
    dbt_cloud_job_id: Optional[int],
    dbt_cloud_run_id: Optional[int],
    dbt_cloud_host: Optional[str],
    verbose: bool,
    quiet: bool,
    show_claude: bool,
) -> None:
    """Push dbt lineage to Databricks Unity Catalog."""
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

    # Find and load config
    if config_path is None:
        config_path = find_config_file(project_dir)

    if config_path and config_path.exists():
        try:
            ctx.config = load_config(config_path)
            if verbose:
                console.print(f"[dim]Loaded config from {config_path}[/dim]")
        except Exception as e:
            if verbose:
                error_console.print(f"[yellow]Warning: Could not load config: {e}[/yellow]")
            ctx.config = Config()
    else:
        ctx.config = Config()
        if verbose:
            console.print("[dim]No config file found, using defaults[/dim]")

    # Load manifest - either from dbt Cloud or local file
    if dbt_cloud:
        # Fetch manifest from dbt Cloud
        if not dbt_cloud_job_id and not dbt_cloud_run_id:
            error_console.print(
                "[red]Error: --dbt-cloud requires either "
                "--dbt-cloud-job-id or --dbt-cloud-run-id[/red]"
            )
            sys.exit(1)

        try:
            cloud_config = DbtCloudConfig.from_env(
                token=dbt_cloud_token,
                account_id=dbt_cloud_account_id,
                host=dbt_cloud_host,
            )
            cloud_client = DbtCloudClient(cloud_config)

            if not quiet:
                if dbt_cloud_job_id:
                    console.print(f"Fetching manifest from dbt Cloud job {dbt_cloud_job_id}...")
                else:
                    console.print(f"Fetching manifest from dbt Cloud run {dbt_cloud_run_id}...")

            manifest_dict = cloud_client.get_manifest(
                run_id=dbt_cloud_run_id,
                job_id=dbt_cloud_job_id,
            )
            ctx.manifest = load_manifest_from_dict(manifest_dict)

            if verbose:
                console.print("[dim]Loaded manifest from dbt Cloud[/dim]")

        except DbtCloudError as e:
            error_console.print(f"[red]Error fetching from dbt Cloud: {e}[/red]")
            sys.exit(1)
    else:
        # Load manifest from local file
        if manifest_path is None:
            manifest_path = find_manifest_file(project_dir)

        if manifest_path and manifest_path.exists():
            try:
                ctx.manifest = load_manifest(manifest_path)
                if verbose:
                    console.print(f"[dim]Loaded manifest from {manifest_path}[/dim]")
            except Exception as e:
                error_console.print(f"[red]Error loading manifest: {e}[/red]")
                sys.exit(1)

    # Get Databricks connection
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


@main.command()
@click.option("--dry-run", is_flag=True, help="Show what would be pushed, don't execute")
@click.option("--no-clean", is_flag=True, help="Don't remove orphaned objects")
@click.option("--sources-only", is_flag=True, help="Only push upstream (sources)")
@click.option("--exposures-only", is_flag=True, help="Only push downstream (exposures)")
@click.option("--batch-size", type=int, help="API batch size")
@click.option("--strict", is_flag=True, help="Fail immediately on first error")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json", "md"]),
    default="text",
    help="Output format",
)
@pass_context
def push(
    ctx: Context,
    dry_run: bool,
    no_clean: bool,
    sources_only: bool,
    exposures_only: bool,
    batch_size: Optional[int],
    strict: bool,
    output_format: str,
) -> None:
    """Push sources and exposures to Unity Catalog."""
    if ctx.manifest is None:
        error_console.print("[red]Error: No manifest.json found. Run 'dbt build' first.[/red]")
        sys.exit(1)

    if ctx.client is None:
        error_console.print("[red]Error: No Databricks connection. Check your profiles.yml.[/red]")
        sys.exit(1)

    if ctx.config is None:
        ctx.config = Config()

    # Override batch size if specified
    if batch_size:
        ctx.config.settings.batch_size = batch_size

    # Build sync plan
    if not ctx.quiet:
        if dry_run:
            console.print("[bold]Dry run mode - no changes will be made[/bold]")
        console.print("Building sync plan...")

    plan = build_sync_plan(
        manifest=ctx.manifest,
        config=ctx.config,
        client=ctx.client,
        sources_only=sources_only,
        exposures_only=exposures_only,
    )

    # Apply plan
    if not dry_run:
        # Count actionable items
        actionable_count = len(plan.to_create) + len(plan.to_update)
        if not no_clean:
            actionable_count += len(plan.to_delete)

        if actionable_count == 0:
            if not ctx.quiet:
                console.print("[green]Everything is in sync, no changes needed.[/green]")
        else:
            try:
                if not ctx.quiet and sys.stdout.isatty():
                    # Use progress bar for interactive terminals
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        BarColumn(),
                        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                        TextColumn("({task.completed}/{task.total})"),
                        console=console,
                        transient=True,
                    ) as progress:
                        task: TaskID = progress.add_task("Syncing...", total=actionable_count)

                        def update_progress(current: int, total: int, item_name: str) -> None:
                            progress.update(
                                task, completed=current, description=f"Syncing {item_name}"
                            )

                        plan = apply_sync_plan(
                            plan=plan,
                            client=ctx.client,
                            dry_run=False,
                            no_clean=no_clean,
                            progress_callback=update_progress,
                            strict=strict,
                        )
                else:
                    # Non-interactive mode or quiet mode
                    if not ctx.quiet:
                        console.print("Applying changes...")
                    plan = apply_sync_plan(
                        plan=plan,
                        client=ctx.client,
                        dry_run=False,
                        no_clean=no_clean,
                        strict=strict,
                    )
            except StrictModeError as e:
                error_console.print(f"[bold red]Strict mode failure:[/bold red] {e}")
                categorized = categorize_api_error(Exception(e.error))
                if categorized.resolution:
                    error_console.print(f"[dim]Resolution: {categorized.resolution}[/dim]")
                sys.exit(EXIT_ERROR)

    # Output results
    fmt = OutputFormat(output_format)
    if fmt == OutputFormat.TEXT and not ctx.quiet:
        print_status_rich(plan, console)
    else:
        output = format_status(plan, fmt, verbose=ctx.verbose)
        console.print(output)

    # Show detailed error information if there were failures
    if plan.errors:
        if fmt == OutputFormat.TEXT and not ctx.quiet:
            console.print("\n[bold red]Errors:[/bold red]")
            for i, item in enumerate(plan.errors, 1):
                console.print(f"  {i}. [bold]{item.identifier}[/bold]: {item.error}")
                # Provide resolution hint based on error
                if item.error:
                    categorized = categorize_api_error(Exception(item.error))
                    if categorized.resolution:
                        console.print(f"     [dim]Resolution: {categorized.resolution}[/dim]")

        # Use appropriate exit code
        if len(plan.errors) == len(plan.items):
            sys.exit(EXIT_ERROR)  # All operations failed
        else:
            sys.exit(EXIT_PARTIAL_FAILURE)  # Some operations failed

    sys.exit(EXIT_SUCCESS)


@main.command()
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json", "md"]),
    default="text",
    help="Output format",
)
@pass_context
def status(ctx: Context, output_format: str) -> None:
    """Show status: local vs remote comparison."""
    if ctx.manifest is None:
        error_console.print("[red]Error: No manifest.json found. Run 'dbt build' first.[/red]")
        sys.exit(1)

    if ctx.client is None:
        error_console.print("[red]Error: No Databricks connection. Check your profiles.yml.[/red]")
        sys.exit(1)

    if ctx.config is None:
        ctx.config = Config()

    # Build sync plan (without applying)
    plan = build_sync_plan(
        manifest=ctx.manifest,
        config=ctx.config,
        client=ctx.client,
    )

    # Output results
    fmt = OutputFormat(output_format)
    if fmt == OutputFormat.TEXT and not ctx.quiet:
        print_status_rich(plan, console)
    else:
        output = format_status(plan, fmt, verbose=ctx.verbose)
        console.print(output)


@main.command()
@click.option("--dry-run", is_flag=True, help="Show what would be removed")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["text", "json", "md"]),
    default="text",
    help="Output format",
)
@pass_context
def clean(ctx: Context, dry_run: bool, output_format: str) -> None:
    """Remove orphaned external metadata objects."""
    if ctx.manifest is None:
        error_console.print("[red]Error: No manifest.json found. Run 'dbt build' first.[/red]")
        sys.exit(1)

    if ctx.client is None:
        error_console.print("[red]Error: No Databricks connection. Check your profiles.yml.[/red]")
        sys.exit(1)

    if ctx.config is None:
        ctx.config = Config()

    # Build sync plan
    plan = build_sync_plan(
        manifest=ctx.manifest,
        config=ctx.config,
        client=ctx.client,
    )

    # Filter to only delete items
    delete_items = plan.to_delete

    if not delete_items:
        if not ctx.quiet:
            console.print("[green]No orphaned objects to remove.[/green]")
        return

    if not ctx.quiet:
        if dry_run:
            console.print("[bold]Dry run mode - no changes will be made[/bold]")
        console.print(f"Found {len(delete_items)} orphaned objects to remove:")
        for item in delete_items:
            console.print(f"  - {item.name}")

    if not dry_run:
        if not ctx.quiet:
            console.print("Removing orphaned objects...")

        for item in delete_items:
            try:
                # Delete lineage edges first
                for edge in ctx.client.list_lineage_edges(item.name, "external"):
                    try:
                        ctx.client.delete_lineage_edge(edge)
                    except Exception:
                        pass
                ctx.client.delete_external_metadata(item.name)
                if not ctx.quiet:
                    console.print(f"  [green]Deleted {item.name}[/green]")
            except Exception as e:
                error_console.print(f"  [red]Failed to delete {item.name}: {e}[/red]")

    if not ctx.quiet:
        console.print("[green]Clean complete.[/green]")


CONFIG_TEMPLATE = """\
# dbt-unity-lineage configuration
# https://github.com/dbt-conceptual/dbt-unity-lineage
version: 1

source_systems:
  # Define your upstream source systems here.
  # The key (e.g., 'erp') is referenced in sources.yml via meta.uc_source
  #
  # Example:
  # erp:
  #   system_type: SAP          # See docs for valid types
  #   description: SAP ECC Production
  #   owner: data-team@example.com
  #
  # salesforce:
  #   system_type: Salesforce
  #   description: Salesforce CRM

# Optional: limit to specific source paths
# source_paths:
#   - staging/erp
#   - staging/crm

settings:
  batch_size: 50
  strict: false
"""


@main.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    default="dbt_unity_lineage.yml",
    help="Output file path",
)
@click.option("--force", "-f", is_flag=True, help="Overwrite existing file")
def init(output: Path, force: bool) -> None:
    """Create a dbt_unity_lineage.yml config file."""
    if output.exists() and not force:
        error_console.print(f"[red]Error: {output} already exists. Use --force to overwrite.[/red]")
        sys.exit(1)

    output.write_text(CONFIG_TEMPLATE)
    console.print(f"[green]Created {output}[/green]")
    console.print("[dim]Edit the file to add your source systems, then run:[/dim]")
    console.print("[dim]  dbt-unity-lineage push --dry-run[/dim]")


if __name__ == "__main__":
    main()
