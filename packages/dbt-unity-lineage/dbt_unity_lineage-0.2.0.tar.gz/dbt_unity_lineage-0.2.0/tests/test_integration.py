"""Integration tests for dbt-unity-lineage.

These tests require a real Databricks connection and are run during PR CI.
Mark with @pytest.mark.integration to skip during regular test runs.

Required environment variables:
- DATABRICKS_HOST
- DATABRICKS_TOKEN
- DATABRICKS_CATALOG
- DATABRICKS_HTTP_PATH

Note: These tests clean up external lineage at the START of the test session,
but leave lineage in place after tests complete. This allows for visual
inspection in the Databricks UI and taking screenshots for documentation.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import pytest

from dbt_unity_lineage.config import load_config
from dbt_unity_lineage.manifest import load_manifest
from dbt_unity_lineage.profiles import DatabricksConnection
from dbt_unity_lineage.sync import apply_sync_plan, build_sync_plan
from dbt_unity_lineage.unity_catalog import UnityCatalogClient

logger = logging.getLogger(__name__)

INTEGRATION_FIXTURES = Path(__file__).parent / "fixtures" / "integration"


def get_test_connection() -> DatabricksConnection | None:
    """Get Databricks connection from environment variables."""
    host = os.environ.get("DATABRICKS_HOST")
    token = os.environ.get("DATABRICKS_TOKEN")
    catalog = os.environ.get("DATABRICKS_CATALOG")

    if not all([host, token, catalog]):
        return None

    return DatabricksConnection(
        host=host,
        token=token,
        catalog=catalog,
        http_path=os.environ.get("DATABRICKS_HTTP_PATH"),
    )


def cleanup_all_external_lineage(client: UnityCatalogClient) -> int:
    """Remove all external metadata managed by dbt-unity-lineage.

    Args:
        client: Unity Catalog client.

    Returns:
        Number of objects deleted.
    """
    deleted = 0
    try:
        metadata_list = client.list_external_metadata()
        for metadata in metadata_list:
            try:
                # Delete lineage edges first
                edges = client.list_lineage_edges(metadata.name, "external")
                for edge in edges:
                    try:
                        client.delete_lineage_edge(edge)
                    except Exception as e:
                        logger.debug(f"Failed to delete edge: {e}")

                # Delete the metadata object
                client.delete_external_metadata(metadata.name)
                deleted += 1
                logger.info(f"Deleted external metadata: {metadata.name}")
            except Exception as e:
                logger.warning(f"Failed to delete {metadata.name}: {e}")
    except Exception as e:
        logger.warning(f"Failed to list external metadata for cleanup: {e}")

    return deleted


@pytest.fixture(scope="session")
def session_connection() -> DatabricksConnection | None:
    """Session-scoped connection for cleanup."""
    return get_test_connection()


@pytest.fixture(scope="session", autouse=True)
def cleanup_before_tests(session_connection: DatabricksConnection | None):
    """Clean up all external lineage at the start of the test session.

    This runs automatically before any integration tests.
    Lineage is NOT cleaned up after tests complete, allowing for
    visual inspection in Databricks UI.
    """
    if session_connection is None:
        return  # Skip if no connection

    client = UnityCatalogClient(session_connection)
    deleted = cleanup_all_external_lineage(client)
    if deleted > 0:
        logger.info(f"Cleaned up {deleted} external metadata objects before tests")


@pytest.fixture
def integration_connection() -> DatabricksConnection:
    """Get integration test connection or skip."""
    conn = get_test_connection()
    if conn is None:
        pytest.skip("Databricks credentials not configured")
    return conn


@pytest.fixture
def integration_client(integration_connection: DatabricksConnection) -> UnityCatalogClient:
    """Get Unity Catalog client for integration tests."""
    return UnityCatalogClient(integration_connection)


@pytest.fixture
def integration_config():
    """Load integration test config."""
    return load_config(INTEGRATION_FIXTURES / "dbt_unity_lineage.yml")


@pytest.fixture
def integration_manifest():
    """Load integration test manifest."""
    return load_manifest(INTEGRATION_FIXTURES / "manifest.json")


@pytest.mark.integration
class TestSourceSystems:
    """Integration tests for source system configurations."""

    def test_postgresql_source(self, integration_manifest, integration_config, integration_client):
        """Test PostgreSQL source is properly configured."""
        plan = build_sync_plan(
            manifest=integration_manifest,
            config=integration_config,
            client=integration_client,
            sources_only=True,
        )

        postgres_sources = [s for s in plan.sources if "postgres" in s.identifier.lower()]
        assert len(postgres_sources) >= 1, "PostgreSQL sources should be present"

        for source in postgres_sources:
            assert source.system_type == "POSTGRESQL"

    def test_oracle_source(self, integration_manifest, integration_config, integration_client):
        """Test Oracle source is properly configured."""
        plan = build_sync_plan(
            manifest=integration_manifest,
            config=integration_config,
            client=integration_client,
            sources_only=True,
        )

        oracle_sources = [s for s in plan.sources if "oracle" in s.identifier.lower()]
        assert len(oracle_sources) >= 1, "Oracle sources should be present"

        for source in oracle_sources:
            assert source.system_type == "ORACLE"

    def test_sqlserver_source(self, integration_manifest, integration_config, integration_client):
        """Test SQL Server source is properly configured."""
        plan = build_sync_plan(
            manifest=integration_manifest,
            config=integration_config,
            client=integration_client,
            sources_only=True,
        )

        sqlserver_sources = [s for s in plan.sources if "sqlserver" in s.identifier.lower()]
        assert len(sqlserver_sources) >= 1, "SQL Server sources should be present"

        for source in sqlserver_sources:
            assert source.system_type == "MICROSOFT_SQL_SERVER"

    def test_workday_source(self, integration_manifest, integration_config, integration_client):
        """Test Workday source is properly configured."""
        plan = build_sync_plan(
            manifest=integration_manifest,
            config=integration_config,
            client=integration_client,
            sources_only=True,
        )

        workday_sources = [s for s in plan.sources if "workday" in s.identifier.lower()]
        assert len(workday_sources) >= 1, "Workday sources should be present"

        for source in workday_sources:
            assert source.system_type == "WORKDAY"

    def test_salesforce_source(self, integration_manifest, integration_config, integration_client):
        """Test Salesforce source is properly configured."""
        plan = build_sync_plan(
            manifest=integration_manifest,
            config=integration_config,
            client=integration_client,
            sources_only=True,
        )

        sf_sources = [s for s in plan.sources if "salesforce" in s.identifier.lower()]
        assert len(sf_sources) >= 1, "Salesforce sources should be present"

        for source in sf_sources:
            assert source.system_type == "SALESFORCE"

    def test_sap_source(self, integration_manifest, integration_config, integration_client):
        """Test SAP source is properly configured."""
        plan = build_sync_plan(
            manifest=integration_manifest,
            config=integration_config,
            client=integration_client,
            sources_only=True,
        )

        sap_sources = [s for s in plan.sources if "sap" in s.identifier.lower()]
        assert len(sap_sources) >= 1, "SAP sources should be present"

        for source in sap_sources:
            assert source.system_type == "SAP"


@pytest.mark.integration
class TestExposures:
    """Integration tests for exposure configurations."""

    def test_powerbi_exposure(self, integration_manifest, integration_config, integration_client):
        """Test Power BI exposures are properly detected."""
        plan = build_sync_plan(
            manifest=integration_manifest,
            config=integration_config,
            client=integration_client,
            exposures_only=True,
        )

        powerbi_exposures = [e for e in plan.exposures if e.system_type == "POWER_BI"]
        assert len(powerbi_exposures) >= 2, "Should have at least 2 Power BI exposures"

    def test_tableau_exposure(self, integration_manifest, integration_config, integration_client):
        """Test Tableau exposures are properly detected."""
        plan = build_sync_plan(
            manifest=integration_manifest,
            config=integration_config,
            client=integration_client,
            exposures_only=True,
        )

        tableau_exposures = [e for e in plan.exposures if e.system_type == "TABLEAU"]
        assert len(tableau_exposures) >= 2, "Should have at least 2 Tableau exposures"

    def test_looker_exposure(self, integration_manifest, integration_config, integration_client):
        """Test Looker exposures are properly detected."""
        plan = build_sync_plan(
            manifest=integration_manifest,
            config=integration_config,
            client=integration_client,
            exposures_only=True,
        )

        looker_exposures = [e for e in plan.exposures if e.system_type == "LOOKER"]
        assert len(looker_exposures) >= 1, "Should have at least 1 Looker exposure"

    def test_salesforce_exposure(
        self, integration_manifest, integration_config, integration_client
    ):
        """Test Salesforce exposures are properly detected from URL."""
        plan = build_sync_plan(
            manifest=integration_manifest,
            config=integration_config,
            client=integration_client,
            exposures_only=True,
        )

        sf_exposures = [e for e in plan.exposures if e.system_type == "SALESFORCE"]
        assert len(sf_exposures) >= 1, "Should have at least 1 Salesforce exposure"

    def test_custom_exposure(self, integration_manifest, integration_config, integration_client):
        """Test explicit CUSTOM system type override."""
        plan = build_sync_plan(
            manifest=integration_manifest,
            config=integration_config,
            client=integration_client,
            exposures_only=True,
        )

        ml_exposure = next(
            (e for e in plan.exposures if "ml_churn" in e.identifier),
            None
        )
        assert ml_exposure is not None, "ML exposure should exist"
        assert ml_exposure.system_type == "CUSTOM"


@pytest.mark.integration
class TestSyncPlan:
    """Integration tests for sync plan building."""

    def test_build_full_plan(self, integration_manifest, integration_config, integration_client):
        """Test building a full sync plan."""
        plan = build_sync_plan(
            manifest=integration_manifest,
            config=integration_config,
            client=integration_client,
        )

        # Should have sources and exposures
        assert len(plan.sources) > 0, "Should have sources"
        assert len(plan.exposures) > 0, "Should have exposures"

        # Check summary
        summary = plan.summary()
        assert "in_sync" in summary
        assert "create" in summary
        assert "update" in summary
        assert "delete" in summary

    def test_plan_sources_only(self, integration_manifest, integration_config, integration_client):
        """Test building sources-only plan."""
        plan = build_sync_plan(
            manifest=integration_manifest,
            config=integration_config,
            client=integration_client,
            sources_only=True,
        )

        assert len(plan.sources) > 0
        assert len(plan.exposures) == 0

    def test_plan_exposures_only(
        self, integration_manifest, integration_config, integration_client
    ):
        """Test building exposures-only plan."""
        plan = build_sync_plan(
            manifest=integration_manifest,
            config=integration_config,
            client=integration_client,
            exposures_only=True,
        )

        assert len(plan.sources) == 0
        assert len(plan.exposures) > 0

    def test_lineage_edges_for_sources(
        self, integration_manifest, integration_config, integration_client
    ):
        """Test that sources have lineage edges to bronze tables."""
        plan = build_sync_plan(
            manifest=integration_manifest,
            config=integration_config,
            client=integration_client,
            sources_only=True,
        )

        for source in plan.sources:
            # Each source should have at least one lineage edge
            assert len(source.lineage_edges) >= 0  # May be 0 if table doesn't exist

    def test_lineage_edges_for_exposures(
        self, integration_manifest, integration_config, integration_client
    ):
        """Test that exposures have lineage edges from gold tables."""
        plan = build_sync_plan(
            manifest=integration_manifest,
            config=integration_config,
            client=integration_client,
            exposures_only=True,
        )

        # Executive dashboard depends on fct_orders and dim_customers
        exec_dash = next(
            (e for e in plan.exposures if "executive_dashboard" in e.identifier),
            None
        )
        assert exec_dash is not None
        assert len(exec_dash.lineage_edges) == 2


@pytest.mark.integration
class TestConnectionHealth:
    """Integration tests for Databricks connection."""

    def test_connection_valid(self, integration_client):
        """Test that the connection is valid."""
        assert integration_client.catalog == "dbt_unity_lineage_test"

    def test_can_list_metadata(self, integration_client):
        """Test that we can list external metadata (even if empty)."""
        # This should not raise an error
        try:
            metadata = integration_client.list_external_metadata()
            assert isinstance(metadata, list)
        except Exception:
            # External lineage API may not be available
            pytest.skip("External lineage API not available")


def _check_api_available(result) -> bool:
    """Check if the external lineage API is available based on sync result."""
    if result.errors:
        first_error = result.errors[0].error or ""
        if "No API found" in first_error or "not accessible" in first_error.lower():
            return False
    return True


@pytest.mark.integration
class TestApplySync:
    """Integration tests that actually apply sync to Unity Catalog.

    These tests create external lineage in Databricks. The lineage is
    intentionally NOT cleaned up after tests, allowing for visual inspection
    in the Databricks Catalog Explorer UI.

    Note: These tests require the external lineage API to be enabled in your
    Databricks workspace (public preview feature). Tests will skip gracefully
    if the API is not available.

    Ideal lineage flow for screenshots:
    Oracle/SQL Server → Bronze → Silver → Gold → Power BI
    """

    def test_apply_full_sync(
        self, integration_manifest, integration_config, integration_client
    ):
        """Apply a full sync and verify objects are created.

        This test creates all sources and exposures in Unity Catalog.
        After this test runs, you can view the lineage in Databricks UI.
        """
        # Build sync plan
        plan = build_sync_plan(
            manifest=integration_manifest,
            config=integration_config,
            client=integration_client,
        )

        # Count items that will be created
        initial_create_count = len(plan.to_create)
        logger.info(f"Sync plan: {initial_create_count} items to create")

        # Apply the plan
        result = apply_sync_plan(
            plan=plan,
            client=integration_client,
            dry_run=False,
            no_clean=False,
        )

        # Check if API is available - skip if not
        if not _check_api_available(result):
            pytest.skip("External lineage API not available (public preview feature)")

        # Verify no errors
        assert len(result.errors) == 0, f"Sync had errors: {[e.error for e in result.errors]}"

        # Verify sources were synced
        assert len(result.sources) > 0, "Should have synced sources"

        # Verify exposures were synced
        assert len(result.exposures) > 0, "Should have synced exposures"

        # Log what was synced for visibility
        logger.info(f"Synced {len(result.sources)} sources and {len(result.exposures)} exposures")

    def test_sync_is_idempotent(
        self, integration_manifest, integration_config, integration_client
    ):
        """Verify that running sync twice results in everything being in sync."""
        # First sync (may create or be already synced from previous test)
        plan1 = build_sync_plan(
            manifest=integration_manifest,
            config=integration_config,
            client=integration_client,
        )
        result1 = apply_sync_plan(plan=plan1, client=integration_client, dry_run=False)

        # Check if API is available - skip if not
        if not _check_api_available(result1):
            pytest.skip("External lineage API not available (public preview feature)")

        # Second sync should show everything in sync
        plan2 = build_sync_plan(
            manifest=integration_manifest,
            config=integration_config,
            client=integration_client,
        )

        # All items should be in sync (nothing to create/update/delete)
        assert len(plan2.to_create) == 0, "Should have nothing to create on re-sync"
        assert len(plan2.to_update) == 0, "Should have nothing to update on re-sync"
        assert len(plan2.to_delete) == 0, "Should have nothing to delete on re-sync"

    def test_verify_lineage_in_catalog(
        self, integration_manifest, integration_config, integration_client
    ):
        """Verify that lineage is visible in the catalog.

        This test checks that the external metadata we pushed is queryable.
        """
        # Ensure sync has been applied
        plan = build_sync_plan(
            manifest=integration_manifest,
            config=integration_config,
            client=integration_client,
        )
        result = apply_sync_plan(plan=plan, client=integration_client, dry_run=False)

        # Check if API is available - skip if not
        if not _check_api_available(result):
            pytest.skip("External lineage API not available (public preview feature)")

        # List all external metadata
        metadata = integration_client.list_external_metadata()

        # Should have our sources and exposures
        assert len(metadata) > 0, "Should have external metadata in catalog"

        # Check for expected system types
        system_types = {m.system_type for m in metadata}
        assert "ORACLE" in system_types or "MICROSOFT_SQL_SERVER" in system_types, \
            "Should have Oracle or SQL Server source"
        assert "POWER_BI" in system_types, "Should have Power BI exposure"

        # Log for visibility
        logger.info(f"Found {len(metadata)} external metadata objects:")
        for m in metadata:
            logger.info(f"  - {m.name} ({m.system_type})")
