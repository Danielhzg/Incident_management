"""
Incident routes — REST API for incident CRUD and lifecycle operations.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.incident import IncidentSeverity, IncidentStatus
from app.schemas.incident import (
    IncidentCreate, IncidentUpdate, IncidentResponse,
    IncidentListResponse, IncidentAcknowledge, IncidentResolve, IncidentClose,
)
from app.services.incident_service import IncidentService
from app.auth.dependencies import get_current_user
from app.cache.redis_cache import cache_get, cache_set, _make_cache_key

router = APIRouter(prefix="/api/incidents", tags=["Incidents"])


def _incident_to_response(incident) -> IncidentResponse:
    """Convert ORM incident to response schema."""
    return IncidentResponse(
        id=incident.id,
        title=incident.title,
        description=incident.description,
        severity=incident.severity,
        status=incident.status,
        source=incident.source,
        tags=incident.tags,
        assigned_to=incident.assigned_to,
        acknowledged_by=incident.acknowledged_by,
        resolved_by=incident.resolved_by,
        escalation_tier=incident.escalation_tier,
        escalation_count=incident.escalation_count,
        created_at=incident.created_at,
        updated_at=incident.updated_at,
        acknowledged_at=incident.acknowledged_at,
        resolved_at=incident.resolved_at,
        assignee_name=incident.assignee.name if incident.assignee else None,
        acknowledger_name=incident.acknowledger.name if incident.acknowledger else None,
        resolver_name=incident.resolver.name if incident.resolver else None,
    )


@router.post("/", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
async def create_incident(
    data: IncidentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new incident."""
    service = IncidentService(db)
    incident = await service.create_incident(data, created_by=current_user)
    return _incident_to_response(incident)


@router.get("/", response_model=IncidentListResponse)
async def list_incidents(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    severity: IncidentSeverity | None = None,
    status: IncidentStatus | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List incidents with pagination and filters."""
    # Try cache
    cache_key = _make_cache_key("incidents", page, per_page, severity, status, search)
    cached = await cache_get(cache_key)
    if cached:
        return IncidentListResponse(**cached)

    service = IncidentService(db)
    incidents, total = await service.list_incidents(page, per_page, severity, status, search)

    response = IncidentListResponse(
        incidents=[_incident_to_response(i) for i in incidents],
        total=total,
        page=page,
        per_page=per_page,
    )

    # Cache the result
    await cache_set(cache_key, response.model_dump(), ttl=60)
    return response


@router.get("/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get incident statistics for dashboard."""
    cache_key = _make_cache_key("stats")
    cached = await cache_get(cache_key)
    if cached:
        return cached

    service = IncidentService(db)
    stats = await service.get_stats()

    await cache_set(cache_key, stats, ttl=30)
    return stats


@router.get("/{incident_id}", response_model=IncidentResponse)
async def get_incident(
    incident_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get a single incident by ID."""
    service = IncidentService(db)
    incident = await service.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return _incident_to_response(incident)


@router.put("/{incident_id}", response_model=IncidentResponse)
async def update_incident(
    incident_id: int,
    data: IncidentUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Update incident fields."""
    service = IncidentService(db)
    incident = await service.update_incident(incident_id, data)
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return _incident_to_response(incident)


@router.post("/{incident_id}/acknowledge")
async def acknowledge_incident(
    incident_id: int,
    data: IncidentAcknowledge | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Acknowledge an incident. Uses Redis SET NX for atomic locking.
    If two engineers try simultaneously, only one succeeds (409 Conflict for the other).
    """
    service = IncidentService(db)
    success, message = await service.acknowledge_incident(incident_id, current_user)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=message,
        )

    return {"status": "success", "message": message}


@router.post("/{incident_id}/resolve")
async def resolve_incident(
    incident_id: int,
    data: IncidentResolve,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Resolve an incident with resolution notes."""
    service = IncidentService(db)
    success, message = await service.resolve_incident(incident_id, current_user, data.resolution_notes)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

    return {"status": "success", "message": message}


@router.post("/{incident_id}/close")
async def close_incident(
    incident_id: int,
    data: IncidentClose | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Close an incident after resolution (terminal archived state)."""
    service = IncidentService(db)
    notes = data.notes if data else None
    success, message = await service.close_incident(incident_id, current_user, notes)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message,
        )

    return {"status": "success", "message": message}


@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_incident(
    incident_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Soft delete an incident."""
    service = IncidentService(db)
    deleted = await service.soft_delete(incident_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
