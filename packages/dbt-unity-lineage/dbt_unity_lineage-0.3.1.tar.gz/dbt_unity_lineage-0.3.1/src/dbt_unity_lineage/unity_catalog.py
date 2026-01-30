"""Unity Catalog API client for external metadata operations."""

from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar

from databricks.sdk import WorkspaceClient

from .profiles import DatabricksConnection

logger = logging.getLogger(__name__)

# Type variable for generic retry decorator
F = TypeVar("F", bound=Callable[..., Any])

# HTTP status codes that should trigger a retry
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


class RetryableError(Exception):
    """An error that can be retried."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class MaxRetriesExceededError(Exception):
    """Raised when max retries are exceeded."""

    def __init__(self, message: str, last_error: Optional[Exception] = None):
        super().__init__(message)
        self.last_error = last_error


def _extract_status_code(error: Exception) -> Optional[int]:
    """Extract HTTP status code from an exception.

    The Databricks SDK raises exceptions with status codes in various formats.
    """
    # Check for status_code attribute
    if hasattr(error, "status_code"):
        return getattr(error, "status_code")

    # Check for response attribute with status_code
    if hasattr(error, "response") and hasattr(error.response, "status_code"):
        return error.response.status_code

    # Check error message for common patterns
    error_str = str(error).lower()
    if "429" in error_str or "rate limit" in error_str:
        return 429
    if "500" in error_str or "internal server error" in error_str:
        return 500
    if "502" in error_str or "bad gateway" in error_str:
        return 502
    if "503" in error_str or "service unavailable" in error_str:
        return 503
    if "504" in error_str or "gateway timeout" in error_str:
        return 504

    return None


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
) -> Callable[[F], F]:
    """Decorator for retrying functions with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay in seconds.
        exponential_base: Base for exponential backoff.
        jitter: Add random jitter to prevent thundering herd.

    Returns:
        Decorated function with retry logic.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Optional[Exception] = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # Check if this is a retryable error
                    status_code = _extract_status_code(e)

                    if status_code not in RETRYABLE_STATUS_CODES:
                        # Not retryable, re-raise immediately
                        raise

                    last_exception = e

                    if attempt == max_retries:
                        # No more retries
                        break

                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base**attempt), max_delay)

                    # Add jitter (0.5x to 1.5x)
                    if jitter:
                        delay = delay * (0.5 + random.random())

                    logger.warning(
                        f"Retryable error (status={status_code}), "
                        f"attempt {attempt + 1}/{max_retries + 1}, "
                        f"retrying in {delay:.2f}s: {e}"
                    )

                    time.sleep(delay)

            # Max retries exceeded
            raise MaxRetriesExceededError(
                f"Max retries ({max_retries}) exceeded for {func.__name__}",
                last_error=last_exception,
            )

        return wrapper  # type: ignore[return-value]

    return decorator


@dataclass
class ExternalMetadata:
    """Represents an external metadata object in Unity Catalog."""

    name: str
    system_type: str
    entity_type: str
    description: Optional[str] = None
    url: Optional[str] = None
    owner: Optional[str] = None
    properties: Dict[str, str] = field(default_factory=dict)

    def to_api_dict(self) -> Dict[str, Any]:
        """Convert to API request format."""
        data: Dict[str, Any] = {
            "name": self.name,
            "system_type": self.system_type,
            "entity_type": self.entity_type,
        }
        if self.description:
            data["description"] = self.description
        if self.url:
            data["url"] = self.url
        if self.owner:
            data["owner"] = self.owner
        if self.properties:
            data["properties"] = self.properties
        return data

    @classmethod
    def from_api_response(cls, data: Dict[str, Any]) -> ExternalMetadata:
        """Create from API response."""
        return cls(
            name=data["name"],
            system_type=data.get("system_type", "CUSTOM"),
            entity_type=data.get("entity_type", "table"),
            description=data.get("description"),
            url=data.get("url"),
            owner=data.get("owner"),
            properties=data.get("properties", {}),
        )


@dataclass
class LineageEdge:
    """Represents a lineage edge between entities."""

    source_entity: str  # External metadata name or UC table name
    target_entity: str  # UC table name or external metadata name
    source_type: str  # "external" or "table"
    target_type: str  # "table" or "external"


