"""Output formatters for dbt-unity-lineage."""

from __future__ import annotations

import json
from enum import Enum
from typing import Optional

from rich.console import Console
from rich.table import Table

from .sync import SyncPlan, SyncStatus


class OutputFormat(str, Enum):
    """Output format options."""

    TEXT = "text"
    JSON = "json"
    MARKDOWN = "md"


# Status icons for text/markdown output
STATUS_ICONS = {
    SyncStatus.IN_SYNC: "\u2705",  # ✅
    SyncStatus.CREATE: "\U0001F195",  # 🆕
    SyncStatus.UPDATE: "\U0001F504",  # 🔄
    SyncStatus.DELETE: "\U0001F5D1\uFE0F",  # 🗑️
    SyncStatus.SKIP: "\u2796",  # ➖
    SyncStatus.ERROR: "\u274C",  # ❌
}

STATUS_LABELS = {
    SyncStatus.IN_SYNC: "In sync",
    SyncStatus.CREATE: "Create",
    SyncStatus.UPDATE: "Update",
    SyncStatus.DELETE: "Delete",
    SyncStatus.SKIP: "Skipped",
    SyncStatus.ERROR: "Error",
}


def format_status_text(
    plan: SyncPlan,
    verbose: bool = False,
    console: Optional[Console] = None,
) -> str:
    """Format sync plan as text output.

    Args:
        plan: The sync plan to format.
        verbose: Include detailed information.
        console: Optional Rich console for colored output.

    Returns:
        Formatted text output.
    """
    lines = []

    # Header
    lines.append(f"Project: {plan.project_name}")
    lines.append(f"Catalog: {plan.catalog}")
    lines.append("")

    # Sources section
    sources = plan.sources
    if sources:
        lines.append("Upstream (Sources):")
        for item in sources:
            icon = STATUS_ICONS.get(item.status, "?")
            label = STATUS_LABELS.get(item.status, item.status.value)
            line = f"  {icon} {item.identifier:<30} {item.system_type:<15} {label}"
            if item.error:
                line += f" - {item.error}"
            lines.append(line)
        lines.append("")

    # Exposures section
    exposures = plan.exposures
    if exposures:
        lines.append("Downstream (Exposures):")
        for item in exposures:
            icon = STATUS_ICONS.get(item.status, "?")
            label = STATUS_LABELS.get(item.status, item.status.value)
            line = f"  {icon} {item.identifier:<30} {item.system_type:<15} {label}"
            if item.error:
                line += f" - {item.error}"
            lines.append(line)
        lines.append("")

    # Summary
    summary = plan.summary()
    summary_parts = []
    if summary["in_sync"]:
        summary_parts.append(f"{summary['in_sync']} in sync")
    if summary["update"]:
        summary_parts.append(f"{summary['update']} update")
    if summary["create"]:
        summary_parts.append(f"{summary['create']} create")
    if summary["delete"]:
        summary_parts.append(f"{summary['delete']} delete")
    if summary["skipped"]:
        summary_parts.append(f"{summary['skipped']} skipped")
    if summary["errors"]:
        summary_parts.append(f"{summary['errors']} errors")

    lines.append(f"Summary: {', '.join(summary_parts)}")

    return "\n".join(lines)


def format_status_json(plan: SyncPlan) -> str:
    """Format sync plan as JSON output.

    Args:
        plan: The sync plan to format.

    Returns:
        JSON string.
    """
    data = {
        "project": plan.project_name,
        "catalog": plan.catalog,
        "upstream": [
            {
                "name": item.identifier,
                "system_type": item.system_type,
                "status": item.status.value,
                "error": item.error,
            }
            for item in plan.sources
        ],
        "downstream": [
            {
                "name": item.identifier,
                "system_type": item.system_type,
                "status": item.status.value,
                "error": item.error,
            }
            for item in plan.exposures
        ],
        "summary": plan.summary(),
    }

    return json.dumps(data, indent=2)


