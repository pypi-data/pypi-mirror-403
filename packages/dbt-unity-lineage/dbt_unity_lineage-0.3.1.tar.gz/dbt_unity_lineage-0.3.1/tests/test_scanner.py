"""Tests for scanner module."""

from __future__ import annotations

from pathlib import Path

from dbt_unity_lineage.config import (
    Config,
    Configuration,
    LayerConfig,
    LayerExposures,
    LayerSources,
    ProjectConfig,
    SourceSystemConfig,
)
from dbt_unity_lineage.scanner import (
    Exposure,
    ExposureOwner,
    ScanResult,
    Source,
    SourceTable,
    get_missing_source_systems,
    get_source_system_for_table,
    scan_config,
    scan_folder,
)


class TestSourceTable:
    """Tests for SourceTable dataclass."""

    def test_basic_properties(self) -> None:
        """Test basic properties."""
        table = SourceTable(
            name="gl_accounts",
            source_name="erp",
            description="General ledger accounts",
            meta={"uc_source": "sap_ecc"},
        )
        assert table.name == "gl_accounts"
        assert table.source_name == "erp"
        assert table.qualified_name == "erp.gl_accounts"
        assert table.uc_source == "sap_ecc"

    def test_uc_source_missing(self) -> None:
        """Test uc_source returns None when not set."""
        table = SourceTable(name="test", source_name="src")
        assert table.uc_source is None

    def test_column_names(self) -> None:
        """Test column_names property."""
        table = SourceTable(
            name="test",
            source_name="src",
            columns=[
                {"name": "col1", "description": "Column 1"},
                {"name": "col2"},
                {"description": "No name"},  # Should be skipped
            ],
        )
        assert table.column_names == ["col1", "col2"]


class TestExposure:
    """Tests for Exposure dataclass."""

    def test_basic_properties(self) -> None:
        """Test basic properties."""
        exposure = Exposure(
            name="sales_dashboard",
            type="dashboard",
            description="Sales performance dashboard",
            url="https://powerbi.com/reports/123",
            owner=ExposureOwner(name="Data Team", email="data@example.com"),
            meta={"uc_system_type": "POWER_BI"},
        )
        assert exposure.name == "sales_dashboard"
        assert exposure.type == "dashboard"
        assert exposure.uc_system_type == "POWER_BI"
        assert exposure.owner.email == "data@example.com"

    def test_uc_system_type_missing(self) -> None:
        """Test uc_system_type returns None when not set."""
        exposure = Exposure(name="test", type="dashboard")
        assert exposure.uc_system_type is None


class TestScanResult:
    """Tests for ScanResult dataclass."""

    def test_empty_result(self) -> None:
        """Test empty scan result."""
        result = ScanResult()
        assert result.source_count == 0
        assert result.exposure_count == 0
        assert result.all_source_tables == []

    def test_with_data(self) -> None:
        """Test scan result with data."""
        source = Source(
            name="erp",
            tables=[
                SourceTable(name="t1", source_name="erp"),
                SourceTable(name="t2", source_name="erp"),
            ],
        )
        exposure = Exposure(name="dashboard", type="dashboard")

        result = ScanResult(sources=[source], exposures=[exposure])
        assert result.source_count == 2
        assert result.exposure_count == 1
        assert len(result.all_source_tables) == 2


