"""
Tests for the Incident Service — CRUD, status transitions, and validation.
"""
from app.models.incident import IncidentStatus, IncidentSeverity, VALID_TRANSITIONS, Incident


def test_valid_status_transitions():
    """Test the state machine allows correct transitions."""
    assert IncidentStatus.ACKNOWLEDGED in VALID_TRANSITIONS[IncidentStatus.OPEN]
    assert IncidentStatus.INVESTIGATING in VALID_TRANSITIONS[IncidentStatus.ACKNOWLEDGED]
    assert IncidentStatus.RESOLVED in VALID_TRANSITIONS[IncidentStatus.INVESTIGATING]
    assert IncidentStatus.CLOSED in VALID_TRANSITIONS[IncidentStatus.RESOLVED]


def test_invalid_status_transitions():
    """Test the state machine blocks invalid transitions."""
    # Can't go from OPEN directly to RESOLVED
    assert IncidentStatus.RESOLVED not in VALID_TRANSITIONS[IncidentStatus.OPEN]
    # Can't go from CLOSED to anything
    assert len(VALID_TRANSITIONS[IncidentStatus.CLOSED]) == 0
    # Can't go from RESOLVED to OPEN
    assert IncidentStatus.OPEN not in VALID_TRANSITIONS[IncidentStatus.RESOLVED]


def test_incident_can_transition_to():
    """Test the Incident model's can_transition_to method."""
    incident = Incident(
        title="Test",
        description="Test incident",
        severity=IncidentSeverity.P1,
        status=IncidentStatus.OPEN,
    )

    assert incident.can_transition_to(IncidentStatus.ACKNOWLEDGED) is True
    assert incident.can_transition_to(IncidentStatus.RESOLVED) is False
    assert incident.can_transition_to(IncidentStatus.CLOSED) is True


def test_severity_values():
    """Test severity enum values."""
    assert IncidentSeverity.P1.value == "P1"
    assert IncidentSeverity.P2.value == "P2"
    assert IncidentSeverity.P3.value == "P3"
    assert IncidentSeverity.P4.value == "P4"


def test_status_values():
    """Test status enum values."""
    assert IncidentStatus.OPEN.value == "open"
    assert IncidentStatus.ACKNOWLEDGED.value == "acknowledged"
    assert IncidentStatus.INVESTIGATING.value == "investigating"
    assert IncidentStatus.RESOLVED.value == "resolved"
    assert IncidentStatus.CLOSED.value == "closed"
