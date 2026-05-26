"""
Incident Service — Service 1
Handles CRUD operations, status machine transitions, and Redis-based optimistic locking.
"""
from datetime import datetime, timezone

import structlog
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.models.incident import Incident, IncidentStatus, IncidentSeverity
from app.models.user import User
from app.schemas.incident import IncidentCreate, IncidentUpdate
from app.events.publisher import publish_event, get_redis_client
from app.events.contracts import (
    IncidentCreatedEvent,
    IncidentAcknowledgedEvent,
    IncidentResolvedEvent,
    IncidentUpdatedEvent,
)

logger = structlog.get_logger(__name__)
settings = get_settings()


class IncidentService:
    """Core service for incident lifecycle management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_incident(self, data: IncidentCreate, created_by: User | None = None) -> Incident:
        """Create a new incident with status OPEN."""
        incident = Incident(
            title=data.title,
            description=data.description,
            severity=data.severity,
            source=data.source,
            tags=data.tags,
            status=IncidentStatus.OPEN,
        )
        self.db.add(incident)
        await self.db.flush()
        await self.db.refresh(incident)

        await logger.ainfo(
            "Incident created",
            incident_id=incident.id,
            severity=incident.severity.value,
            title=incident.title,
        )

        # Publish event
        await publish_event(IncidentCreatedEvent(
            incident_id=incident.id,
            title=incident.title,
            severity=incident.severity.value,
            status=incident.status.value,
            source=incident.source,
            created_by=created_by.email if created_by else None,
        ))

        return incident

    async def get_incident(self, incident_id: int) -> Incident | None:
        """Get a single incident by ID."""
        result = await self.db.execute(
            select(Incident)
            .options(
                selectinload(Incident.assignee),
                selectinload(Incident.acknowledger),
                selectinload(Incident.resolver),
            )
            .where(and_(Incident.id == incident_id, Incident.is_deleted.is_(False)))
        )
        return result.scalar_one_or_none()

    async def list_incidents(
        self,
        page: int = 1,
        per_page: int = 20,
        severity: IncidentSeverity | None = None,
        status: IncidentStatus | None = None,
        search: str | None = None,
    ) -> tuple[list[Incident], int]:
        """List incidents with pagination and filters."""
        query = (
            select(Incident)
            .options(
                selectinload(Incident.assignee),
                selectinload(Incident.acknowledger),
                selectinload(Incident.resolver),
            )
            .where(Incident.is_deleted.is_(False))
        )
        count_query = select(func.count(Incident.id)).where(Incident.is_deleted.is_(False))

        if severity:
            query = query.where(Incident.severity == severity)
            count_query = count_query.where(Incident.severity == severity)
        if status:
            query = query.where(Incident.status == status)
            count_query = count_query.where(Incident.status == status)
        if search:
            search_filter = Incident.title.ilike(f"%{search}%")
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)

        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        offset = (page - 1) * per_page
        query = query.order_by(Incident.created_at.desc()).offset(offset).limit(per_page)
        result = await self.db.execute(query)
        incidents = list(result.scalars().all())

        return incidents, total

    async def update_incident(self, incident_id: int, data: IncidentUpdate) -> Incident | None:
        """Update incident fields (not status)."""
        incident = await self.get_incident(incident_id)
        if not incident:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(incident, field, value)

        await self.db.flush()
        await self.db.refresh(incident)

        await logger.ainfo("Incident updated", incident_id=incident_id, changes=update_data)
        return incident

    async def acknowledge_incident(self, incident_id: int, user: User) -> tuple[bool, str]:
        """
        Acknowledge an incident using Redis SET NX for atomic locking.
        Returns (success, message).

        Race condition handling:
        - Two engineers try to acknowledge simultaneously
        - Redis SET NX is atomic: only one will succeed
        - The loser gets 409 Conflict
        """
        redis_client = await get_redis_client()
        lock_key = f"incident:lock:{incident_id}"

        # Atomic compare-and-swap via SET NX
        acquired = await redis_client.set(
            lock_key,
            f"{user.id}:{user.email}",
            nx=True,   # Only set if key does NOT exist
            ex=3600,    # 1 hour expiry as safety net
        )

        if not acquired:
            # Someone else already acknowledged
            existing = await redis_client.get(lock_key)
            existing_email = existing.split(":")[1] if existing and ":" in existing else "unknown"
            await logger.awarning(
                "Acknowledge conflict",
                incident_id=incident_id,
                rejected_user=user.email,
                existing_holder=existing_email,
            )
            return False, f"Already acknowledged by {existing_email}"

        # Lock acquired — update the database
        incident = await self.get_incident(incident_id)
        if not incident:
            await redis_client.delete(lock_key)
            return False, "Incident not found"

        if not incident.can_transition_to(IncidentStatus.ACKNOWLEDGED):
            await redis_client.delete(lock_key)
            return False, f"Cannot acknowledge incident in status '{incident.status.value}'"

        incident.status = IncidentStatus.ACKNOWLEDGED
        incident.acknowledged_by = user.id
        incident.acknowledged_at = datetime.now(timezone.utc)
        await self.db.flush()

        await logger.ainfo(
            "Incident acknowledged",
            incident_id=incident_id,
            engineer=user.email,
        )

        # Publish event
        await publish_event(IncidentAcknowledgedEvent(
            incident_id=incident_id,
            engineer_id=user.id,
            engineer_email=user.email,
            engineer_name=user.name,
        ))

        return True, "Incident acknowledged successfully"

    async def resolve_incident(
        self, incident_id: int, user: User, resolution_notes: str
    ) -> tuple[bool, str]:
        """Resolve an incident and record resolution metadata."""
        incident = await self.get_incident(incident_id)
        if not incident:
            return False, "Incident not found"

        if not incident.can_transition_to(IncidentStatus.RESOLVED):
            return False, f"Cannot resolve incident in status '{incident.status.value}'"

        now = datetime.now(timezone.utc)
        incident.status = IncidentStatus.RESOLVED
        incident.resolved_by = user.id
        incident.resolved_at = now

        # Calculate time to resolve
        ttr = None
        if incident.created_at:
            ttr = (now - incident.created_at).total_seconds()

        await self.db.flush()

        # Clean up Redis lock
        redis_client = await get_redis_client()
        await redis_client.delete(f"incident:lock:{incident_id}")

        await logger.ainfo(
            "Incident resolved",
            incident_id=incident_id,
            resolver=user.email,
            ttr_seconds=ttr,
        )

        # Publish event
        await publish_event(IncidentResolvedEvent(
            incident_id=incident_id,
            resolver_id=user.id,
            resolver_email=user.email,
            resolver_name=user.name,
            resolution_notes=resolution_notes,
            time_to_resolve_seconds=ttr,
        ))

        return True, "Incident resolved successfully"

    async def close_incident(
        self, incident_id: int, user: User, notes: str | None = None
    ) -> tuple[bool, str]:
        """Formally close an incident (terminal archived state)."""
        incident = await self.get_incident(incident_id)
        if not incident:
            return False, "Incident not found"

        if not incident.can_transition_to(IncidentStatus.CLOSED):
            return False, f"Cannot close incident in status '{incident.status.value}'"

        incident.status = IncidentStatus.CLOSED
        await self.db.flush()

        redis_client = await get_redis_client()
        await redis_client.delete(f"incident:lock:{incident_id}")

        await logger.ainfo(
            "Incident closed",
            incident_id=incident_id,
            closed_by=user.email,
            notes=notes,
        )

        await publish_event(IncidentUpdatedEvent(
            incident_id=incident_id,
            changes={"status": IncidentStatus.CLOSED.value, "closed_by": user.email},
        ))

        return True, "Incident closed successfully"

    async def transition_status(self, incident_id: int, new_status: IncidentStatus) -> tuple[bool, str]:
        """Transition incident to a new status (for internal use, e.g., escalation)."""
        incident = await self.get_incident(incident_id)
        if not incident:
            return False, "Incident not found"

        if not incident.can_transition_to(new_status):
            return False, f"Invalid transition from '{incident.status.value}' to '{new_status.value}'"

        incident.status = new_status
        await self.db.flush()

        await logger.ainfo(
            "Incident status transitioned",
            incident_id=incident_id,
            new_status=new_status.value,
        )
        return True, f"Status changed to {new_status.value}"

    async def soft_delete(self, incident_id: int) -> bool:
        """Soft delete an incident."""
        incident = await self.get_incident(incident_id)
        if not incident:
            return False
        incident.is_deleted = True
        await self.db.flush()
        await logger.ainfo("Incident soft deleted", incident_id=incident_id)
        return True

    async def get_stats(self) -> dict:
        """Get incident statistics for dashboard."""
        # Count by status
        status_result = await self.db.execute(
            select(Incident.status, func.count(Incident.id))
            .where(Incident.is_deleted.is_(False))
            .group_by(Incident.status)
        )
        status_counts = {row[0].value: row[1] for row in status_result.all()}

        # Count by severity
        severity_result = await self.db.execute(
            select(Incident.severity, func.count(Incident.id))
            .where(Incident.is_deleted.is_(False))
            .group_by(Incident.severity)
        )
        severity_counts = {row[0].value: row[1] for row in severity_result.all()}

        # Average TTR for resolved incidents
        ttr_result = await self.db.execute(
            select(func.avg(
                func.extract('epoch', Incident.resolved_at) - func.extract('epoch', Incident.created_at)
            ))
            .where(and_(
                Incident.status == IncidentStatus.RESOLVED,
                Incident.resolved_at.isnot(None),
                Incident.is_deleted.is_(False),
            ))
        )
        avg_ttr = ttr_result.scalar()

        total_result = await self.db.execute(
            select(func.count(Incident.id)).where(Incident.is_deleted.is_(False))
        )
        total = total_result.scalar()

        return {
            "total_incidents": total,
            "by_status": status_counts,
            "by_severity": severity_counts,
            "avg_ttr_seconds": round(avg_ttr, 2) if avg_ttr else None,
        }
