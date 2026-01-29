"""Integration tests using the FastAPI mock server.

These tests verify the full sync workflow against a mock Unity Catalog API,
testing stateful behavior without requiring a real Databricks workspace.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pytest
import requests

from dbt_unity_lineage.config import load_config
from dbt_unity_lineage.manifest import load_manifest
from dbt_unity_lineage.profiles import DatabricksConnection
from dbt_unity_lineage.sync import apply_sync_plan, build_sync_plan
from dbt_unity_lineage.unity_catalog import UnityCatalogClient


def make_mock_client(
    mock_server_url: str,
    connection: DatabricksConnection,
) -> UnityCatalogClient:
    """Create a UnityCatalogClient that uses the mock server.

    We need to patch the SDK's api_client.do method to use our mock server.
    """
    client = UnityCatalogClient(connection)

    def mock_do(method: str, path: str, **kwargs):
        """Route API calls to mock server."""
        url = f"{mock_server_url}{path}"

        # Convert SDK kwargs to requests kwargs
        request_kwargs: Dict[str, Any] = {}
        if "query" in kwargs:
            request_kwargs["params"] = kwargs["query"]
        if "body" in kwargs:
            request_kwargs["json"] = kwargs["body"]

        # Make request to mock server
        response = requests.request(method, url, **request_kwargs)

        if response.status_code >= 400:
            # Raise an exception similar to what the SDK would raise
            error_msg = response.text
            try:
                error_data = response.json()
                if "message" in error_data:
                    error_msg = error_data["message"]
                elif "detail" in error_data:
                    detail = error_data["detail"]
                    if isinstance(detail, dict):
                        error_msg = detail.get("message", str(detail))
                    else:
                        error_msg = str(detail)
            except Exception:
                pass

            # Create exception with status_code attribute
            exc = Exception(f"HTTP {response.status_code}: {error_msg}")
            exc.status_code = response.status_code  # type: ignore
            raise exc

        # Return JSON response or empty dict
        try:
            return response.json()
        except Exception:
            return {}

    client._client.api_client.do = mock_do
    return client


@pytest.mark.mock_api
class TestMockServerBasics:
    """Basic tests for the mock server functionality."""

    def test_server_health(self, mock_server_reset: str):
        """Test that mock server is running and healthy."""
        response = requests.get(f"{mock_server_reset}/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_create_and_list_metadata(self, mock_server_reset: str):
        """Test creating and listing external metadata directly."""
        # Create metadata
        create_response = requests.post(
            f"{mock_server_reset}/api/2.1/unity-catalog/external-metadata",
            json={
                "name": "test_source",
                "catalog_name": "test_catalog",
                "system_type": "POSTGRESQL",
                "entity_type": "table",
                "properties": {"managed_by": "test"},
            },
        )
        assert create_response.status_code == 200

        # List metadata
        list_response = requests.get(
            f"{mock_server_reset}/api/2.1/unity-catalog/external-metadata",
            params={"catalog_name": "test_catalog"},
        )
        assert list_response.status_code == 200
        data = list_response.json()
        assert len(data["external_metadata"]) == 1
        assert data["external_metadata"][0]["name"] == "test_source"

    def test_create_and_delete_metadata(self, mock_server_reset: str):
        """Test creating and deleting external metadata."""
        # Create
        requests.post(
            f"{mock_server_reset}/api/2.1/unity-catalog/external-metadata",
            json={
                "name": "to_delete",
                "catalog_name": "test_catalog",
                "system_type": "SAP",
                "entity_type": "table",
            },
        )

        # Delete
        delete_response = requests.delete(
            f"{mock_server_reset}/api/2.1/unity-catalog/external-metadata/to_delete",
            params={"catalog_name": "test_catalog"},
        )
        assert delete_response.status_code == 200

        # Verify deleted
        list_response = requests.get(
            f"{mock_server_reset}/api/2.1/unity-catalog/external-metadata",
            params={"catalog_name": "test_catalog"},
        )
        assert len(list_response.json()["external_metadata"]) == 0


@pytest.mark.mock_api
class TestSyncWithMockServer:
    """Tests for sync operations using the mock server."""

    def test_build_sync_plan(
        self,
        mock_server_reset: str,
        mock_connection: DatabricksConnection,
        sample_manifest_path: Path,
        sample_config_path: Path,
    ):
        """Test building a sync plan with the mock server."""
        client = make_mock_client(mock_server_reset, mock_connection)
        manifest = load_manifest(sample_manifest_path)
        config = load_config(sample_config_path)

        plan = build_sync_plan(
            manifest=manifest,
            config=config,
            client=client,
        )

        # Should have sources and exposures to create
        assert len(plan.sources) > 0
        assert len(plan.exposures) > 0
        assert len(plan.to_create) > 0

    def test_apply_sync_creates_metadata(
        self,
        mock_server_reset: str,
        mock_connection: DatabricksConnection,
        sample_manifest_path: Path,
        sample_config_path: Path,
    ):
        """Test that applying sync creates metadata in the mock server."""
        client = make_mock_client(mock_server_reset, mock_connection)
        manifest = load_manifest(sample_manifest_path)
        config = load_config(sample_config_path)

        # Build and apply plan
        plan = build_sync_plan(manifest=manifest, config=config, client=client)
        result = apply_sync_plan(plan=plan, client=client, dry_run=False)

        # Should have no errors
        assert len(result.errors) == 0

        # Verify metadata was created in mock server
        list_response = requests.get(
            f"{mock_server_reset}/api/2.1/unity-catalog/external-metadata",
            params={"catalog_name": "test_catalog"},
        )
        metadata = list_response.json()["external_metadata"]
        assert len(metadata) > 0

        # Check for expected sources
        names = [m["name"] for m in metadata]
        assert any("postgres" in name.lower() for name in names)

    def test_sync_is_idempotent(
        self,
        mock_server_reset: str,
        mock_connection: DatabricksConnection,
        sample_manifest_path: Path,
        sample_config_path: Path,
    ):
        """Test that running sync twice results in no additional changes."""
        client = make_mock_client(mock_server_reset, mock_connection)
        manifest = load_manifest(sample_manifest_path)
        config = load_config(sample_config_path)

        # First sync
        plan1 = build_sync_plan(manifest=manifest, config=config, client=client)
        apply_sync_plan(plan=plan1, client=client, dry_run=False)

        # Second sync should show everything in sync
        plan2 = build_sync_plan(manifest=manifest, config=config, client=client)

        assert len(plan2.to_create) == 0, "Nothing should need to be created"
        assert len(plan2.to_update) == 0, "Nothing should need to be updated"
        assert len(plan2.to_delete) == 0, "Nothing should need to be deleted"

    def test_delete_orphaned_metadata(
        self,
        mock_server_reset: str,
        mock_connection: DatabricksConnection,
        sample_manifest_path: Path,
        sample_config_path: Path,
    ):
        """Test that orphaned metadata is deleted during sync."""
        client = make_mock_client(mock_server_reset, mock_connection)
        manifest = load_manifest(sample_manifest_path)
        config = load_config(sample_config_path)

        # Create an "orphaned" metadata object directly
        requests.post(
            f"{mock_server_reset}/api/2.1/unity-catalog/external-metadata",
            json={
                "name": "orphaned_source",
                "catalog_name": "test_catalog",
                "system_type": "CUSTOM",
                "entity_type": "table",
                "properties": {
                    "managed_by": "dbt-unity-lineage",
                    "dbt_project": "test_project",
                    "dbt_source": "orphaned.table",
                },
            },
        )

        # Build plan - orphaned object should be marked for deletion
        plan = build_sync_plan(manifest=manifest, config=config, client=client)

        orphaned_delete = [d for d in plan.to_delete if "orphaned" in d.name]
        assert len(orphaned_delete) == 1, "Orphaned source should be marked for deletion"

        # Apply sync
        apply_sync_plan(plan=plan, client=client, dry_run=False, no_clean=False)

        # Verify orphaned object was deleted
        list_response = requests.get(
            f"{mock_server_reset}/api/2.1/unity-catalog/external-metadata",
            params={"catalog_name": "test_catalog"},
        )
        names = [m["name"] for m in list_response.json()["external_metadata"]]
        assert "orphaned_source" not in names


@pytest.mark.mock_api
class TestErrorSimulation:
    """Tests for error simulation in the mock server."""

    def test_rate_limit_simulation(self, mock_server_reset: str):
        """Test that rate limit simulation works."""
        # Enable rate limiting
        requests.post(
            f"{mock_server_reset}/test/simulate-rate-limit",
            params={"duration_seconds": 1},
        )

        # Request should fail with 429
        response = requests.get(
            f"{mock_server_reset}/api/2.1/unity-catalog/external-metadata",
            params={"catalog_name": "test"},
        )
        assert response.status_code == 429

    def test_auth_error_simulation(self, mock_server_reset: str):
        """Test that auth error simulation works."""
        # Enable auth error
        requests.post(f"{mock_server_reset}/test/simulate-auth-error", params={"enabled": True})

        # Request should fail with 401
        response = requests.get(
            f"{mock_server_reset}/api/2.1/unity-catalog/external-metadata",
            params={"catalog_name": "test"},
        )
        assert response.status_code == 401

        # Disable and verify normal operation
        requests.post(f"{mock_server_reset}/test/simulate-auth-error", params={"enabled": False})
        response = requests.get(
            f"{mock_server_reset}/api/2.1/unity-catalog/external-metadata",
            params={"catalog_name": "test"},
        )
        assert response.status_code == 200

    def test_api_unavailable_simulation(self, mock_server_reset: str):
        """Test API unavailable simulation (404 for all endpoints)."""
        # Enable API unavailable
        requests.post(
            f"{mock_server_reset}/test/simulate-api-unavailable",
            params={"enabled": True},
        )

        # Request should fail with 404 ENDPOINT_NOT_FOUND
        response = requests.get(
            f"{mock_server_reset}/api/2.1/unity-catalog/external-metadata",
            params={"catalog_name": "test"},
        )
        assert response.status_code == 404
        assert "ENDPOINT_NOT_FOUND" in response.json().get("error_code", "")


@pytest.mark.mock_api
class TestDbtCloudMock:
    """Tests for dbt Cloud API mock."""

    def test_add_job_and_run(self, mock_server_reset: str):
        """Test adding a job and run to the mock server."""
        # Add job
        job_response = requests.post(
            f"{mock_server_reset}/test/dbt-cloud/add-job",
            params={"job_id": 123, "name": "Production Build"},
        )
        assert job_response.status_code == 200

        # Add run
        run_response = requests.post(
            f"{mock_server_reset}/test/dbt-cloud/add-run",
            params={"job_id": 123, "run_id": 456, "status": 10},
        )
        assert run_response.status_code == 200

        # List jobs
        jobs = requests.get(f"{mock_server_reset}/api/v2/accounts/12345/jobs/")
        assert len(jobs.json()["data"]) == 1
        assert jobs.json()["data"][0]["name"] == "Production Build"

        # List runs
        runs = requests.get(
            f"{mock_server_reset}/api/v2/accounts/12345/runs/",
            params={"job_definition_id": 123, "status": 10},
        )
        assert len(runs.json()["data"]) == 1

    def test_get_manifest_artifact(self, mock_server_reset: str):
        """Test fetching manifest artifact from mock server."""
        import json

        # Add job and run with custom manifest
        manifest = {
            "metadata": {"project_name": "my_project"},
            "nodes": {},
            "sources": {},
            "exposures": {},
        }

        requests.post(f"{mock_server_reset}/test/dbt-cloud/add-job", params={"job_id": 100})
        requests.post(
            f"{mock_server_reset}/test/dbt-cloud/add-run",
            params={
                "job_id": 100,
                "run_id": 200,
                "manifest_content": json.dumps(manifest),
            },
        )

        # Fetch artifact
        artifact = requests.get(
            f"{mock_server_reset}/api/v2/accounts/12345/runs/200/artifacts/manifest.json"
        )
        assert artifact.status_code == 200
        assert artifact.json()["metadata"]["project_name"] == "my_project"


@pytest.mark.mock_api
class TestLineageEdges:
    """Tests for lineage edge operations."""

    def test_create_and_list_edges(self, mock_server_reset: str):
        """Test creating and listing lineage edges."""
        # Create source metadata
        requests.post(
            f"{mock_server_reset}/api/2.1/unity-catalog/external-metadata",
            json={
                "name": "source_system",
                "catalog_name": "test_catalog",
                "system_type": "POSTGRESQL",
                "entity_type": "table",
            },
        )

        # Create lineage edge
        edge_response = requests.post(
            f"{mock_server_reset}/api/2.1/unity-catalog/lineage/external-edges",
            json={
                "catalog_name": "test_catalog",
                "source_external_metadata": "source_system",
                "target_table": "test_catalog.bronze.orders",
            },
        )
        assert edge_response.status_code == 200

        # List edges
        list_response = requests.get(
            f"{mock_server_reset}/api/2.1/unity-catalog/lineage/external-edges",
            params={"catalog_name": "test_catalog", "external_metadata_name": "source_system"},
        )
        edges = list_response.json()["edges"]
        assert len(edges) == 1
        assert edges[0]["source_external_metadata"] == "source_system"

    def test_delete_edge(self, mock_server_reset: str):
        """Test deleting a lineage edge."""
        # Create edge
        requests.post(
            f"{mock_server_reset}/api/2.1/unity-catalog/lineage/external-edges",
            json={
                "catalog_name": "test_catalog",
                "source_table": "test_catalog.gold.orders",
                "target_external_metadata": "powerbi_dashboard",
            },
        )

        # Delete edge
        delete_response = requests.delete(
            f"{mock_server_reset}/api/2.1/unity-catalog/lineage/external-edges",
            json={
                "catalog_name": "test_catalog",
                "source_table": "test_catalog.gold.orders",
                "target_external_metadata": "powerbi_dashboard",
            },
        )
        assert delete_response.status_code == 200

        # Verify deleted
        list_response = requests.get(
            f"{mock_server_reset}/api/2.1/unity-catalog/lineage/external-edges",
            params={"catalog_name": "test_catalog"},
        )
        assert len(list_response.json()["edges"]) == 0
