"""FastAPI mock server for Unity Catalog external lineage API.

This mock server implements the Unity Catalog external metadata and lineage
endpoints for integration testing without requiring a real Databricks workspace.

Features:
- In-memory state for stateful testing (create -> list -> delete)
- Error simulation (rate limits, auth errors, not found)
- Request validation matching real API schemas
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# =============================================================================
# Request/Response Models
# =============================================================================


class ExternalMetadataCreate(BaseModel):
    """Request model for creating external metadata."""

    name: str
    catalog_name: str
    system_type: str
    entity_type: str
    description: Optional[str] = None
    url: Optional[str] = None
    owner: Optional[str] = None
    properties: Optional[Dict[str, str]] = None


class ExternalMetadataUpdate(BaseModel):
    """Request model for updating external metadata."""

    catalog_name: str
    system_type: Optional[str] = None
    entity_type: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    owner: Optional[str] = None
    properties: Optional[Dict[str, str]] = None


class LineageEdgeCreate(BaseModel):
    """Request model for creating a lineage edge."""

    catalog_name: str
    source_external_metadata: Optional[str] = None
    source_table: Optional[str] = None
    target_external_metadata: Optional[str] = None
    target_table: Optional[str] = None


# =============================================================================
# Server State
# =============================================================================


@dataclass
class ServerState:
    """In-memory state for the mock server."""

    # External metadata: {name: metadata_dict}
    external_metadata: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Lineage edges: list of edge dicts
    lineage_edges: List[Dict[str, Any]] = field(default_factory=list)

    # Error simulation
    simulate_rate_limit: bool = False
    rate_limit_until: float = 0
    simulate_auth_error: bool = False
    simulate_api_unavailable: bool = False

    # Request tracking for testing
    requests: List[Dict[str, Any]] = field(default_factory=list)

    def reset(self) -> None:
        """Reset all state."""
        self.external_metadata.clear()
        self.lineage_edges.clear()
        self.simulate_rate_limit = False
        self.rate_limit_until = 0
        self.simulate_auth_error = False
        self.simulate_api_unavailable = False
        self.requests.clear()

    def record_request(self, method: str, path: str, body: Any = None) -> None:
        """Record a request for later inspection."""
        self.requests.append({
            "method": method,
            "path": path,
            "body": body,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })


# Global state instance
state = ServerState()

# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(
    title="Unity Catalog External Lineage Mock",
    description="Mock server for testing dbt-unity-lineage",
    version="0.1.0",
)


@app.middleware("http")
async def error_simulation_middleware(request: Request, call_next):
    """Middleware to simulate various error conditions."""
    # Test control endpoints and health check bypass all error simulation
    if request.url.path.startswith("/test/") or request.url.path == "/health":
        return await call_next(request)

    # Record all requests
    body = None
    if request.method in ("POST", "PATCH", "DELETE"):
        try:
            body = await request.json()
        except Exception:
            body = None

    state.record_request(request.method, request.url.path, body)

    # Simulate API unavailable (404 for all endpoints)
    if state.simulate_api_unavailable:
        return JSONResponse(
            status_code=404,
            content={
                "error_code": "ENDPOINT_NOT_FOUND",
                "message": f"No API found for '{request.method} {request.url.path}'",
            },
        )

    # Simulate authentication error
    if state.simulate_auth_error:
        return JSONResponse(
            status_code=401,
            content={
                "error_code": "UNAUTHENTICATED",
                "message": "Invalid access token",
            },
        )

    # Simulate rate limiting
    if state.simulate_rate_limit:
        if time.time() < state.rate_limit_until:
            return JSONResponse(
                status_code=429,
                content={
                    "error_code": "RATE_LIMIT_EXCEEDED",
                    "message": "Rate limit exceeded. Please retry after some time.",
                },
                headers={"Retry-After": "1"},
            )

    return await call_next(request)


# =============================================================================
# Control Endpoints (for test setup)
# =============================================================================


@app.post("/test/reset")
async def reset_state():
    """Reset all server state. Used in test setup."""
    state.reset()
    return {"status": "ok"}


@app.post("/test/simulate-rate-limit")
async def simulate_rate_limit(duration_seconds: float = 2.0):
    """Enable rate limit simulation for specified duration."""
    state.simulate_rate_limit = True
    state.rate_limit_until = time.time() + duration_seconds
    return {"status": "ok", "until": state.rate_limit_until}


@app.post("/test/simulate-auth-error")
async def simulate_auth_error(enabled: bool = True):
    """Enable/disable auth error simulation."""
    state.simulate_auth_error = enabled
    return {"status": "ok", "enabled": enabled}


@app.post("/test/simulate-api-unavailable")
async def simulate_api_unavailable(enabled: bool = True):
    """Enable/disable API unavailable simulation (404 for all endpoints)."""
    state.simulate_api_unavailable = enabled
    return {"status": "ok", "enabled": enabled}


@app.get("/test/requests")
async def get_requests():
    """Get recorded requests for inspection."""
    return {"requests": state.requests}


@app.get("/test/state")
async def get_state():
    """Get current server state for debugging."""
    return {
        "external_metadata_count": len(state.external_metadata),
        "lineage_edges_count": len(state.lineage_edges),
        "external_metadata": list(state.external_metadata.keys()),
    }


# =============================================================================
# External Metadata Endpoints
# =============================================================================


@app.post("/api/2.1/unity-catalog/external-metadata")
async def create_external_metadata(data: ExternalMetadataCreate):
    """Create an external metadata object."""
    name = data.name

    if name in state.external_metadata:
        raise HTTPException(
            status_code=409,
            detail={
                "error_code": "RESOURCE_ALREADY_EXISTS",
                "message": f"External metadata '{name}' already exists",
            },
        )

    metadata = {
        "name": name,
        "catalog_name": data.catalog_name,
        "system_type": data.system_type,
        "entity_type": data.entity_type,
        "description": data.description,
        "url": data.url,
        "owner": data.owner,
        "properties": data.properties or {},
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    state.external_metadata[name] = metadata
    return metadata


@app.get("/api/2.1/unity-catalog/external-metadata")
async def list_external_metadata(catalog_name: str = Query(...)):
    """List all external metadata objects in a catalog."""
    items = [
        m for m in state.external_metadata.values()
        if m.get("catalog_name") == catalog_name
    ]
    return {"external_metadata": items}


@app.get("/api/2.1/unity-catalog/external-metadata/{name}")
async def get_external_metadata(name: str, catalog_name: str = Query(...)):
    """Get a specific external metadata object."""
    if name not in state.external_metadata:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "RESOURCE_DOES_NOT_EXIST",
                "message": f"External metadata '{name}' does not exist",
            },
        )

    metadata = state.external_metadata[name]
    if metadata.get("catalog_name") != catalog_name:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "RESOURCE_DOES_NOT_EXIST",
                "message": f"External metadata '{name}' not found in catalog '{catalog_name}'",
            },
        )

    return metadata


@app.patch("/api/2.1/unity-catalog/external-metadata/{name}")
async def update_external_metadata(name: str, data: ExternalMetadataUpdate):
    """Update an external metadata object."""
    if name not in state.external_metadata:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "RESOURCE_DOES_NOT_EXIST",
                "message": f"External metadata '{name}' does not exist",
            },
        )

    metadata = state.external_metadata[name]

    # Update fields if provided
    if data.system_type is not None:
        metadata["system_type"] = data.system_type
    if data.entity_type is not None:
        metadata["entity_type"] = data.entity_type
    if data.description is not None:
        metadata["description"] = data.description
    if data.url is not None:
        metadata["url"] = data.url
    if data.owner is not None:
        metadata["owner"] = data.owner
    if data.properties is not None:
        metadata["properties"] = data.properties

    metadata["updated_at"] = datetime.now(timezone.utc).isoformat()

    return metadata


@app.delete("/api/2.1/unity-catalog/external-metadata/{name}")
async def delete_external_metadata(name: str, catalog_name: str = Query(...)):
    """Delete an external metadata object."""
    if name not in state.external_metadata:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "RESOURCE_DOES_NOT_EXIST",
                "message": f"External metadata '{name}' does not exist",
            },
        )

    del state.external_metadata[name]

    # Also delete any lineage edges referencing this metadata
    state.lineage_edges = [
        e for e in state.lineage_edges
        if e.get("source_external_metadata") != name
        and e.get("target_external_metadata") != name
    ]

    return {}


# =============================================================================
# Lineage Edge Endpoints
# =============================================================================


@app.post("/api/2.1/unity-catalog/lineage/external-edges")
async def create_lineage_edge(data: LineageEdgeCreate):
    """Create a lineage edge between entities."""
    edge = {
        "catalog_name": data.catalog_name,
        "source_external_metadata": data.source_external_metadata,
        "source_table": data.source_table,
        "target_external_metadata": data.target_external_metadata,
        "target_table": data.target_table,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    # Check for duplicate
    for existing in state.lineage_edges:
        if (
            existing.get("source_external_metadata") == edge.get("source_external_metadata")
            and existing.get("source_table") == edge.get("source_table")
            and existing.get("target_external_metadata") == edge.get("target_external_metadata")
            and existing.get("target_table") == edge.get("target_table")
        ):
            # Idempotent - return existing edge
            return existing

    state.lineage_edges.append(edge)
    return edge


@app.get("/api/2.1/unity-catalog/lineage/external-edges")
async def list_lineage_edges(
    catalog_name: str = Query(...),
    external_metadata_name: Optional[str] = Query(None),
    table_name: Optional[str] = Query(None),
):
    """List lineage edges, optionally filtered by entity."""
    edges = [e for e in state.lineage_edges if e.get("catalog_name") == catalog_name]

    if external_metadata_name:
        edges = [
            e for e in edges
            if e.get("source_external_metadata") == external_metadata_name
            or e.get("target_external_metadata") == external_metadata_name
        ]

    if table_name:
        edges = [
            e for e in edges
            if e.get("source_table") == table_name
            or e.get("target_table") == table_name
        ]

    return {"edges": edges}


@app.delete("/api/2.1/unity-catalog/lineage/external-edges")
async def delete_lineage_edge(data: LineageEdgeCreate):
    """Delete a lineage edge."""
    original_count = len(state.lineage_edges)

    state.lineage_edges = [
        e for e in state.lineage_edges
        if not (
            e.get("catalog_name") == data.catalog_name
            and e.get("source_external_metadata") == data.source_external_metadata
            and e.get("source_table") == data.source_table
            and e.get("target_external_metadata") == data.target_external_metadata
            and e.get("target_table") == data.target_table
        )
    ]

    if len(state.lineage_edges) == original_count:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "RESOURCE_DOES_NOT_EXIST",
                "message": "Lineage edge not found",
            },
        )

    return {}


# =============================================================================
# Health Check
# =============================================================================


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# =============================================================================
# dbt Cloud API Mock Endpoints
# =============================================================================


@dataclass
class DbtCloudState:
    """State for dbt Cloud API mock."""

    # Jobs: {job_id: job_dict}
    jobs: Dict[int, Dict[str, Any]] = field(default_factory=dict)

    # Runs: {run_id: run_dict}
    runs: Dict[int, Dict[str, Any]] = field(default_factory=dict)

    # Artifacts: {run_id: {artifact_name: content}}
    artifacts: Dict[int, Dict[str, bytes]] = field(default_factory=dict)

    # Counter for auto-generating IDs
    next_run_id: int = 1000
    next_job_id: int = 100

    def reset(self) -> None:
        """Reset dbt Cloud state."""
        self.jobs.clear()
        self.runs.clear()
        self.artifacts.clear()
        self.next_run_id = 1000
        self.next_job_id = 100


# Global dbt Cloud state
dbt_cloud_state = DbtCloudState()


@app.post("/test/dbt-cloud/reset")
async def reset_dbt_cloud_state():
    """Reset dbt Cloud state."""
    dbt_cloud_state.reset()
    return {"status": "ok"}


@app.post("/test/dbt-cloud/add-job")
async def add_dbt_cloud_job(
    job_id: Optional[int] = None,
    name: str = "Test Job",
    project_id: int = 1,
):
    """Add a mock dbt Cloud job."""
    if job_id is None:
        job_id = dbt_cloud_state.next_job_id
        dbt_cloud_state.next_job_id += 1

    dbt_cloud_state.jobs[job_id] = {
        "id": job_id,
        "name": name,
        "project_id": project_id,
        "environment_id": 1,
        "account_id": 12345,
        "execute_steps": ["dbt build"],
        "state": 1,  # Active
    }
    return {"job_id": job_id}


@app.post("/test/dbt-cloud/add-run")
async def add_dbt_cloud_run(
    job_id: int,
    run_id: Optional[int] = None,
    status: int = 10,  # 10 = Success
    status_humanized: str = "Success",
    has_docs_generated: bool = True,
    manifest_content: Optional[str] = None,
):
    """Add a mock dbt Cloud run with optional manifest artifact."""
    import json

    if run_id is None:
        run_id = dbt_cloud_state.next_run_id
        dbt_cloud_state.next_run_id += 1

    dbt_cloud_state.runs[run_id] = {
        "id": run_id,
        "job_definition_id": job_id,
        "status": status,
        "status_humanized": status_humanized,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "has_docs_generated": has_docs_generated,
    }

    # Add default manifest if not provided
    if manifest_content is None:
        manifest_content = json.dumps({
            "metadata": {
                "project_name": "test_project",
                "dbt_version": "1.7.0",
            },
            "nodes": {},
            "sources": {},
            "exposures": {},
        })

    dbt_cloud_state.artifacts[run_id] = {
        "manifest.json": manifest_content.encode("utf-8"),
    }

    return {"run_id": run_id}


# dbt Cloud API v2 endpoints
@app.get("/api/v2/accounts/{account_id}/jobs/")
async def list_dbt_cloud_jobs(account_id: int):
    """List all jobs in an account."""
    jobs = list(dbt_cloud_state.jobs.values())
    return {"data": jobs, "status": {"code": 200}}


@app.get("/api/v2/accounts/{account_id}/runs/")
async def list_dbt_cloud_runs(
    account_id: int,
    job_definition_id: Optional[int] = Query(None),
    status: Optional[int] = Query(None),
    order_by: Optional[str] = Query(None),
    limit: int = Query(100),
):
    """List runs, optionally filtered by job and status."""
    runs = list(dbt_cloud_state.runs.values())

    if job_definition_id is not None:
        runs = [r for r in runs if r["job_definition_id"] == job_definition_id]

    if status is not None:
        runs = [r for r in runs if r["status"] == status]

    # Sort by finished_at descending if requested
    if order_by == "-finished_at":
        runs = sorted(runs, key=lambda r: r.get("finished_at", ""), reverse=True)

    runs = runs[:limit]

    return {"data": runs, "status": {"code": 200}}


@app.get("/api/v2/accounts/{account_id}/runs/{run_id}/")
async def get_dbt_cloud_run(account_id: int, run_id: int):
    """Get a specific run."""
    if run_id not in dbt_cloud_state.runs:
        raise HTTPException(
            status_code=404,
            detail={"status": {"user_message": f"Run {run_id} not found"}},
        )

    return {"data": dbt_cloud_state.runs[run_id], "status": {"code": 200}}


@app.get("/api/v2/accounts/{account_id}/runs/{run_id}/artifacts/{artifact_path:path}")
async def get_dbt_cloud_artifact(account_id: int, run_id: int, artifact_path: str):
    """Get an artifact from a run."""
    if run_id not in dbt_cloud_state.artifacts:
        raise HTTPException(
            status_code=404,
            detail={"status": {"user_message": f"Run {run_id} not found"}},
        )

    artifacts = dbt_cloud_state.artifacts[run_id]
    if artifact_path not in artifacts:
        raise HTTPException(
            status_code=404,
            detail={"status": {"user_message": f"Artifact {artifact_path} not found"}},
        )

    from fastapi.responses import Response
    return Response(
        content=artifacts[artifact_path],
        media_type="application/json",
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