class UnityCatalogClient:
    """Client for Unity Catalog external metadata operations.

    Note: The external lineage API is in public preview as of January 2026.
    This implementation uses the Databricks SDK and REST API where needed.
    """

    MANAGED_BY = "dbt-unity-lineage"
    DEFAULT_MAX_RETRIES = 3
    DEFAULT_BASE_DELAY = 1.0
    DEFAULT_MAX_DELAY = 60.0

    def __init__(
        self,
        connection: DatabricksConnection,
        max_retries: int = DEFAULT_MAX_RETRIES,
        base_delay: float = DEFAULT_BASE_DELAY,
        max_delay: float = DEFAULT_MAX_DELAY,
    ) -> None:
        """Initialize the Unity Catalog client.

        Args:
            connection: Databricks connection details.
            max_retries: Maximum number of retry attempts for transient errors.
            base_delay: Initial delay in seconds for retry backoff.
            max_delay: Maximum delay in seconds for retry backoff.
        """
        self.connection = connection
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self._client = WorkspaceClient(
            host=connection.workspace_url,
            token=connection.token,
        )

    @property
    def catalog(self) -> str:
        """Get the catalog name."""
        return self.connection.catalog

    def _make_ownership_properties(
        self,
        dbt_project: str,
        identifier: str,
        identifier_type: str,
    ) -> Dict[str, str]:
        """Create ownership tracking properties.

        Args:
            dbt_project: The dbt project name.
            identifier: The source/exposure identifier.
            identifier_type: Either "source" or "exposure".

        Returns:
            Properties dict for ownership tracking.
        """
        now = datetime.now(timezone.utc).isoformat()
        props = {
            "managed_by": self.MANAGED_BY,
            "dbt_project": dbt_project,
            f"dbt_{identifier_type}": identifier,
            "updated_at": now,
        }
        return props

    def _api_call_with_retry(
        self,
        method: str,
        path: str,
        query: Optional[Dict[str, str]] = None,
        body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an API call with retry logic for transient errors.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE).
            path: API path.
            query: Query parameters.
            body: Request body.

        Returns:
            API response as dictionary.

        Raises:
            MaxRetriesExceededError: If max retries exceeded for retryable errors.
            Exception: For non-retryable errors.
        """
        last_exception: Optional[Exception] = None

        for attempt in range(self.max_retries + 1):
            try:
                kwargs: Dict[str, Any] = {}
                if query:
                    kwargs["query"] = query
                if body:
                    kwargs["body"] = body

                result = self._client.api_client.do(method, path, **kwargs)
                return result if result is not None else {}

            except Exception as e:
                status_code = _extract_status_code(e)

                if status_code not in RETRYABLE_STATUS_CODES:
                    # Not retryable, re-raise immediately
                    raise

                last_exception = e

                if attempt == self.max_retries:
                    break

                # Calculate delay with exponential backoff and jitter
                delay = min(self.base_delay * (2**attempt), self.max_delay)
                delay = delay * (0.5 + random.random())

                logger.warning(
                    f"API call failed (status={status_code}), "
                    f"attempt {attempt + 1}/{self.max_retries + 1}, "
                    f"retrying in {delay:.2f}s: {e}"
                )

                time.sleep(delay)

        raise MaxRetriesExceededError(
            f"Max retries ({self.max_retries}) exceeded for {method} {path}",
            last_error=last_exception,
        )

    def list_external_metadata(
        self,
        dbt_project: Optional[str] = None,
    ) -> List[ExternalMetadata]:
        """List external metadata objects.

        Args:
            dbt_project: Optional filter by dbt project.

        Returns:
            List of external metadata objects.
        """
        try:
            response = self._api_call_with_retry(
                "GET",
                "/api/2.1/unity-catalog/external-metadata",
                query={"catalog_name": self.catalog},
            )
            items = response.get("external_metadata", [])
        except MaxRetriesExceededError:
            logger.error("Failed to list external metadata after retries")
            raise
        except Exception as e:
            # API may not be available yet or have different path
            logger.debug(f"list_external_metadata failed: {e}")
            return []

        result = []
        for item in items:
            metadata = ExternalMetadata.from_api_response(item)

            # Filter by managed_by
            if metadata.properties.get("managed_by") != self.MANAGED_BY:
                continue

            # Filter by dbt_project if specified
            if dbt_project and metadata.properties.get("dbt_project") != dbt_project:
                continue

            result.append(metadata)

        return result

    def get_external_metadata(self, name: str) -> Optional[ExternalMetadata]:
        """Get a single external metadata object by name.

        Args:
            name: The name of the external metadata object.

        Returns:
            The external metadata object, or None if not found.
        """
        try:
            response = self._api_call_with_retry(
                "GET",
                f"/api/2.1/unity-catalog/external-metadata/{name}",
                query={"catalog_name": self.catalog},
            )
            return ExternalMetadata.from_api_response(response)
        except Exception as e:
            # Not found or other error
            logger.debug(f"get_external_metadata failed: {e}")
            return None

    def create_external_metadata(
        self,
        metadata: ExternalMetadata,
        dbt_project: Optional[str] = None,
        identifier: Optional[str] = None,
        identifier_type: Optional[str] = None,
    ) -> ExternalMetadata:
        """Create an external metadata object.

        Args:
            metadata: The external metadata to create (properties should already
                      include ownership tracking if needed).
            dbt_project: Optional dbt project name (for backward compatibility).
            identifier: Optional source/exposure identifier (for backward compatibility).
            identifier_type: Optional "source" or "exposure" (for backward compatibility).

        Returns:
            The created external metadata object.
        """
        # Add ownership properties if provided (backward compatibility)
        if dbt_project and identifier and identifier_type:
            ownership_props = self._make_ownership_properties(
                dbt_project, identifier, identifier_type
            )
            metadata.properties.update(ownership_props)
            metadata.properties["created_at"] = metadata.properties["updated_at"]

        # Use REST API with retry
        request_data = metadata.to_api_dict()
        request_data["catalog_name"] = self.catalog

        try:
            response = self._api_call_with_retry(
                "POST",
                "/api/2.1/unity-catalog/external-metadata",
                body=request_data,
            )
            return ExternalMetadata.from_api_response(response)
        except MaxRetriesExceededError:
            logger.error(f"Failed to create external metadata '{metadata.name}' after retries")
            raise
        except Exception as e:
            logger.error(f"Failed to create external metadata '{metadata.name}': {e}")
            raise

    def update_external_metadata(
        self,
        metadata: ExternalMetadata,
        dbt_project: Optional[str] = None,
        identifier: Optional[str] = None,
        identifier_type: Optional[str] = None,
    ) -> ExternalMetadata:
        """Update an external metadata object.

        Args:
            metadata: The external metadata to update (properties should already
                      include ownership tracking if needed).
            dbt_project: Optional dbt project name (for backward compatibility).
            identifier: Optional source/exposure identifier (for backward compatibility).
            identifier_type: Optional "source" or "exposure" (for backward compatibility).

        Returns:
            The updated external metadata object.
        """
        # Update ownership properties if provided (backward compatibility)
        if dbt_project and identifier and identifier_type:
            ownership_props = self._make_ownership_properties(
                dbt_project, identifier, identifier_type
            )
            # Don't overwrite created_at
            if "created_at" in metadata.properties:
                ownership_props.pop("created_at", None)
            metadata.properties.update(ownership_props)

        # Use REST API with retry
        request_data = metadata.to_api_dict()
        request_data["catalog_name"] = self.catalog

        try:
            response = self._api_call_with_retry(
                "PATCH",
                f"/api/2.1/unity-catalog/external-metadata/{metadata.name}",
                body=request_data,
            )
            return ExternalMetadata.from_api_response(response)
        except MaxRetriesExceededError:
            logger.error(f"Failed to update external metadata '{metadata.name}' after retries")
            raise
        except Exception as e:
            logger.error(f"Failed to update external metadata '{metadata.name}': {e}")
            raise

    def delete_external_metadata(self, name: str) -> None:
        """Delete an external metadata object.

        Args:
            name: The name of the external metadata to delete.

        Raises:
            MaxRetriesExceededError: If max retries exceeded for retryable errors.
            Exception: For non-retryable errors.
        """
        try:
            self._api_call_with_retry(
                "DELETE",
                f"/api/2.1/unity-catalog/external-metadata/{name}",
                query={"catalog_name": self.catalog},
            )
        except MaxRetriesExceededError:
            logger.error(f"Failed to delete external metadata '{name}' after retries")
            raise
        except Exception as e:
            logger.error(f"Failed to delete external metadata '{name}': {e}")
            raise

    def create_lineage_edge(self, edge: LineageEdge) -> None:
        """Create a lineage edge between entities.

        Args:
            edge: The lineage edge to create.

        Raises:
            MaxRetriesExceededError: If max retries exceeded for retryable errors.
            Exception: For non-retryable errors.
        """
        # Build the lineage request based on direction
        request_data: Dict[str, str] = {
            "catalog_name": self.catalog,
        }

        if edge.source_type == "external":
            request_data["source_external_metadata"] = edge.source_entity
            request_data["target_table"] = edge.target_entity
        else:
            request_data["source_table"] = edge.source_entity
            request_data["target_external_metadata"] = edge.target_entity

        try:
            self._api_call_with_retry(
                "POST",
                "/api/2.1/unity-catalog/lineage/external-edges",
                body=request_data,
            )
        except MaxRetriesExceededError:
            logger.error(
                f"Failed to create lineage edge {edge.source_entity} -> "
                f"{edge.target_entity} after retries"
            )
            raise
        except Exception as e:
            logger.debug(f"Failed to create lineage edge: {e}")
            raise

    def delete_lineage_edge(self, edge: LineageEdge) -> None:
        """Delete a lineage edge.

        Args:
            edge: The lineage edge to delete.

        Raises:
            MaxRetriesExceededError: If max retries exceeded for retryable errors.
            Exception: For non-retryable errors.
        """
        request_data: Dict[str, str] = {
            "catalog_name": self.catalog,
        }

        if edge.source_type == "external":
            request_data["source_external_metadata"] = edge.source_entity
            request_data["target_table"] = edge.target_entity
        else:
            request_data["source_table"] = edge.source_entity
            request_data["target_external_metadata"] = edge.target_entity

        try:
            self._api_call_with_retry(
                "DELETE",
                "/api/2.1/unity-catalog/lineage/external-edges",
                body=request_data,
            )
        except MaxRetriesExceededError:
            logger.error(
                f"Failed to delete lineage edge {edge.source_entity} -> "
                f"{edge.target_entity} after retries"
            )
            raise
        except Exception as e:
            logger.debug(f"Failed to delete lineage edge: {e}")
            raise

    def list_lineage_edges(
        self,
        entity_name: str,
        entity_type: str,
    ) -> List[LineageEdge]:
        """List lineage edges for an entity.

        Args:
            entity_name: The entity name.
            entity_type: Either "external" or "table".

        Returns:
            List of lineage edges.
        """
        query: Dict[str, str] = {"catalog_name": self.catalog}

        if entity_type == "external":
            query["external_metadata_name"] = entity_name
        else:
            query["table_name"] = entity_name

        try:
            response = self._api_call_with_retry(
                "GET",
                "/api/2.1/unity-catalog/lineage/external-edges",
                query=query,
            )
            raw_edges = response.get("edges", [])
        except MaxRetriesExceededError:
            logger.error(f"Failed to list lineage edges for '{entity_name}' after retries")
            raise
        except Exception as e:
            logger.debug(f"list_lineage_edges failed: {e}")
            return []

        edges = []
        for raw_edge in raw_edges:
            source_ext = raw_edge.get("source_external_metadata")
            source_table = raw_edge.get("source_table")
            target_ext = raw_edge.get("target_external_metadata")
            target_table = raw_edge.get("target_table")

            if source_ext:
                edges.append(
                    LineageEdge(
                        source_entity=source_ext,
                        target_entity=target_table or "",
                        source_type="external",
                        target_type="table",
                    )
                )
            elif target_ext:
                edges.append(
                    LineageEdge(
                        source_entity=source_table or "",
                        target_entity=target_ext,
                        source_type="table",
                        target_type="external",
                    )
                )

        return edges
