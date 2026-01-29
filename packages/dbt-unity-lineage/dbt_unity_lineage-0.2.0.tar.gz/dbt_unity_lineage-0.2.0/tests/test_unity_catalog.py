"""Tests for Unity Catalog client."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from dbt_unity_lineage.profiles import DatabricksConnection
from dbt_unity_lineage.unity_catalog import (
    ExternalMetadata,
    LineageEdge,
    MaxRetriesExceededError,
    RetryableError,
    UnityCatalogClient,
    _extract_status_code,
)


@pytest.fixture
def mock_connection() -> DatabricksConnection:
    """Create a mock Databricks connection."""
    return DatabricksConnection(
        host="test.databricks.com",
        token="test-token",
        catalog="test_catalog",
        http_path="/sql/test",
    )


class TestExternalMetadata:
    """Tests for ExternalMetadata dataclass."""

    def test_basic_creation(self):
        """Test basic metadata creation."""
        metadata = ExternalMetadata(
            name="test_source",
            system_type="SAP",
            entity_type="table",
        )
        assert metadata.name == "test_source"
        assert metadata.system_type == "SAP"
        assert metadata.entity_type == "table"
        assert metadata.description is None
        assert metadata.url is None
        assert metadata.properties == {}

    def test_full_creation(self):
        """Test metadata with all fields."""
        metadata = ExternalMetadata(
            name="test_source",
            system_type="SAP",
            entity_type="table",
            description="Test description",
            url="https://example.com",
            owner="test@example.com",
            properties={"key": "value"},
        )
        assert metadata.description == "Test description"
        assert metadata.url == "https://example.com"
        assert metadata.owner == "test@example.com"
        assert metadata.properties == {"key": "value"}

    def test_to_api_dict_minimal(self):
        """Test conversion to API dict with minimal fields."""
        metadata = ExternalMetadata(
            name="test_source",
            system_type="SAP",
            entity_type="table",
        )
        api_dict = metadata.to_api_dict()
        assert api_dict == {
            "name": "test_source",
            "system_type": "SAP",
            "entity_type": "table",
        }

    def test_to_api_dict_full(self):
        """Test conversion to API dict with all fields."""
        metadata = ExternalMetadata(
            name="test_source",
            system_type="SAP",
            entity_type="table",
            description="Test description",
            url="https://example.com",
            owner="test@example.com",
            properties={"key": "value"},
        )
        api_dict = metadata.to_api_dict()
        assert api_dict["description"] == "Test description"
        assert api_dict["url"] == "https://example.com"
        assert api_dict["owner"] == "test@example.com"
        assert api_dict["properties"] == {"key": "value"}

    def test_from_api_response(self):
        """Test creation from API response."""
        response = {
            "name": "test_source",
            "system_type": "SAP",
            "entity_type": "table",
            "description": "Test",
            "url": "https://example.com",
            "owner": "test@example.com",
            "properties": {"managed_by": "dbt-unity-lineage"},
        }
        metadata = ExternalMetadata.from_api_response(response)
        assert metadata.name == "test_source"
        assert metadata.system_type == "SAP"
        assert metadata.entity_type == "table"
        assert metadata.description == "Test"
        assert metadata.url == "https://example.com"
        assert metadata.owner == "test@example.com"
        assert metadata.properties["managed_by"] == "dbt-unity-lineage"

    def test_from_api_response_minimal(self):
        """Test creation from minimal API response."""
        response = {"name": "test_source"}
        metadata = ExternalMetadata.from_api_response(response)
        assert metadata.name == "test_source"
        assert metadata.system_type == "CUSTOM"  # default
        assert metadata.entity_type == "table"  # default


class TestLineageEdge:
    """Tests for LineageEdge dataclass."""

    def test_source_to_table_edge(self):
        """Test edge from external source to table."""
        edge = LineageEdge(
            source_entity="sap_orders",
            target_entity="catalog.schema.orders",
            source_type="external",
            target_type="table",
        )
        assert edge.source_entity == "sap_orders"
        assert edge.target_entity == "catalog.schema.orders"
        assert edge.source_type == "external"
        assert edge.target_type == "table"

    def test_table_to_exposure_edge(self):
        """Test edge from table to external exposure."""
        edge = LineageEdge(
            source_entity="catalog.schema.orders",
            target_entity="powerbi_dashboard",
            source_type="table",
            target_type="external",
        )
        assert edge.source_type == "table"
        assert edge.target_type == "external"


class TestExtractStatusCode:
    """Tests for _extract_status_code function."""

    def test_status_code_attribute(self):
        """Test extraction from status_code attribute."""
        error = Exception("Error")
        error.status_code = 429  # type: ignore
        assert _extract_status_code(error) == 429

    def test_response_status_code(self):
        """Test extraction from response.status_code."""
        error = Exception("Error")
        error.response = MagicMock()  # type: ignore
        error.response.status_code = 503
        assert _extract_status_code(error) == 503

    def test_message_429(self):
        """Test extraction from error message."""
        error = Exception("HTTP 429 rate limit")
        assert _extract_status_code(error) == 429

    def test_message_rate_limit(self):
        """Test extraction from rate limit message."""
        error = Exception("rate limit exceeded")
        assert _extract_status_code(error) == 429

    def test_message_500(self):
        """Test extraction from 500 message."""
        error = Exception("HTTP 500 Internal Server Error")
        assert _extract_status_code(error) == 500

    def test_message_502(self):
        """Test extraction from 502 message."""
        error = Exception("HTTP 502 Bad Gateway")
        assert _extract_status_code(error) == 502

    def test_message_503(self):
        """Test extraction from 503 message."""
        error = Exception("HTTP 503 Service Unavailable")
        assert _extract_status_code(error) == 503

    def test_message_504(self):
        """Test extraction from 504 message."""
        error = Exception("HTTP 504 Gateway Timeout")
        assert _extract_status_code(error) == 504

    def test_unknown_error(self):
        """Test extraction returns None for unknown errors."""
        error = Exception("Something went wrong")
        assert _extract_status_code(error) is None


class TestRetryableError:
    """Tests for RetryableError class."""

    def test_basic_creation(self):
        """Test basic error creation."""
        error = RetryableError("Test error")
        assert str(error) == "Test error"
        assert error.status_code is None

    def test_with_status_code(self):
        """Test error with status code."""
        error = RetryableError("Rate limited", status_code=429)
        assert error.status_code == 429


class TestMaxRetriesExceededError:
    """Tests for MaxRetriesExceededError class."""

    def test_basic_creation(self):
        """Test basic error creation."""
        error = MaxRetriesExceededError("Max retries")
        assert str(error) == "Max retries"
        assert error.last_error is None

    def test_with_last_error(self):
        """Test error with last error."""
        last = Exception("Original error")
        error = MaxRetriesExceededError("Max retries", last_error=last)
        assert error.last_error is last


class TestUnityCatalogClient:
    """Tests for UnityCatalogClient."""

    @patch("dbt_unity_lineage.unity_catalog.WorkspaceClient")
    def test_initialization(
        self,
        mock_workspace_client: MagicMock,
        mock_connection: DatabricksConnection,
    ):
        """Test client initialization."""
        client = UnityCatalogClient(mock_connection)
        assert client.connection == mock_connection
        assert client.catalog == "test_catalog"
        mock_workspace_client.assert_called_once()

    @patch("dbt_unity_lineage.unity_catalog.WorkspaceClient")
    def test_catalog_property(
        self,
        mock_workspace_client: MagicMock,
        mock_connection: DatabricksConnection,
    ):
        """Test catalog property."""
        client = UnityCatalogClient(mock_connection)
        assert client.catalog == "test_catalog"

    @patch("dbt_unity_lineage.unity_catalog.WorkspaceClient")
    def test_make_ownership_properties(
        self,
        mock_workspace_client: MagicMock,
        mock_connection: DatabricksConnection,
    ):
        """Test ownership properties creation."""
        client = UnityCatalogClient(mock_connection)
        props = client._make_ownership_properties(
            dbt_project="my_project",
            identifier="sap.orders",
            identifier_type="source",
        )
        assert props["managed_by"] == "dbt-unity-lineage"
        assert props["dbt_project"] == "my_project"
        assert props["dbt_source"] == "sap.orders"
        assert "updated_at" in props

    @patch("dbt_unity_lineage.unity_catalog.WorkspaceClient")
    def test_list_external_metadata_empty(
        self,
        mock_workspace_client: MagicMock,
        mock_connection: DatabricksConnection,
    ):
        """Test listing external metadata with empty response."""
        client = UnityCatalogClient(mock_connection)
        mock_workspace_client.return_value.api_client.do.return_value = {
            "external_metadata": []
        }

        result = client.list_external_metadata()
        assert result == []

    @patch("dbt_unity_lineage.unity_catalog.WorkspaceClient")
    def test_list_external_metadata_filters_by_managed_by(
        self,
        mock_workspace_client: MagicMock,
        mock_connection: DatabricksConnection,
    ):
        """Test that list filters by managed_by property."""
        client = UnityCatalogClient(mock_connection)
        mock_workspace_client.return_value.api_client.do.return_value = {
            "external_metadata": [
                {
                    "name": "managed_source",
                    "system_type": "SAP",
                    "entity_type": "table",
                    "properties": {"managed_by": "dbt-unity-lineage"},
                },
                {
                    "name": "other_source",
                    "system_type": "SAP",
                    "entity_type": "table",
                    "properties": {"managed_by": "other-tool"},
                },
            ]
        }

        result = client.list_external_metadata()
        assert len(result) == 1
        assert result[0].name == "managed_source"

    @patch("dbt_unity_lineage.unity_catalog.WorkspaceClient")
    def test_list_external_metadata_filters_by_project(
        self,
        mock_workspace_client: MagicMock,
        mock_connection: DatabricksConnection,
    ):
        """Test that list filters by dbt_project."""
        client = UnityCatalogClient(mock_connection)
        mock_workspace_client.return_value.api_client.do.return_value = {
            "external_metadata": [
                {
                    "name": "project_a_source",
                    "system_type": "SAP",
                    "entity_type": "table",
                    "properties": {
                        "managed_by": "dbt-unity-lineage",
                        "dbt_project": "project_a",
                    },
                },
                {
                    "name": "project_b_source",
                    "system_type": "SAP",
                    "entity_type": "table",
                    "properties": {
                        "managed_by": "dbt-unity-lineage",
                        "dbt_project": "project_b",
                    },
                },
            ]
        }

        result = client.list_external_metadata(dbt_project="project_a")
        assert len(result) == 1
        assert result[0].name == "project_a_source"

    @patch("dbt_unity_lineage.unity_catalog.WorkspaceClient")
    def test_list_external_metadata_handles_error(
        self,
        mock_workspace_client: MagicMock,
        mock_connection: DatabricksConnection,
    ):
        """Test that list handles non-retryable errors gracefully."""
        client = UnityCatalogClient(mock_connection)
        mock_workspace_client.return_value.api_client.do.side_effect = Exception("Not found")

        result = client.list_external_metadata()
        assert result == []

    @patch("dbt_unity_lineage.unity_catalog.WorkspaceClient")
    def test_create_external_metadata(
        self,
        mock_workspace_client: MagicMock,
        mock_connection: DatabricksConnection,
    ):
        """Test creating external metadata."""
        client = UnityCatalogClient(mock_connection)
        mock_workspace_client.return_value.api_client.do.return_value = {
            "name": "sap_orders",
            "system_type": "SAP",
            "entity_type": "table",
            "properties": {"managed_by": "dbt-unity-lineage"},
        }

        metadata = ExternalMetadata(
            name="sap_orders",
            system_type="SAP",
            entity_type="table",
        )

        result = client.create_external_metadata(
            metadata=metadata,
            dbt_project="test_project",
            identifier="sap.orders",
            identifier_type="source",
        )

        assert result.name == "sap_orders"
        mock_workspace_client.return_value.api_client.do.assert_called()

    @patch("dbt_unity_lineage.unity_catalog.WorkspaceClient")
    def test_update_external_metadata(
        self,
        mock_workspace_client: MagicMock,
        mock_connection: DatabricksConnection,
    ):
        """Test updating external metadata."""
        client = UnityCatalogClient(mock_connection)
        mock_workspace_client.return_value.api_client.do.return_value = {
            "name": "sap_orders",
            "system_type": "SAP",
            "entity_type": "table",
            "properties": {"managed_by": "dbt-unity-lineage"},
        }

        metadata = ExternalMetadata(
            name="sap_orders",
            system_type="SAP",
            entity_type="table",
            properties={"created_at": "2024-01-01T00:00:00Z"},
        )

        result = client.update_external_metadata(
            metadata=metadata,
            dbt_project="test_project",
            identifier="sap.orders",
            identifier_type="source",
        )

        assert result.name == "sap_orders"

    @patch("dbt_unity_lineage.unity_catalog.WorkspaceClient")
    def test_delete_external_metadata(
        self,
        mock_workspace_client: MagicMock,
        mock_connection: DatabricksConnection,
    ):
        """Test deleting external metadata."""
        client = UnityCatalogClient(mock_connection)
        mock_workspace_client.return_value.api_client.do.return_value = {}

        # Should not raise
        client.delete_external_metadata("sap_orders")

        mock_workspace_client.return_value.api_client.do.assert_called_once()
        call_args = mock_workspace_client.return_value.api_client.do.call_args
        assert call_args[0][0] == "DELETE"

    @patch("dbt_unity_lineage.unity_catalog.WorkspaceClient")
    def test_create_lineage_edge_source_to_table(
        self,
        mock_workspace_client: MagicMock,
        mock_connection: DatabricksConnection,
    ):
        """Test creating lineage edge from source to table."""
        client = UnityCatalogClient(mock_connection)
        mock_workspace_client.return_value.api_client.do.return_value = {}

        edge = LineageEdge(
            source_entity="sap_orders",
            target_entity="test_catalog.bronze.orders",
            source_type="external",
            target_type="table",
        )

        client.create_lineage_edge(edge)

        call_args = mock_workspace_client.return_value.api_client.do.call_args
        assert call_args[0][0] == "POST"
        assert "source_external_metadata" in call_args[1]["body"]

    @patch("dbt_unity_lineage.unity_catalog.WorkspaceClient")
    def test_create_lineage_edge_table_to_exposure(
        self,
        mock_workspace_client: MagicMock,
        mock_connection: DatabricksConnection,
    ):
        """Test creating lineage edge from table to exposure."""
        client = UnityCatalogClient(mock_connection)
        mock_workspace_client.return_value.api_client.do.return_value = {}

        edge = LineageEdge(
            source_entity="test_catalog.gold.orders",
            target_entity="powerbi_dashboard",
            source_type="table",
            target_type="external",
        )

        client.create_lineage_edge(edge)

        call_args = mock_workspace_client.return_value.api_client.do.call_args
        assert "source_table" in call_args[1]["body"]
        assert "target_external_metadata" in call_args[1]["body"]

    @patch("dbt_unity_lineage.unity_catalog.WorkspaceClient")
    def test_delete_lineage_edge(
        self,
        mock_workspace_client: MagicMock,
        mock_connection: DatabricksConnection,
    ):
        """Test deleting lineage edge."""
        client = UnityCatalogClient(mock_connection)
        mock_workspace_client.return_value.api_client.do.return_value = {}

        edge = LineageEdge(
            source_entity="sap_orders",
            target_entity="test_catalog.bronze.orders",
            source_type="external",
            target_type="table",
        )

        client.delete_lineage_edge(edge)

        call_args = mock_workspace_client.return_value.api_client.do.call_args
        assert call_args[0][0] == "DELETE"

    @patch("dbt_unity_lineage.unity_catalog.WorkspaceClient")
    def test_list_lineage_edges_for_external(
        self,
        mock_workspace_client: MagicMock,
        mock_connection: DatabricksConnection,
    ):
        """Test listing lineage edges for external entity."""
        client = UnityCatalogClient(mock_connection)
        mock_workspace_client.return_value.api_client.do.return_value = {
            "edges": [
                {
                    "source_external_metadata": "sap_orders",
                    "target_table": "test_catalog.bronze.orders",
                },
            ]
        }

        edges = client.list_lineage_edges("sap_orders", "external")

        assert len(edges) == 1
        assert edges[0].source_entity == "sap_orders"
        assert edges[0].source_type == "external"

    @patch("dbt_unity_lineage.unity_catalog.WorkspaceClient")
    def test_list_lineage_edges_for_table(
        self,
        mock_workspace_client: MagicMock,
        mock_connection: DatabricksConnection,
    ):
        """Test listing lineage edges for table entity."""
        client = UnityCatalogClient(mock_connection)
        mock_workspace_client.return_value.api_client.do.return_value = {
            "edges": [
                {
                    "source_table": "test_catalog.gold.orders",
                    "target_external_metadata": "powerbi_dashboard",
                },
            ]
        }

        edges = client.list_lineage_edges("test_catalog.gold.orders", "table")

        assert len(edges) == 1
        assert edges[0].target_entity == "powerbi_dashboard"
        assert edges[0].target_type == "external"

    @patch("dbt_unity_lineage.unity_catalog.WorkspaceClient")
    def test_list_lineage_edges_handles_error(
        self,
        mock_workspace_client: MagicMock,
        mock_connection: DatabricksConnection,
    ):
        """Test that list edges handles errors gracefully."""
        client = UnityCatalogClient(mock_connection)
        mock_workspace_client.return_value.api_client.do.side_effect = Exception("Not found")

        edges = client.list_lineage_edges("sap_orders", "external")
        assert edges == []


class TestApiCallWithRetry:
    """Tests for API call retry logic."""

    @patch("dbt_unity_lineage.unity_catalog.WorkspaceClient")
    @patch("dbt_unity_lineage.unity_catalog.time.sleep")
    def test_retries_on_429(
        self,
        mock_sleep: MagicMock,
        mock_workspace_client: MagicMock,
        mock_connection: DatabricksConnection,
    ):
        """Test that 429 errors trigger retries."""
        client = UnityCatalogClient(mock_connection, max_retries=2)

        # First two calls fail with 429, third succeeds
        error = Exception("HTTP 429 Rate Limit")
        error.status_code = 429  # type: ignore
        mock_workspace_client.return_value.api_client.do.side_effect = [
            error,
            error,
            {"result": "success"},
        ]

        result = client._api_call_with_retry("GET", "/test")
        assert result == {"result": "success"}
        assert mock_sleep.call_count == 2

    @patch("dbt_unity_lineage.unity_catalog.WorkspaceClient")
    @patch("dbt_unity_lineage.unity_catalog.time.sleep")
    def test_no_retry_on_400(
        self,
        mock_sleep: MagicMock,
        mock_workspace_client: MagicMock,
        mock_connection: DatabricksConnection,
    ):
        """Test that 400 errors don't trigger retries."""
        client = UnityCatalogClient(mock_connection, max_retries=2)

        error = Exception("HTTP 400 Bad Request")
        error.status_code = 400  # type: ignore
        mock_workspace_client.return_value.api_client.do.side_effect = error

        with pytest.raises(Exception) as exc_info:
            client._api_call_with_retry("GET", "/test")

        assert "400" in str(exc_info.value)
        mock_sleep.assert_not_called()

    @patch("dbt_unity_lineage.unity_catalog.WorkspaceClient")
    @patch("dbt_unity_lineage.unity_catalog.time.sleep")
    def test_max_retries_exceeded(
        self,
        mock_sleep: MagicMock,
        mock_workspace_client: MagicMock,
        mock_connection: DatabricksConnection,
    ):
        """Test that max retries raises MaxRetriesExceededError."""
        client = UnityCatalogClient(mock_connection, max_retries=2)

        error = Exception("HTTP 503 Service Unavailable")
        error.status_code = 503  # type: ignore
        mock_workspace_client.return_value.api_client.do.side_effect = error

        with pytest.raises(MaxRetriesExceededError) as exc_info:
            client._api_call_with_retry("GET", "/test")

        assert exc_info.value.last_error is error
        assert mock_sleep.call_count == 2  # Retried twice before giving up