class TestScanFolder:
    """Tests for scan_folder function."""

    def test_scan_nonexistent_folder(self, tmp_path: Path) -> None:
        """Test scanning nonexistent folder."""
        result = scan_folder(tmp_path / "nonexistent")
        assert result.source_count == 0
        assert len(result.warnings) == 1
        assert "does not exist" in result.warnings[0]

    def test_scan_empty_folder(self, tmp_path: Path) -> None:
        """Test scanning empty folder."""
        result = scan_folder(tmp_path)
        assert result.source_count == 0
        assert result.exposure_count == 0

    def test_scan_sources_file(self, tmp_path: Path) -> None:
        """Test scanning a _sources.yml file."""
        sources_file = tmp_path / "_sources.yml"
        sources_file.write_text(
            """
sources:
  - name: erp
    description: ERP source
    meta:
      uc_source: sap_ecc
    tables:
      - name: gl_accounts
        description: GL accounts
      - name: cost_centers
        description: Cost centers
"""
        )

        result = scan_folder(tmp_path)
        assert result.source_count == 2
        assert result.exposure_count == 0

        tables = result.all_source_tables
        assert tables[0].source_name == "erp"
        assert tables[0].name == "gl_accounts"
        assert tables[0].uc_source == "sap_ecc"  # Inherited from source

    def test_scan_sources_meta_inheritance(self, tmp_path: Path) -> None:
        """Test that table meta inherits from source meta."""
        sources_file = tmp_path / "_sources.yml"
        sources_file.write_text(
            """
sources:
  - name: erp
    meta:
      uc_source: sap
      team: data
    tables:
      - name: table1
        meta:
          team: override_team  # Override source-level meta
"""
        )

        result = scan_folder(tmp_path)
        table = result.all_source_tables[0]
        assert table.uc_source == "sap"  # Inherited
        assert table.meta["team"] == "override_team"  # Overridden

    def test_scan_exposures_file(self, tmp_path: Path) -> None:
        """Test scanning an _exposures.yml file."""
        exposures_file = tmp_path / "_exposures.yml"
        exposures_file.write_text(
            """
exposures:
  - name: sales_dashboard
    type: dashboard
    description: Sales metrics
    url: https://powerbi.com/reports/123
    owner:
      name: Data Team
      email: data@example.com
    depends_on:
      - ref('sales_fact')
      - ref('dim_customer')
"""
        )

        result = scan_folder(tmp_path)
        assert result.source_count == 0
        assert result.exposure_count == 1

        exposure = result.exposures[0]
        assert exposure.name == "sales_dashboard"
        assert exposure.type == "dashboard"
        assert exposure.url == "https://powerbi.com/reports/123"
        assert exposure.owner.email == "data@example.com"

    def test_scan_schema_file_with_both(self, tmp_path: Path) -> None:
        """Test scanning a schema.yml with both sources and exposures."""
        schema_file = tmp_path / "schema.yml"
        schema_file.write_text(
            """
sources:
  - name: crm
    tables:
      - name: customers

exposures:
  - name: customer_report
    type: analysis
"""
        )

        result = scan_folder(tmp_path)
        assert result.source_count == 1
        assert result.exposure_count == 1

    def test_scan_sources_only(self, tmp_path: Path) -> None:
        """Test scanning for sources only."""
        # Create both sources and exposures files
        (tmp_path / "_sources.yml").write_text(
            """
sources:
  - name: src
    tables:
      - name: t1
"""
        )
        (tmp_path / "_exposures.yml").write_text(
            """
exposures:
  - name: exp1
    type: dashboard
"""
        )

        result = scan_folder(tmp_path, scan_type="sources")
        assert result.source_count == 1
        assert result.exposure_count == 0

    def test_scan_exposures_only(self, tmp_path: Path) -> None:
        """Test scanning for exposures only."""
        (tmp_path / "_sources.yml").write_text(
            """
sources:
  - name: src
    tables:
      - name: t1
"""
        )
        (tmp_path / "_exposures.yml").write_text(
            """
exposures:
  - name: exp1
    type: dashboard
"""
        )

        result = scan_folder(tmp_path, scan_type="exposures")
        assert result.source_count == 0
        assert result.exposure_count == 1

    def test_scan_invalid_yaml(self, tmp_path: Path) -> None:
        """Test scanning invalid YAML file."""
        invalid_file = tmp_path / "_sources.yml"
        invalid_file.write_text("invalid: yaml: content: [")

        result = scan_folder(tmp_path)
        assert len(result.errors) == 1
        assert "YAML parse error" in result.errors[0]

    def test_scan_missing_required_fields(self, tmp_path: Path) -> None:
        """Test scanning with missing required fields."""
        sources_file = tmp_path / "_sources.yml"
        sources_file.write_text(
            """
sources:
  - name: valid_source
    tables:
      - name: valid_table
      - description: missing name
"""
        )

        result = scan_folder(tmp_path)
        assert result.source_count == 1
        assert len(result.errors) == 1
        assert "missing 'name'" in result.errors[0]


class TestScanConfig:
    """Tests for scan_config function."""

    def test_scan_all_layers(self, tmp_path: Path) -> None:
        """Test scanning all layers."""
        # Create folder structure
        bronze_erp = tmp_path / "bronze" / "erp"
        bronze_erp.mkdir(parents=True)
        (bronze_erp / "_sources.yml").write_text(
            """
sources:
  - name: erp
    tables:
      - name: orders
"""
        )

        gold_dashboards = tmp_path / "gold" / "dashboards"
        gold_dashboards.mkdir(parents=True)
        (gold_dashboards / "_exposures.yml").write_text(
            """
exposures:
  - name: sales_report
    type: dashboard
"""
        )

        config = Config(
            project=ProjectConfig(name="test"),
            configuration=Configuration(
                layers={
                    "bronze": LayerConfig(
                        sources=LayerSources(folders=["bronze/erp"])
                    ),
                    "gold": LayerConfig(
                        exposures=LayerExposures(folders=["gold/dashboards"])
                    ),
                }
            ),
        )

        result = scan_config(config, tmp_path)
        assert result.source_count == 1
        assert result.exposure_count == 1

    def test_scan_with_select_pattern(self, tmp_path: Path) -> None:
        """Test scanning with select pattern."""
        # Create folders
        bronze_a = tmp_path / "bronze" / "a"
        bronze_a.mkdir(parents=True)
        (bronze_a / "_sources.yml").write_text(
            """
sources:
  - name: a
    tables:
      - name: t1
"""
        )

        bronze_b = tmp_path / "bronze" / "b"
        bronze_b.mkdir(parents=True)
        (bronze_b / "_sources.yml").write_text(
            """
sources:
  - name: b
    tables:
      - name: t2
"""
        )

        config = Config(
            project=ProjectConfig(name="test"),
            configuration=Configuration(
                layers={
                    "bronze": LayerConfig(
                        sources=LayerSources(folders=["bronze/a", "bronze/b"])
                    ),
                }
            ),
        )

        # Scan only bronze/a
        result = scan_config(config, tmp_path, select="bronze/a")
        assert result.source_count == 1
        tables = result.all_source_tables
        assert tables[0].source_name == "a"


