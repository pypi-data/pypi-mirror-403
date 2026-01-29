"""Flag schemas for slopit.

This module defines the flag types generated during capture and analysis.
"""

from typing import Literal

from pydantic import BaseModel, Field

from slopit.schemas.types import JsonValue

Severity = Literal["info", "low", "medium", "high"]


class CaptureFlag(BaseModel):
    """Flag generated during data capture.

    Attributes
    ----------
    type
        Flag type identifier.
    severity
        Severity level of the flag.
    message
        Human-readable description.
    timestamp
        Unix timestamp in milliseconds when flag was generated.
    details
        Additional details about the flag.
    """

    type: str
    severity: Severity
    message: str
    timestamp: int
    details: dict[str, JsonValue] | None = None


class AnalysisFlag(BaseModel):
    """Flag generated during server-side analysis.

    Attributes
    ----------
    type
        Flag type identifier.
    analyzer
        Name of the analyzer that generated this flag.
    severity
        Severity level of the flag.
    message
        Human-readable description.
    confidence
        Confidence score between 0.0 and 1.0.
    evidence
        Evidence supporting this flag.
    trial_ids
        Related trial IDs if trial-specific.
    """

    type: str
    analyzer: str
    severity: Severity
    message: str
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    evidence: dict[str, JsonValue] | None = None
    trial_ids: list[str] | None = None
