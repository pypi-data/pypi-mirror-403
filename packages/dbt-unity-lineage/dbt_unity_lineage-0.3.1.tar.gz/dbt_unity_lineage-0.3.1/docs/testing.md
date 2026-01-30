# Testing Guide

This document describes the testing strategy and practices for dbt-unity-lineage.

## Test Structure

```
tests/
├── conftest.py           # Shared fixtures
├── fixtures/             # Test data files
│   ├── profiles.yml      # Sample dbt profiles
│   └── unity_lineage.yml # Sample configuration
├── test_cli.py           # CLI command tests
├── test_config.py        # Configuration parsing tests
├── test_errors.py        # Error handling tests
├── test_mapping.py       # System type mapping tests
├── test_profiles.py      # Profile parsing tests
├── test_scanner.py       # YAML scanning tests
└── test_unity_catalog.py # Unity Catalog client tests
```

## Running Tests

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_cli.py

# Run tests matching a pattern
pytest tests/ -k "test_scan"

# Run with coverage
pytest tests/ --cov=src/dbt_unity_lineage --cov-report=html
```

## Test Categories

### Unit Tests (Default)

Unit tests run without external dependencies. They use mocked Databricks SDK calls.

```bash
pytest tests/ -m "not integration"
```

### Integration Tests

Integration tests require a real Databricks connection. They are marked with `@pytest.mark.integration`.

```bash
# Requires env vars: DATABRICKS_HOST, DATABRICKS_TOKEN
pytest tests/ -m "integration"
```

## Mocking Strategy

### Databricks SDK Mocking

We mock the Databricks SDK at the client level using `unittest.mock`:

```python
from unittest.mock import MagicMock, patch

def test_list_external_metadata():
    """Test listing external metadata from Unity Catalog."""
    # Create mock workspace client
    mock_client = MagicMock()
    mock_client.api_client.do.return_value = {
        "external_metadata": [
            {"name": "source1", "properties": {"managed_by": "dbt-unity-lineage"}},
            {"name": "source2", "properties": {"managed_by": "other-tool"}},
        ]
    }

    # Inject mock into UnityCatalogClient
    with patch("databricks.sdk.WorkspaceClient", return_value=mock_client):
        client = UnityCatalogClient(
            host="test.databricks.com",
            token="test-token",
            catalog="test_catalog",
            project_name="test_project",
        )

        result = client.list_external_metadata("test_project")

        # Should filter to only our managed objects
        assert len(result) == 1
        assert result[0].name == "source1"
```

### CLI Testing

CLI tests use Click's `CliRunner` with isolated filesystems:

```python
from click.testing import CliRunner
from dbt_unity_lineage.cli import main

def test_scan_command():
    runner = CliRunner()

    with runner.isolated_filesystem():
        # Create test config
        Path("models/lineage").mkdir(parents=True)
        Path("models/lineage/unity_lineage.yml").write_text("""
version: 1
project:
  name: test
configuration:
  layers:
    bronze:
      sources:
        folders:
          - models/bronze
""")

        # Create test source file
        Path("models/bronze").mkdir(parents=True)
        Path("models/bronze/_sources.yml").write_text("""
sources:
  - name: erp
    tables:
      - name: orders
""")

        result = runner.invoke(main, ["scan"])

        assert result.exit_code == 0
        assert "orders" in result.output
```

## Writing New Tests

### Test Naming Convention

```python
class TestFeatureName:
    """Tests for feature name."""

    def test_basic_functionality(self):
        """Test basic happy path."""
        pass

    def test_edge_case_description(self):
        """Test specific edge case."""
        pass

    def test_error_handling(self):
        """Test error scenarios."""
        pass
```

### Using Fixtures

Define reusable fixtures in `conftest.py`:

```python
import pytest

@pytest.fixture
def sample_config():
    """Return a minimal valid configuration."""
    return Config(
        version=1,
        project=ProjectConfig(name="test_project"),
        configuration=Configuration(
            layers={"bronze": LayerConfig(sources=LayerSources(folders=["bronze"]))}
        ),
    )

@pytest.fixture
def mock_uc_client():
    """Return a mocked Unity Catalog client."""
    with patch("dbt_unity_lineage.unity_catalog.WorkspaceClient"):
        yield UnityCatalogClient(
            host="test.com",
            token="token",
            catalog="catalog",
            project_name="project",
        )
```

## Future: FastAPI Mock Server

For more realistic integration testing, we plan to implement a FastAPI-based mock server that simulates the Databricks Unity Catalog API:

```python
# tests/mock_server.py (planned)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# In-memory storage for test state
external_metadata: dict[str, dict] = {}

@app.get("/api/2.1/unity-catalog/external-metadata")
def list_external_metadata():
    return {"external_metadata": list(external_metadata.values())}

@app.post("/api/2.1/unity-catalog/external-metadata")
def create_external_metadata(data: dict):
    external_metadata[data["name"]] = data
    return data

@app.delete("/api/2.1/unity-catalog/external-metadata/{name}")
def delete_external_metadata(name: str):
    if name not in external_metadata:
        raise HTTPException(status_code=404)
    del external_metadata[name]
    return {"status": "deleted"}
```

This would enable:
- Full round-trip testing without Databricks connection
- Controlled error injection
- Performance testing
- CI pipeline testing without secrets

## CI Pipeline

Tests run automatically in GitHub Actions:

| Event | Tests Run |
|-------|-----------|
| Push to main | Unit tests only |
| Pull request | Unit tests + Integration tests (if secrets available) |

See `.github/workflows/ci.yml` for configuration.
