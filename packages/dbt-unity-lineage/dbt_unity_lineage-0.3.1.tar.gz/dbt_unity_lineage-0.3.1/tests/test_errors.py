"""Tests for error handling module."""

from __future__ import annotations

from dbt_unity_lineage.errors import (
    EXIT_CONFIG_ERROR,
    EXIT_CONNECTION_ERROR,
    EXIT_ERROR,
    EXIT_PARTIAL_FAILURE,
    EXIT_SUCCESS,
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    ConflictError,
    ConnectionError,
    DataError,
    DbtUnityLineageError,
    ErrorCategory,
    NotFoundError,
    RateLimitError,
    ValidationError,
    categorize_api_error,
)


class TestErrorCategory:
    """Tests for ErrorCategory enum."""

    def test_all_categories(self):
        """Test all error categories exist."""
        assert ErrorCategory.CONFIGURATION.value == "configuration"
        assert ErrorCategory.CONNECTION.value == "connection"
        assert ErrorCategory.AUTHENTICATION.value == "authentication"
        assert ErrorCategory.AUTHORIZATION.value == "authorization"
        assert ErrorCategory.RATE_LIMIT.value == "rate_limit"
        assert ErrorCategory.SERVER_ERROR.value == "server_error"
        assert ErrorCategory.NOT_FOUND.value == "not_found"
        assert ErrorCategory.CONFLICT.value == "conflict"
        assert ErrorCategory.VALIDATION.value == "validation"
        assert ErrorCategory.DATA.value == "data"
        assert ErrorCategory.UNKNOWN.value == "unknown"


class TestDbtUnityLineageError:
    """Tests for base error class."""

    def test_basic_error(self):
        """Test basic error creation."""
        error = DbtUnityLineageError("Test error")
        assert str(error) == "Test error"
        assert error.category == ErrorCategory.UNKNOWN

    def test_error_with_category(self):
        """Test error with category."""
        error = DbtUnityLineageError(
            "Auth error", category=ErrorCategory.AUTHENTICATION
        )
        assert error.category == ErrorCategory.AUTHENTICATION

    def test_error_with_resolution(self):
        """Test error with resolution hint."""
        error = DbtUnityLineageError(
            "Test error", resolution="Try this to fix it"
        )
        assert "Test error" in str(error)
        assert "Try this to fix it" in str(error)

    def test_error_with_details(self):
        """Test error with details."""
        error = DbtUnityLineageError("Test error", details="More info here")
        assert "Test error" in str(error)
        assert "More info here" in str(error)

    def test_error_with_all_fields(self):
        """Test error with all fields."""
        error = DbtUnityLineageError(
            "Test error",
            category=ErrorCategory.CONNECTION,
            resolution="Fix it",
            details="Details here",
        )
        output = str(error)
        assert "Test error" in output
        assert "Fix it" in output
        assert "Details here" in output


class TestConfigurationError:
    """Tests for ConfigurationError."""

    def test_default_resolution(self):
        """Test default resolution message."""
        error = ConfigurationError("Config is invalid")
        assert error.category == ErrorCategory.CONFIGURATION
        assert "dbt_unity_lineage.yml" in error.resolution

    def test_custom_resolution(self):
        """Test custom resolution message."""
        error = ConfigurationError(
            "Config is invalid", resolution="Check this specific thing"
        )
        assert error.resolution == "Check this specific thing"


class TestConnectionError:
    """Tests for ConnectionError."""

    def test_default_resolution(self):
        """Test default resolution message."""
        error = ConnectionError("Cannot connect")
        assert error.category == ErrorCategory.CONNECTION
        assert "network" in error.resolution.lower()

    def test_custom_resolution(self):
        """Test custom resolution message."""
        error = ConnectionError(
            "Cannot connect", resolution="Check firewall"
        )
        assert error.resolution == "Check firewall"


class TestAuthenticationError:
    """Tests for AuthenticationError."""

    def test_default_resolution(self):
        """Test default resolution message."""
        error = AuthenticationError("Token expired")
        assert error.category == ErrorCategory.AUTHENTICATION
        assert "token" in error.resolution.lower()


class TestAuthorizationError:
    """Tests for AuthorizationError."""

    def test_default_resolution(self):
        """Test default resolution message."""
        error = AuthorizationError("Permission denied")
        assert error.category == ErrorCategory.AUTHORIZATION
        assert "permission" in error.resolution.lower()


class TestRateLimitError:
    """Tests for RateLimitError."""

    def test_default_resolution(self):
        """Test default resolution message."""
        error = RateLimitError("Too many requests")
        assert error.category == ErrorCategory.RATE_LIMIT
        assert "batch" in error.resolution.lower() or "retry" in error.resolution.lower()


class TestNotFoundError:
    """Tests for NotFoundError."""

    def test_default_resolution(self):
        """Test default resolution message."""
        error = NotFoundError("Resource not found")
        assert error.category == ErrorCategory.NOT_FOUND
        assert "exists" in error.resolution.lower()


class TestConflictError:
    """Tests for ConflictError."""

    def test_default_resolution(self):
        """Test default resolution message."""
        error = ConflictError("Already exists")
        assert error.category == ErrorCategory.CONFLICT


