"""System type mapping and normalization for Unity Catalog."""

from __future__ import annotations

import re
from enum import Enum
from typing import Optional


class UCSystemType(str, Enum):
    """Valid Unity Catalog system types."""

    CUSTOM = "CUSTOM"
    AMAZON_REDSHIFT = "AMAZON_REDSHIFT"
    AZURE_SYNAPSE = "AZURE_SYNAPSE"
    GOOGLE_BIGQUERY = "GOOGLE_BIGQUERY"
    KAFKA = "KAFKA"
    LOOKER = "LOOKER"
    MICROSOFT_FABRIC = "MICROSOFT_FABRIC"
    MICROSOFT_SQL_SERVER = "MICROSOFT_SQL_SERVER"
    MONGODB = "MONGODB"
    MYSQL = "MYSQL"
    ORACLE = "ORACLE"
    POSTGRESQL = "POSTGRESQL"
    POWER_BI = "POWER_BI"
    SALESFORCE = "SALESFORCE"
    SAP = "SAP"
    SERVICENOW = "SERVICENOW"
    SNOWFLAKE = "SNOWFLAKE"
    TABLEAU = "TABLEAU"
    TERADATA = "TERADATA"
    WORKDAY = "WORKDAY"
    DATABRICKS = "DATABRICKS"


# Alias table for normalizing system type inputs
SYSTEM_TYPE_ALIASES: dict[str, UCSystemType] = {
    # SAP variants
    "sap": UCSystemType.SAP,
    "sap_ecc": UCSystemType.SAP,
    "sap_hana": UCSystemType.SAP,
    "sap_s4hana": UCSystemType.SAP,
    # Salesforce variants
    "salesforce": UCSystemType.SALESFORCE,
    "sfdc": UCSystemType.SALESFORCE,
    # PostgreSQL variants
    "postgresql": UCSystemType.POSTGRESQL,
    "postgres": UCSystemType.POSTGRESQL,
    "pg": UCSystemType.POSTGRESQL,
    # SQL Server variants
    "sql_server": UCSystemType.MICROSOFT_SQL_SERVER,
    "sqlserver": UCSystemType.MICROSOFT_SQL_SERVER,
    "mssql": UCSystemType.MICROSOFT_SQL_SERVER,
    "microsoft_sql_server": UCSystemType.MICROSOFT_SQL_SERVER,
    # BigQuery variants
    "bigquery": UCSystemType.GOOGLE_BIGQUERY,
    "bq": UCSystemType.GOOGLE_BIGQUERY,
    "google_bigquery": UCSystemType.GOOGLE_BIGQUERY,
    # Redshift variants
    "redshift": UCSystemType.AMAZON_REDSHIFT,
    "amazon_redshift": UCSystemType.AMAZON_REDSHIFT,
    # Synapse variants
    "synapse": UCSystemType.AZURE_SYNAPSE,
    "azure_synapse": UCSystemType.AZURE_SYNAPSE,
    # Fabric variants
    "fabric": UCSystemType.MICROSOFT_FABRIC,
    "microsoft_fabric": UCSystemType.MICROSOFT_FABRIC,
    # MongoDB variants
    "mongodb": UCSystemType.MONGODB,
    "mongo": UCSystemType.MONGODB,
    # Power BI variants
    "powerbi": UCSystemType.POWER_BI,
    "power_bi": UCSystemType.POWER_BI,
    # MySQL
    "mysql": UCSystemType.MYSQL,
    # Oracle
    "oracle": UCSystemType.ORACLE,
    # Kafka
    "kafka": UCSystemType.KAFKA,
    # Looker
    "looker": UCSystemType.LOOKER,
    # Tableau
    "tableau": UCSystemType.TABLEAU,
    # Snowflake
    "snowflake": UCSystemType.SNOWFLAKE,
    # Workday
    "workday": UCSystemType.WORKDAY,
    # ServiceNow
    "servicenow": UCSystemType.SERVICENOW,
    # Teradata
    "teradata": UCSystemType.TERADATA,
    # Databricks
    "databricks": UCSystemType.DATABRICKS,
    # Custom
    "custom": UCSystemType.CUSTOM,
}


# URL patterns for automatic system type inference from exposure URLs
URL_PATTERNS: list[tuple[re.Pattern[str], UCSystemType]] = [
    (re.compile(r"powerbi\.com", re.IGNORECASE), UCSystemType.POWER_BI),
    (re.compile(r"app\.powerbi\.com", re.IGNORECASE), UCSystemType.POWER_BI),
    (re.compile(r"tableau\.com", re.IGNORECASE), UCSystemType.TABLEAU),
    (re.compile(r"looker\.com", re.IGNORECASE), UCSystemType.LOOKER),
    (re.compile(r"lookerstudio\.google\.com", re.IGNORECASE), UCSystemType.LOOKER),
    (re.compile(r"cloud\.looker\.com", re.IGNORECASE), UCSystemType.LOOKER),
    (re.compile(r"salesforce\.com", re.IGNORECASE), UCSystemType.SALESFORCE),
    (re.compile(r"lightning\.force\.com", re.IGNORECASE), UCSystemType.SALESFORCE),
    (re.compile(r"servicenow\.com", re.IGNORECASE), UCSystemType.SERVICENOW),
    (re.compile(r"workday\.com", re.IGNORECASE), UCSystemType.WORKDAY),
    (re.compile(r"snowflake\.com", re.IGNORECASE), UCSystemType.SNOWFLAKE),
    (re.compile(r"databricks\.com", re.IGNORECASE), UCSystemType.DATABRICKS),
]


# dbt exposure type to UC entity type mapping
EXPOSURE_TYPE_TO_ENTITY: dict[str, str] = {
    "dashboard": "dashboard",
    "notebook": "notebook",
    "analysis": "report",
    "ml": "model",
    "application": "application",
}


def normalize_system_type(input_type: str) -> UCSystemType:
    """Normalize a system type input to a valid UC system type.

    Args:
        input_type: The input system type string (case-insensitive).

    Returns:
        The normalized UCSystemType. Returns CUSTOM if not recognized.
    """
    normalized = input_type.lower().strip()

    # Check aliases first
    if normalized in SYSTEM_TYPE_ALIASES:
        return SYSTEM_TYPE_ALIASES[normalized]

    # Check if it's already a valid UC type (case-insensitive)
    for uc_type in UCSystemType:
        if normalized == uc_type.value.lower():
            return uc_type

    # Unknown type defaults to CUSTOM
    return UCSystemType.CUSTOM


def infer_system_type_from_url(url: Optional[str]) -> UCSystemType:
    """Infer the system type from a URL pattern.

    Args:
        url: The URL to analyze (typically from an exposure).

    Returns:
        The inferred UCSystemType. Returns CUSTOM if no pattern matches.
    """
    if not url:
        return UCSystemType.CUSTOM

    for pattern, system_type in URL_PATTERNS:
        if pattern.search(url):
            return system_type

    return UCSystemType.CUSTOM


def get_entity_type_for_exposure(exposure_type: str) -> str:
    """Get the UC entity type for a dbt exposure type.

    Args:
        exposure_type: The dbt exposure type (dashboard, notebook, etc.).

    Returns:
        The corresponding UC entity type.
    """
    return EXPOSURE_TYPE_TO_ENTITY.get(exposure_type.lower(), "application")
