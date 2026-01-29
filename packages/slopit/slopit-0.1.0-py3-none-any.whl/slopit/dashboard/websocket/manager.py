"""WebSocket connection manager."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import WebSocket

    from slopit.dashboard.websocket.events import WebSocketEvent


class ConnectionManager:
    """Manages WebSocket connections for real-time updates.

    Handles connection lifecycle and message broadcasting to
    all connected clients.

    Examples
    --------
    >>> manager = ConnectionManager()
    >>> # In FastAPI endpoint:
    >>> await manager.connect(websocket)
    >>> await manager.broadcast(SessionNewEvent(data={"session_id": "abc"}))
    """

    def __init__(self) -> None:
        self._connections: list[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection.

        Parameters
        ----------
        websocket
            The WebSocket connection to register.
        """
        await websocket.accept()
        async with self._lock:
            self._connections.append(websocket)

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection.

        Parameters
        ----------
        websocket
            The WebSocket connection to remove.
        """
        async with self._lock:
            if websocket in self._connections:
                self._connections.remove(websocket)

    async def broadcast(self, event: WebSocketEvent) -> None:
        """Send an event to all connected clients.

        Parameters
        ----------
        event
            The event to broadcast.
        """
        message = event.model_dump_json()
        async with self._lock:
            disconnected: list[WebSocket] = []
            for connection in self._connections:
                try:
                    await connection.send_text(message)
                except Exception:
                    disconnected.append(connection)

            # Clean up disconnected clients
            for ws in disconnected:
                self._connections.remove(ws)

    async def send_personal(self, websocket: WebSocket, event: WebSocketEvent) -> None:
        """Send an event to a specific client.

        Parameters
        ----------
        websocket
            The target WebSocket connection.
        event
            The event to send.
        """
        await websocket.send_text(event.model_dump_json())

    @property
    def connection_count(self) -> int:
        """Number of active connections."""
        return len(self._connections)
