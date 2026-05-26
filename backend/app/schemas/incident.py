"""
Pydantic schemas for Incident request/response validation.
"""
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.incident import IncidentSeverity, IncidentStatus


class IncidentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500, examples=["Database connection pool exhausted"])
    description: str = Field(..., min_length=1, examples=["PostgreSQL connection pool reached max limit, causing 503 errors"])
    severity: IncidentSeverity = Field(..., examples=[IncidentSeverity.P1])
    source: str = Field(default="manual", max_length=255, examples=["monitoring", "manual", "webhook"])
    tags: str | None = Field(default=None, examples=["database,postgres,connection"])


class IncidentUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=500)
    description: str | None = None
    severity: IncidentSeverity | None = None
    tags: str | None = None


class IncidentAcknowledge(BaseModel):
    notes: str | None = Field(default=None, examples=["Looking into this now"])


class IncidentResolve(BaseModel):
    resolution_notes: str = Field(..., min_length=1, examples=["Increased pool size from 20 to 50"])


class IncidentClose(BaseModel):
    notes: str | None = Field(default=None, examples=["Post-mortem complete, incident archived"])


class IncidentResponse(BaseModel):
    id: int
    title: str
    description: str
    severity: IncidentSeverity
    status: IncidentStatus
    source: str
    tags: str | None
    assigned_to: int | None
    acknowledged_by: int | None
    resolved_by: int | None
    escalation_tier: int
    escalation_count: int
    created_at: datetime
    updated_at: datetime
    acknowledged_at: datetime | None
    resolved_at: datetime | None

    # Populated from relationships
    assignee_name: str | None = None
    acknowledger_name: str | None = None
    resolver_name: str | None = None

    model_config = {"from_attributes": True}


class IncidentListResponse(BaseModel):
    incidents: list[IncidentResponse]
    total: int
    page: int
    per_page: int
