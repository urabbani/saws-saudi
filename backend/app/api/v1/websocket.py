"""
SAWS WebSocket API Endpoints

Real-time alert notifications via WebSocket.
"""

import json
from typing import Optional

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.base import get_db
from app.schemas.alert import Alert, AlertSummary

router = APIRouter()
settings = get_settings()


class ConnectionManager:
    """
    WebSocket connection manager for real-time alerts.

    Manages active WebSocket connections and broadcasts messages.
    """

    def __init__(self) -> None:
        """Initialize the connection manager."""
        # Store active connections by user_id
        self.active_connections: dict[str, list[WebSocket]] = {}
        self.logger = None

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        """
        Accept a new WebSocket connection.

        Args:
            websocket: WebSocket connection
            user_id: User ID for this connection
        """
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = []

        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        """
        Remove a WebSocket connection.

        Args:
            websocket: WebSocket connection to remove
            user_id: User ID for this connection
        """
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)

            # Clean up empty lists
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, websocket: WebSocket) -> None:
        """
        Send a message to a specific WebSocket connection.

        Args:
            message: Message to send (will be JSON serialized)
            websocket: Target WebSocket connection
        """
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            # Connection may be closed
            pass

    async def broadcast_to_user(self, message: dict, user_id: str) -> None:
        """
        Broadcast a message to all connections for a specific user.

        Args:
            message: Message to broadcast (will be JSON serialized)
            user_id: Target user ID
        """
        if user_id not in self.active_connections:
            return

        # Send to all connections for this user
        for connection in self.active_connections[user_id].copy():
            await self.send_personal_message(message, connection)

    async def broadcast_to_all(self, message: dict) -> None:
        """
        Broadcast a message to all active connections.

        Args:
            message: Message to broadcast (will be JSON serialized)
        """
        # Send to all users
        for user_id in list(self.active_connections.keys()):
            await self.broadcast_to_user(message, user_id)

    def get_connection_count(self, user_id: Optional[str] = None) -> int:
        """
        Get the number of active connections.

        Args:
            user_id: Optional user ID to count connections for

        Returns:
            Number of active connections
        """
        if user_id:
            return len(self.active_connections.get(user_id, []))
        return sum(len(conns) for conns in self.active_connections.values())


# Global connection manager instance
manager = ConnectionManager()


async def validate_websocket_token(token: Optional[str]) -> Optional[str]:
    """
    Validate WebSocket authentication token.

    Args:
        token: JWT token from query parameter

    Returns:
        User ID if valid, None otherwise
    """
    if not token:
        return None

    # TODO: Implement proper JWT validation
    # For now, accept any non-empty token in development
    if settings.debug:
        # In development, you can pass user_id directly as token
        # or use a simple token format: "user:{user_id}"
        if token.startswith("user:"):
            return token.split(":", 1)[1]
        return "dev_user"

    # In production, validate JWT properly
    # This is a placeholder - implement proper JWT validation
    try:
        # from jose import jwt
        # payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        # return payload.get("sub")
        return None
    except Exception:
        return None


