"""Tests for dbt Cloud API client."""

from __future__ import annotations

import json
import os
from unittest.mock import Mock, patch

import pytest

from dbt_unity_lineage.dbt_cloud import (
    DEFAULT_DBT_CLOUD_HOST,
    DbtCloudAuthError,
    DbtCloudClient,
    DbtCloudConfig,
    DbtCloudError,
    DbtCloudNotFoundError,
    RunInfo,
)


class TestDbtCloudConfig:
    """Tests for DbtCloudConfig."""

    def test_from_env_with_all_values(self):
        """Test creating config with all explicit values."""
        config = DbtCloudConfig.from_env(
            token="test-token",
            account_id=12345,
            host="custom.dbt.com",
        )
        assert config.token == "test-token"
        assert config.account_id == 12345
        assert config.host == "custom.dbt.com"

    def test_from_env_with_env_vars(self):
        """Test creating config from environment variables."""
        with patch.dict(
            os.environ,
            {
                "DBT_CLOUD_TOKEN": "env-token",
                "DBT_CLOUD_ACCOUNT_ID": "67890",
                "DBT_CLOUD_HOST": "env.dbt.com",
            },
        ):
            config = DbtCloudConfig.from_env()
            assert config.token == "env-token"
            assert config.account_id == 67890
            assert config.host == "env.dbt.com"

    def test_from_env_with_default_host(self):
        """Test that default host is used when not specified."""
        with patch.dict(
            os.environ,
            {
                "DBT_CLOUD_TOKEN": "token",
                "DBT_CLOUD_ACCOUNT_ID": "123",
            },
            clear=True,
        ):
            config = DbtCloudConfig.from_env()
            assert config.host == DEFAULT_DBT_CLOUD_HOST

    def test_from_env_missing_token(self):
        """Test error when token is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(DbtCloudError, match="token required"):
                DbtCloudConfig.from_env(account_id=123)

    def test_from_env_missing_account_id(self):
        """Test error when account ID is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(DbtCloudError, match="account ID required"):
                DbtCloudConfig.from_env(token="token")

    def test_from_env_invalid_account_id(self):
        """Test error when account ID is not a valid integer."""
        with patch.dict(
            os.environ,
            {"DBT_CLOUD_TOKEN": "token", "DBT_CLOUD_ACCOUNT_ID": "not-a-number"},
        ):
            with pytest.raises(DbtCloudError, match="Invalid account ID"):
                DbtCloudConfig.from_env()


class TestRunInfo:
    """Tests for RunInfo."""

    def test_from_api_response(self):
        """Test creating RunInfo from API response."""
        data = {
            "id": 123,
            "job_definition_id": 456,
            "status_humanized": "Success",
            "finished_at": "2024-01-15T10:00:00Z",
            "has_docs_generated": True,
        }
        run_info = RunInfo.from_api_response(data)
        assert run_info.id == 123
        assert run_info.job_id == 456
        assert run_info.status == "Success"
        assert run_info.finished_at == "2024-01-15T10:00:00Z"
        assert run_info.has_docs_generated is True

    def test_from_api_response_minimal(self):
        """Test creating RunInfo with minimal data."""
        data = {
            "id": 123,
            "job_definition_id": 456,
            "status_humanized": "Running",
        }
        run_info = RunInfo.from_api_response(data)
        assert run_info.id == 123
        assert run_info.finished_at is None
        assert run_info.has_docs_generated is False


