"""WebSocket message handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import WebSocket

    from slopit.dashboard.websocket.manager import ConnectionManager


async def handle_message(
    websocket: WebSocket,
    message: str,
    manager: ConnectionManager,
) -> None:
    """Handle incoming WebSocket message.

    Parameters
    ----------
    websocket
        The WebSocket connection that sent the message.
    message
        The raw message string.
    manager
        The connection manager for broadcasting responses.
    """
    # TODO: Implement message handling (subscriptions, filters, etc.)
    _ = websocket
    _ = message
    _ = manager