@router.websocket("/ws/alerts")
async def websocket_alerts(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="Authentication token"),
) -> None:
    """
    WebSocket endpoint for real-time alert notifications.

    Connects clients to receive real-time alerts. Messages are sent as JSON.

    Message Types:
    - ALERT: New alert created
    - ALERT_UPDATE: Alert updated
    - WEATHER_UPDATE: Weather data updated
    - SATELLITE_UPDATE: Satellite data updated
    - DROUGHT_UPDATE: Drought status updated
    - PING: Keep-alive ping

    Example Message:
    ```json
    {
        "type": "ALERT",
        "data": {
            "id": "alert-123",
            "severity": "critical",
            "title": "Extreme Drought Alert",
            "message": "Severe drought conditions detected",
            "created_at": "2026-03-03T10:00:00Z"
        }
    }
    ```

    Args:
        websocket: WebSocket connection
        token: Authentication token (optional in development)
    """
    # Validate token and get user_id
    user_id = await validate_websocket_token(token)

    if not user_id:
        await websocket.close(code=1008, reason="Unauthorized")
        return

    # Connect the websocket
    await manager.connect(websocket, user_id)

    try:
        # Send welcome message
        await websocket.send_text(
            json.dumps(
                {
                    "type": "CONNECTED",
                    "data": {
                        "user_id": user_id,
                        "message": "Connected to SAWS alert stream",
                    },
                }
            )
        )

        # Keep connection alive and handle incoming messages
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)

                # Handle different message types
                message_type = message.get("type")

                if message_type == "PONG":
                    # Response to keep-alive ping
                    continue

                elif message_type == "SUBSCRIBE":
                    # Subscribe to specific alert types
                    # TODO: Implement subscription filtering
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "SUBSCRIBED",
                                "data": {"topics": message.get("topics", [])},
                            }
                        )
                    )

                elif message_type == "UNSUBSCRIBE":
                    # Unsubscribe from specific alert types
                    # TODO: Implement subscription filtering
                    await websocket.send_text(
                        json.dumps({"type": "UNSUBSCRIBED", "data": {}})
                    )

                elif message_type == "PING":
                    # Respond to ping with pong
                    await websocket.send_text(json.dumps({"type": "PONG", "data": {}}))

                else:
                    # Unknown message type
                    await websocket.send_text(
                        json.dumps(
                            {
                                "type": "ERROR",
                                "data": {"message": f"Unknown message type: {message_type}"},
                            }
                        )
                    )

            except json.JSONDecodeError:
                await websocket.send_text(
                    json.dumps(
                        {"type": "ERROR", "data": {"message": "Invalid JSON"}}
                    )
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception:
        manager.disconnect(websocket, user_id)


# Helper functions for broadcasting alerts

async def broadcast_alert(alert: Alert, user_id: str) -> None:
    """
    Broadcast an alert to a user's WebSocket connections.

    Args:
        alert: Alert to broadcast
        user_id: Target user ID
    """
    message = {
        "type": "ALERT",
        "data": {
            "id": alert.id,
            "severity": alert.severity.value,
            "alert_type": alert.alert_type.value,
            "title": alert.title,
            "message": alert.message,
            "field_id": alert.field_id,
            "district": alert.district,
            "is_read": alert.is_read,
            "created_at": alert.created_at.isoformat(),
        },
    }

    await manager.broadcast_to_user(message, user_id)


async def broadcast_alert_update(alert_id: str, user_id: str) -> None:
    """
    Broadcast an alert update to a user's WebSocket connections.

    Args:
        alert_id: Alert ID that was updated
        user_id: Target user ID
    """
    message = {
        "type": "ALERT_UPDATE",
        "data": {"alert_id": alert_id, "updated_at": alert_id},
    }

    await manager.broadcast_to_user(message, user_id)


async def broadcast_weather_update(
    field_id: str, user_id: str, weather_data: dict
) -> None:
    """
    Broadcast weather data update.

    Args:
        field_id: Field ID for the weather update
        user_id: Target user ID
        weather_data: Weather data to broadcast
    """
    message = {
        "type": "WEATHER_UPDATE",
        "data": {"field_id": field_id, **weather_data},
    }

    await manager.broadcast_to_user(message, user_id)


async def broadcast_satellite_update(
    field_id: str, user_id: str, satellite_data: dict
) -> None:
    """
    Broadcast satellite data update.

    Args:
        field_id: Field ID for the satellite update
        user_id: Target user ID
        satellite_data: Satellite data to broadcast
    """
    message = {
        "type": "SATELLITE_UPDATE",
        "data": {"field_id": field_id, **satellite_data},
    }

    await manager.broadcast_to_user(message, user_id)


async def broadcast_drought_update(
    district: str, drought_data: dict
) -> None:
    """
    Broadcast drought status update to all users in a district.

    Args:
        district: District name
        drought_data: Drought data to broadcast
    """
    message = {
        "type": "DROUGHT_UPDATE",
        "data": {"district": district, **drought_data},
    }

    # Broadcast to all users (district filtering could be added)
    await manager.broadcast_to_all(message)


__all__ = [
    "router",
    "manager",
    "broadcast_alert",
    "broadcast_alert_update",
    "broadcast_weather_update",
    "broadcast_satellite_update",
    "broadcast_drought_update",
]
