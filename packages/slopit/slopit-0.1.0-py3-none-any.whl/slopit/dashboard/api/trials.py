"""Trial endpoints.

This module provides API endpoints for accessing and managing
individual trial data within sessions.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

router = APIRouter()


class KeystrokeEvent(BaseModel):
    """A single keystroke event.

    Attributes
    ----------
    time
        Time since trial start in milliseconds.
    key
        Key value from KeyboardEvent.key.
    code
        Physical key code from KeyboardEvent.code.
    event
        Event type, either keydown or keyup.
    """

    time: float = Field(ge=0, description="Time in milliseconds")
    key: str = Field(description="Key value")
    code: str = Field(description="Physical key code")
    event: str = Field(description="Event type (keydown/keyup)")


class TrialDetail(BaseModel):
    """Full trial details.

    Attributes
    ----------
    session_id
        Parent session identifier.
    trial_index
        Zero-based index of the trial.
    trial_type
        Type or name of the trial.
    response_text
        Text response submitted by the participant.
    keystrokes
        List of keystroke events captured during the trial.
    start_time
        Trial start timestamp in milliseconds.
    end_time
        Trial end timestamp in milliseconds.
    metadata
        Additional trial metadata.
    """

    session_id: str = Field(description="Parent session identifier")
    trial_index: int = Field(ge=0, description="Trial index")
    trial_type: str = Field(description="Trial type identifier")
    response_text: str = Field(default="", description="Response text")
    keystrokes: list[KeystrokeEvent] = Field(
        default_factory=list[KeystrokeEvent], description="Keystroke events"
    )
    start_time: float = Field(ge=0, description="Start timestamp (ms)")
    end_time: float = Field(ge=0, description="End timestamp (ms)")
    metadata: dict[str, str | int | float | bool | None] = Field(
        default_factory=dict, description="Trial metadata"
    )


class TrialMetrics(BaseModel):
    """Computed metrics for a trial.

    Attributes
    ----------
    session_id
        Parent session identifier.
    trial_index
        Zero-based index of the trial.
    total_keystrokes
        Total number of keystroke events.
    mean_iki
        Mean inter-keystroke interval in milliseconds.
    iki_variance
        Variance of inter-keystroke intervals.
    typing_speed
        Characters per minute.
    pause_count
        Number of pauses exceeding threshold.
    backspace_rate
        Proportion of keystrokes that were backspaces.
    """

    session_id: str = Field(description="Parent session identifier")
    trial_index: int = Field(ge=0, description="Trial index")
    total_keystrokes: int = Field(ge=0, description="Total keystroke events")
    mean_iki: float | None = Field(default=None, ge=0, description="Mean IKI (ms)")
    iki_variance: float | None = Field(default=None, ge=0, description="IKI variance")
    typing_speed: float | None = Field(default=None, ge=0, description="Characters per minute")
    pause_count: int = Field(default=0, ge=0, description="Number of pauses")
    backspace_rate: float | None = Field(
        default=None, ge=0, le=1, description="Backspace proportion"
    )


class TrialListItem(BaseModel):
    """Summary of a trial for list views.

    Attributes
    ----------
    session_id
        Parent session identifier.
    trial_index
        Zero-based index of the trial.
    trial_type
        Type or name of the trial.
    response_length
        Character count of the response.
    keystroke_count
        Number of keystroke events.
    """

    session_id: str = Field(description="Parent session identifier")
    trial_index: int = Field(ge=0, description="Trial index")
    trial_type: str = Field(description="Trial type identifier")
    response_length: int = Field(ge=0, description="Response length")
    keystroke_count: int = Field(ge=0, description="Keystroke count")


class TrialListResponse(BaseModel):
    """Paginated response for trial list endpoint.

    Attributes
    ----------
    trials
        List of trial summaries for the current page.
    total
        Total number of trials matching the query.
    page
        Current page number (1-indexed).
    page_size
        Number of trials per page.
    """

    trials: list[TrialListItem] = Field(description="Trial summaries")
    total: int = Field(ge=0, description="Total matching trials")
    page: int = Field(ge=1, description="Current page number")
    page_size: int = Field(ge=1, description="Trials per page")


@router.get("/", response_model=TrialListResponse)
async def list_trials(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=200, description="Trials per page"),
    session_id: str | None = Query(default=None, description="Filter by session"),
    trial_type: str | None = Query(default=None, description="Filter by trial type"),
) -> TrialListResponse:
    """List trials with pagination.

    Returns a paginated list of trial summaries across all sessions.
    Use session_id or trial_type parameters to filter results.

    Parameters
    ----------
    page
        Page number to retrieve (1-indexed).
    page_size
        Number of trials per page (max 200).
    session_id
        Filter by parent session identifier.
    trial_type
        Filter by trial type.

    Returns
    -------
    TrialListResponse
        Paginated list of trial summaries.
    """
    # TODO: Implement with storage service
    _ = (session_id, trial_type)  # Suppress unused variable warning
    return TrialListResponse(trials=[], total=0, page=page, page_size=page_size)


@router.get("/{session_id}/{trial_index}", response_model=TrialDetail)
async def get_trial(session_id: str, trial_index: int) -> TrialDetail:
    """Get trial details.

    Retrieves full details for a specific trial, including response
    text and keystroke data.

    Parameters
    ----------
    session_id
        Parent session identifier.
    trial_index
        Zero-based index of the trial.

    Returns
    -------
    TrialDetail
        Full trial details with keystrokes.

    Raises
    ------
    HTTPException
        404 if session or trial not found.
    """
    # TODO: Implement with storage service
    raise HTTPException(
        status_code=404,
        detail=f"Trial not found: session={session_id}, index={trial_index}",
    )


@router.get("/{session_id}/{trial_index}/keystrokes", response_model=list[KeystrokeEvent])
async def get_trial_keystrokes(
    session_id: str,
    trial_index: int,
    limit: int = Query(default=1000, ge=1, le=10000, description="Maximum events to return"),
    offset: int = Query(default=0, ge=0, description="Number of events to skip"),
) -> list[KeystrokeEvent]:
    """Get keystroke events for a trial.

    Retrieves keystroke events with pagination support for trials
    with large numbers of events.

    Parameters
    ----------
    session_id
        Parent session identifier.
    trial_index
        Zero-based index of the trial.
    limit
        Maximum number of events to return (max 10000).
    offset
        Number of events to skip.

    Returns
    -------
    list[KeystrokeEvent]
        List of keystroke events.

    Raises
    ------
    HTTPException
        404 if session or trial not found.
    """
    # TODO: Implement with storage service
    _ = (session_id, trial_index, limit, offset)  # Suppress unused variable warning
    return []


@router.get("/{session_id}/{trial_index}/metrics", response_model=TrialMetrics)
async def get_trial_metrics(session_id: str, trial_index: int) -> TrialMetrics:
    """Get computed metrics for a trial.

    Retrieves pre-computed behavioral metrics for a trial, including
    typing speed, IKI statistics, and pause analysis.

    Parameters
    ----------
    session_id
        Parent session identifier.
    trial_index
        Zero-based index of the trial.

    Returns
    -------
    TrialMetrics
        Computed metrics for the trial.

    Raises
    ------
    HTTPException
        404 if session or trial not found.
    """
    # TODO: Implement with analysis service
    raise HTTPException(
        status_code=404,
        detail=f"Metrics not found: session={session_id}, index={trial_index}",
    )
