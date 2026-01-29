"""Type definitions for slopit schemas.

This module defines type aliases used throughout the slopit package.
"""

from typing import Literal

# JSON-compatible value type
type JsonPrimitive = str | int | float | bool | None
type JsonValue = JsonPrimitive | list["JsonValue"] | dict[str, "JsonValue"]

# Schema types
type Severity = Literal["info", "low", "medium", "high"]
type EventType = Literal["keydown", "keyup"]
type FocusEventType = Literal["focus", "blur", "visibilitychange"]
type VisibilityState = Literal["visible", "hidden"]
type StimulusType = Literal["text", "image", "audio", "video", "html", "other"]
type ResponseType = Literal[
    "text", "choice", "multi-choice", "slider", "likert", "annotation", "other"
]
type VerdictStatus = Literal["clean", "suspicious", "flagged"]

# Timing types
type Milliseconds = float
type UnixTimestamp = int

# Identifier types
type SessionId = str
type TrialId = str
type ParticipantId = str
type StudyId = str