class TestValidationError:
    """Tests for ValidationError."""

    def test_default_resolution(self):
        """Test default resolution message."""
        error = ValidationError("Invalid data")
        assert error.category == ErrorCategory.VALIDATION
        assert "api" in error.resolution.lower()


class TestDataError:
    """Tests for DataError."""

    def test_default_resolution(self):
        """Test default resolution message."""
        error = DataError("Invalid manifest")
        assert error.category == ErrorCategory.DATA
        assert "manifest" in error.resolution.lower()


class TestCategorizeApiError:
    """Tests for categorize_api_error function."""

    def test_authentication_401(self):
        """Test 401 errors are categorized as authentication."""
        result = categorize_api_error(Exception("HTTP 401 Unauthorized"))
        assert isinstance(result, AuthenticationError)

    def test_authentication_keyword(self):
        """Test unauthorized keyword is categorized."""
        result = categorize_api_error(Exception("unauthorized request"))
        assert isinstance(result, AuthenticationError)

    def test_authentication_invalid_token(self):
        """Test invalid token is categorized."""
        result = categorize_api_error(Exception("invalid token provided"))
        assert isinstance(result, AuthenticationError)

    def test_authorization_403(self):
        """Test 403 errors are categorized as authorization."""
        result = categorize_api_error(Exception("HTTP 403 Forbidden"))
        assert isinstance(result, AuthorizationError)

    def test_authorization_permission(self):
        """Test permission keyword is categorized."""
        result = categorize_api_error(Exception("Permission denied for resource"))
        assert isinstance(result, AuthorizationError)

    def test_rate_limit_429(self):
        """Test 429 errors are categorized as rate limit."""
        result = categorize_api_error(Exception("HTTP 429 Too Many Requests"))
        assert isinstance(result, RateLimitError)

    def test_rate_limit_keyword(self):
        """Test rate limit keyword is categorized."""
        result = categorize_api_error(Exception("rate limit exceeded"))
        assert isinstance(result, RateLimitError)

    def test_not_found_404(self):
        """Test 404 errors are categorized as not found."""
        result = categorize_api_error(Exception("HTTP 404 Not Found"))
        assert isinstance(result, NotFoundError)

    def test_conflict_409(self):
        """Test 409 errors are categorized as conflict."""
        result = categorize_api_error(Exception("HTTP 409 Conflict"))
        assert isinstance(result, ConflictError)

    def test_conflict_already_exists(self):
        """Test already exists is categorized as conflict."""
        result = categorize_api_error(Exception("Resource already exists"))
        assert isinstance(result, ConflictError)

    def test_validation_400(self):
        """Test 400 errors are categorized as validation."""
        result = categorize_api_error(Exception("HTTP 400 Bad Request"))
        assert isinstance(result, ValidationError)

    def test_validation_keyword(self):
        """Test validation keyword is categorized."""
        result = categorize_api_error(Exception("validation failed"))
        assert isinstance(result, ValidationError)

    def test_server_error_500(self):
        """Test 500 errors are categorized as server error."""
        result = categorize_api_error(Exception("HTTP 500 Internal Server Error"))
        assert result.category == ErrorCategory.SERVER_ERROR

    def test_server_error_502(self):
        """Test 502 errors are categorized as server error."""
        result = categorize_api_error(Exception("HTTP 502 Bad Gateway"))
        assert result.category == ErrorCategory.SERVER_ERROR

    def test_server_error_503(self):
        """Test 503 errors are categorized as server error."""
        result = categorize_api_error(Exception("HTTP 503 Service Unavailable"))
        assert result.category == ErrorCategory.SERVER_ERROR

    def test_server_error_504(self):
        """Test 504 errors are categorized as server error."""
        result = categorize_api_error(Exception("HTTP 504 Gateway Timeout"))
        assert result.category == ErrorCategory.SERVER_ERROR

    def test_connection_error_keyword(self):
        """Test connection keyword is categorized."""
        result = categorize_api_error(Exception("connection refused"))
        assert isinstance(result, ConnectionError)

    def test_connection_timeout(self):
        """Test timeout is categorized as connection error."""
        result = categorize_api_error(Exception("request timeout"))
        assert isinstance(result, ConnectionError)

    def test_unknown_error(self):
        """Test unknown errors are categorized correctly."""
        result = categorize_api_error(Exception("Something weird happened"))
        assert result.category == ErrorCategory.UNKNOWN


class TestExitCodes:
    """Tests for exit codes."""

    def test_exit_success(self):
        """Test success exit code."""
        assert EXIT_SUCCESS == 0

    def test_exit_error(self):
        """Test error exit code."""
        assert EXIT_ERROR == 1

    def test_exit_config_error(self):
        """Test config error exit code."""
        assert EXIT_CONFIG_ERROR == 2

    def test_exit_connection_error(self):
        """Test connection error exit code."""
        assert EXIT_CONNECTION_ERROR == 3

    def test_exit_partial_failure(self):
        """Test partial failure exit code."""
        assert EXIT_PARTIAL_FAILURE == 4
