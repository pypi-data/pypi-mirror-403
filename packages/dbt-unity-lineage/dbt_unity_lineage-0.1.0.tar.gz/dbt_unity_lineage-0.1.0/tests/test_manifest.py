"""Tests for manifest module."""

from __future__ import annotations

from pathlib import Path

import pytest

from dbt_unity_lineage.manifest import (
    Manifest,
    get_sources_with_uc_source,
    load_manifest,
    resolve_exposure_dependencies,
)


class TestLoadManifest:
    """Tests for load_manifest function."""

    def test_load_sample_manifest(self, sample_manifest_path: Path) -> None:
        """Test loading the sample manifest file."""
        manifest = load_manifest(sample_manifest_path)

        assert manifest.project_name == "jaffle_shop"
        assert manifest.metadata.dbt_version == "1.7.0"

    def test_load_nonexistent_file(self, tmp_path: Path) -> None:
        """Test that loading nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_manifest(tmp_path / "nonexistent.json")


class TestManifestSources:
    """Tests for manifest source parsing."""

    def test_sources_loaded(self, sample_manifest: Manifest) -> None:
        """Test that sources are loaded correctly."""
        assert len(sample_manifest.sources) == 3

        # Check first source
        gl_accounts = sample_manifest.sources["source.jaffle_shop.erp.gl_accounts"]
        assert gl_accounts.name == "gl_accounts"
        assert gl_accounts.source_name == "erp"
        assert gl_accounts.description == "General ledger accounts from SAP"
        assert gl_accounts.database == "main"
        assert gl_accounts.schema_ == "bronze_erp"

    def test_source_uc_source_meta(self, sample_manifest: Manifest) -> None:
        """Test that uc_source is correctly extracted from source_meta."""
        gl_accounts = sample_manifest.sources["source.jaffle_shop.erp.gl_accounts"]
        assert gl_accounts.uc_source == "sap_ecc"

    def test_source_qualified_name(self, sample_manifest: Manifest) -> None:
        """Test qualified name generation."""
        gl_accounts = sample_manifest.sources["source.jaffle_shop.erp.gl_accounts"]
        assert gl_accounts.qualified_name == "erp.gl_accounts"

    def test_source_uc_table_name(self, sample_manifest: Manifest) -> None:
        """Test UC table name generation."""
        gl_accounts = sample_manifest.sources["source.jaffle_shop.erp.gl_accounts"]
        assert gl_accounts.uc_table_name == "main.bronze_erp.gl_accounts"


class TestManifestExposures:
    """Tests for manifest exposure parsing."""

    def test_exposures_loaded(self, sample_manifest: Manifest) -> None:
        """Test that exposures are loaded correctly."""
        assert len(sample_manifest.exposures) == 3

    def test_exposure_with_url(self, sample_manifest: Manifest) -> None:
        """Test exposure with URL."""
        exec_dash = sample_manifest.exposures["exposure.jaffle_shop.executive_dashboard"]
        assert exec_dash.name == "executive_dashboard"
        assert exec_dash.type == "dashboard"
        assert exec_dash.url == "https://app.powerbi.com/groups/abc/reports/xyz"
        assert exec_dash.description == "Executive KPI overview dashboard"

    def test_exposure_owner(self, sample_manifest: Manifest) -> None:
        """Test exposure owner parsing."""
        exec_dash = sample_manifest.exposures["exposure.jaffle_shop.executive_dashboard"]
        assert exec_dash.owner is not None
        assert exec_dash.owner.name == "BI Team"
        assert exec_dash.owner.email == "bi-team@example.com"

    def test_exposure_depends_on(self, sample_manifest: Manifest) -> None:
        """Test exposure depends_on parsing."""
        exec_dash = sample_manifest.exposures["exposure.jaffle_shop.executive_dashboard"]
        assert len(exec_dash.depends_on_nodes) == 2
        assert "model.jaffle_shop.fct_orders" in exec_dash.depends_on_nodes
        assert "model.jaffle_shop.dim_customers" in exec_dash.depends_on_nodes

    def test_exposure_uc_system_type_override(self, sample_manifest: Manifest) -> None:
        """Test exposure with explicit uc_system_type."""
        custom_app = sample_manifest.exposures["exposure.jaffle_shop.custom_app"]
        assert custom_app.uc_system_type == "CUSTOM"


class TestManifestModels:
    """Tests for manifest model parsing."""

    def test_models_loaded(self, sample_manifest: Manifest) -> None:
        """Test that models are loaded correctly."""
        assert len(sample_manifest.models) == 3

    def test_model_uc_table_name(self, sample_manifest: Manifest) -> None:
        """Test model UC table name generation."""
        fct_orders = sample_manifest.models["model.jaffle_shop.fct_orders"]
        assert fct_orders.uc_table_name == "main.gold.fct_orders"


class TestGetSourcesWithUcSource:
    """Tests for get_sources_with_uc_source function."""

    def test_get_sources_with_uc_source(self, sample_manifest: Manifest) -> None:
        """Test filtering sources with uc_source."""
        sources = get_sources_with_uc_source(sample_manifest)
        assert len(sources) == 3
        assert all(s.uc_source is not None for s in sources)


class TestResolveExposureDependencies:
    """Tests for resolve_exposure_dependencies function."""

    def test_resolve_dependencies(self, sample_manifest: Manifest) -> None:
        """Test resolving exposure dependencies to UC table names."""
        exec_dash = sample_manifest.exposures["exposure.jaffle_shop.executive_dashboard"]
        uc_tables = resolve_exposure_dependencies(sample_manifest, exec_dash)

        assert len(uc_tables) == 2
        assert "main.gold.fct_orders" in uc_tables
        assert "main.gold.dim_customers" in uc_tables

    def test_resolve_empty_dependencies(self, sample_manifest: Manifest) -> None:
        """Test resolving exposure with no dependencies."""
        custom_app = sample_manifest.exposures["exposure.jaffle_shop.custom_app"]
        uc_tables = resolve_exposure_dependencies(sample_manifest, custom_app)
        assert uc_tables == []
