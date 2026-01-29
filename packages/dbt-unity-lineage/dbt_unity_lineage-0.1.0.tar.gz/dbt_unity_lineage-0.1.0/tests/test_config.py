"""Tests for config module."""

from __future__ import annotations

from pathlib import Path

import pytest

from dbt_unity_lineage.config import Config, SourceSystemConfig, load_config
from dbt_unity_lineage.mapping import UCSystemType


class TestSourceSystemConfig:
    """Tests for SourceSystemConfig."""

    def test_system_type_normalization(self) -> None:
        """Test that system type is normalized on creation."""
        config = SourceSystemConfig(system_type="postgres")
        assert config.system_type == "POSTGRESQL"
        assert config.normalized_system_type == UCSystemType.POSTGRESQL

    def test_default_entity_type(self) -> None:
        """Test that entity_type defaults to 'table'."""
        config = SourceSystemConfig(system_type="SAP")
        assert config.entity_type == "table"

    def test_optional_fields(self) -> None:
        """Test that optional fields are None by default."""
        config = SourceSystemConfig(system_type="SAP")
        assert config.description is None
        assert config.url is None
        assert config.owner is None
        assert config.properties == {}

    def test_full_config(self) -> None:
        """Test config with all fields populated."""
        config = SourceSystemConfig(
            system_type="SAP",
            entity_type="table",
            description="SAP ECC Production",
            url="https://sap.example.com",
            owner="erp-team@example.com",
            properties={"environment": "production"},
        )
        assert config.system_type == "SAP"
        assert config.entity_type == "table"
        assert config.description == "SAP ECC Production"
        assert config.url == "https://sap.example.com"
        assert config.owner == "erp-team@example.com"
        assert config.properties == {"environment": "production"}


class TestConfig:
    """Tests for Config model."""

    def test_default_config(self) -> None:
        """Test default empty config."""
        config = Config()
        assert config.version == 1
        assert config.source_systems == {}
        assert config.source_paths == []
        assert config.settings.batch_size == 50
        assert config.settings.strict is False

    def test_invalid_version(self) -> None:
        """Test that invalid version raises error."""
        with pytest.raises(ValueError, match="Unsupported config version"):
            Config(version=2)


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_sample_config(self, sample_config_path: Path) -> None:
        """Test loading the sample config file."""
        config = load_config(sample_config_path)

        assert config.version == 1
        assert len(config.source_systems) == 3

        # Check SAP config
        sap = config.source_systems["sap_ecc"]
        assert sap.system_type == "SAP"
        assert sap.entity_type == "table"
        assert sap.description == "SAP ECC 6.0 Production"
        assert sap.url == "https://sap.example.com"
        assert sap.owner == "erp-team@example.com"
        assert sap.properties["environment"] == "production"

        # Check Salesforce config
        sf = config.source_systems["salesforce_prod"]
        assert sf.system_type == "SALESFORCE"
        assert sf.description == "Salesforce Sales Cloud Production"

        # Check PostgreSQL config (normalized from 'postgres')
        pg = config.source_systems["postgres_app"]
        assert pg.system_type == "POSTGRESQL"

        # Check source paths
        assert config.source_paths == ["bronze_erp", "bronze_crm"]

        # Check settings
        assert config.settings.batch_size == 50
        assert config.settings.strict is False

    def test_load_nonexistent_file(self, tmp_path: Path) -> None:
        """Test that loading nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_config(tmp_path / "nonexistent.yml")

    def test_load_empty_file(self, tmp_path: Path) -> None:
        """Test loading an empty config file."""
        config_path = tmp_path / "empty.yml"
        config_path.write_text("")

        config = load_config(config_path)
        assert config.version == 1
        assert config.source_systems == {}

    def test_load_minimal_config(self, tmp_path: Path) -> None:
        """Test loading a minimal config file."""
        config_path = tmp_path / "minimal.yml"
        config_path.write_text(
            """
version: 1
source_systems:
  my_source:
    system_type: SAP
"""
        )

        config = load_config(config_path)
        assert len(config.source_systems) == 1
        assert config.source_systems["my_source"].system_type == "SAP"
