"""Pydantic schemas for slopit data structures.

These schemas mirror the TypeScript schemas in @slopit/core exactly,
providing the same validation and type safety in Python.
"""

from slopit.schemas.behavioral import (
    BehavioralData,
    BehavioralMetrics,
    ClipboardCopyEvent,
    ErrorEvent,
    FocusEvent,
    FocusMetrics,
    GlobalEvents,
    InputDurationEvent,
    InputDurationMetrics,
    KeystrokeEvent,
    KeystrokeMetrics,
    ModifierState,
    MouseEvent,
    MouseMetrics,
    PasteEvent,
    ScrollEvent,
    ScrollMetrics,
    SessionFocusEvent,
    TimingMetrics,
)
from slopit.schemas.flags import AnalysisFlag, CaptureFlag, Severity
from slopit.schemas.session import (
    EnvironmentInfo,
    PlatformInfo,
    ResponseInfo,
    SessionTiming,
    SlopitSession,
    SlopitTrial,
    StimulusInfo,
)

__all__ = [
    "AnalysisFlag",
    "BehavioralData",
    "BehavioralMetrics",
    "CaptureFlag",
    "ClipboardCopyEvent",
    "EnvironmentInfo",
    "ErrorEvent",
    "FocusEvent",
    "FocusMetrics",
    "GlobalEvents",
    "InputDurationEvent",
    "InputDurationMetrics",
    "KeystrokeEvent",
    "KeystrokeMetrics",
    "ModifierState",
    "MouseEvent",
    "MouseMetrics",
    "PasteEvent",
    "PlatformInfo",
    "ResponseInfo",
    "ScrollEvent",
    "ScrollMetrics",
    "SessionFocusEvent",
    "SessionTiming",
    "Severity",
    "SlopitSession",
    "SlopitTrial",
    "StimulusInfo",
    "TimingMetrics",
]
