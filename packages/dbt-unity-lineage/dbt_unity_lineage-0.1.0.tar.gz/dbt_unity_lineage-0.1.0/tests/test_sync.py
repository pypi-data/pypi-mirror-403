"""Tests for sync module."""

from __future__ import annotations

from unittest.mock import MagicMock

from dbt_unity_lineage.config import Config
from dbt_unity_lineage.manifest import Manifest
from dbt_unity_lineage.sync import (
    SyncStatus,
    _make_external_name,
    build_sync_plan,
)
from dbt_unity_lineage.unity_catalog import ExternalMetadata


class TestMakeExternalName:
    """Tests for _make_external_name function."""

    def test_simple_name(self) -> None:
        """Test simple name generation."""
        name = _make_external_name("my_project", "source", "table")
        assert name == "my_project__source__table"

    def test_single_part(self) -> None:
        """Test with single part."""
        name = _make_external_name("my_project", "exposure")
        assert name == "my_project__exposure"


class TestBuildSyncPlan:
    """Tests for build_sync_plan function."""

    def test_build_plan_with_sources(
        self,
        sample_manifest: Manifest,
        sample_config: Config,
        mock_client: MagicMock,
    ) -> None:
        """Test building sync plan includes sources."""
        plan = build_sync_plan(
            manifest=sample_manifest,
            config=sample_config,
            client=mock_client,
        )

        assert plan.project_name == "jaffle_shop"
        assert plan.catalog == "main"

        # Check sources are included
        sources = plan.sources
        assert len(sources) == 3

        # All should be CREATE since mock returns empty list
        assert all(s.status == SyncStatus.CREATE for s in sources)

    def test_build_plan_with_exposures(
        self,
        sample_manifest: Manifest,
        sample_config: Config,
        mock_client: MagicMock,
    ) -> None:
        """Test building sync plan includes exposures."""
        plan = build_sync_plan(
            manifest=sample_manifest,
            config=sample_config,
            client=mock_client,
        )

        exposures = plan.exposures
        assert len(exposures) == 3

        # Check exposure types are inferred correctly
        exec_dash = next(e for e in exposures if e.identifier == "executive_dashboard")
        assert exec_dash.system_type == "POWER_BI"  # Inferred from URL

        sales_report = next(e for e in exposures if e.identifier == "sales_report")
        assert sales_report.system_type == "TABLEAU"  # Inferred from URL

        custom_app = next(e for e in exposures if e.identifier == "custom_app")
        assert custom_app.system_type == "CUSTOM"  # Explicit override

    def test_build_plan_sources_only(
        self,
        sample_manifest: Manifest,
        sample_config: Config,
        mock_client: MagicMock,
    ) -> None:
        """Test building plan with sources_only flag."""
        plan = build_sync_plan(
            manifest=sample_manifest,
            config=sample_config,
            client=mock_client,
            sources_only=True,
        )

        assert len(plan.sources) == 3
        assert len(plan.exposures) == 0

    def test_build_plan_exposures_only(
        self,
        sample_manifest: Manifest,
        sample_config: Config,
        mock_client: MagicMock,
    ) -> None:
        """Test building plan with exposures_only flag."""
        plan = build_sync_plan(
            manifest=sample_manifest,
            config=sample_config,
            client=mock_client,
            exposures_only=True,
        )

        assert len(plan.sources) == 0
        assert len(plan.exposures) == 3

    def test_build_plan_detects_update(
        self,
        sample_manifest: Manifest,
        sample_config: Config,
        mock_client: MagicMock,
    ) -> None:
        """Test that plan detects when update is needed."""
        # Mock existing metadata with different description
        existing = ExternalMetadata(
            name="jaffle_shop__sap_ecc__erp.gl_accounts",
            system_type="SAP",
            entity_type="table",
            description="Old description",  # Different from source
            properties={
                "managed_by": "dbt-unity-lineage",
                "dbt_project": "jaffle_shop",
                "dbt_source": "erp.gl_accounts",
            },
        )
        mock_client.list_external_metadata.return_value = [existing]

        plan = build_sync_plan(
            manifest=sample_manifest,
            config=sample_config,
            client=mock_client,
        )

        # Find the gl_accounts source
        gl_accounts = next(
            (s for s in plan.sources if "gl_accounts" in s.identifier),
            None,
        )
        assert gl_accounts is not None
        assert gl_accounts.status == SyncStatus.UPDATE

    def test_build_plan_detects_delete(
        self,
        sample_manifest: Manifest,
        sample_config: Config,
        mock_client: MagicMock,
    ) -> None:
        """Test that plan detects orphaned objects for deletion."""
        # Mock existing metadata that doesn't exist in manifest
        orphaned = ExternalMetadata(
            name="jaffle_shop__old_source__old_table",
            system_type="SAP",
            entity_type="table",
            properties={
                "managed_by": "dbt-unity-lineage",
                "dbt_project": "jaffle_shop",
                "dbt_source": "old_source.old_table",
            },
        )
        mock_client.list_external_metadata.return_value = [orphaned]

        plan = build_sync_plan(
            manifest=sample_manifest,
            config=sample_config,
            client=mock_client,
        )

        # Check that orphaned object is marked for deletion
        to_delete = plan.to_delete
        assert len(to_delete) == 1
        assert to_delete[0].name == "jaffle_shop__old_source__old_table"

    def test_build_plan_in_sync(
        self,
        sample_manifest: Manifest,
        sample_config: Config,
        mock_client: MagicMock,
    ) -> None:
        """Test that plan detects when object is in sync."""
        # Mock existing metadata that matches desired state
        # Note: description comes from source first, then config fallback
        existing = ExternalMetadata(
            name="jaffle_shop__sap_ecc__erp.gl_accounts",
            system_type="SAP",
            entity_type="table",
            description="General ledger accounts from SAP",  # Matches source
            url="https://sap.example.com",
            owner="erp-team@example.com",
            properties={
                "managed_by": "dbt-unity-lineage",
                "dbt_project": "jaffle_shop",
                "dbt_source": "erp.gl_accounts",
                "environment": "production",
                "data_classification": "confidential",
            },
        )
        mock_client.list_external_metadata.return_value = [existing]

        plan = build_sync_plan(
            manifest=sample_manifest,
            config=sample_config,
            client=mock_client,
        )

        # Find the gl_accounts source
        gl_accounts = next(
            (s for s in plan.sources if "gl_accounts" in s.identifier),
            None,
        )
        assert gl_accounts is not None
        assert gl_accounts.status == SyncStatus.IN_SYNC


class TestSyncPlan:
    """Tests for SyncPlan model."""

    def test_summary(
        self,
        sample_manifest: Manifest,
        sample_config: Config,
        mock_client: MagicMock,
    ) -> None:
        """Test plan summary generation."""
        plan = build_sync_plan(
            manifest=sample_manifest,
            config=sample_config,
            client=mock_client,
        )

        summary = plan.summary()
        assert "in_sync" in summary
        assert "create" in summary
        assert "update" in summary
        assert "delete" in summary
        assert "skipped" in summary
        assert "errors" in summary

        # With mock returning empty, all should be CREATE
        assert summary["create"] == 6  # 3 sources + 3 exposures
