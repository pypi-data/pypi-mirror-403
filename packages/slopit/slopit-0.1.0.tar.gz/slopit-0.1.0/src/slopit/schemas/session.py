"""Session and environment schemas for slopit.

This module defines the root container types for participant sessions
and environment metadata.
"""

from typing import Literal

from pydantic import BaseModel, Field

from slopit.schemas.behavioral import BehavioralData, GlobalEvents
from slopit.schemas.flags import CaptureFlag
from slopit.schemas.types import JsonValue


class PlatformInfo(BaseModel):
    """Information about the experiment platform.

    Attributes
    ----------
    name
        Platform identifier. Known values include "jspsych", "labjs",
        "psychojs", "gorilla", "qualtrics", and "custom".
    version
        Platform version string.
    adapter_version
        Version of the slopit adapter used.
    """

    name: str
    version: str | None = None
    adapter_version: str | None = None


class EnvironmentInfo(BaseModel):
    """Client environment information captured at session start.

    Attributes
    ----------
    user_agent
        Browser user agent string.
    screen_resolution
        Screen dimensions as (width, height) in pixels.
    viewport_size
        Viewport dimensions as (width, height) in pixels.
    device_pixel_ratio
        Device pixel ratio for high-DPI displays.
    timezone
        IANA timezone identifier (e.g., "America/New_York").
    language
        Browser language setting (e.g., "en-US").
    touch_capable
        Whether touch input is available.
    connection_type
        Estimated connection type from Navigator.connection API.
    """

    user_agent: str
    screen_resolution: tuple[int, int]
    viewport_size: tuple[int, int]
    device_pixel_ratio: float
    timezone: str
    language: str
    touch_capable: bool
    connection_type: str | None = None


class SessionTiming(BaseModel):
    """Session-level timing information.

    Attributes
    ----------
    start_time
        Session start as Unix timestamp in milliseconds.
    end_time
        Session end as Unix timestamp in milliseconds.
        None if session is incomplete.
    duration
        Total duration in milliseconds.
    """

    start_time: int
    end_time: int | None = None
    duration: int | None = None


class StimulusInfo(BaseModel):
    """Information about a trial stimulus.

    Attributes
    ----------
    type
        Stimulus type category.
    content
        Stimulus content. For text, the text content. For media,
        URL or data URI. For HTML, the HTML string.
    content_hash
        SHA-256 hash of content for deduplication.
    parameters
        Additional stimulus parameters.
    """

    type: Literal["text", "image", "audio", "video", "html", "other"]
    content: str | None = None
    content_hash: str | None = None
    parameters: dict[str, JsonValue] | None = None


class ResponseInfo(BaseModel):
    """Participant response information.

    Attributes
    ----------
    type
        Response type category.
    value
        Response value. Type depends on response type.
    character_count
        For text responses, the character count.
    word_count
        For text responses, the word count.
    """

    type: Literal["text", "choice", "multi-choice", "slider", "likert", "annotation", "other"]
    value: JsonValue
    character_count: int | None = None
    word_count: int | None = None


class SlopitTrial(BaseModel):
    """Data for a single trial.

    Attributes
    ----------
    trial_id
        Unique trial identifier.
    trial_index
        Zero-indexed position in the session.
    trial_type
        Trial type identifier from the platform.
    start_time
        Trial start as Unix timestamp in milliseconds.
    end_time
        Trial end as Unix timestamp in milliseconds.
    rt
        Response time in milliseconds.
    stimulus
        Stimulus information.
    response
        Participant response.
    behavioral
        Behavioral capture data.
    platform_data
        Platform-specific trial data passed through.
    capture_flags
        Flags generated during capture.
    """

    trial_id: str
    trial_index: int
    trial_type: str | None = None
    start_time: int
    end_time: int
    rt: int | None = None
    stimulus: StimulusInfo | None = None
    response: ResponseInfo | None = None
    behavioral: BehavioralData | None = None
    platform_data: dict[str, JsonValue] | None = None
    capture_flags: list[CaptureFlag] | None = None


class SlopitSession(BaseModel):
    """Root container for a participant session.

    This is the primary data structure consumed by all analyzers.
    Platform adapters convert their native formats to this schema.

    Attributes
    ----------
    schema_version
        Schema version for forward compatibility. Current: "1.0".
    session_id
        Unique session identifier.
    participant_id
        Participant identifier from recruitment platform.
    study_id
        Study identifier.
    platform
        Platform information.
    environment
        Client environment information.
    timing
        Session timing information.
    trials
        List of trial data.
    global_events
        Events not tied to specific trials.
    metadata
        Additional session metadata.

    Examples
    --------
    Load a session from a JSON file:

    >>> from slopit import load_session
    >>> session = load_session("data/participant_001.json")
    >>> print(f"Session {session.session_id} has {len(session.trials)} trials")

    Validate raw data:

    >>> from slopit.schemas import SlopitSession
    >>> session = SlopitSession.model_validate(raw_dict)
    """

    schema_version: Literal["1.0"] = "1.0"
    session_id: str
    participant_id: str | None = None
    study_id: str | None = None
    platform: PlatformInfo
    environment: EnvironmentInfo
    timing: SessionTiming
    trials: list[SlopitTrial] = Field(default_factory=lambda: list[SlopitTrial]())
    global_events: GlobalEvents
    metadata: dict[str, JsonValue] | None = None
