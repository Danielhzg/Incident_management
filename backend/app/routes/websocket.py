"""
WebSocket route — real-time communication endpoint.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.auth.jwt_handler import decode_access_token
from app.services.notification_service import manager

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(default="")):
    """
    WebSocket endpoint for real-time notifications.
    Auth via query parameter: ws://host/ws?token=JWT_TOKEN
    """
    # Authenticate
    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Invalid or missing token")
        return

    user_id = int(payload.get("sub", 0))
    if not user_id:
        await websocket.close(code=4001, reason="Invalid token payload")
        return

    # Connect
    await manager.connect(user_id, websocket)

    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "data": {
                "message": "Connected to incident notification stream",
                "user_id": user_id,
                "active_connections": manager.connection_count,
            }
        })

        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            # Client can send ping/pong or other messages
            if data == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        await manager.disconnect(user_id)
    except Exception:
        await manager.disconnect(user_id)
