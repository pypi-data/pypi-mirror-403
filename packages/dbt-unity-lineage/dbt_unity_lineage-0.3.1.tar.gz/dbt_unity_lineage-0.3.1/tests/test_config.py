"""Tests for config module (V2 schema)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from dbt_unity_lineage.config import (
    Config,
    Configuration,
    LayerConfig,
    LayerExposures,
    LayerSources,
    ProjectConfig,
    SourceSystemConfig,
    ValidationConfig,
    expand_env_vars,
    find_config_file,
    load_config,
)


class TestSourceSystemConfig:
    """Tests for SourceSystemConfig."""

    def test_system_type_normalization(self) -> None:
        """Test that system type is normalized on creation."""
        config = SourceSystemConfig(system_type="postgres")
        assert config.system_type == "POSTGRESQL"

    def test_optional_fields(self) -> None:
        """Test that optional fields have correct defaults."""
        config = SourceSystemConfig(system_type="SAP")
        assert config.description is None
        assert config.url is None
        assert config.owner is None
        assert config.meta == {}
        assert config.table_lineage is False
        assert config.meta_columns == []

    def test_full_config(self) -> None:
        """Test config with all fields populated."""
        config = SourceSystemConfig(
            system_type="SAP",
            description="SAP ECC Production",
            url="https://sap.example.com",
            owner="erp-team@example.com",
            meta={"environment": "production"},
            table_lineage=True,
            meta_columns=["_loaded_at", "_batch_id"],
        )
        assert config.system_type == "SAP"
        assert config.description == "SAP ECC Production"
        assert config.url == "https://sap.example.com"
        assert config.owner == "erp-team@example.com"
        assert config.meta == {"environment": "production"}
        assert config.table_lineage is True
        assert config.meta_columns == ["_loaded_at", "_batch_id"]


class TestValidationConfig:
    """Tests for ValidationConfig."""

    def test_defaults(self) -> None:
        """Test default values."""
        config = ValidationConfig()
        assert config.require_owner is False
        assert config.require_description is False
        assert config.require_source_system is False

    def test_all_enabled(self) -> None:
        """Test with all validations enabled."""
        config = ValidationConfig(
            require_owner=True,
            require_description=True,
            require_source_system=True,
        )
        assert config.require_owner is True
        assert config.require_description is True
        assert config.require_source_system is True


class TestLayerConfig:
    """Tests for LayerConfig."""

    def test_sources_only(self) -> None:
        """Test layer with only sources."""
        layer = LayerConfig(
            sources=LayerSources(folders=["bronze/erp", "bronze/crm"])
        )
        assert layer.source_folders == ["bronze/erp", "bronze/crm"]
        assert layer.exposure_folders == []

    def test_exposures_only(self) -> None:
        """Test layer with only exposures."""
        layer = LayerConfig(
            exposures=LayerExposures(folders=["gold/dashboards"])
        )
        assert layer.source_folders == []
        assert layer.exposure_folders == ["gold/dashboards"]

    def test_both_sources_and_exposures(self) -> None:
        """Test layer with both sources and exposures."""
        layer = LayerConfig(
            sources=LayerSources(folders=["silver/shared"]),
            exposures=LayerExposures(folders=["silver/reports"]),
        )
        assert layer.source_folders == ["silver/shared"]
        assert layer.exposure_folders == ["silver/reports"]

    def test_requires_at_least_one(self) -> None:
        """Test that layer must have at least one of sources or exposures."""
        with pytest.raises(ValueError, match="at least one of 'sources' or 'exposures'"):
            LayerConfig()


class TestConfiguration:
    """Tests for Configuration."""

    def test_requires_layers(self) -> None:
        """Test that at least one layer is required."""
        with pytest.raises(ValueError, match="At least one layer"):
            Configuration(layers={})

    def test_with_layers(self) -> None:
        """Test configuration with layers."""
        config = Configuration(
            layers={
                "bronze": LayerConfig(
                    sources=LayerSources(folders=["bronze/erp"])
                )
            }
        )
        assert "bronze" in config.layers
        assert config.layers["bronze"].source_folders == ["bronze/erp"]


class TestConfig:
    """Tests for Config model."""

    def test_minimal_config(self) -> None:
        """Test minimal valid config."""
        config = Config(
            project=ProjectConfig(name="test_project"),
            configuration=Configuration(
                layers={
                    "bronze": LayerConfig(
                        sources=LayerSources(folders=["bronze/src"])
                    )
                }
            ),
        )
        assert config.version == 1
        assert config.project_name == "test_project"
        assert config.source_systems == {}
        assert config.get_all_source_folders() == ["bronze/src"]
        assert config.get_all_exposure_folders() == []

    def test_invalid_version(self) -> None:
        """Test that invalid version raises error."""
        with pytest.raises(ValueError, match="Unsupported config version"):
            Config(
                version=2,
                project=ProjectConfig(name="test"),
                configuration=Configuration(
                    layers={"x": LayerConfig(sources=LayerSources(folders=["x"]))}
                ),
            )

    def test_full_config(self) -> None:
        """Test full config with all options."""
        config = Config(
            project=ProjectConfig(name="enterprise_analytics"),
            configuration=Configuration(
                validation=ValidationConfig(
                    require_owner=True,
                    require_source_system=True,
                ),
                layers={
                    "bronze": LayerConfig(
                        sources=LayerSources(folders=["bronze/erp", "bronze/crm"])
                    ),
                    "gold": LayerConfig(
                        exposures=LayerExposures(folders=["gold/dashboards"])
                    ),
                },
            ),
            source_systems={
                "sap": SourceSystemConfig(
                    system_type="SAP",
                    description="SAP ECC",
                    owner="erp@example.com",
                ),
            },
        )

        assert config.project_name == "enterprise_analytics"
        assert config.configuration.validation.require_owner is True
        assert config.get_all_source_folders() == ["bronze/erp", "bronze/crm"]
        assert config.get_all_exposure_folders() == ["gold/dashboards"]
        assert "sap" in config.source_systems
        assert config.source_systems["sap"].system_type == "SAP"

    def test_get_folders_for_layer(self) -> None:
        """Test getting folders for specific layer."""
        config = Config(
            project=ProjectConfig(name="test"),
            configuration=Configuration(
                layers={
                    "bronze": LayerConfig(
                        sources=LayerSources(folders=["bronze/a", "bronze/b"])
                    ),
                    "silver": LayerConfig(
                        sources=LayerSources(folders=["silver/x"])
                    ),
                }
            ),
        )

        assert config.get_source_folders_for_layer("bronze") == ["bronze/a", "bronze/b"]
        assert config.get_source_folders_for_layer("silver") == ["silver/x"]
        assert config.get_source_folders_for_layer("gold") == []


class TestEnvVarExpansion:
    """Tests for environment variable expansion."""

    def test_expand_simple_var(self) -> None:
        """Test expanding simple env var."""
        os.environ["TEST_VAR"] = "hello"
        try:
            result = expand_env_vars("${TEST_VAR}")
            assert result == "hello"
        finally:
            del os.environ["TEST_VAR"]

    def test_expand_with_default(self) -> None:
        """Test expanding env var with default value."""
        # Ensure var is not set
        os.environ.pop("UNSET_VAR", None)
        result = expand_env_vars("${UNSET_VAR:-default_value}")
        assert result == "default_value"

    def test_expand_boolean_true(self) -> None:
        """Test that 'true' string is converted to boolean."""
        os.environ["BOOL_VAR"] = "true"
        try:
            result = expand_env_vars("${BOOL_VAR}")
            assert result is True
        finally:
            del os.environ["BOOL_VAR"]

    def test_expand_boolean_false(self) -> None:
        """Test that 'false' string is converted to boolean."""
        os.environ["BOOL_VAR"] = "false"
        try:
            result = expand_env_vars("${BOOL_VAR}")
            assert result is False
        finally:
            del os.environ["BOOL_VAR"]

    def test_expand_default_boolean(self) -> None:
        """Test default boolean expansion."""
        os.environ.pop("UNSET_BOOL", None)
        result = expand_env_vars("${UNSET_BOOL:-false}")
        assert result is False

    def test_expand_nested_dict(self) -> None:
        """Test expanding env vars in nested dict."""
        os.environ["NESTED_VAR"] = "nested_value"
        try:
            data = {"level1": {"level2": "${NESTED_VAR}"}}
            result = expand_env_vars(data)
            assert result["level1"]["level2"] == "nested_value"
        finally:
            del os.environ["NESTED_VAR"]

    def test_expand_list(self) -> None:
        """Test expanding env vars in list."""
        os.environ["LIST_VAR"] = "item"
        try:
            data = ["${LIST_VAR}", "static"]
            result = expand_env_vars(data)
            assert result == ["item", "static"]
        finally:
            del os.environ["LIST_VAR"]


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_nonexistent_file(self, tmp_path: Path) -> None:
        """Test that loading nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_config(tmp_path / "nonexistent.yml")

    def test_load_minimal_config(self, tmp_path: Path) -> None:
        """Test loading a minimal config file."""
        config_path = tmp_path / "minimal.yml"
        config_path.write_text(
            """
version: 1
project:
  name: test_project
configuration:
  layers:
    bronze:
      sources:
        folders:
          - bronze/src
"""
        )

        config = load_config(config_path)
        assert config.project_name == "test_project"
        assert config.get_all_source_folders() == ["bronze/src"]

    def test_load_full_config(self, tmp_path: Path) -> None:
        """Test loading a full config file."""
        config_path = tmp_path / "full.yml"
        config_path.write_text(
            """
version: 1
project:
  name: enterprise_analytics
configuration:
  validation:
    require_owner: true
    require_source_system: true
  layers:
    bronze:
      sources:
        folders:
          - bronze/erp
          - bronze/crm
    gold:
      exposures:
        folders:
          - gold/dashboards
source_systems:
  sap_ecc:
    system_type: SAP
    description: SAP ECC Production
    owner: erp@example.com
    table_lineage: true
    meta_columns:
      - _loaded_at
      - _batch_id
    meta:
      environment: production
"""
        )

        config = load_config(config_path)
        assert config.project_name == "enterprise_analytics"
        assert config.configuration.validation.require_owner is True
        assert config.configuration.validation.require_source_system is True
        assert config.get_all_source_folders() == ["bronze/erp", "bronze/crm"]
        assert config.get_all_exposure_folders() == ["gold/dashboards"]

        sap = config.source_systems["sap_ecc"]
        assert sap.system_type == "SAP"
        assert sap.description == "SAP ECC Production"
        assert sap.owner == "erp@example.com"
        assert sap.table_lineage is True
        assert sap.meta_columns == ["_loaded_at", "_batch_id"]
        assert sap.meta["environment"] == "production"

    def test_load_with_env_vars(self, tmp_path: Path) -> None:
        """Test loading config with environment variable expansion."""
        config_path = tmp_path / "env.yml"
        config_path.write_text(
            """
version: 1
project:
  name: test
configuration:
  validation:
    require_owner: ${REQUIRE_OWNER:-false}
  layers:
    bronze:
      sources:
        folders:
          - bronze/src
"""
        )

        # Test with env var not set (uses default)
        os.environ.pop("REQUIRE_OWNER", None)
        config = load_config(config_path)
        assert config.configuration.validation.require_owner is False

        # Test with env var set
        os.environ["REQUIRE_OWNER"] = "true"
        try:
            config = load_config(config_path)
            assert config.configuration.validation.require_owner is True
        finally:
            del os.environ["REQUIRE_OWNER"]


