"""
Event contracts — defines all event types and their payloads.
These are the shared contracts between publishers and subscribers.
"""
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field


class EventType(str, Enum):
    INCIDENT_CREATED = "incident.created"
    INCIDENT_ACKNOWLEDGED = "incident.acknowledged"
    INCIDENT_RESOLVED = "incident.resolved"
    INCIDENT_ESCALATED = "incident.escalated"
    INCIDENT_UPDATED = "incident.updated"


REDIS_CHANNEL = "events:incident"


class BaseEvent(BaseModel):
    """Base event with metadata."""
    event_type: EventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_service: str = "incident-service"


class IncidentCreatedEvent(BaseEvent):
    event_type: EventType = EventType.INCIDENT_CREATED
    incident_id: int
    title: str
    severity: str
    status: str
    source: str
    created_by: str | None = None


class IncidentAcknowledgedEvent(BaseEvent):
    event_type: EventType = EventType.INCIDENT_ACKNOWLEDGED
    incident_id: int
    engineer_id: int
    engineer_email: str
    engineer_name: str


class IncidentResolvedEvent(BaseEvent):
    event_type: EventType = EventType.INCIDENT_RESOLVED
    incident_id: int
    resolver_id: int
    resolver_email: str
    resolver_name: str
    resolution_notes: str
    time_to_resolve_seconds: float | None = None


class IncidentEscalatedEvent(BaseEvent):
    event_type: EventType = EventType.INCIDENT_ESCALATED
    incident_id: int
    title: str
    severity: str
    from_tier: int
    to_tier: int
    reason: str = "No acknowledgement within SLA"


class IncidentUpdatedEvent(BaseEvent):
    event_type: EventType = EventType.INCIDENT_UPDATED
    incident_id: int
    changes: dict = {}
