"""Tests for output formatters."""

from __future__ import annotations

import json
from io import StringIO

import pytest
from rich.console import Console

from dbt_unity_lineage.output import (
    STATUS_ICONS,
    STATUS_LABELS,
    OutputFormat,
    format_status,
    format_status_json,
    format_status_markdown,
    format_status_text,
    print_status_rich,
)
from dbt_unity_lineage.sync import SyncItem, SyncPlan, SyncStatus


@pytest.fixture
def empty_plan() -> SyncPlan:
    """Create an empty sync plan."""
    return SyncPlan(project_name="test_project", catalog="test_catalog")


@pytest.fixture
def plan_with_sources() -> SyncPlan:
    """Create a plan with sources."""
    plan = SyncPlan(project_name="test_project", catalog="test_catalog")
    plan.items = [
        SyncItem(
            identifier="sap.orders",
            name="sap__orders",
            system_type="SAP",
            entity_type="table",
            status=SyncStatus.IN_SYNC,
            item_type="source",
        ),
        SyncItem(
            identifier="postgres.users",
            name="postgres__users",
            system_type="POSTGRESQL",
            entity_type="table",
            status=SyncStatus.CREATE,
            item_type="source",
        ),
    ]
    return plan


@pytest.fixture
def plan_with_exposures() -> SyncPlan:
    """Create a plan with exposures."""
    plan = SyncPlan(project_name="test_project", catalog="test_catalog")
    plan.items = [
        SyncItem(
            identifier="sales_dashboard",
            name="sales_dashboard",
            system_type="POWER_BI",
            entity_type="dashboard",
            status=SyncStatus.UPDATE,
            item_type="exposure",
        ),
    ]
    return plan


@pytest.fixture
def plan_with_all_statuses() -> SyncPlan:
    """Create a plan with all status types."""
    plan = SyncPlan(project_name="test_project", catalog="test_catalog")
    plan.items = [
        SyncItem(
            identifier="source_in_sync",
            name="source_in_sync",
            system_type="SAP",
            entity_type="table",
            status=SyncStatus.IN_SYNC,
            item_type="source",
        ),
        SyncItem(
            identifier="source_create",
            name="source_create",
            system_type="POSTGRESQL",
            entity_type="table",
            status=SyncStatus.CREATE,
            item_type="source",
        ),
        SyncItem(
            identifier="source_update",
            name="source_update",
            system_type="MYSQL",
            entity_type="table",
            status=SyncStatus.UPDATE,
            item_type="source",
        ),
        SyncItem(
            identifier="source_delete",
            name="source_delete",
            system_type="ORACLE",
            entity_type="table",
            status=SyncStatus.DELETE,
            item_type="source",
        ),
        SyncItem(
            identifier="source_skip",
            name="source_skip",
            system_type="CUSTOM",
            entity_type="table",
            status=SyncStatus.SKIP,
            item_type="source",
        ),
        SyncItem(
            identifier="source_error",
            name="source_error",
            system_type="KAFKA",
            entity_type="table",
            status=SyncStatus.ERROR,
            item_type="source",
            error="Connection failed",
        ),
        SyncItem(
            identifier="exposure_sync",
            name="exposure_sync",
            system_type="POWER_BI",
            entity_type="dashboard",
            status=SyncStatus.IN_SYNC,
            item_type="exposure",
        ),
    ]
    return plan


class TestOutputFormat:
    """Tests for OutputFormat enum."""

    def test_text_format(self):
        """Test TEXT format value."""
        assert OutputFormat.TEXT.value == "text"

    def test_json_format(self):
        """Test JSON format value."""
        assert OutputFormat.JSON.value == "json"

    def test_markdown_format(self):
        """Test MARKDOWN format value."""
        assert OutputFormat.MARKDOWN.value == "md"


class TestStatusIcons:
    """Tests for status icons."""

    def test_all_statuses_have_icons(self):
        """Test that all sync statuses have icons."""
        for status in SyncStatus:
            assert status in STATUS_ICONS

    def test_all_statuses_have_labels(self):
        """Test that all sync statuses have labels."""
        for status in SyncStatus:
            assert status in STATUS_LABELS


class TestFormatStatusText:
    """Tests for text format output."""

    def test_empty_plan(self, empty_plan: SyncPlan):
        """Test formatting empty plan."""
        output = format_status_text(empty_plan)
        assert "test_project" in output
        assert "test_catalog" in output
        assert "Summary:" in output

    def test_plan_with_sources(self, plan_with_sources: SyncPlan):
        """Test formatting plan with sources."""
        output = format_status_text(plan_with_sources)
        assert "Upstream (Sources):" in output
        assert "sap.orders" in output
        assert "SAP" in output
        assert "postgres.users" in output
        assert "POSTGRESQL" in output

    def test_plan_with_exposures(self, plan_with_exposures: SyncPlan):
        """Test formatting plan with exposures."""
        output = format_status_text(plan_with_exposures)
        assert "Downstream (Exposures):" in output
        assert "sales_dashboard" in output
        assert "POWER_BI" in output

    def test_error_display(self, plan_with_all_statuses: SyncPlan):
        """Test that errors are displayed."""
        output = format_status_text(plan_with_all_statuses)
        assert "Connection failed" in output

    def test_summary_counts(self, plan_with_all_statuses: SyncPlan):
        """Test that summary counts are correct."""
        output = format_status_text(plan_with_all_statuses)
        assert "in sync" in output.lower()
        assert "create" in output.lower()
        assert "update" in output.lower()
        assert "delete" in output.lower()


