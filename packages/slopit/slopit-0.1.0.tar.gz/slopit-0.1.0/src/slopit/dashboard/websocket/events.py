"""WebSocket event types.

This module defines the event types used for real-time communication
between the dashboard server and connected clients.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SessionNewEvent(BaseModel):
    """New session received event.

    Sent when a new session is received and stored by the dashboard,
    allowing connected clients to update their session lists.

    Attributes
    ----------
    type
        Fixed to "session.new" for this event type.
    data
        Contains session metadata (session_id, timestamp, etc.).

    Examples
    --------
    >>> event = SessionNewEvent(data={"session_id": "abc123"})
    >>> print(event.type)
    session.new
    """

    type: Literal["session.new"] = "session.new"
    data: dict[str, object] = Field(default_factory=dict, description="Event payload data")


class VerdictComputedEvent(BaseModel):
    """Analysis complete event.

    Sent when behavioral analysis has been computed for a session,
    providing verdict and flag information to connected clients.

    Attributes
    ----------
    type
        Fixed to "verdict.computed" for this event type.
    data
        Contains verdict results (session_id, flags, confidence, etc.).

    Examples
    --------
    >>> event = VerdictComputedEvent(
    ...     data={"session_id": "abc123", "verdict": "suspicious"}
    ... )
    >>> print(event.type)
    verdict.computed
    """

    type: Literal["verdict.computed"] = "verdict.computed"
    data: dict[str, object] = Field(default_factory=dict, description="Event payload data")


class SyncProgressEvent(BaseModel):
    """Sync progress event.

    Sent during JATOS or Prolific data synchronization to report
    progress and status to connected clients.

    Attributes
    ----------
    type
        Fixed to "sync.progress" for this event type.
    data
        Contains sync status (source, progress, total, status, etc.).

    Examples
    --------
    >>> event = SyncProgressEvent(
    ...     data={"source": "jatos", "progress": 50, "total": 100}
    ... )
    >>> print(event.type)
    sync.progress
    """

    type: Literal["sync.progress"] = "sync.progress"
    data: dict[str, object] = Field(default_factory=dict, description="Event payload data")


# Type alias for all WebSocket events (discriminated by "type" field)
type WebSocketEvent = SessionNewEvent | VerdictComputedEvent | SyncProgressEvent