def format_status_markdown(plan: SyncPlan) -> str:
    """Format sync plan as Markdown output.

    Args:
        plan: The sync plan to format.

    Returns:
        Markdown string.
    """
    lines = []

    # Header
    lines.append("## dbt-unity-lineage Status")
    lines.append("")
    lines.append(f"**Project:** {plan.project_name}  ")
    lines.append(f"**Catalog:** {plan.catalog}  ")
    lines.append("")

    # Sources section
    sources = plan.sources
    if sources:
        lines.append("### Upstream (Sources)")
        lines.append("")
        lines.append("| Source | System | Status |")
        lines.append("|--------|--------|--------|")
        for item in sources:
            icon = STATUS_ICONS.get(item.status, "?")
            label = STATUS_LABELS.get(item.status, item.status.value)
            status_text = f"{icon} {label}"
            if item.error:
                status_text += f" ({item.error})"
            lines.append(f"| {item.identifier} | {item.system_type} | {status_text} |")
        lines.append("")

    # Exposures section
    exposures = plan.exposures
    if exposures:
        lines.append("### Downstream (Exposures)")
        lines.append("")
        lines.append("| Exposure | System | Status |")
        lines.append("|----------|--------|--------|")
        for item in exposures:
            icon = STATUS_ICONS.get(item.status, "?")
            label = STATUS_LABELS.get(item.status, item.status.value)
            status_text = f"{icon} {label}"
            if item.error:
                status_text += f" ({item.error})"
            lines.append(f"| {item.identifier} | {item.system_type} | {status_text} |")
        lines.append("")

    # Summary
    lines.append("### Summary")
    lines.append("")
    lines.append("| Status | Count |")
    lines.append("|--------|-------|")

    summary = plan.summary()
    lines.append(f"| {STATUS_ICONS[SyncStatus.IN_SYNC]} In sync | {summary['in_sync']} |")
    lines.append(f"| {STATUS_ICONS[SyncStatus.UPDATE]} Update | {summary['update']} |")
    lines.append(f"| {STATUS_ICONS[SyncStatus.CREATE]} Create | {summary['create']} |")
    lines.append(f"| {STATUS_ICONS[SyncStatus.DELETE]} Delete | {summary['delete']} |")
    lines.append(f"| {STATUS_ICONS[SyncStatus.SKIP]} Skipped | {summary['skipped']} |")
    if summary["errors"]:
        lines.append(f"| {STATUS_ICONS[SyncStatus.ERROR]} Errors | {summary['errors']} |")

    return "\n".join(lines)


def format_status(
    plan: SyncPlan,
    output_format: OutputFormat = OutputFormat.TEXT,
    verbose: bool = False,
) -> str:
    """Format sync plan according to the specified format.

    Args:
        plan: The sync plan to format.
        output_format: The output format to use.
        verbose: Include detailed information (text format only).

    Returns:
        Formatted output string.
    """
    if output_format == OutputFormat.JSON:
        return format_status_json(plan)
    elif output_format == OutputFormat.MARKDOWN:
        return format_status_markdown(plan)
    else:
        return format_status_text(plan, verbose=verbose)


def print_status_rich(plan: SyncPlan, console: Console) -> None:
    """Print sync plan using Rich for enhanced terminal output.

    Args:
        plan: The sync plan to print.
        console: Rich console to print to.
    """
    # Header
    console.print(f"[bold]Project:[/bold] {plan.project_name}")
    console.print(f"[bold]Catalog:[/bold] {plan.catalog}")
    console.print()

    # Sources table
    sources = plan.sources
    if sources:
        table = Table(title="Upstream (Sources)")
        table.add_column("Source", style="cyan")
        table.add_column("System", style="magenta")
        table.add_column("Status")

        for item in sources:
            icon = STATUS_ICONS.get(item.status, "?")
            label = STATUS_LABELS.get(item.status, item.status.value)

            # Color based on status
            status_style = {
                SyncStatus.IN_SYNC: "green",
                SyncStatus.CREATE: "blue",
                SyncStatus.UPDATE: "yellow",
                SyncStatus.DELETE: "red",
                SyncStatus.ERROR: "red bold",
            }.get(item.status, "white")

            status_text = f"{icon} {label}"
            if item.error:
                status_text += f"\n[dim]{item.error}[/dim]"

            table.add_row(
                item.identifier,
                item.system_type,
                f"[{status_style}]{status_text}[/{status_style}]",
            )

        console.print(table)
        console.print()

    # Exposures table
    exposures = plan.exposures
    if exposures:
        table = Table(title="Downstream (Exposures)")
        table.add_column("Exposure", style="cyan")
        table.add_column("System", style="magenta")
        table.add_column("Status")

        for item in exposures:
            icon = STATUS_ICONS.get(item.status, "?")
            label = STATUS_LABELS.get(item.status, item.status.value)

            status_style = {
                SyncStatus.IN_SYNC: "green",
                SyncStatus.CREATE: "blue",
                SyncStatus.UPDATE: "yellow",
                SyncStatus.DELETE: "red",
                SyncStatus.ERROR: "red bold",
            }.get(item.status, "white")

            status_text = f"{icon} {label}"
            if item.error:
                status_text += f"\n[dim]{item.error}[/dim]"

            table.add_row(
                item.identifier,
                item.system_type,
                f"[{status_style}]{status_text}[/{status_style}]",
            )

        console.print(table)
        console.print()

    # Summary
    summary = plan.summary()
    summary_parts = []
    if summary["in_sync"]:
        summary_parts.append(f"[green]{summary['in_sync']} in sync[/green]")
    if summary["update"]:
        summary_parts.append(f"[yellow]{summary['update']} update[/yellow]")
    if summary["create"]:
        summary_parts.append(f"[blue]{summary['create']} create[/blue]")
    if summary["delete"]:
        summary_parts.append(f"[red]{summary['delete']} delete[/red]")
    if summary["skipped"]:
        summary_parts.append(f"[dim]{summary['skipped']} skipped[/dim]")
    if summary["errors"]:
        summary_parts.append(f"[red bold]{summary['errors']} errors[/red bold]")

    console.print(f"[bold]Summary:[/bold] {', '.join(summary_parts)}")
