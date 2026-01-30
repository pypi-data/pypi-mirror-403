"""Tests for CLI commands (V2)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from dbt_unity_lineage.cli import main
from dbt_unity_lineage.profiles import DatabricksConnection


@pytest.fixture
def runner() -> CliRunner:
    """Create a Click test runner."""
    return CliRunner()


@pytest.fixture
def mock_connection() -> DatabricksConnection:
    """Create a mock Databricks connection."""
    return DatabricksConnection(
        host="test.databricks.com",
        token="test-token",
        catalog="test_catalog",
        http_path="/sql/test",
    )


@pytest.fixture
def sample_config_yaml() -> str:
    """Sample V2 config YAML."""
    return """\
version: 1
project:
  name: test_project
configuration:
  layers:
    bronze:
      sources:
        folders:
          - bronze/erp
"""


@pytest.fixture
def sample_sources_yaml() -> str:
    """Sample sources YAML."""
    return """\
sources:
  - name: erp
    meta:
      uc_source: sap_ecc
    tables:
      - name: orders
        description: Customer orders
      - name: customers
        description: Customer master data
"""


@pytest.fixture
def sample_exposures_yaml() -> str:
    """Sample exposures YAML."""
    return """\
exposures:
  - name: sales_dashboard
    type: dashboard
    description: Sales metrics
    url: https://powerbi.com/reports/123
    owner:
      name: Data Team
      email: data@example.com
"""


class TestMainGroup:
    """Tests for main CLI group."""

    def test_version(self, runner: CliRunner) -> None:
        """Test version option."""
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "version" in result.output.lower()

    def test_help(self, runner: CliRunner) -> None:
        """Test help output."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Push dbt lineage" in result.output
        assert "--project-dir" in result.output
        assert "--verbose" in result.output
        assert "--claude" in result.output

    def test_verbose_and_quiet_flags(self, runner: CliRunner) -> None:
        """Test verbose and quiet flags are present."""
        result = runner.invoke(main, ["--help"])
        assert "-v" in result.output or "--verbose" in result.output
        assert "-q" in result.output or "--quiet" in result.output

    def test_no_subcommand_shows_help(self, runner: CliRunner) -> None:
        """Test that running without subcommand shows help."""
        result = runner.invoke(main, [])
        assert result.exit_code == 0
        assert "Commands:" in result.output


