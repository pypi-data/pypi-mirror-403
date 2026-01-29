"""Pytest fixtures for mock API tests."""

from __future__ import annotations

import json
import multiprocessing
import socket
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, Optional

import pytest
import requests

from dbt_unity_lineage.profiles import DatabricksConnection


def find_free_port() -> int:
    """Find a free port on localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def run_server(port: int) -> None:
    """Run the mock server in a subprocess."""
    import uvicorn

    from tests.mock_api.server import app

    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


@contextmanager
def mock_server_context(port: Optional[int] = None) -> Generator[str, None, None]:
    """Context manager that starts and stops the mock server.

    Yields:
        The base URL of the mock server.
    """
    if port is None:
        port = find_free_port()

    # Start server in subprocess
    process = multiprocessing.Process(target=run_server, args=(port,), daemon=True)
    process.start()

    base_url = f"http://127.0.0.1:{port}"

    # Wait for server to be ready
    max_wait = 10
    start = time.time()
    while time.time() - start < max_wait:
        try:
            response = requests.get(f"{base_url}/health", timeout=1)
            if response.status_code == 200:
                break
        except requests.RequestException:
            pass
        time.sleep(0.1)
    else:
        process.terminate()
        raise RuntimeError(f"Mock server failed to start on port {port}")

    try:
        yield base_url
    finally:
        process.terminate()
        process.join(timeout=5)


@pytest.fixture(scope="session")
def mock_server_url() -> Generator[str, None, None]:
    """Session-scoped fixture that provides the mock server URL.

    The server runs for the entire test session.
    """
    with mock_server_context() as url:
        yield url


@pytest.fixture
def mock_server_reset(mock_server_url: str) -> str:
    """Reset the mock server state before each test.

    Returns the mock server URL after resetting state.
    """
    # Reset Unity Catalog state
    requests.post(f"{mock_server_url}/test/reset")
    # Reset dbt Cloud state
    requests.post(f"{mock_server_url}/test/dbt-cloud/reset")
    return mock_server_url


@pytest.fixture
def mock_connection(mock_server_reset: str) -> DatabricksConnection:
    """Create a DatabricksConnection pointing to the mock server."""
    # Extract host from URL (remove http://)
    host = mock_server_reset.replace("http://", "").replace("https://", "")

    return DatabricksConnection(
        host=host,
        token="mock-token",
        catalog="test_catalog",
        http_path="/sql/test",
    )


@pytest.fixture
def sample_manifest_dict() -> Dict[str, Any]:
    """Return a sample manifest as a dictionary."""
    return {
        "metadata": {
            "project_name": "test_project",
            "dbt_version": "1.7.0",
        },
        "nodes": {
            "model.test_project.stg_orders": {
                "unique_id": "model.test_project.stg_orders",
                "resource_type": "model",
                "name": "stg_orders",
                "database": "test_catalog",
                "schema": "bronze",
                "alias": "stg_orders",
            },
            "model.test_project.fct_orders": {
                "unique_id": "model.test_project.fct_orders",
                "resource_type": "model",
                "name": "fct_orders",
                "database": "test_catalog",
                "schema": "gold",
                "alias": "fct_orders",
            },
        },
        "sources": {
            "source.test_project.postgres.orders": {
                "unique_id": "source.test_project.postgres.orders",
                "resource_type": "source",
                "source_name": "postgres",
                "name": "orders",
                "database": "test_catalog",
                "schema": "bronze",
                "identifier": "orders",
                "source_meta": {
                    "uc_source": "postgres_app",
                },
                "meta": {},
            },
            "source.test_project.sap.materials": {
                "unique_id": "source.test_project.sap.materials",
                "resource_type": "source",
                "source_name": "sap",
                "name": "materials",
                "database": "test_catalog",
                "schema": "bronze",
                "identifier": "materials",
                "source_meta": {
                    "uc_source": "sap_ecc",
                },
                "meta": {},
            },
        },
        "exposures": {
            "exposure.test_project.sales_dashboard": {
                "unique_id": "exposure.test_project.sales_dashboard",
                "resource_type": "exposure",
                "name": "sales_dashboard",
                "type": "dashboard",
                "url": "https://app.powerbi.com/reports/abc123",
                "owner": {"name": "Data Team", "email": "data@example.com"},
                "depends_on": {
                    "nodes": ["model.test_project.fct_orders"],
                },
            },
            "exposure.test_project.analytics_report": {
                "unique_id": "exposure.test_project.analytics_report",
                "resource_type": "exposure",
                "name": "analytics_report",
                "type": "dashboard",
                "url": "https://tableau.example.com/views/report",
                "owner": {"name": "Analytics", "email": "analytics@example.com"},
                "depends_on": {
                    "nodes": ["model.test_project.fct_orders"],
                },
            },
        },
    }


@pytest.fixture
def sample_manifest_path(tmp_path: Path, sample_manifest_dict: Dict[str, Any]) -> Path:
    """Write sample manifest to a temp file and return its path."""
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(sample_manifest_dict))
    return manifest_path


@pytest.fixture
def sample_config_dict() -> Dict[str, Any]:
    """Return a sample config as a dictionary."""
    return {
        "source_systems": {
            "postgres_app": {
                "system_type": "postgresql",
                "entity_type": "table",
            },
            "sap_ecc": {
                "system_type": "sap",
                "entity_type": "table",
            },
        },
        "settings": {
            "batch_size": 50,
        },
    }


@pytest.fixture
def sample_config_path(tmp_path: Path, sample_config_dict: Dict[str, Any]) -> Path:
    """Write sample config to a temp file and return its path."""
    import yaml

    config_path = tmp_path / "dbt_unity_lineage.yml"
    config_path.write_text(yaml.dump(sample_config_dict))
    return config_path
