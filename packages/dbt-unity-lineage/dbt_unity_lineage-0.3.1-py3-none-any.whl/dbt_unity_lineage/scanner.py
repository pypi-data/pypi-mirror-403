"""Folder scanning for dbt sources and exposures YAML files."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from .config import Config, SourceSystemConfig


@dataclass
class SourceTable:
    """A source table from a _sources.yml file."""

    name: str
    source_name: str
    description: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)
    columns: List[Dict[str, Any]] = field(default_factory=list)
    # File location for error reporting
    file_path: Optional[Path] = None
    # Layer and folder info
    layer: Optional[str] = None
    folder: Optional[str] = None

    @property
    def uc_source(self) -> Optional[str]:
        """Get the uc_source from meta."""
        return self.meta.get("uc_source")

    @property
    def qualified_name(self) -> str:
        """Get the fully qualified source.table name."""
        return f"{self.source_name}.{self.name}"

    @property
    def column_names(self) -> List[str]:
        """Get list of column names."""
        return [col.get("name", "") for col in self.columns if col.get("name")]


@dataclass
class Source:
    """A source (collection of tables) from a _sources.yml file."""

    name: str
    description: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)
    tables: List[SourceTable] = field(default_factory=list)
    # File location for error reporting
    file_path: Optional[Path] = None
    # Layer and folder info
    layer: Optional[str] = None
    folder: Optional[str] = None

    @property
    def uc_source(self) -> Optional[str]:
        """Get the uc_source from meta at the source level."""
        return self.meta.get("uc_source")


@dataclass
class ExposureOwner:
    """Owner information for an exposure."""

    name: Optional[str] = None
    email: Optional[str] = None


@dataclass
class Exposure:
    """An exposure from a _exposures.yml file."""

    name: str
    type: str
    description: Optional[str] = None
    url: Optional[str] = None
    owner: Optional[ExposureOwner] = None
    meta: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    # File location for error reporting
    file_path: Optional[Path] = None
    # Layer and folder info
    layer: Optional[str] = None
    folder: Optional[str] = None

    @property
    def uc_system_type(self) -> Optional[str]:
        """Get explicit system type override from meta."""
        return self.meta.get("uc_system_type")


@dataclass
class ScanResult:
    """Result of scanning folders for sources and exposures."""

    sources: List[Source] = field(default_factory=list)
    exposures: List[Exposure] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def all_source_tables(self) -> List[SourceTable]:
        """Get all source tables across all sources."""
        tables = []
        for source in self.sources:
            tables.extend(source.tables)
        return tables

    @property
    def source_count(self) -> int:
        """Get total number of source tables."""
        return len(self.all_source_tables)

    @property
    def exposure_count(self) -> int:
        """Get total number of exposures."""
        return len(self.exposures)


# File patterns to scan for
SOURCE_FILE_PATTERNS = ["_sources.yml", "sources.yml", "_sources.yaml", "sources.yaml"]
EXPOSURE_FILE_PATTERNS = ["_exposures.yml", "exposures.yml", "_exposures.yaml", "exposures.yaml"]
SCHEMA_FILE_PATTERNS = ["schema.yml", "schema.yaml", "_schema.yml", "_schema.yaml"]


def scan_folder(
    folder_path: Path,
    scan_type: str = "all",
    layer: Optional[str] = None,
) -> ScanResult:
    """Scan a single folder for sources and/or exposures.

    Args:
        folder_path: Path to the folder to scan.
        scan_type: What to scan for: 'sources', 'exposures', or 'all'.
        layer: Optional layer name for context.

    Returns:
        ScanResult with found sources and exposures.
    """
    result = ScanResult()

    if not folder_path.exists():
        result.warnings.append(f"Folder does not exist: {folder_path}")
        return result

    if not folder_path.is_dir():
        result.errors.append(f"Not a directory: {folder_path}")
        return result

    folder_str = str(folder_path)

    # Scan for sources
    if scan_type in ("sources", "all"):
        for pattern in SOURCE_FILE_PATTERNS:
            file_path = folder_path / pattern
            if file_path.exists():
                sources, errors = _parse_sources_file(file_path, layer, folder_str)
                result.sources.extend(sources)
                result.errors.extend(errors)

        # Also check schema files for sources
        for pattern in SCHEMA_FILE_PATTERNS:
            file_path = folder_path / pattern
            if file_path.exists():
                sources, errors = _parse_sources_file(file_path, layer, folder_str)
                result.sources.extend(sources)
                result.errors.extend(errors)

    # Scan for exposures
    if scan_type in ("exposures", "all"):
        for pattern in EXPOSURE_FILE_PATTERNS:
            file_path = folder_path / pattern
            if file_path.exists():
                exposures, errors = _parse_exposures_file(file_path, layer, folder_str)
                result.exposures.extend(exposures)
                result.errors.extend(errors)

        # Also check schema files for exposures
        for pattern in SCHEMA_FILE_PATTERNS:
            file_path = folder_path / pattern
            if file_path.exists():
                exposures, errors = _parse_exposures_file(file_path, layer, folder_str)
                result.exposures.extend(exposures)
                result.errors.extend(errors)

    return result


def _parse_sources_file(
    file_path: Path,
    layer: Optional[str],
    folder: Optional[str],
) -> tuple[List[Source], List[str]]:
    """Parse a sources YAML file.

    Args:
        file_path: Path to the YAML file.
        layer: Optional layer name.
        folder: Optional folder path.

    Returns:
        Tuple of (sources list, errors list).
    """
    sources: List[Source] = []
    errors: List[str] = []

    try:
        with open(file_path) as f:
            content = yaml.safe_load(f)
    except yaml.YAMLError as e:
        errors.append(f"YAML parse error in {file_path}: {e}")
        return sources, errors
    except Exception as e:
        errors.append(f"Error reading {file_path}: {e}")
        return sources, errors

    if content is None:
        return sources, errors

    # Handle dbt schema format (sources key at top level)
    raw_sources = content.get("sources", [])
    if not isinstance(raw_sources, list):
        return sources, errors

    for source_data in raw_sources:
        if not isinstance(source_data, dict):
            continue

        source_name = source_data.get("name", "")
        if not source_name:
            errors.append(f"Source missing 'name' in {file_path}")
            continue

        source_meta = source_data.get("meta", {})
        source_description = source_data.get("description")

        tables: List[SourceTable] = []
        raw_tables = source_data.get("tables", [])
        if isinstance(raw_tables, list):
            for table_data in raw_tables:
                if not isinstance(table_data, dict):
                    continue

                table_name = table_data.get("name", "")
                if not table_name:
                    errors.append(f"Table missing 'name' in source '{source_name}' in {file_path}")
                    continue

                # Table meta inherits from source meta, with table-level overrides
                table_meta = {**source_meta, **table_data.get("meta", {})}

                tables.append(
                    SourceTable(
                        name=table_name,
                        source_name=source_name,
                        description=table_data.get("description"),
                        meta=table_meta,
                        columns=table_data.get("columns", []),
                        file_path=file_path,
                        layer=layer,
                        folder=folder,
                    )
                )

        sources.append(
            Source(
                name=source_name,
                description=source_description,
                meta=source_meta,
                tables=tables,
                file_path=file_path,
                layer=layer,
                folder=folder,
            )
        )

    return sources, errors


def _parse_exposures_file(
    file_path: Path,
    layer: Optional[str],
    folder: Optional[str],
) -> tuple[List[Exposure], List[str]]:
    """Parse an exposures YAML file.

    Args:
        file_path: Path to the YAML file.
        layer: Optional layer name.
        folder: Optional folder path.

    Returns:
        Tuple of (exposures list, errors list).
    """
    exposures: List[Exposure] = []
    errors: List[str] = []

    try:
        with open(file_path) as f:
            content = yaml.safe_load(f)
    except yaml.YAMLError as e:
        errors.append(f"YAML parse error in {file_path}: {e}")
        return exposures, errors
    except Exception as e:
        errors.append(f"Error reading {file_path}: {e}")
        return exposures, errors

    if content is None:
        return exposures, errors

    # Handle dbt schema format (exposures key at top level)
    raw_exposures = content.get("exposures", [])
    if not isinstance(raw_exposures, list):
        return exposures, errors

    for exposure_data in raw_exposures:
        if not isinstance(exposure_data, dict):
            continue

        name = exposure_data.get("name", "")
        if not name:
            errors.append(f"Exposure missing 'name' in {file_path}")
            continue

        exposure_type = exposure_data.get("type", "")
        if not exposure_type:
            errors.append(f"Exposure '{name}' missing 'type' in {file_path}")
            continue

        # Parse owner
        owner_data = exposure_data.get("owner", {})
        owner = None
        if owner_data:
            owner = ExposureOwner(
                name=owner_data.get("name"),
                email=owner_data.get("email"),
            )

        # Parse depends_on - can be list of strings (refs) or dict with nodes key
        depends_on: List[str] = []
        raw_depends = exposure_data.get("depends_on", [])
        if isinstance(raw_depends, list):
            depends_on = raw_depends
        elif isinstance(raw_depends, dict):
            depends_on = raw_depends.get("nodes", [])

        exposures.append(
            Exposure(
                name=name,
                type=exposure_type,
                description=exposure_data.get("description"),
                url=exposure_data.get("url"),
                owner=owner,
                meta=exposure_data.get("meta", {}),
                depends_on=depends_on,
                file_path=file_path,
                layer=layer,
                folder=folder,
            )
        )

    return exposures, errors


def scan_config(
    config: Config,
    project_dir: Optional[Union[Path, str]] = None,
    select: Optional[str] = None,
    scan_type: str = "all",
) -> ScanResult:
    """Scan all folders configured in the config.

    Args:
        config: The loaded configuration.
        project_dir: Base directory for relative paths.
        select: Optional select pattern (e.g., 'bronze/*', 'bronze/erp').
        scan_type: What to scan for: 'sources', 'exposures', or 'all'.

    Returns:
        ScanResult with all found sources and exposures.
    """
    result = ScanResult()
    base_dir = Path(project_dir) if project_dir else Path.cwd()

    for layer_name, layer_config in config.configuration.layers.items():
        # Check if this layer matches the select pattern
        if select and not _matches_select(layer_name, "", select):
            # Check individual folders
            pass  # Will check each folder individually

        # Scan source folders
        if scan_type in ("sources", "all"):
            for folder in layer_config.source_folders:
                if select and not _matches_select(layer_name, folder, select):
                    continue

                folder_path = base_dir / folder
                folder_result = scan_folder(folder_path, "sources", layer_name)
                result.sources.extend(folder_result.sources)
                result.errors.extend(folder_result.errors)
                result.warnings.extend(folder_result.warnings)

        # Scan exposure folders
        if scan_type in ("exposures", "all"):
            for folder in layer_config.exposure_folders:
                if select and not _matches_select(layer_name, folder, select):
                    continue

                folder_path = base_dir / folder
                folder_result = scan_folder(folder_path, "exposures", layer_name)
                result.exposures.extend(folder_result.exposures)
                result.errors.extend(folder_result.errors)
                result.warnings.extend(folder_result.warnings)

    return result


def _matches_select(layer: str, folder: str, pattern: str) -> bool:
    """Check if a layer/folder matches a select pattern.

    Patterns:
    - 'bronze/*' - matches all folders in bronze layer
    - 'bronze/erp' - matches specific folder path
    - '*/erp' - matches folder across all layers
    - 'bronze/erp/*' - matches folder and subfolders

    Args:
        layer: Layer name.
        folder: Folder path (as configured, e.g., "bronze/erp").
        pattern: Select pattern.

    Returns:
        True if the layer/folder matches the pattern.
    """
    import fnmatch

    pattern_parts = pattern.split("/")

    # Check if pattern matches the folder directly
    if fnmatch.fnmatch(folder, pattern):
        return True

    # Check if pattern starts with layer name
    if pattern_parts[0] == layer or pattern_parts[0] == "*":
        # Match against folder
        if len(pattern_parts) == 1:
            # Just layer name - check if folder is in this layer
            return folder.startswith(f"{layer}/") or folder == layer

        # Build pattern for the folder
        folder_pattern = "/".join(pattern_parts)
        if pattern_parts[0] == "*":
            # Replace * with the layer name for matching
            folder_pattern = f"{layer}/" + "/".join(pattern_parts[1:])

        return fnmatch.fnmatch(folder, folder_pattern)

    return False


def get_missing_source_systems(
    scan_result: ScanResult,
    config: Config,
) -> Dict[str, List[SourceTable]]:
    """Find sources that reference undefined source_systems.

    Args:
        scan_result: The scan result with sources.
        config: The configuration with source_systems.

    Returns:
        Dict mapping undefined uc_source values to the tables referencing them.
    """
    missing: Dict[str, List[SourceTable]] = {}

    for table in scan_result.all_source_tables:
        uc_source = table.uc_source
        if uc_source and uc_source not in config.source_systems:
            if uc_source not in missing:
                missing[uc_source] = []
            missing[uc_source].append(table)

    return missing


def get_source_system_for_table(
    table: SourceTable,
    config: Config,
) -> Optional[SourceSystemConfig]:
    """Get the source system configuration for a source table.

    Args:
        table: The source table.
        config: The configuration.

    Returns:
        The source system config, or None if not found.
    """
    uc_source = table.uc_source
    if uc_source:
        return config.source_systems.get(uc_source)
    return None