class TestDbtCloudClient:
    """Tests for DbtCloudClient."""

    @pytest.fixture
    def config(self) -> DbtCloudConfig:
        """Create a test config."""
        return DbtCloudConfig(
            token="test-token",
            account_id=12345,
            host="test.dbt.com",
        )

    @pytest.fixture
    def client(self, config: DbtCloudConfig) -> DbtCloudClient:
        """Create a test client."""
        return DbtCloudClient(config)

    def test_base_url(self, client: DbtCloudClient):
        """Test base URL construction."""
        assert client.base_url == "https://test.dbt.com/api/v2/accounts/12345/"

    def test_get_latest_successful_run(self, client: DbtCloudClient):
        """Test fetching the latest successful run."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "id": 999,
                    "job_definition_id": 100,
                    "status_humanized": "Success",
                    "finished_at": "2024-01-15T12:00:00Z",
                    "has_docs_generated": True,
                }
            ]
        }

        with patch.object(client._session, "request", return_value=mock_response):
            run_info = client.get_latest_successful_run(job_id=100)
            assert run_info.id == 999
            assert run_info.job_id == 100

    def test_get_latest_successful_run_not_found(self, client: DbtCloudClient):
        """Test error when no successful runs found."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}

        with patch.object(client._session, "request", return_value=mock_response):
            with pytest.raises(DbtCloudNotFoundError, match="No successful runs"):
                client.get_latest_successful_run(job_id=100)

    def test_get_run(self, client: DbtCloudClient):
        """Test fetching a specific run."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "id": 123,
                "job_definition_id": 456,
                "status_humanized": "Success",
            }
        }

        with patch.object(client._session, "request", return_value=mock_response):
            run_info = client.get_run(run_id=123)
            assert run_info.id == 123

    def test_get_manifest_with_job_id(self, client: DbtCloudClient):
        """Test fetching manifest via job ID."""
        # Mock the get_latest_successful_run call
        mock_run_response = Mock()
        mock_run_response.status_code = 200
        mock_run_response.json.return_value = {
            "data": [
                {
                    "id": 999,
                    "job_definition_id": 100,
                    "status_humanized": "Success",
                }
            ]
        }

        # Mock the artifact fetch
        mock_artifact_response = Mock()
        mock_artifact_response.status_code = 200
        mock_artifact_response.content = json.dumps(
            {"metadata": {"project_name": "test"}, "sources": {}, "exposures": {}}
        ).encode()

        def mock_request(method, url, **kwargs):
            if "runs/" in url and "artifacts" not in url:
                return mock_run_response
            return None

        with patch.object(client._session, "request", side_effect=mock_request):
            with patch.object(client._session, "get", return_value=mock_artifact_response):
                manifest = client.get_manifest(job_id=100)
                assert manifest["metadata"]["project_name"] == "test"

    def test_get_manifest_with_run_id(self, client: DbtCloudClient):
        """Test fetching manifest via run ID."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = json.dumps(
            {"metadata": {"project_name": "test"}, "sources": {}, "exposures": {}}
        ).encode()

        with patch.object(client._session, "get", return_value=mock_response):
            manifest = client.get_manifest(run_id=123)
            assert manifest["metadata"]["project_name"] == "test"

    def test_get_manifest_no_id_provided(self, client: DbtCloudClient):
        """Test error when neither run_id nor job_id provided."""
        with pytest.raises(DbtCloudError, match="Either run_id or job_id"):
            client.get_manifest()

    def test_auth_error(self, client: DbtCloudClient):
        """Test handling of authentication errors."""
        mock_response = Mock()
        mock_response.status_code = 401

        with patch.object(client._session, "request", return_value=mock_response):
            with pytest.raises(DbtCloudAuthError, match="Invalid dbt Cloud token"):
                client.get_run(run_id=123)

    def test_not_found_error(self, client: DbtCloudClient):
        """Test handling of 404 errors."""
        mock_response = Mock()
        mock_response.status_code = 404

        with patch.object(client._session, "request", return_value=mock_response):
            with pytest.raises(DbtCloudNotFoundError, match="Resource not found"):
                client.get_run(run_id=123)

    def test_list_jobs(self, client: DbtCloudClient):
        """Test listing jobs."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"id": 1, "name": "Job 1"},
                {"id": 2, "name": "Job 2"},
            ]
        }

        with patch.object(client._session, "request", return_value=mock_response):
            jobs = client.list_jobs()
            assert len(jobs) == 2
            assert jobs[0]["name"] == "Job 1"
