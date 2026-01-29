"""dbt manifest.json parsing for sources and exposures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class SourceTable(BaseModel):
    """A source table from the manifest."""

    model_config = ConfigDict(populate_by_name=True)

    unique_id: str
    name: str
    source_name: str
    description: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)
    database: Optional[str] = None
    schema_: Optional[str] = Field(default=None, alias="schema")
    identifier: Optional[str] = None

    @property
    def uc_source(self) -> Optional[str]:
        """Get the uc_source from meta, checking both source-level and table-level."""
        return self.meta.get("uc_source")

    @property
    def qualified_name(self) -> str:
        """Get the fully qualified source.table name."""
        return f"{self.source_name}.{self.name}"

    @property
    def uc_table_name(self) -> Optional[str]:
        """Get the Unity Catalog table name (catalog.schema.table)."""
        if self.database and self.schema_:
            table = self.identifier or self.name
            return f"{self.database}.{self.schema_}.{table}"
        return None


class ExposureOwner(BaseModel):
    """Owner information for an exposure."""

    name: Optional[str] = None
    email: Optional[str] = None


class Exposure(BaseModel):
    """An exposure from the manifest."""

    unique_id: str
    name: str
    type: str
    description: Optional[str] = None
    url: Optional[str] = None
    owner: Optional[ExposureOwner] = None
    meta: Dict[str, Any] = Field(default_factory=dict)
    depends_on: Dict[str, List[str]] = Field(default_factory=dict)

    @property
    def uc_system_type(self) -> Optional[str]:
        """Get explicit system type override from meta."""
        return self.meta.get("uc_system_type")

    @property
    def depends_on_nodes(self) -> List[str]:
        """Get list of node unique_ids this exposure depends on."""
        return self.depends_on.get("nodes", [])


class Model(BaseModel):
    """A model from the manifest (for resolving exposure dependencies)."""

    model_config = ConfigDict(populate_by_name=True)

    unique_id: str
    name: str
    database: Optional[str] = None
    schema_: Optional[str] = Field(default=None, alias="schema")
    alias: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)

    @property
    def uc_source(self) -> Optional[str]:
        """Get uc_source from meta if this model represents an external source."""
        return self.meta.get("uc_source")

    @property
    def uc_table_name(self) -> Optional[str]:
        """Get the Unity Catalog table name (catalog.schema.table)."""
        if self.database and self.schema_:
            table = self.alias or self.name
            return f"{self.database}.{self.schema_}.{table}"
        return None


class ManifestMetadata(BaseModel):
    """Metadata from the manifest."""

    project_name: Optional[str] = None
    project_id: Optional[str] = None
    dbt_version: Optional[str] = None


class Manifest(BaseModel):
    """Parsed dbt manifest with relevant data."""

    metadata: ManifestMetadata
    sources: Dict[str, SourceTable] = Field(default_factory=dict)
    exposures: Dict[str, Exposure] = Field(default_factory=dict)
    models: Dict[str, Model] = Field(default_factory=dict)

    @property
    def project_name(self) -> str:
        """Get the project name from metadata."""
        return self.metadata.project_name or "unknown"


def load_manifest(manifest_path: Union[Path, str]) -> Manifest:
    """Load and parse the dbt manifest.json file.

    Args:
        manifest_path: Path to manifest.json.

    Returns:
        Parsed Manifest object.

    Raises:
        FileNotFoundError: If the manifest file doesn't exist.
        ValueError: If the manifest is invalid.
    """
    manifest_path = Path(manifest_path)

    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

    with open(manifest_path) as f:
        raw_manifest = json.load(f)

    return parse_manifest(raw_manifest)


def load_manifest_from_dict(raw_manifest: Dict[str, Any]) -> Manifest:
    """Load and parse a manifest from a dictionary.

    This is useful when the manifest is fetched from dbt Cloud or other sources.

    Args:
        raw_manifest: The raw manifest data as a dictionary.

    Returns:
        Parsed Manifest object.
    """
    return parse_manifest(raw_manifest)


def parse_manifest(raw_manifest: Dict[str, Any]) -> Manifest:
    """Parse a raw manifest dictionary into a Manifest object.

    Args:
        raw_manifest: The raw manifest data.

    Returns:
        Parsed Manifest object.
    """
    # Parse metadata
    raw_metadata = raw_manifest.get("metadata", {})
    metadata = ManifestMetadata(
        project_name=raw_metadata.get("project_name"),
        project_id=raw_metadata.get("project_id"),
        dbt_version=raw_metadata.get("dbt_version"),
    )

    # Parse sources
    sources: Dict[str, SourceTable] = {}
    raw_sources = raw_manifest.get("sources", {})
    for source_id, source_data in raw_sources.items():
        # Handle source-level meta inheritance
        source_meta = source_data.get("source_meta", {})
        table_meta = source_data.get("meta", {})
        # Merge: table meta overrides source meta
        merged_meta = {**source_meta, **table_meta}

        sources[source_id] = SourceTable(
            unique_id=source_id,
            name=source_data.get("name", ""),
            source_name=source_data.get("source_name", ""),
            description=source_data.get("description"),
            meta=merged_meta,
            database=source_data.get("database"),
            schema=source_data.get("schema"),
            identifier=source_data.get("identifier"),
        )

    # Parse exposures
    exposures: Dict[str, Exposure] = {}
    raw_exposures = raw_manifest.get("exposures", {})
    for exposure_id, exposure_data in raw_exposures.items():
        owner_data = exposure_data.get("owner", {})
        owner = None
        if owner_data:
            owner = ExposureOwner(
                name=owner_data.get("name"),
                email=owner_data.get("email"),
            )

        exposures[exposure_id] = Exposure(
            unique_id=exposure_id,
            name=exposure_data.get("name", ""),
            type=exposure_data.get("type", ""),
            description=exposure_data.get("description"),
            url=exposure_data.get("url"),
            owner=owner,
            meta=exposure_data.get("meta", {}),
            depends_on=exposure_data.get("depends_on", {}),
        )

    # Parse models (for resolving exposure dependencies)
    models: Dict[str, Model] = {}
    raw_nodes = raw_manifest.get("nodes", {})
    for node_id, node_data in raw_nodes.items():
        if node_data.get("resource_type") == "model":
            models[node_id] = Model(
                unique_id=node_id,
                name=node_data.get("name", ""),
                database=node_data.get("database"),
                schema=node_data.get("schema"),
                alias=node_data.get("alias"),
                meta=node_data.get("meta", {}),
            )

    return Manifest(
        metadata=metadata,
        sources=sources,
        exposures=exposures,
        models=models,
    )


def find_manifest_file(project_dir: Optional[Union[Path, str]] = None) -> Optional[Path]:
    """Find the manifest.json file.

    Searches in order:
    1. project_dir/target/manifest.json
    2. ./target/manifest.json

    Args:
        project_dir: Optional project directory to search in.

    Returns:
        Path to the manifest file, or None if not found.
    """
    search_paths = []

    if project_dir:
        search_paths.append(Path(project_dir) / "target" / "manifest.json")

    search_paths.append(Path.cwd() / "target" / "manifest.json")

    for path in search_paths:
        if path.exists():
            return path

    return None


def get_sources_with_uc_source(
    manifest: Manifest,
    source_paths: Optional[List[str]] = None,
) -> List[SourceTable]:
    """Get sources that have the uc_source meta tag.

    Args:
        manifest: The parsed manifest.
        source_paths: Optional list of source paths to filter by.

    Returns:
        List of SourceTable objects with uc_source defined.
    """
    sources = []
    for source in manifest.sources.values():
        if source.uc_source:
            # If source_paths specified, check if source is in one of those paths
            if source_paths:
                # For now, we don't filter by path - would need file_path info
                pass
            sources.append(source)
    return sources


def get_models_with_uc_source(manifest: Manifest) -> List[Model]:
    """Get models that have the uc_source meta tag.

    These are typically bronze models that represent external sources.

    Args:
        manifest: The parsed manifest.

    Returns:
        List of Model objects with uc_source defined.
    """
    return [model for model in manifest.models.values() if model.uc_source]


def resolve_exposure_dependencies(
    manifest: Manifest,
    exposure: Exposure,
) -> List[str]:
    """Resolve the UC table names that an exposure depends on.

    Args:
        manifest: The parsed manifest.
        exposure: The exposure to resolve dependencies for.

    Returns:
        List of Unity Catalog table names (catalog.schema.table).
    """
    uc_tables = []
    for node_id in exposure.depends_on_nodes:
        # Check if it's a model
        if node_id in manifest.models:
            model = manifest.models[node_id]
            if model.uc_table_name:
                uc_tables.append(model.uc_table_name)
        # Check if it's a source
        elif node_id in manifest.sources:
            source = manifest.sources[node_id]
            if source.uc_table_name:
                uc_tables.append(source.uc_table_name)
    return uc_tables