class TestFormatStatusJson:
    """Tests for JSON format output."""

    def test_empty_plan(self, empty_plan: SyncPlan):
        """Test JSON output for empty plan."""
        output = format_status_json(empty_plan)
        data = json.loads(output)
        assert data["project"] == "test_project"
        assert data["catalog"] == "test_catalog"
        assert data["upstream"] == []
        assert data["downstream"] == []

    def test_plan_with_sources(self, plan_with_sources: SyncPlan):
        """Test JSON output with sources."""
        output = format_status_json(plan_with_sources)
        data = json.loads(output)
        assert len(data["upstream"]) == 2
        assert data["upstream"][0]["name"] == "sap.orders"
        assert data["upstream"][0]["system_type"] == "SAP"
        assert data["upstream"][0]["status"] == "in_sync"

    def test_plan_with_exposures(self, plan_with_exposures: SyncPlan):
        """Test JSON output with exposures."""
        output = format_status_json(plan_with_exposures)
        data = json.loads(output)
        assert len(data["downstream"]) == 1
        assert data["downstream"][0]["name"] == "sales_dashboard"

    def test_json_is_valid(self, plan_with_all_statuses: SyncPlan):
        """Test that output is valid JSON."""
        output = format_status_json(plan_with_all_statuses)
        data = json.loads(output)
        assert "summary" in data
        assert isinstance(data["summary"], dict)

    def test_error_in_json(self, plan_with_all_statuses: SyncPlan):
        """Test that errors are included in JSON output."""
        output = format_status_json(plan_with_all_statuses)
        data = json.loads(output)
        error_items = [
            item for item in data["upstream"] if item["error"] is not None
        ]
        assert len(error_items) > 0
        assert error_items[0]["error"] == "Connection failed"


class TestFormatStatusMarkdown:
    """Tests for Markdown format output."""

    def test_empty_plan(self, empty_plan: SyncPlan):
        """Test Markdown output for empty plan."""
        output = format_status_markdown(empty_plan)
        assert "## dbt-unity-lineage Status" in output
        assert "**Project:**" in output
        assert "**Catalog:**" in output

    def test_plan_with_sources(self, plan_with_sources: SyncPlan):
        """Test Markdown output with sources."""
        output = format_status_markdown(plan_with_sources)
        assert "### Upstream (Sources)" in output
        assert "| Source | System | Status |" in output
        assert "sap.orders" in output
        assert "SAP" in output

    def test_plan_with_exposures(self, plan_with_exposures: SyncPlan):
        """Test Markdown output with exposures."""
        output = format_status_markdown(plan_with_exposures)
        assert "### Downstream (Exposures)" in output
        assert "| Exposure | System | Status |" in output
        assert "sales_dashboard" in output

    def test_summary_table(self, plan_with_all_statuses: SyncPlan):
        """Test Markdown summary table."""
        output = format_status_markdown(plan_with_all_statuses)
        assert "### Summary" in output
        assert "| Status | Count |" in output

    def test_error_in_markdown(self, plan_with_all_statuses: SyncPlan):
        """Test that errors are shown in Markdown."""
        output = format_status_markdown(plan_with_all_statuses)
        assert "Connection failed" in output


class TestFormatStatus:
    """Tests for format_status dispatcher function."""

    def test_dispatch_text(self, empty_plan: SyncPlan):
        """Test dispatch to text format."""
        output = format_status(empty_plan, OutputFormat.TEXT)
        assert "Project:" in output

    def test_dispatch_json(self, empty_plan: SyncPlan):
        """Test dispatch to JSON format."""
        output = format_status(empty_plan, OutputFormat.JSON)
        data = json.loads(output)
        assert "project" in data

    def test_dispatch_markdown(self, empty_plan: SyncPlan):
        """Test dispatch to Markdown format."""
        output = format_status(empty_plan, OutputFormat.MARKDOWN)
        assert "## dbt-unity-lineage Status" in output

    def test_default_is_text(self, empty_plan: SyncPlan):
        """Test default format is text."""
        output = format_status(empty_plan)
        assert "Project:" in output


class TestPrintStatusRich:
    """Tests for Rich console output."""

    def test_prints_without_error(self, empty_plan: SyncPlan):
        """Test that Rich output doesn't raise errors."""
        console = Console(file=StringIO(), force_terminal=True)
        print_status_rich(empty_plan, console)
        # No exception means success

    def test_prints_sources(self, plan_with_sources: SyncPlan):
        """Test Rich output includes sources."""
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=120)
        print_status_rich(plan_with_sources, console)
        rendered = output.getvalue()
        assert "Upstream" in rendered or "Sources" in rendered

    def test_prints_exposures(self, plan_with_exposures: SyncPlan):
        """Test Rich output includes exposures."""
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=120)
        print_status_rich(plan_with_exposures, console)
        rendered = output.getvalue()
        assert "Downstream" in rendered or "Exposures" in rendered

    def test_prints_summary(self, plan_with_all_statuses: SyncPlan):
        """Test Rich output includes summary."""
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=120)
        print_status_rich(plan_with_all_statuses, console)
        rendered = output.getvalue()
        assert "Summary" in rendered

    def test_all_status_styles(self, plan_with_all_statuses: SyncPlan):
        """Test that all statuses can be rendered."""
        output = StringIO()
        console = Console(file=output, force_terminal=True, width=120)
        print_status_rich(plan_with_all_statuses, console)
        # Should not raise any errors
        assert len(output.getvalue()) > 0
