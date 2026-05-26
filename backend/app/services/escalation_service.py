"""
Escalation Service — Service 3
Manages configurable escalation timers per severity level.
Auto-assigns incidents to higher tiers when SLA breached.
"""
import asyncio

import structlog
from sqlalchemy import select

from app.config import get_settings
from app.database import async_session_maker
from app.models.incident import Incident, IncidentStatus
from app.models.user import User, UserTier
from app.events.publisher import publish_event
from app.events.contracts import EventType, IncidentEscalatedEvent
from app.events.subscriber import register_handler

logger = structlog.get_logger(__name__)
settings = get_settings()

# Active escalation timers: incident_id -> asyncio.Task
_active_timers: dict[int, asyncio.Task] = {}


def get_escalation_timeout(severity: str) -> int:
    """Get escalation timeout in seconds based on severity."""
    timeouts = {
        "P1": settings.ESCALATION_P1,
        "P2": settings.ESCALATION_P2,
        "P3": settings.ESCALATION_P3,
        "P4": settings.ESCALATION_P4,
    }
    return timeouts.get(severity, settings.ESCALATION_P3)


async def _escalation_timer(incident_id: int, severity: str, current_tier: int):
    """
    Background task that waits for the SLA timeout, then escalates.
    Gets cancelled if the incident is acknowledged in time.
    """
    timeout = get_escalation_timeout(severity)
    await logger.ainfo(
        "Escalation timer started",
        incident_id=incident_id,
        severity=severity,
        timeout_seconds=timeout,
        current_tier=current_tier,
    )

    try:
        await asyncio.sleep(timeout)

        # Timer expired — escalate!
        new_tier = min(current_tier + 1, 3)
        await logger.awarning(
            "Escalation triggered",
            incident_id=incident_id,
            from_tier=current_tier,
            to_tier=new_tier,
        )

        # Update incident in database
        async with async_session_maker() as db:
            result = await db.execute(
                select(Incident).where(Incident.id == incident_id)
            )
            incident = result.scalar_one_or_none()

            if incident and incident.status == IncidentStatus.OPEN:
                incident.escalation_tier = new_tier
                incident.escalation_count += 1

                # Try to auto-assign to someone in the higher tier
                higher_tier_user = await db.execute(
                    select(User).where(
                        User.tier == UserTier(new_tier),
                        User.is_active.is_(True),
                    ).limit(1)
                )
                assignee = higher_tier_user.scalar_one_or_none()
                if assignee:
                    incident.assigned_to = assignee.id

                await db.commit()

                # Publish escalation event
                await publish_event(IncidentEscalatedEvent(
                    incident_id=incident_id,
                    title=incident.title,
                    severity=severity,
                    from_tier=current_tier,
                    to_tier=new_tier,
                ))

                # Start another timer for the next tier
                if new_tier < 3:
                    start_escalation_timer(incident_id, severity, new_tier)

    except asyncio.CancelledError:
        await logger.ainfo(
            "Escalation timer cancelled (incident acknowledged)",
            incident_id=incident_id,
        )
    finally:
        _active_timers.pop(incident_id, None)


def start_escalation_timer(incident_id: int, severity: str, current_tier: int = 1):
    """Start an escalation timer for a new incident."""
    # Cancel any existing timer for this incident
    cancel_escalation_timer(incident_id)

    task = asyncio.create_task(
        _escalation_timer(incident_id, severity, current_tier)
    )
    _active_timers[incident_id] = task


def cancel_escalation_timer(incident_id: int):
    """Cancel an active escalation timer (e.g., when incident is acknowledged)."""
    task = _active_timers.pop(incident_id, None)
    if task and not task.done():
        task.cancel()


def cancel_all_timers():
    """Cancel all active timers (for shutdown)."""
    for incident_id, task in _active_timers.items():
        if not task.done():
            task.cancel()
    _active_timers.clear()


# === Event Handlers ===

async def handle_incident_created(data: dict):
    """Start escalation timer when a new incident is created."""
    incident_id = data.get("incident_id")
    severity = data.get("severity", "P3")
    if incident_id:
        start_escalation_timer(incident_id, severity)


async def handle_incident_acknowledged(data: dict):
    """Cancel escalation timer when incident is acknowledged."""
    incident_id = data.get("incident_id")
    if incident_id:
        cancel_escalation_timer(incident_id)
        await logger.ainfo("Escalation cancelled due to acknowledgement", incident_id=incident_id)


def register_escalation_handlers():
    """Register escalation event handlers with the subscriber."""
    register_handler(EventType.INCIDENT_CREATED, handle_incident_created)
    register_handler(EventType.INCIDENT_ACKNOWLEDGED, handle_incident_acknowledged)
    logger.info("Escalation handlers registered")
