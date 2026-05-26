"""
Notification Service — Service 2
Manages WebSocket connections and pushes real-time alerts to connected clients.
"""
import asyncio
from datetime import datetime, timezone
from fastapi import WebSocket

import structlog

from app.events.contracts import EventType
from app.events.subscriber import register_handler

logger = structlog.get_logger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self):
        self.active_connections: dict[int, WebSocket] = {}  # user_id -> websocket
        self._lock = asyncio.Lock()

    async def connect(self, user_id: int, websocket: WebSocket):
        """Register a new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self.active_connections[user_id] = websocket
        await logger.ainfo("WebSocket connected", user_id=user_id, total=len(self.active_connections))

    async def disconnect(self, user_id: int):
        """Remove a WebSocket connection."""
        async with self._lock:
            self.active_connections.pop(user_id, None)
        await logger.ainfo("WebSocket disconnected", user_id=user_id, total=len(self.active_connections))

    async def send_personal(self, user_id: int, message: dict):
        """Send a message to a specific user."""
        ws = self.active_connections.get(user_id)
        if ws:
            try:
                await ws.send_json(message)
            except Exception as e:
                await logger.aerror("Failed to send personal message", user_id=user_id, error=str(e))
                await self.disconnect(user_id)

    async def broadcast(self, message: dict, exclude_user: int | None = None):
        """Broadcast a message to all connected clients."""
        disconnected = []
        async with self._lock:
            connections = dict(self.active_connections)

        for user_id, ws in connections.items():
            if exclude_user and user_id == exclude_user:
                continue
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(user_id)

        # Clean up dead connections
        for uid in disconnected:
            await self.disconnect(uid)

        await logger.ainfo(
            "Broadcast sent",
            recipients=len(connections) - len(disconnected) - (1 if exclude_user else 0),
        )

    @property
    def connection_count(self) -> int:
        return len(self.active_connections)


# Singleton instance
manager = ConnectionManager()


# === Event Handlers ===

async def handle_incident_created(data: dict):
    """Push notification when a new incident is created."""
    await manager.broadcast({
        "type": "incident_created",
        "data": {
            "incident_id": data.get("incident_id"),
            "title": data.get("title"),
            "severity": data.get("severity"),
            "source": data.get("source"),
            "message": f"🚨 New {data.get('severity')} incident: {data.get('title')}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    })


async def handle_incident_acknowledged(data: dict):
    """Push notification when an incident is acknowledged."""
    await manager.broadcast({
        "type": "incident_acknowledged",
        "data": {
            "incident_id": data.get("incident_id"),
            "engineer_name": data.get("engineer_name"),
            "message": f"✅ Incident #{data.get('incident_id')} acknowledged by {data.get('engineer_name')}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    })


async def handle_incident_resolved(data: dict):
    """Push notification when an incident is resolved."""
    await manager.broadcast({
        "type": "incident_resolved",
        "data": {
            "incident_id": data.get("incident_id"),
            "resolver_name": data.get("resolver_name"),
            "ttr": data.get("time_to_resolve_seconds"),
            "message": f"🎉 Incident #{data.get('incident_id')} resolved by {data.get('resolver_name')}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    })


async def handle_incident_escalated(data: dict):
    """Push notification when an incident is escalated."""
    await manager.broadcast({
        "type": "incident_escalated",
        "data": {
            "incident_id": data.get("incident_id"),
            "title": data.get("title"),
            "severity": data.get("severity"),
            "from_tier": data.get("from_tier"),
            "to_tier": data.get("to_tier"),
            "message": f"⬆️ Incident #{data.get('incident_id')} escalated to Tier {data.get('to_tier')}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    })


def register_notification_handlers():
    """Register all notification event handlers with the subscriber."""
    register_handler(EventType.INCIDENT_CREATED, handle_incident_created)
    register_handler(EventType.INCIDENT_ACKNOWLEDGED, handle_incident_acknowledged)
    register_handler(EventType.INCIDENT_RESOLVED, handle_incident_resolved)
    register_handler(EventType.INCIDENT_ESCALATED, handle_incident_escalated)
    logger.info("Notification handlers registered")
