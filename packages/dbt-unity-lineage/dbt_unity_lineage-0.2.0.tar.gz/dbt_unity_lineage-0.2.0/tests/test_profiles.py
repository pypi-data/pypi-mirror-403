"""Tests for profiles module."""

from __future__ import annotations

from pathlib import Path

import pytest

from dbt_unity_lineage.profiles import (
    DatabricksConnection,
    _expand_env_vars,
    get_target_config,
    load_profiles,
)


class TestExpandEnvVars:
    """Tests for _expand_env_vars function."""

    def test_env_var_simple(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test simple env_var expansion."""
        monkeypatch.setenv("MY_VAR", "my_value")
        result = _expand_env_vars("{{ env_var('MY_VAR') }}")
        assert result == "my_value"

    def test_env_var_with_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test env_var with default value."""
        monkeypatch.delenv("MISSING_VAR", raising=False)
        result = _expand_env_vars("{{ env_var('MISSING_VAR', 'default') }}")
        assert result == "default"

    def test_env_var_missing_no_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test env_var without default raises error."""
        monkeypatch.delenv("MISSING_VAR", raising=False)
        with pytest.raises(ValueError, match="not set"):
            _expand_env_vars("{{ env_var('MISSING_VAR') }}")

    def test_env_var_double_quotes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test env_var with double quotes."""
        monkeypatch.setenv("MY_VAR", "my_value")
        result = _expand_env_vars('{{ env_var("MY_VAR") }}')
        assert result == "my_value"

    def test_shell_style_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test shell-style $VAR expansion."""
        monkeypatch.setenv("MY_VAR", "my_value")
        result = _expand_env_vars("$MY_VAR")
        assert result == "my_value"

    def test_non_string_passthrough(self) -> None:
        """Test that non-strings pass through unchanged."""
        assert _expand_env_vars(123) == 123
        assert _expand_env_vars(None) is None
        assert _expand_env_vars(True) is True


class TestDatabricksConnection:
    """Tests for DatabricksConnection."""

    def test_workspace_url_with_https(self) -> None:
        """Test workspace URL when host includes https."""
        conn = DatabricksConnection(
            host="https://dbc-abc123.cloud.databricks.com",
            token="token",
            catalog="main",
        )
        assert conn.workspace_url == "https://dbc-abc123.cloud.databricks.com"

    def test_workspace_url_without_https(self) -> None:
        """Test workspace URL when host doesn't include https."""
        conn = DatabricksConnection(
            host="dbc-abc123.cloud.databricks.com",
            token="token",
            catalog="main",
        )
        assert conn.workspace_url == "https://dbc-abc123.cloud.databricks.com"


class TestLoadProfiles:
    """Tests for load_profiles function."""

    def test_load_sample_profiles(
        self,
        sample_profiles_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test loading sample profiles."""
        monkeypatch.setenv("DATABRICKS_TOKEN", "test-token")

        profiles = load_profiles(sample_profiles_path.parent)

        assert "jaffle_shop" in profiles
        assert profiles["jaffle_shop"]["target"] == "dev"
        assert "dev" in profiles["jaffle_shop"]["outputs"]
        assert "prod" in profiles["jaffle_shop"]["outputs"]

        # Check that env var was expanded
        dev_config = profiles["jaffle_shop"]["outputs"]["dev"]
        assert dev_config["token"] == "test-token"

    def test_load_nonexistent_profiles(self, tmp_path: Path) -> None:
        """Test that loading nonexistent profiles raises error."""
        with pytest.raises(FileNotFoundError):
            load_profiles(tmp_path / "nonexistent")


class TestGetTargetConfig:
    """Tests for get_target_config function."""

    def test_get_default_target(
        self,
        sample_profiles_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test getting default target config."""
        monkeypatch.setenv("DATABRICKS_TOKEN", "test-token")
        profiles = load_profiles(sample_profiles_path.parent)

        config = get_target_config(profiles, "jaffle_shop")

        assert config["type"] == "databricks"
        assert config["host"] == "dbc-abc123.cloud.databricks.com"
        assert config["catalog"] == "main"
        assert config["schema"] == "dev"  # Default target

    def test_get_specific_target(
        self,
        sample_profiles_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test getting specific target config."""
        monkeypatch.setenv("DATABRICKS_TOKEN", "test-token")
        profiles = load_profiles(sample_profiles_path.parent)

        config = get_target_config(profiles, "jaffle_shop", "prod")

        assert config["schema"] == "prod"

    def test_missing_profile(
        self,
        sample_profiles_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test error on missing profile."""
        monkeypatch.setenv("DATABRICKS_TOKEN", "test-token")
        profiles = load_profiles(sample_profiles_path.parent)

        with pytest.raises(ValueError, match="not found"):
            get_target_config(profiles, "nonexistent_profile")

    def test_missing_target(
        self,
        sample_profiles_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test error on missing target."""
        monkeypatch.setenv("DATABRICKS_TOKEN", "test-token")
        profiles = load_profiles(sample_profiles_path.parent)

        with pytest.raises(ValueError, match="not found"):
            get_target_config(profiles, "jaffle_shop", "nonexistent_target")