class TestFindConfigFile:
    """Tests for find_config_file function."""

    def test_find_in_models_lineage(self, tmp_path: Path) -> None:
        """Test finding config in models/lineage/."""
        config_dir = tmp_path / "models" / "lineage"
        config_dir.mkdir(parents=True)
        config_path = config_dir / "unity_lineage.yml"
        config_path.write_text("version: 1")

        found = find_config_file(tmp_path)
        assert found == config_path

    def test_find_in_root(self, tmp_path: Path) -> None:
        """Test finding config in project root."""
        config_path = tmp_path / "unity_lineage.yml"
        config_path.write_text("version: 1")

        found = find_config_file(tmp_path)
        assert found == config_path

    def test_models_lineage_takes_precedence(self, tmp_path: Path) -> None:
        """Test that models/lineage/ takes precedence over root."""
        # Create both files
        root_config = tmp_path / "unity_lineage.yml"
        root_config.write_text("version: 1")

        config_dir = tmp_path / "models" / "lineage"
        config_dir.mkdir(parents=True)
        nested_config = config_dir / "unity_lineage.yml"
        nested_config.write_text("version: 1")

        found = find_config_file(tmp_path)
        assert found == nested_config

    def test_not_found(self, tmp_path: Path) -> None:
        """Test when config file is not found."""
        found = find_config_file(tmp_path)
        assert found is None
