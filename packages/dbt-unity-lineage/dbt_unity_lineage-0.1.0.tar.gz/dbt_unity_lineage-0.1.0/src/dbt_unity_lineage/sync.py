"""Core sync logic for dbt-unity-lineage."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional

from .config import Config, SourceSystemConfig
from .manifest import (
    Exposure,
    Manifest,
    SourceTable,
    get_models_with_uc_source,
    get_sources_with_uc_source,
    resolve_exposure_dependencies,
)
from .mapping import (
    get_entity_type_for_exposure,
    infer_system_type_from_url,
    normalize_system_type,
)
from .unity_catalog import ExternalMetadata, LineageEdge, UnityCatalogClient

logger = logging.getLogger(__name__)

# Type for progress callback: (current: int, total: int, item_name: str) -> None
ProgressCallback = Optional[Callable[[int, int, str], None]]


class StrictModeError(Exception):
    """Raised when an error occurs in strict mode."""

    def __init__(self, item_name: str, error: str):
        super().__init__(f"Failed to process '{item_name}': {error}")
        self.item_name = item_name
        self.error = error


class SyncStatus(str, Enum):
    """Status of a sync item."""

    IN_SYNC = "in_sync"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    SKIP = "skip"
    ERROR = "error"


@dataclass
class SyncItem:
    """An item to be synced."""

    name: str
    identifier: str  # Source qualified name or exposure name
    system_type: str
    entity_type: str
    status: SyncStatus
    item_type: str  # "source" or "exposure"
    desired: Optional[ExternalMetadata] = None
    current: Optional[ExternalMetadata] = None
    error: Optional[str] = None
    lineage_edges: List[LineageEdge] = field(default_factory=list)


@dataclass
class SyncPlan:
    """A plan for syncing changes to Unity Catalog."""

    project_name: str
    catalog: str
    items: List[SyncItem] = field(default_factory=list)

    @property
    def sources(self) -> List[SyncItem]:
        """Get source items."""
        return [i for i in self.items if i.item_type == "source"]

    @property
    def exposures(self) -> List[SyncItem]:
        """Get exposure items."""
        return [i for i in self.items if i.item_type == "exposure"]

    @property
    def to_create(self) -> List[SyncItem]:
        """Items to create."""
        return [i for i in self.items if i.status == SyncStatus.CREATE]

    @property
    def to_update(self) -> List[SyncItem]:
        """Items to update."""
        return [i for i in self.items if i.status == SyncStatus.UPDATE]

    @property
    def to_delete(self) -> List[SyncItem]:
        """Items to delete."""
        return [i for i in self.items if i.status == SyncStatus.DELETE]

    @property
    def in_sync(self) -> List[SyncItem]:
        """Items in sync."""
        return [i for i in self.items if i.status == SyncStatus.IN_SYNC]

    @property
    def skipped(self) -> List[SyncItem]:
        """Skipped items."""
        return [i for i in self.items if i.status == SyncStatus.SKIP]

    @property
    def errors(self) -> List[SyncItem]:
        """Items with errors."""
        return [i for i in self.items if i.status == SyncStatus.ERROR]

    def summary(self) -> Dict[str, int]:
        """Get summary counts."""
        return {
            "in_sync": len(self.in_sync),
            "create": len(self.to_create),
            "update": len(self.to_update),
            "delete": len(self.to_delete),
            "skipped": len(self.skipped),
            "errors": len(self.errors),
        }


def _make_external_name(project: str, *parts: str) -> str:
    """Create an external metadata object name.

    Format: {project}__{part1}__{part2}...
    """
    all_parts = [project] + list(parts)
    return "__".join(all_parts)


def _build_source_metadata(
    project: str,
    source: SourceTable,
    config: SourceSystemConfig,
) -> ExternalMetadata:
    """Build external metadata for a source.

    Args:
        project: The dbt project name.
        source: The source table from manifest.
        config: The source system configuration.

    Returns:
        ExternalMetadata object.
    """
    name = _make_external_name(project, source.uc_source or "", source.qualified_name)

    # Start with config properties
    properties = dict(config.properties)

    return ExternalMetadata(
        name=name,
        system_type=config.system_type,
        entity_type=config.entity_type,
        description=source.description or config.description,
        url=config.url,
        owner=config.owner,
        properties=properties,
    )


def _build_exposure_metadata(
    project: str,
    exposure: Exposure,
) -> ExternalMetadata:
    """Build external metadata for an exposure.

    Args:
        project: The dbt project name.
        exposure: The exposure from manifest.

    Returns:
        ExternalMetadata object.
    """
    name = _make_external_name(project, exposure.name)

    # Determine system type
    if exposure.uc_system_type:
        system_type = normalize_system_type(exposure.uc_system_type)
    else:
        system_type = infer_system_type_from_url(exposure.url)

    # Determine entity type
    entity_type = get_entity_type_for_exposure(exposure.type)

    # Get owner
    owner = None
    if exposure.owner:
        owner = exposure.owner.email or exposure.owner.name

    return ExternalMetadata(
        name=name,
        system_type=system_type.value,
        entity_type=entity_type,
        description=exposure.description,
        url=exposure.url,
        owner=owner,
        properties={},
    )


def _metadata_differs(desired: ExternalMetadata, current: ExternalMetadata) -> bool:
    """Check if two metadata objects differ (ignoring ownership properties)."""
    # Compare core fields
    if desired.system_type != current.system_type:
        return True
    if desired.entity_type != current.entity_type:
        return True
    if desired.description != current.description:
        return True
    if desired.url != current.url:
        return True
    if desired.owner != current.owner:
        return True

    # Compare properties (excluding managed_by, dbt_*, timestamps)
    excluded_keys = {"managed_by", "dbt_project", "dbt_source", "dbt_exposure",
                     "created_at", "updated_at"}

    desired_props = {k: v for k, v in desired.properties.items() if k not in excluded_keys}
    current_props = {k: v for k, v in current.properties.items() if k not in excluded_keys}

    return desired_props != current_props


def build_sync_plan(
    manifest: Manifest,
    config: Config,
    client: UnityCatalogClient,
    sources_only: bool = False,
    exposures_only: bool = False,
) -> SyncPlan:
    """Build a sync plan by comparing desired and current state.

    Args:
        manifest: The parsed dbt manifest.
        config: The tool configuration.
        client: The Unity Catalog client.
        sources_only: Only include sources in the plan.
        exposures_only: Only include exposures in the plan.

    Returns:
        A SyncPlan describing the required changes.
    """
    project = manifest.project_name
    plan = SyncPlan(project_name=project, catalog=client.catalog)

    # Build desired state
    desired_sources: dict[str, tuple[ExternalMetadata, SourceTable]] = {}
    desired_exposures: dict[str, tuple[ExternalMetadata, Exposure]] = {}

    if not exposures_only:
        # Process sources
        for source in get_sources_with_uc_source(manifest, config.source_paths):
            uc_source = source.uc_source
            if not uc_source:
                continue

            # Get config for this source system
            source_config = config.source_systems.get(uc_source)
            if source_config is None:
                if config.settings.strict:
                    plan.items.append(
                        SyncItem(
                            name=_make_external_name(project, uc_source, source.qualified_name),
                            identifier=source.qualified_name,
                            system_type="UNKNOWN",
                            entity_type="table",
                            status=SyncStatus.ERROR,
                            item_type="source",
                            error=f"Unknown source system: {uc_source}",
                        )
                    )
                continue

            metadata = _build_source_metadata(project, source, source_config)
            desired_sources[metadata.name] = (metadata, source)

        # Process models with uc_source (bronze models representing external sources)
        for model in get_models_with_uc_source(manifest):
            uc_source = model.uc_source
            if not uc_source:
                continue

            source_config = config.source_systems.get(uc_source)
            if source_config is None:
                if config.settings.strict:
                    plan.items.append(
                        SyncItem(
                            name=_make_external_name(project, uc_source, model.name),
                            identifier=model.name,
                            system_type="UNKNOWN",
                            entity_type="table",
                            status=SyncStatus.ERROR,
                            item_type="source",
                            error=f"Unknown source system: {uc_source}",
                        )
                    )
                continue

            # Build metadata similar to source
            name = _make_external_name(project, uc_source, model.name)
            properties = dict(source_config.properties)

            metadata = ExternalMetadata(
                name=name,
                system_type=source_config.system_type,
                entity_type=source_config.entity_type,
                description=source_config.description,
                url=source_config.url,
                owner=source_config.owner,
                properties=properties,
            )
            # Store with a synthetic source for tracking
            desired_sources[metadata.name] = (
                metadata,
                SourceTable(
                    unique_id=model.unique_id,
                    name=model.name,
                    source_name=uc_source,
                    meta=model.meta,
                    database=model.database,
                    schema=model.schema_,
                ),
            )

    if not sources_only:
        # Process exposures
        for exposure in manifest.exposures.values():
            metadata = _build_exposure_metadata(project, exposure)
            desired_exposures[metadata.name] = (metadata, exposure)

    # Get current state from UC
    current_metadata = client.list_external_metadata(dbt_project=project)
    current_by_name = {m.name: m for m in current_metadata}

    # Compare sources
    for name, (desired, source) in desired_sources.items():
        current = current_by_name.pop(name, None)

        # Build lineage edges for this source
        lineage_edges = []
        if source.uc_table_name:
            lineage_edges.append(
                LineageEdge(
                    source_entity=name,
                    target_entity=source.uc_table_name,
                    source_type="external",
                    target_type="table",
                )
            )

        if current is None:
            plan.items.append(
                SyncItem(
                    name=name,
                    identifier=source.qualified_name,
                    system_type=desired.system_type,
                    entity_type=desired.entity_type,
                    status=SyncStatus.CREATE,
                    item_type="source",
                    desired=desired,
                    lineage_edges=lineage_edges,
                )
            )
        elif _metadata_differs(desired, current):
            plan.items.append(
                SyncItem(
                    name=name,
                    identifier=source.qualified_name,
                    system_type=desired.system_type,
                    entity_type=desired.entity_type,
                    status=SyncStatus.UPDATE,
                    item_type="source",
                    desired=desired,
                    current=current,
                    lineage_edges=lineage_edges,
                )
            )
        else:
            plan.items.append(
                SyncItem(
                    name=name,
                    identifier=source.qualified_name,
                    system_type=desired.system_type,
                    entity_type=desired.entity_type,
                    status=SyncStatus.IN_SYNC,
                    item_type="source",
                    desired=desired,
                    current=current,
                    lineage_edges=lineage_edges,
                )
            )

    # Compare exposures
    for name, (desired, exposure) in desired_exposures.items():
        current = current_by_name.pop(name, None)

        # Build lineage edges for this exposure
        lineage_edges = []
        for uc_table in resolve_exposure_dependencies(manifest, exposure):
            lineage_edges.append(
                LineageEdge(
                    source_entity=uc_table,
                    target_entity=name,
                    source_type="table",
                    target_type="external",
                )
            )

        if current is None:
            plan.items.append(
                SyncItem(
                    name=name,
                    identifier=exposure.name,
                    system_type=desired.system_type,
                    entity_type=desired.entity_type,
                    status=SyncStatus.CREATE,
                    item_type="exposure",
                    desired=desired,
                    lineage_edges=lineage_edges,
                )
            )
        elif _metadata_differs(desired, current):
            plan.items.append(
                SyncItem(
                    name=name,
                    identifier=exposure.name,
                    system_type=desired.system_type,
                    entity_type=desired.entity_type,
                    status=SyncStatus.UPDATE,
                    item_type="exposure",
                    desired=desired,
                    current=current,
                    lineage_edges=lineage_edges,
                )
            )
        else:
            plan.items.append(
                SyncItem(
                    name=name,
                    identifier=exposure.name,
                    system_type=desired.system_type,
                    entity_type=desired.entity_type,
                    status=SyncStatus.IN_SYNC,
                    item_type="exposure",
                    desired=desired,
                    current=current,
                    lineage_edges=lineage_edges,
                )
            )

    # Remaining items in current_by_name are orphaned (should be deleted)
    for name, current in current_by_name.items():
        # Determine type from properties
        is_source = "dbt_source" in current.properties
        item_type = "source" if is_source else "exposure"
        identifier = current.properties.get(f"dbt_{item_type}", name)

        plan.items.append(
            SyncItem(
                name=name,
                identifier=identifier,
                system_type=current.system_type,
                entity_type=current.entity_type,
                status=SyncStatus.DELETE,
                item_type=item_type,
                current=current,
            )
        )

    return plan


def apply_sync_plan(
    plan: SyncPlan,
    client: UnityCatalogClient,
    dry_run: bool = False,
    no_clean: bool = False,
    progress_callback: ProgressCallback = None,
    strict: bool = False,
) -> SyncPlan:
    """Apply a sync plan to Unity Catalog.

    Args:
        plan: The sync plan to apply.
        client: The Unity Catalog client.
        dry_run: If True, don't make any changes.
        no_clean: If True, don't delete orphaned objects.
        progress_callback: Optional callback for progress updates.
            Called with (current, total, item_name) for each item processed.
        strict: If True, fail immediately on first error.

    Returns:
        The updated sync plan with results.

    Raises:
        StrictModeError: If strict mode is enabled and an error occurs.
    """
    if dry_run:
        return plan

    # Count items that need processing
    actionable_items = [
        item for item in plan.items
        if item.status in (SyncStatus.CREATE, SyncStatus.UPDATE, SyncStatus.DELETE)
    ]

    # Filter out DELETE items if no_clean is True
    if no_clean:
        actionable_items = [
            item for item in actionable_items
            if item.status != SyncStatus.DELETE
        ]

    total = len(actionable_items)
    processed = 0

    for item in plan.items:
        # Skip items that don't need action
        if item.status not in (SyncStatus.CREATE, SyncStatus.UPDATE, SyncStatus.DELETE):
            continue

        # Skip DELETE if no_clean is True
        if item.status == SyncStatus.DELETE and no_clean:
            continue

        try:
            if item.status == SyncStatus.CREATE and item.desired:
                logger.debug(f"Creating external metadata: {item.name}")
                client.create_external_metadata(
                    metadata=item.desired,
                    dbt_project=plan.project_name,
                    identifier=item.identifier,
                    identifier_type=item.item_type,
                )
                # Create lineage edges
                for edge in item.lineage_edges:
                    try:
                        client.create_lineage_edge(edge)
                    except Exception as e:
                        # Lineage edge creation may fail if table doesn't exist yet
                        logger.debug(f"Lineage edge creation skipped: {e}")

            elif item.status == SyncStatus.UPDATE and item.desired:
                logger.debug(f"Updating external metadata: {item.name}")
                client.update_external_metadata(
                    metadata=item.desired,
                    dbt_project=plan.project_name,
                    identifier=item.identifier,
                    identifier_type=item.item_type,
                )
                # Update lineage edges (recreate)
                for edge in item.lineage_edges:
                    try:
                        client.delete_lineage_edge(edge)
                    except Exception:
                        pass
                    try:
                        client.create_lineage_edge(edge)
                    except Exception as e:
                        logger.debug(f"Lineage edge creation skipped: {e}")

            elif item.status == SyncStatus.DELETE:
                logger.debug(f"Deleting external metadata: {item.name}")
                # Delete lineage edges first
                for edge in client.list_lineage_edges(item.name, "external"):
                    try:
                        client.delete_lineage_edge(edge)
                    except Exception:
                        pass
                client.delete_external_metadata(item.name)

        except Exception as e:
            item.status = SyncStatus.ERROR
            item.error = str(e)
            logger.error(f"Failed to process {item.name}: {e}")

            # In strict mode, fail immediately
            if strict:
                raise StrictModeError(item.identifier, str(e))

        # Update progress
        processed += 1
        if progress_callback:
            progress_callback(processed, total, item.identifier)

    return plan
