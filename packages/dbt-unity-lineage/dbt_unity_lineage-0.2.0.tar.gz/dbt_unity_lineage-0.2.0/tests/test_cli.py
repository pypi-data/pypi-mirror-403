"""Tests for CLI commands."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from dbt_unity_lineage.cli import main
from dbt_unity_lineage.manifest import Manifest
from dbt_unity_lineage.profiles import DatabricksConnection
from dbt_unity_lineage.sync import SyncItem, SyncPlan, SyncStatus


@pytest.fixture
def runner() -> CliRunner:
    """Create a Click test runner."""
    return CliRunner()


@pytest.fixture
def mock_manifest() -> Manifest:
    """Create a mock manifest."""
    manifest = MagicMock(spec=Manifest)
    manifest.project_name = "test_project"
    manifest.sources = {}
    manifest.exposures = {}
    manifest.models = {}
    return manifest


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
def mock_sync_plan() -> SyncPlan:
    """Create a mock sync plan."""
    plan = SyncPlan(project_name="test_project", catalog="test_catalog")
    plan.items = [
        SyncItem(
            identifier="sap.orders",
            name="sap__orders",
            system_type="SAP",
            entity_type="table",
            status=SyncStatus.IN_SYNC,
            item_type="source",
        ),
    ]
    return plan


class TestMainGroup:
    """Tests for main CLI group."""

    def test_version(self, runner: CliRunner):
        """Test version option."""
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "version" in result.output.lower()

    def test_help(self, runner: CliRunner):
        """Test help output."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Push dbt lineage" in result.output
        assert "--config" in result.output
        assert "--manifest" in result.output
        assert "--verbose" in result.output

    def test_verbose_and_quiet_flags(self, runner: CliRunner):
        """Test verbose and quiet flags are mutually available."""
        result = runner.invoke(main, ["--help"])
        assert "-v" in result.output or "--verbose" in result.output
        assert "-q" in result.output or "--quiet" in result.output


class TestPushCommand:
    """Tests for push command."""

    def test_push_no_manifest(self, runner: CliRunner):
        """Test push fails when no manifest is found."""
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["push"])
            assert result.exit_code != 0
            assert "manifest" in result.output.lower()

    def test_push_no_connection(self, runner: CliRunner, tmp_path: Path):
        """Test push fails when no connection is available."""
        # Create a minimal manifest
        manifest = {
            "metadata": {"project_name": "test"},
            "nodes": {},
            "sources": {},
            "exposures": {},
        }
        manifest_path = tmp_path / "target" / "manifest.json"
        manifest_path.parent.mkdir(parents=True)
        manifest_path.write_text(json.dumps(manifest))

        result = runner.invoke(main, ["--manifest", str(manifest_path), "push"])
        # Should fail due to no connection
        assert result.exit_code != 0

    def test_push_help(self, runner: CliRunner):
        """Test push command help."""
        result = runner.invoke(main, ["push", "--help"])
        assert result.exit_code == 0
        assert "--dry-run" in result.output
        assert "--no-clean" in result.output
        assert "--sources-only" in result.output
        assert "--exposures-only" in result.output
        assert "--batch-size" in result.output
        assert "--format" in result.output

    @patch("dbt_unity_lineage.cli.get_databricks_connection")
    @patch("dbt_unity_lineage.cli.load_manifest")
    @patch("dbt_unity_lineage.cli.UnityCatalogClient")
    @patch("dbt_unity_lineage.cli.build_sync_plan")
    def test_push_dry_run(
        self,
        mock_build_plan: MagicMock,
        mock_client_cls: MagicMock,
        mock_load_manifest: MagicMock,
        mock_get_connection: MagicMock,
        runner: CliRunner,
        mock_manifest: Manifest,
        mock_connection: DatabricksConnection,
        mock_sync_plan: SyncPlan,
        tmp_path: Path,
    ):
        """Test push with dry-run flag."""
        # Setup mocks
        mock_load_manifest.return_value = mock_manifest
        mock_get_connection.return_value = mock_connection
        mock_build_plan.return_value = mock_sync_plan

        # Create minimal manifest file for path detection
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text('{"metadata": {"project_name": "test"}}')

        result = runner.invoke(
            main, ["--manifest", str(manifest_path), "push", "--dry-run"]
        )
        # Should complete without error
        assert result.exit_code == 0
        assert "dry run" in result.output.lower()


