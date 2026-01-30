"""Error handling and categorization for dbt-unity-lineage."""

from __future__ import annotations

from enum import Enum
from typing import Optional


class ErrorCategory(str, Enum):
    """Categories of errors that can occur."""

    CONFIGURATION = "configuration"
    CONNECTION = "connection"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RATE_LIMIT = "rate_limit"
    SERVER_ERROR = "server_error"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    VALIDATION = "validation"
    DATA = "data"
    UNKNOWN = "unknown"


class DbtUnityLineageError(Exception):
    """Base exception for dbt-unity-lineage errors."""

    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        resolution: Optional[str] = None,
        details: Optional[str] = None,
    ):
        super().__init__(message)
        self.category = category
        self.resolution = resolution
        self.details = details

    def __str__(self) -> str:
        parts = [super().__str__()]
        if self.details:
            parts.append(f"Details: {self.details}")
        if self.resolution:
            parts.append(f"Resolution: {self.resolution}")
        return "\n".join(parts)


class ConfigurationError(DbtUnityLineageError):
    """Error in configuration files."""

    def __init__(
        self,
        message: str,
        resolution: Optional[str] = None,
        details: Optional[str] = None,
    ):
        super().__init__(
            message,
            category=ErrorCategory.CONFIGURATION,
            resolution=resolution or "Check your dbt_unity_lineage.yml configuration file.",
            details=details,
        )


class ConnectionError(DbtUnityLineageError):
    """Error connecting to Databricks."""

    def __init__(
        self,
        message: str,
        resolution: Optional[str] = None,
        details: Optional[str] = None,
    ):
        super().__init__(
            message,
            category=ErrorCategory.CONNECTION,
            resolution=resolution or "Check your network connection and Databricks host URL.",
            details=details,
        )


class AuthenticationError(DbtUnityLineageError):
    """Authentication failed."""

    def __init__(
        self,
        message: str,
        resolution: Optional[str] = None,
        details: Optional[str] = None,
    ):
        super().__init__(
            message,
            category=ErrorCategory.AUTHENTICATION,
            resolution=resolution or "Check your Databricks token in profiles.yml or environment.",
            details=details,
        )


class AuthorizationError(DbtUnityLineageError):
    """Permission denied."""

    def __init__(
        self,
        message: str,
        resolution: Optional[str] = None,
        details: Optional[str] = None,
    ):
        super().__init__(
            message,
            category=ErrorCategory.AUTHORIZATION,
            resolution=resolution
            or "Check that you have the required permissions on the Unity Catalog.",
            details=details,
        )


class RateLimitError(DbtUnityLineageError):
    """Rate limit exceeded."""

    def __init__(
        self,
        message: str,
        resolution: Optional[str] = None,
        details: Optional[str] = None,
    ):
        super().__init__(
            message,
            category=ErrorCategory.RATE_LIMIT,
            resolution=resolution or "Wait and retry, or reduce batch size with --batch-size.",
            details=details,
        )


class NotFoundError(DbtUnityLineageError):
    """Resource not found."""

    def __init__(
        self,
        message: str,
        resolution: Optional[str] = None,
        details: Optional[str] = None,
    ):
        super().__init__(
            message,
            category=ErrorCategory.NOT_FOUND,
            resolution=resolution or "Check that the referenced resource exists.",
            details=details,
        )


class ConflictError(DbtUnityLineageError):
    """Resource conflict."""

    def __init__(
        self,
        message: str,
        resolution: Optional[str] = None,
        details: Optional[str] = None,
    ):
        super().__init__(
            message,
            category=ErrorCategory.CONFLICT,
            resolution=resolution
            or "The resource already exists. Use --conflict option to handle conflicts.",
            details=details,
        )


class ValidationError(DbtUnityLineageError):
    """Validation error from the API."""

    def __init__(
        self,
        message: str,
        resolution: Optional[str] = None,
        details: Optional[str] = None,
    ):
        super().__init__(
            message,
            category=ErrorCategory.VALIDATION,
            resolution=resolution or "Check the data being sent matches API requirements.",
            details=details,
        )


class DataError(DbtUnityLineageError):
    """Error with input data (manifest, config)."""

    def __init__(
        self,
        message: str,
        resolution: Optional[str] = None,
        details: Optional[str] = None,
    ):
        super().__init__(
            message,
            category=ErrorCategory.DATA,
            resolution=resolution or "Check your manifest.json and dbt_unity_lineage.yml files.",
            details=details,
        )


def categorize_api_error(error: Exception) -> DbtUnityLineageError:
    """Convert an API exception to a categorized error.

    Args:
        error: The original exception.

    Returns:
        A categorized DbtUnityLineageError.
    """
    error_str = str(error).lower()

    # Check for authentication errors
    if "401" in error_str or "unauthorized" in error_str or "invalid token" in error_str:
        return AuthenticationError(
            f"Authentication failed: {error}",
            resolution="Check your Databricks token is valid and not expired.",
        )

    # Check for authorization errors
    if "403" in error_str or "forbidden" in error_str or "permission" in error_str:
        return AuthorizationError(
            f"Permission denied: {error}",
            resolution="Check you have CREATE_EXTERNAL_METADATA and related permissions.",
        )

    # Check for rate limit
    if "429" in error_str or "rate limit" in error_str or "too many requests" in error_str:
        return RateLimitError(
            f"Rate limit exceeded: {error}",
            resolution="Wait and retry, or use --batch-size to reduce API calls.",
        )

    # Check for not found
    if "404" in error_str or "not found" in error_str:
        return NotFoundError(f"Resource not found: {error}")

    # Check for conflict
    if "409" in error_str or "conflict" in error_str or "already exists" in error_str:
        return ConflictError(f"Resource conflict: {error}")

    # Check for validation errors
    if "400" in error_str or "validation" in error_str or "invalid" in error_str:
        return ValidationError(f"Validation error: {error}")

    # Check for server errors
    if "500" in error_str or "502" in error_str or "503" in error_str or "504" in error_str:
        return DbtUnityLineageError(
            f"Server error: {error}",
            category=ErrorCategory.SERVER_ERROR,
            resolution="This is a temporary server issue. Wait and retry.",
        )

    # Check for connection errors
    if "connection" in error_str or "timeout" in error_str or "network" in error_str:
        return ConnectionError(f"Connection error: {error}")

    # Unknown error
    return DbtUnityLineageError(f"Unexpected error: {error}", category=ErrorCategory.UNKNOWN)


# Exit codes
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_CONFIG_ERROR = 2
EXIT_CONNECTION_ERROR = 3
EXIT_PARTIAL_FAILURE = 4  # Some operations failed but others succeeded
