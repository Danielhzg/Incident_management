"""
Incident ORM model.
Core entity representing a production incident with full lifecycle tracking.
"""
import enum
from datetime import datetime

from sqlalchemy import String, Text, Enum, DateTime, ForeignKey, Integer, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class IncidentSeverity(str, enum.Enum):
    P1 = "P1"  # Critical
    P2 = "P2"  # High
    P3 = "P3"  # Medium
    P4 = "P4"  # Low


class IncidentStatus(str, enum.Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    CLOSED = "closed"


# Valid status transitions (state machine)
VALID_TRANSITIONS = {
    IncidentStatus.OPEN: [IncidentStatus.ACKNOWLEDGED, IncidentStatus.CLOSED],
    IncidentStatus.ACKNOWLEDGED: [IncidentStatus.INVESTIGATING, IncidentStatus.RESOLVED, IncidentStatus.CLOSED],
    IncidentStatus.INVESTIGATING: [IncidentStatus.RESOLVED, IncidentStatus.CLOSED],
    IncidentStatus.RESOLVED: [IncidentStatus.CLOSED],
    IncidentStatus.CLOSED: [],  # Terminal state
}


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[IncidentSeverity] = mapped_column(
        Enum(IncidentSeverity, name="incident_severity", create_constraint=True),
        nullable=False,
        index=True,
    )
    status: Mapped[IncidentStatus] = mapped_column(
        Enum(IncidentStatus, name="incident_status", create_constraint=True),
        default=IncidentStatus.OPEN,
        nullable=False,
        index=True,
    )
    source: Mapped[str] = mapped_column(String(255), default="manual", nullable=False)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)  # Comma-separated tags

    # Assignment & acknowledgement
    assigned_to: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    acknowledged_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    resolved_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )

    # Escalation
    escalation_tier: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    escalation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Soft delete
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    assignee = relationship("User", back_populates="assigned_incidents", foreign_keys=[assigned_to])
    acknowledger = relationship("User", back_populates="acknowledged_incidents", foreign_keys=[acknowledged_by])
    resolver = relationship("User", back_populates="resolved_incidents", foreign_keys=[resolved_by])
    postmortems = relationship("PostMortem", back_populates="incident", cascade="all, delete-orphan")

    def can_transition_to(self, new_status: IncidentStatus) -> bool:
        """Check if a status transition is valid per the state machine."""
        return new_status in VALID_TRANSITIONS.get(self.status, [])

    def __repr__(self) -> str:
        return f"<Incident(id={self.id}, title={self.title}, severity={self.severity}, status={self.status})>"
