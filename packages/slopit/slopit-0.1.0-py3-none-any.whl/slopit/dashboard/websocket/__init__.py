"""WebSocket support for the slopit dashboard.

This subpackage provides WebSocket connection management, message handlers,
and event types for real-time updates to connected clients.
"""

from __future__ import annotations

from slopit.dashboard.websocket.events import (
    SessionNewEvent,
    SyncProgressEvent,
    VerdictComputedEvent,
    WebSocketEvent,
)
from slopit.dashboard.websocket.handlers import handle_message
from slopit.dashboard.websocket.manager import ConnectionManager

__all__ = [
    "ConnectionManager",
    "SessionNewEvent",
    "SyncProgressEvent",
    "VerdictComputedEvent",
    "WebSocketEvent",
    "handle_message",
]