class TestStatusCommand:
    """Tests for status command."""

    def test_status_no_manifest(self, runner: CliRunner):
        """Test status fails when no manifest is found."""
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["status"])
            assert result.exit_code != 0
            assert "manifest" in result.output.lower()

    def test_status_help(self, runner: CliRunner):
        """Test status command help."""
        result = runner.invoke(main, ["status", "--help"])
        assert result.exit_code == 0
        assert "--format" in result.output

    @patch("dbt_unity_lineage.cli.get_databricks_connection")
    @patch("dbt_unity_lineage.cli.load_manifest")
    @patch("dbt_unity_lineage.cli.UnityCatalogClient")
    @patch("dbt_unity_lineage.cli.build_sync_plan")
    def test_status_json_format(
        self,
        mock_build_plan: MagicMock,
        mock_client_cls: MagicMock,
        mock_load_manifest: MagicMock,
        mock_get_connection: MagicMock,
        runner: CliRunner,
        mock_manifest: Manifest,
        mock_connection: DatabricksConnection,
        mock_sync_plan: SyncPlan,
        tmp_path: Path,
    ):
        """Test status with JSON format."""
        mock_load_manifest.return_value = mock_manifest
        mock_get_connection.return_value = mock_connection
        mock_build_plan.return_value = mock_sync_plan

        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text('{"metadata": {"project_name": "test"}}')

        result = runner.invoke(
            main, ["--manifest", str(manifest_path), "status", "--format", "json"]
        )
        assert result.exit_code == 0
        # Should be valid JSON
        output_data = json.loads(result.output)
        assert "project" in output_data


class TestCleanCommand:
    """Tests for clean command."""

    def test_clean_no_manifest(self, runner: CliRunner):
        """Test clean fails when no manifest is found."""
        with runner.isolated_filesystem():
            result = runner.invoke(main, ["clean"])
            assert result.exit_code != 0
            assert "manifest" in result.output.lower()

    def test_clean_help(self, runner: CliRunner):
        """Test clean command help."""
        result = runner.invoke(main, ["clean", "--help"])
        assert result.exit_code == 0
        assert "--dry-run" in result.output
        assert "--format" in result.output


class TestDbtCloudOptions:
    """Tests for dbt Cloud integration options."""

    def test_dbt_cloud_requires_job_or_run_id(self, runner: CliRunner, tmp_path: Path):
        """Test that --dbt-cloud requires either job-id or run-id."""
        # Create minimal profiles.yml
        profiles_dir = tmp_path / "profiles"
        profiles_dir.mkdir()
        profiles = {
            "test": {
                "target": "dev",
                "outputs": {
                    "dev": {
                        "type": "databricks",
                        "host": "test.databricks.com",
                        "token": "test-token",
                        "catalog": "main",
                    }
                },
            }
        }
        (profiles_dir / "profiles.yml").write_text(
            __import__("yaml").dump(profiles)
        )

        result = runner.invoke(
            main,
            [
                "--dbt-cloud",
                "--dbt-cloud-token", "test-token",
                "--dbt-cloud-account-id", "123",
                "--profiles-dir", str(profiles_dir),
                "--profile", "test",
                "push",
            ],
        )
        assert result.exit_code != 0
        assert "job-id" in result.output.lower() or "run-id" in result.output.lower()