class TestGetMissingSourceSystems:
    """Tests for get_missing_source_systems function."""

    def test_no_missing(self) -> None:
        """Test when all source systems are defined."""
        result = ScanResult(
            sources=[
                Source(
                    name="erp",
                    tables=[
                        SourceTable(
                            name="t1",
                            source_name="erp",
                            meta={"uc_source": "sap"},
                        )
                    ],
                )
            ]
        )
        config = Config(
            project=ProjectConfig(name="test"),
            configuration=Configuration(
                layers={"x": LayerConfig(sources=LayerSources(folders=["x"]))}
            ),
            source_systems={
                "sap": SourceSystemConfig(system_type="SAP"),
            },
        )

        missing = get_missing_source_systems(result, config)
        assert missing == {}

    def test_with_missing(self) -> None:
        """Test when some source systems are missing."""
        result = ScanResult(
            sources=[
                Source(
                    name="erp",
                    tables=[
                        SourceTable(
                            name="t1",
                            source_name="erp",
                            meta={"uc_source": "sap"},
                        ),
                        SourceTable(
                            name="t2",
                            source_name="erp",
                            meta={"uc_source": "oracle"},
                        ),
                    ],
                )
            ]
        )
        config = Config(
            project=ProjectConfig(name="test"),
            configuration=Configuration(
                layers={"x": LayerConfig(sources=LayerSources(folders=["x"]))}
            ),
            source_systems={
                "sap": SourceSystemConfig(system_type="SAP"),
            },
        )

        missing = get_missing_source_systems(result, config)
        assert "oracle" in missing
        assert len(missing["oracle"]) == 1
        assert missing["oracle"][0].name == "t2"

    def test_sources_without_uc_source(self) -> None:
        """Test that sources without uc_source are not counted as missing."""
        result = ScanResult(
            sources=[
                Source(
                    name="src",
                    tables=[
                        SourceTable(name="t1", source_name="src", meta={}),
                    ],
                )
            ]
        )
        config = Config(
            project=ProjectConfig(name="test"),
            configuration=Configuration(
                layers={"x": LayerConfig(sources=LayerSources(folders=["x"]))}
            ),
        )

        missing = get_missing_source_systems(result, config)
        assert missing == {}


class TestGetSourceSystemForTable:
    """Tests for get_source_system_for_table function."""

    def test_found(self) -> None:
        """Test when source system is found."""
        table = SourceTable(name="t1", source_name="erp", meta={"uc_source": "sap"})
        config = Config(
            project=ProjectConfig(name="test"),
            configuration=Configuration(
                layers={"x": LayerConfig(sources=LayerSources(folders=["x"]))}
            ),
            source_systems={
                "sap": SourceSystemConfig(
                    system_type="SAP",
                    description="SAP ECC",
                ),
            },
        )

        source_system = get_source_system_for_table(table, config)
        assert source_system is not None
        assert source_system.system_type == "SAP"
        assert source_system.description == "SAP ECC"

    def test_not_found(self) -> None:
        """Test when source system is not found."""
        table = SourceTable(name="t1", source_name="erp", meta={"uc_source": "oracle"})
        config = Config(
            project=ProjectConfig(name="test"),
            configuration=Configuration(
                layers={"x": LayerConfig(sources=LayerSources(folders=["x"]))}
            ),
            source_systems={
                "sap": SourceSystemConfig(system_type="SAP"),
            },
        )

        source_system = get_source_system_for_table(table, config)
        assert source_system is None

    def test_no_uc_source(self) -> None:
        """Test when table has no uc_source."""
        table = SourceTable(name="t1", source_name="erp", meta={})
        config = Config(
            project=ProjectConfig(name="test"),
            configuration=Configuration(
                layers={"x": LayerConfig(sources=LayerSources(folders=["x"]))}
            ),
        )

        source_system = get_source_system_for_table(table, config)
        assert source_system is None