class TestInitCommand:
    """Tests for init command."""

    def test_init_creates_config_file(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test init creates a config file."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(main, ["init", "-o", "config.yml"])
            assert result.exit_code == 0
            assert Path("config.yml").exists()
            content = Path("config.yml").read_text()
            assert "version: 1" in content
            assert "project:" in content
            assert "configuration:" in content
            assert "layers:" in content

    def test_init_creates_in_models_lineage(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test init creates file in models/lineage by default."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(main, ["init"])
            assert result.exit_code == 0
            assert Path("models/lineage/unity_lineage.yml").exists()

    def test_init_custom_output(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test init with custom output path."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(main, ["init", "-o", "custom.yml"])
            assert result.exit_code == 0
            assert Path("custom.yml").exists()

    def test_init_refuses_overwrite(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test init refuses to overwrite existing file."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path("config.yml").write_text("existing")
            result = runner.invoke(main, ["init", "-o", "config.yml"])
            assert result.exit_code == 1
            assert "already exists" in result.output

    def test_init_force_overwrites(self, runner: CliRunner, tmp_path: Path) -> None:
        """Test init --force overwrites existing file."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path("config.yml").write_text("existing")
            result = runner.invoke(main, ["init", "-o", "config.yml", "--force"])
            assert result.exit_code == 0
            content = Path("config.yml").read_text()
            assert "version: 1" in content

    def test_init_help(self, runner: CliRunner) -> None:
        """Test init command help."""
        result = runner.invoke(main, ["init", "--help"])
        assert result.exit_code == 0
        assert "--output" in result.output
        assert "--force" in result.output


class TestValidateCommand:
    """Tests for validate command."""

    def test_validate_no_config(self, runner: CliRunner) -> None:
        """Test validate fails when no config found."""
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["validate"])
            assert result.exit_code != 0
            assert "No config file" in result.output

    def test_validate_with_config(
        self, runner: CliRunner, tmp_path: Path, sample_config_yaml: str, sample_sources_yaml: str
    ) -> None:
        """Test validate with valid config."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            # Create config
            Path("models/lineage").mkdir(parents=True)
            Path("models/lineage/unity_lineage.yml").write_text(sample_config_yaml)

            # Create source folder and file
            Path("bronze/erp").mkdir(parents=True)
            Path("bronze/erp/_sources.yml").write_text(sample_sources_yaml)

            result = runner.invoke(main, ["validate"])
            assert result.exit_code == 0
            assert "Sources found:" in result.output or "sources" in result.output.lower()

    def test_validate_json_format(
        self, runner: CliRunner, tmp_path: Path, sample_config_yaml: str, sample_sources_yaml: str
    ) -> None:
        """Test validate with JSON output format."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path("models/lineage").mkdir(parents=True)
            Path("models/lineage/unity_lineage.yml").write_text(sample_config_yaml)
            Path("bronze/erp").mkdir(parents=True)
            Path("bronze/erp/_sources.yml").write_text(sample_sources_yaml)

            result = runner.invoke(main, ["validate", "--format", "json"])
            assert result.exit_code == 0
            output = json.loads(result.output)
            assert "valid" in output
            assert "sources_found" in output

    def test_validate_warns_missing_folder(
        self, runner: CliRunner, tmp_path: Path, sample_config_yaml: str
    ) -> None:
        """Test validate warns about missing folders."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path("models/lineage").mkdir(parents=True)
            Path("models/lineage/unity_lineage.yml").write_text(sample_config_yaml)
            # Don't create bronze/erp folder

            result = runner.invoke(main, ["validate"])
            # Should warn but not fail
            assert "bronze/erp" in result.output or "does not exist" in result.output

    def test_validate_help(self, runner: CliRunner) -> None:
        """Test validate command help."""
        result = runner.invoke(main, ["validate", "--help"])
        assert result.exit_code == 0
        assert "--format" in result.output


class TestScanCommand:
    """Tests for scan command."""

    def test_scan_no_config(self, runner: CliRunner) -> None:
        """Test scan fails when no config found."""
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["scan"])
            assert result.exit_code != 0
            assert "No config file" in result.output

    def test_scan_with_sources(
        self, runner: CliRunner, tmp_path: Path, sample_config_yaml: str, sample_sources_yaml: str
    ) -> None:
        """Test scan finds sources."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path("models/lineage").mkdir(parents=True)
            Path("models/lineage/unity_lineage.yml").write_text(sample_config_yaml)
            Path("bronze/erp").mkdir(parents=True)
            Path("bronze/erp/_sources.yml").write_text(sample_sources_yaml)

            result = runner.invoke(main, ["scan"])
            assert result.exit_code == 0
            assert "erp" in result.output
            assert "orders" in result.output

    def test_scan_json_format(
        self, runner: CliRunner, tmp_path: Path, sample_config_yaml: str, sample_sources_yaml: str
    ) -> None:
        """Test scan with JSON output format."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path("models/lineage").mkdir(parents=True)
            Path("models/lineage/unity_lineage.yml").write_text(sample_config_yaml)
            Path("bronze/erp").mkdir(parents=True)
            Path("bronze/erp/_sources.yml").write_text(sample_sources_yaml)

            result = runner.invoke(main, ["scan", "--format", "json"])
            assert result.exit_code == 0
            output = json.loads(result.output)
            assert "sources" in output
            assert len(output["sources"]) > 0

    def test_scan_type_filter(
        self, runner: CliRunner, tmp_path: Path, sample_config_yaml: str, sample_sources_yaml: str
    ) -> None:
        """Test scan with type filter."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path("models/lineage").mkdir(parents=True)
            Path("models/lineage/unity_lineage.yml").write_text(sample_config_yaml)
            Path("bronze/erp").mkdir(parents=True)
            Path("bronze/erp/_sources.yml").write_text(sample_sources_yaml)

            result = runner.invoke(main, ["scan", "--type", "source"])
            assert result.exit_code == 0
            assert "orders" in result.output

    def test_scan_help(self, runner: CliRunner) -> None:
        """Test scan command help."""
        result = runner.invoke(main, ["scan", "--help"])
        assert result.exit_code == 0
        assert "--select" in result.output
        assert "--type" in result.output
        assert "--format" in result.output


class TestSyncCommand:
    """Tests for sync command."""

    def test_sync_no_config(self, runner: CliRunner) -> None:
        """Test sync fails when no config found."""
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["sync"])
            assert result.exit_code != 0
            assert "No config file" in result.output

    def test_sync_no_missing_systems(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        """Test sync when all systems are defined."""
        config = """\
version: 1
project:
  name: test_project
configuration:
  layers:
    bronze:
      sources:
        folders:
          - bronze/erp
source_systems:
  sap_ecc:
    system_type: SAP
"""
        sources = """\
sources:
  - name: erp
    meta:
      uc_source: sap_ecc
    tables:
      - name: orders
"""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path("models/lineage").mkdir(parents=True)
            Path("models/lineage/unity_lineage.yml").write_text(config)
            Path("bronze/erp").mkdir(parents=True)
            Path("bronze/erp/_sources.yml").write_text(sources)

            result = runner.invoke(main, ["sync"])
            assert result.exit_code == 0
            assert "All source systems are defined" in result.output

    def test_sync_finds_missing_systems(
        self, runner: CliRunner, tmp_path: Path, sample_config_yaml: str, sample_sources_yaml: str
    ) -> None:
        """Test sync identifies missing source systems."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path("models/lineage").mkdir(parents=True)
            Path("models/lineage/unity_lineage.yml").write_text(sample_config_yaml)
            Path("bronze/erp").mkdir(parents=True)
            Path("bronze/erp/_sources.yml").write_text(sample_sources_yaml)

            result = runner.invoke(main, ["sync", "--dry-run"])
            assert result.exit_code == 0
            # sap_ecc is referenced but not defined
            assert "sap_ecc" in result.output

    def test_sync_help(self, runner: CliRunner) -> None:
        """Test sync command help."""
        result = runner.invoke(main, ["sync", "--help"])
        assert result.exit_code == 0
        assert "--dry-run" in result.output
        assert "--format" in result.output


class TestStatusCommand:
    """Tests for status command."""

    def test_status_no_config(self, runner: CliRunner) -> None:
        """Test status fails when no config found."""
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["status"])
            assert result.exit_code != 0
            assert "No config file" in result.output

    def test_status_no_connection(
        self, runner: CliRunner, tmp_path: Path, sample_config_yaml: str
    ) -> None:
        """Test status fails when no connection."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path("models/lineage").mkdir(parents=True)
            Path("models/lineage/unity_lineage.yml").write_text(sample_config_yaml)

            result = runner.invoke(main, ["status"])
            assert result.exit_code != 0
            no_conn = "No Databricks connection" in result.output
            profiles_msg = "profiles" in result.output.lower()
            assert no_conn or profiles_msg

    def test_status_help(self, runner: CliRunner) -> None:
        """Test status command help."""
        result = runner.invoke(main, ["status", "--help"])
        assert result.exit_code == 0
        assert "--format" in result.output
        assert "--select" in result.output


class TestPushCommand:
    """Tests for push command."""

    def test_push_no_config(self, runner: CliRunner) -> None:
        """Test push fails when no config found."""
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["push"])
            assert result.exit_code != 0
            assert "No config file" in result.output

    def test_push_no_connection(
        self, runner: CliRunner, tmp_path: Path, sample_config_yaml: str
    ) -> None:
        """Test push fails when no connection."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path("models/lineage").mkdir(parents=True)
            Path("models/lineage/unity_lineage.yml").write_text(sample_config_yaml)

            result = runner.invoke(main, ["push"])
            assert result.exit_code != 0
            no_conn = "No Databricks connection" in result.output
            profiles_msg = "profiles" in result.output.lower()
            assert no_conn or profiles_msg

    def test_push_help(self, runner: CliRunner) -> None:
        """Test push command help."""
        result = runner.invoke(main, ["push", "--help"])
        assert result.exit_code == 0
        assert "--dry-run" in result.output
        assert "--format" in result.output
        assert "--select" in result.output


class TestCleanCommand:
    """Tests for clean command."""

    def test_clean_no_config(self, runner: CliRunner) -> None:
        """Test clean fails when no config found."""
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["clean"])
            assert result.exit_code != 0
            assert "No config file" in result.output

    def test_clean_no_connection(
        self, runner: CliRunner, tmp_path: Path, sample_config_yaml: str
    ) -> None:
        """Test clean fails when no connection."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path("models/lineage").mkdir(parents=True)
            Path("models/lineage/unity_lineage.yml").write_text(sample_config_yaml)

            result = runner.invoke(main, ["clean"])
            assert result.exit_code != 0
            no_conn = "No Databricks connection" in result.output
            profiles_msg = "profiles" in result.output.lower()
            assert no_conn or profiles_msg

    def test_clean_help(self, runner: CliRunner) -> None:
        """Test clean command help."""
        result = runner.invoke(main, ["clean", "--help"])
        assert result.exit_code == 0
        assert "--dry-run" in result.output
        assert "--force" in result.output
        assert "--format" in result.output


class TestClaudeFlag:
    """Tests for --claude flag."""

    def test_claude_flag_in_help(self, runner: CliRunner) -> None:
        """Test that --claude flag appears in help."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "--claude" in result.output

    @patch("dbt_unity_lineage.cli.urllib.request.urlopen")
    def test_claude_flag_fetches_content(
        self,
        mock_urlopen: MagicMock,
        runner: CliRunner,
    ) -> None:
        """Test that --claude fetches and outputs CLAUDE.md content."""
        mock_response = MagicMock()
        mock_response.read.return_value = b"# Test CLAUDE.md content"
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = runner.invoke(main, ["--claude"])
        assert result.exit_code == 0
        assert "Test CLAUDE.md content" in result.output

    @patch("dbt_unity_lineage.cli.urllib.request.urlopen")
    def test_claude_flag_fallback_to_main(
        self,
        mock_urlopen: MagicMock,
        runner: CliRunner,
    ) -> None:
        """Test that --claude falls back to main branch on 404."""
        import urllib.error

        error_404 = urllib.error.HTTPError(
            url="test", code=404, msg="Not Found", hdrs={}, fp=None  # type: ignore
        )
        mock_response = MagicMock()
        mock_response.read.return_value = b"# Fallback content"
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        mock_urlopen.side_effect = [error_404, mock_response]

        result = runner.invoke(main, ["--claude"])
        assert result.exit_code == 0
        assert "Fallback content" in result.output
        assert mock_urlopen.call_count == 2

    @patch("dbt_unity_lineage.cli.urllib.request.urlopen")
    def test_claude_flag_http_error_non_404(
        self,
        mock_urlopen: MagicMock,
        runner: CliRunner,
    ) -> None:
        """Test that --claude exits on non-404 HTTP errors."""
        import urllib.error

        error_500 = urllib.error.HTTPError(
            url="test", code=500, msg="Server Error", hdrs={}, fp=None  # type: ignore
        )
        mock_urlopen.side_effect = error_500

        result = runner.invoke(main, ["--claude"])
        assert result.exit_code == 1
        assert "HTTP 500" in result.output

    @patch("dbt_unity_lineage.cli.urllib.request.urlopen")
    def test_claude_flag_network_error(
        self,
        mock_urlopen: MagicMock,
        runner: CliRunner,
    ) -> None:
        """Test that --claude handles network errors."""
        import urllib.error

        network_error = urllib.error.URLError("Connection refused")
        mock_urlopen.side_effect = network_error

        result = runner.invoke(main, ["--claude"])
        assert result.exit_code == 1
        assert "Connection refused" in result.output or "network" in result.output.lower()

    @patch("dbt_unity_lineage.cli.urllib.request.urlopen")
    def test_claude_flag_all_urls_404(
        self,
        mock_urlopen: MagicMock,
        runner: CliRunner,
    ) -> None:
        """Test that --claude exits when all URLs return 404."""
        import urllib.error

        error_404 = urllib.error.HTTPError(
            url="test", code=404, msg="Not Found", hdrs={}, fp=None  # type: ignore
        )
        mock_urlopen.side_effect = [error_404, error_404]

        result = runner.invoke(main, ["--claude"])
        assert result.exit_code == 1
        assert "not found" in result.output.lower()


class TestContext:
    """Tests for CLI context."""

    def test_context_default_values(self) -> None:
        """Test Context default values."""
        from dbt_unity_lineage.cli import Context

        ctx = Context()
        assert ctx.verbose is False
        assert ctx.quiet is False
        assert ctx.config is None
        assert ctx.connection is None
        assert ctx.client is None
        assert ctx.project_dir is None