class TestConfigLoading:
    """Tests for config file loading."""

    def test_loads_config_from_path(self, runner: CliRunner, tmp_path: Path):
        """Test that config is loaded from specified path."""
        config_content = """
version: 1
source_systems:
  test:
    system_type: CUSTOM
"""
        config_path = tmp_path / "config.yml"
        config_path.write_text(config_content)

        result = runner.invoke(
            main, ["--config", str(config_path), "-v", "--help"]
        )
        assert result.exit_code == 0

    def test_handles_missing_config_gracefully(self, runner: CliRunner, tmp_path: Path):
        """Test that missing config is handled gracefully."""
        result = runner.invoke(
            main, ["--config", str(tmp_path / "nonexistent.yml"), "-v", "--help"]
        )
        # Should not error out on help
        assert result.exit_code == 0


class TestClaudeFlag:
    """Tests for --claude flag."""

    def test_claude_flag_in_help(self, runner: CliRunner):
        """Test that --claude flag appears in help."""
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "--claude" in result.output

    @patch("dbt_unity_lineage.cli.urllib.request.urlopen")
    def test_claude_flag_fetches_content(
        self,
        mock_urlopen: MagicMock,
        runner: CliRunner,
    ):
        """Test that --claude fetches and outputs CLAUDE.md content."""
        # Mock the response
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
    ):
        """Test that --claude falls back to main branch on 404."""
        import urllib.error

        # First call (version tag) returns 404, second call (main) succeeds
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
    ):
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
    ):
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
    ):
        """Test that --claude exits when all URLs return 404."""
        import urllib.error

        error_404 = urllib.error.HTTPError(
            url="test", code=404, msg="Not Found", hdrs={}, fp=None  # type: ignore
        )
        # Both version tag and main branch return 404
        mock_urlopen.side_effect = [error_404, error_404]

        result = runner.invoke(main, ["--claude"])
        assert result.exit_code == 1
        assert "not found" in result.output.lower()


class TestInitCommand:
    """Tests for init command."""

    def test_init_creates_config_file(self, runner: CliRunner, tmp_path: Path):
        """Test init creates a config file."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(main, ["init"])
            assert result.exit_code == 0
            assert Path("dbt_unity_lineage.yml").exists()
            content = Path("dbt_unity_lineage.yml").read_text()
            assert "version: 1" in content
            assert "source_systems:" in content

    def test_init_custom_output(self, runner: CliRunner, tmp_path: Path):
        """Test init with custom output path."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(main, ["init", "-o", "custom.yml"])
            assert result.exit_code == 0
            assert Path("custom.yml").exists()

    def test_init_refuses_overwrite(self, runner: CliRunner, tmp_path: Path):
        """Test init refuses to overwrite existing file."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path("dbt_unity_lineage.yml").write_text("existing")
            result = runner.invoke(main, ["init"])
            assert result.exit_code == 1
            assert "already exists" in result.output

    def test_init_force_overwrites(self, runner: CliRunner, tmp_path: Path):
        """Test init --force overwrites existing file."""
        with runner.isolated_filesystem(temp_dir=tmp_path):
            Path("dbt_unity_lineage.yml").write_text("existing")
            result = runner.invoke(main, ["init", "--force"])
            assert result.exit_code == 0
            content = Path("dbt_unity_lineage.yml").read_text()
            assert "version: 1" in content

    def test_init_help(self, runner: CliRunner):
        """Test init command help."""
        result = runner.invoke(main, ["init", "--help"])
        assert result.exit_code == 0
        assert "--output" in result.output
        assert "--force" in result.output


class TestContext:
    """Tests for CLI context."""

    def test_context_default_values(self):
        """Test Context default values."""
        from dbt_unity_lineage.cli import Context

        ctx = Context()
        assert ctx.verbose is False
        assert ctx.quiet is False
        assert ctx.config is None
        assert ctx.manifest is None
        assert ctx.connection is None
        assert ctx.client is None
