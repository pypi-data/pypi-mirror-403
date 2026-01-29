"""dbt Cloud API client for fetching artifacts."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import requests

logger = logging.getLogger(__name__)

# Environment variable names
ENV_DBT_CLOUD_TOKEN = "DBT_CLOUD_TOKEN"
ENV_DBT_CLOUD_ACCOUNT_ID = "DBT_CLOUD_ACCOUNT_ID"
ENV_DBT_CLOUD_HOST = "DBT_CLOUD_HOST"

# Default dbt Cloud host
DEFAULT_DBT_CLOUD_HOST = "cloud.getdbt.com"


class DbtCloudError(Exception):
    """Base exception for dbt Cloud API errors."""

    pass


class DbtCloudAuthError(DbtCloudError):
    """Authentication error."""

    pass


class DbtCloudNotFoundError(DbtCloudError):
    """Resource not found."""

    pass


@dataclass
class DbtCloudConfig:
    """Configuration for dbt Cloud API access."""

    token: str
    account_id: int
    host: str = DEFAULT_DBT_CLOUD_HOST

    @classmethod
    def from_env(
        cls,
        token: Optional[str] = None,
        account_id: Optional[int] = None,
        host: Optional[str] = None,
    ) -> DbtCloudConfig:
        """Create config from environment variables with optional overrides.

        Args:
            token: API token (overrides DBT_CLOUD_TOKEN env var).
            account_id: Account ID (overrides DBT_CLOUD_ACCOUNT_ID env var).
            host: API host (overrides DBT_CLOUD_HOST env var).

        Returns:
            DbtCloudConfig instance.

        Raises:
            DbtCloudError: If required config is missing.
        """
        resolved_token = token or os.environ.get(ENV_DBT_CLOUD_TOKEN)
        if not resolved_token:
            raise DbtCloudError(
                f"dbt Cloud token required. Set {ENV_DBT_CLOUD_TOKEN} or pass --dbt-cloud-token"
            )

        account_id_str = str(account_id) if account_id else os.environ.get(
            ENV_DBT_CLOUD_ACCOUNT_ID
        )
        if not account_id_str:
            raise DbtCloudError(
                f"dbt Cloud account ID required. Set {ENV_DBT_CLOUD_ACCOUNT_ID} "
                "or pass --dbt-cloud-account-id"
            )

        try:
            resolved_account_id = int(account_id_str)
        except ValueError:
            raise DbtCloudError(f"Invalid account ID: {account_id_str}")

        resolved_host = (
            host or os.environ.get(ENV_DBT_CLOUD_HOST) or DEFAULT_DBT_CLOUD_HOST
        )

        return cls(
            token=resolved_token,
            account_id=resolved_account_id,
            host=resolved_host,
        )


@dataclass
class RunInfo:
    """Information about a dbt Cloud run."""

    id: int
    job_id: int
    status: str
    finished_at: Optional[str]
    has_docs_generated: bool

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> RunInfo:
        """Create RunInfo from API response."""
        return cls(
            id=data["id"],
            job_id=data["job_definition_id"],
            status=data["status_humanized"],
            finished_at=data.get("finished_at"),
            has_docs_generated=data.get("has_docs_generated", False),
        )


class DbtCloudClient:
    """Client for dbt Cloud Administrative API.

    Used to fetch artifacts (manifest.json) from dbt Cloud runs.
    """

    def __init__(self, config: DbtCloudConfig) -> None:
        """Initialize the client.

        Args:
            config: dbt Cloud configuration.
        """
        self.config = config
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Token {config.token}",
                "Content-Type": "application/json",
            }
        )

    @property
    def base_url(self) -> str:
        """Get the API base URL."""
        return f"https://{self.config.host}/api/v2/accounts/{self.config.account_id}/"

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an API request.

        Args:
            method: HTTP method.
            path: API path (relative to base URL).
            params: Query parameters.

        Returns:
            JSON response data.

        Raises:
            DbtCloudAuthError: If authentication fails.
            DbtCloudNotFoundError: If resource not found.
            DbtCloudError: For other API errors.
        """
        url = urljoin(self.base_url, path)

        try:
            response = self._session.request(method, url, params=params)
        except requests.RequestException as e:
            raise DbtCloudError(f"Request failed: {e}")

        if response.status_code == 401:
            raise DbtCloudAuthError("Invalid dbt Cloud token")
        elif response.status_code == 404:
            raise DbtCloudNotFoundError(f"Resource not found: {path}")
        elif response.status_code >= 400:
            try:
                error_data = response.json()
                message = error_data.get("status", {}).get(
                    "user_message", response.text
                )
            except json.JSONDecodeError:
                message = response.text
            raise DbtCloudError(f"API error ({response.status_code}): {message}")

        return response.json()

    def _request_artifact(self, path: str) -> bytes:
        """Fetch an artifact file.

        Args:
            path: API path to the artifact.

        Returns:
            Raw artifact content.

        Raises:
            DbtCloudError: If request fails.
        """
        url = urljoin(self.base_url, path)

        try:
            response = self._session.get(url)
        except requests.RequestException as e:
            raise DbtCloudError(f"Request failed: {e}")

        if response.status_code == 401:
            raise DbtCloudAuthError("Invalid dbt Cloud token")
        elif response.status_code == 404:
            raise DbtCloudNotFoundError(f"Artifact not found: {path}")
        elif response.status_code >= 400:
            raise DbtCloudError(f"API error ({response.status_code}): {response.text}")

        return response.content

    def get_latest_successful_run(self, job_id: int) -> RunInfo:
        """Get the latest successful run for a job.

        Args:
            job_id: The job definition ID.

        Returns:
            RunInfo for the latest successful run.

        Raises:
            DbtCloudNotFoundError: If no successful runs found.
            DbtCloudError: For other API errors.
        """
        response = self._request(
            "GET",
            "runs/",
            params={
                "job_definition_id": job_id,
                "status": 10,  # 10 = Success
                "order_by": "-finished_at",
                "limit": 1,
            },
        )

        runs = response.get("data", [])
        if not runs:
            raise DbtCloudNotFoundError(
                f"No successful runs found for job {job_id}"
            )

        return RunInfo.from_api_response(runs[0])

    def get_run(self, run_id: int) -> RunInfo:
        """Get information about a specific run.

        Args:
            run_id: The run ID.

        Returns:
            RunInfo for the run.

        Raises:
            DbtCloudNotFoundError: If run not found.
            DbtCloudError: For other API errors.
        """
        response = self._request("GET", f"runs/{run_id}/")
        return RunInfo.from_api_response(response["data"])

    def get_manifest(
        self,
        run_id: Optional[int] = None,
        job_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Fetch manifest.json from a dbt Cloud run.

        Either run_id or job_id must be provided. If job_id is provided,
        fetches from the latest successful run.

        Args:
            run_id: Specific run ID to fetch from.
            job_id: Job ID to fetch latest successful run from.

        Returns:
            Parsed manifest.json content.

        Raises:
            DbtCloudError: If neither run_id nor job_id provided.
            DbtCloudNotFoundError: If manifest not found.
        """
        if run_id is None and job_id is None:
            raise DbtCloudError("Either run_id or job_id must be provided")

        if run_id is None:
            # Get latest successful run for the job
            run_info = self.get_latest_successful_run(job_id)  # type: ignore
            run_id = run_info.id
            logger.info(f"Using run {run_id} (latest successful for job {job_id})")

        # Fetch the manifest artifact
        artifact_path = f"runs/{run_id}/artifacts/manifest.json"
        content = self._request_artifact(artifact_path)

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise DbtCloudError(f"Invalid manifest.json: {e}")

    def list_jobs(self) -> list[Dict[str, Any]]:
        """List all jobs in the account.

        Returns:
            List of job data dictionaries.
        """
        response = self._request("GET", "jobs/")
        return response.get("data", [])
