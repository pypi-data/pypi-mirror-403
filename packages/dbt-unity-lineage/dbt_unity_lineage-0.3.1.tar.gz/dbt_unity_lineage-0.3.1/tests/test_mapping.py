"""Tests for mapping module."""

from __future__ import annotations

import pytest

from dbt_unity_lineage.mapping import (
    UCSystemType,
    get_entity_type_for_exposure,
    infer_system_type_from_url,
    normalize_system_type,
)


class TestNormalizeSystemType:
    """Tests for normalize_system_type function."""

    @pytest.mark.parametrize(
        "input_type,expected",
        [
            # SAP variants
            ("sap", UCSystemType.SAP),
            ("SAP", UCSystemType.SAP),
            ("sap_ecc", UCSystemType.SAP),
            ("sap_hana", UCSystemType.SAP),
            ("sap_s4hana", UCSystemType.SAP),
            # Salesforce variants
            ("salesforce", UCSystemType.SALESFORCE),
            ("SALESFORCE", UCSystemType.SALESFORCE),
            ("sfdc", UCSystemType.SALESFORCE),
            # PostgreSQL variants
            ("postgresql", UCSystemType.POSTGRESQL),
            ("postgres", UCSystemType.POSTGRESQL),
            ("pg", UCSystemType.POSTGRESQL),
            # SQL Server variants
            ("sql_server", UCSystemType.MICROSOFT_SQL_SERVER),
            ("sqlserver", UCSystemType.MICROSOFT_SQL_SERVER),
            ("mssql", UCSystemType.MICROSOFT_SQL_SERVER),
            # BigQuery variants
            ("bigquery", UCSystemType.GOOGLE_BIGQUERY),
            ("bq", UCSystemType.GOOGLE_BIGQUERY),
            # Power BI variants
            ("powerbi", UCSystemType.POWER_BI),
            ("power_bi", UCSystemType.POWER_BI),
            # Other systems
            ("mysql", UCSystemType.MYSQL),
            ("oracle", UCSystemType.ORACLE),
            ("kafka", UCSystemType.KAFKA),
            ("snowflake", UCSystemType.SNOWFLAKE),
            ("workday", UCSystemType.WORKDAY),
            # Unknown -> CUSTOM
            ("unknown_system", UCSystemType.CUSTOM),
            ("random", UCSystemType.CUSTOM),
        ],
    )
    def test_normalize_system_type(self, input_type: str, expected: UCSystemType) -> None:
        """Test system type normalization."""
        assert normalize_system_type(input_type) == expected

    def test_normalize_system_type_with_whitespace(self) -> None:
        """Test that whitespace is trimmed."""
        assert normalize_system_type("  sap  ") == UCSystemType.SAP

    def test_normalize_system_type_case_insensitive(self) -> None:
        """Test case insensitivity."""
        assert normalize_system_type("POSTGRESQL") == UCSystemType.POSTGRESQL
        assert normalize_system_type("PostgreSQL") == UCSystemType.POSTGRESQL


class TestInferSystemTypeFromUrl:
    """Tests for infer_system_type_from_url function."""

    @pytest.mark.parametrize(
        "url,expected",
        [
            # Power BI
            ("https://app.powerbi.com/groups/abc/reports/xyz", UCSystemType.POWER_BI),
            ("https://powerbi.com/dashboard", UCSystemType.POWER_BI),
            # Tableau
            ("https://public.tableau.com/views/sales", UCSystemType.TABLEAU),
            ("https://online.tableau.com/dashboard", UCSystemType.TABLEAU),
            # Looker
            ("https://looker.com/dashboard", UCSystemType.LOOKER),
            ("https://lookerstudio.google.com/report", UCSystemType.LOOKER),
            ("https://cloud.looker.com/dashboards/123", UCSystemType.LOOKER),
            # Salesforce
            ("https://example.salesforce.com/report", UCSystemType.SALESFORCE),
            ("https://example.lightning.force.com/report", UCSystemType.SALESFORCE),
            # ServiceNow
            ("https://example.servicenow.com/dashboard", UCSystemType.SERVICENOW),
            # Workday
            ("https://wd5.workday.com/report", UCSystemType.WORKDAY),
            # Snowflake
            ("https://app.snowflake.com/dashboard", UCSystemType.SNOWFLAKE),
            # Databricks
            ("https://dbc-123.cloud.databricks.com/sql/dashboards/abc", UCSystemType.DATABRICKS),
            # Unknown
            ("https://custom-app.example.com", UCSystemType.CUSTOM),
            ("https://internal.corp.net/dashboard", UCSystemType.CUSTOM),
        ],
    )
    def test_infer_system_type_from_url(self, url: str, expected: UCSystemType) -> None:
        """Test URL pattern inference."""
        assert infer_system_type_from_url(url) == expected

    def test_infer_system_type_from_none_url(self) -> None:
        """Test that None URL returns CUSTOM."""
        assert infer_system_type_from_url(None) == UCSystemType.CUSTOM

    def test_infer_system_type_from_empty_url(self) -> None:
        """Test that empty URL returns CUSTOM."""
        assert infer_system_type_from_url("") == UCSystemType.CUSTOM


class TestGetEntityTypeForExposure:
    """Tests for get_entity_type_for_exposure function."""

    @pytest.mark.parametrize(
        "exposure_type,expected",
        [
            ("dashboard", "dashboard"),
            ("Dashboard", "dashboard"),
            ("notebook", "notebook"),
            ("analysis", "report"),
            ("ml", "model"),
            ("application", "application"),
            ("unknown", "application"),  # Default
        ],
    )
    def test_get_entity_type_for_exposure(self, exposure_type: str, expected: str) -> None:
        """Test exposure type to entity type mapping."""
        assert get_entity_type_for_exposure(exposure_type) == expected
