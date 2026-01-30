"""Pytest configuration and shared fixtures."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from dbt_unity_lineage.config import Config, load_config
from dbt_unity_lineage.profiles import DatabricksConnection
from dbt_unity_lineage.unity_catalog import UnityCatalogClient

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the fixtures directory path."""
    return FIXTURES_DIR


@pytest.fixture
def sample_config_path(fixtures_dir: Path) -> Path:
    """Return path to sample config file."""
    return fixtures_dir / "unity_lineage.yml"


@pytest.fixture
def sample_profiles_path(fixtures_dir: Path) -> Path:
    """Return path to sample profiles file."""
    return fixtures_dir / "profiles.yml"


@pytest.fixture
def sample_config(sample_config_path: Path) -> Config:
    """Load and return sample config."""
    return load_config(sample_config_path)


@pytest.fixture
def mock_connection() -> DatabricksConnection:
    """Return a mock Databricks connection."""
    return DatabricksConnection(
        host="dbc-abc123.cloud.databricks.com",
        token="test-token",
        catalog="main",
        http_path="/sql/1.0/warehouses/xyz",
    )


@pytest.fixture
def mock_client(mock_connection: DatabricksConnection) -> MagicMock:
    """Return a mock Unity Catalog client."""
    client = MagicMock(spec=UnityCatalogClient)
    client.connection = mock_connection
    client.catalog = mock_connection.catalog
    client.list_external_metadata.return_value = []
    return client
