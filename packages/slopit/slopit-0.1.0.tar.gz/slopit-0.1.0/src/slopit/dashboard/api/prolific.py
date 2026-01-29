"""Prolific integration endpoints.

This module provides API endpoints for interacting with the
Prolific participant recruitment platform.
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from slopit.dashboard.integrations import (
    ParticipantAction,
    ProlificClient,
    SubmissionStatus,
)

if TYPE_CHECKING:
    from slopit.schemas.types import JsonValue

router = APIRouter()


def _get_int(data: dict[str, JsonValue], key: str, default: int = 0) -> int:
    """Safely extract an integer value from a JSON dictionary."""
    value = data.get(key, default)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    return default


def _get_str(data: dict[str, JsonValue], key: str, default: str = "") -> str:
    """Safely extract a string value from a JSON dictionary."""
    value = data.get(key)
    if value is None:
        return default
    return str(value)


class ProlificConnectionConfig(BaseModel):
    """Configuration for connecting to Prolific.

    Attributes
    ----------
    token
        Prolific API token for authentication.
    """

    token: str = Field(description="Prolific API token")


class ProlificStudySummary(BaseModel):
    """Summary of a Prolific study.

    Attributes
    ----------
    id
        Prolific study ID.
    name
        Study name.
    status
        Current study status.
    total_available_places
        Total participant slots.
    places_taken
        Number of slots filled.
    """

    id: str = Field(description="Study ID")
    name: str = Field(description="Study name")
    status: str = Field(description="Study status")
    total_available_places: int = Field(ge=0, description="Total participant slots")
    places_taken: int = Field(ge=0, description="Slots filled")


class ProlificStudyListResponse(BaseModel):
    """Response containing list of Prolific studies.

    Attributes
    ----------
    studies
        List of study summaries.
    """

    studies: list[ProlificStudySummary] = Field(description="List of studies")


class ProlificSubmissionSummary(BaseModel):
    """Summary of a Prolific submission.

    Attributes
    ----------
    id
        Submission ID.
    participant_id
        Prolific participant ID.
    status
        Current submission status.
    started_at
        ISO 8601 timestamp when participant started.
    completed_at
        ISO 8601 timestamp when participant completed.
    """

    id: str = Field(description="Submission ID")
    participant_id: str = Field(description="Participant ID")
    status: str = Field(description="Submission status")
    started_at: str | None = Field(default=None, description="Start timestamp")
    completed_at: str | None = Field(default=None, description="Completion timestamp")


class ProlificSubmissionListResponse(BaseModel):
    """Response containing list of submissions.

    Attributes
    ----------
    submissions
        List of submission summaries.
    total
        Total number of submissions.
    """

    submissions: list[ProlificSubmissionSummary] = Field(description="Submissions")
    total: int = Field(ge=0, description="Total submissions")


class TransitionRequest(BaseModel):
    """Request to transition a submission.

    Attributes
    ----------
    token
        Prolific API token.
    submission_id
        The submission to transition.
    action
        Action to perform (APPROVE, REJECT, RETURN).
    rejection_category
        Required when action is REJECT.
    message
        Optional message to participant.
    """

    token: str = Field(description="Prolific API token")
    submission_id: str = Field(description="Submission ID")
    action: ParticipantAction = Field(description="Action to take")
    rejection_category: str | None = Field(
        default=None, description="Rejection category (required for REJECT)"
    )
    message: str | None = Field(default=None, description="Message to participant")


class BatchTransitionRequest(BaseModel):
    """Request to batch transition multiple submissions.

    Attributes
    ----------
    token
        Prolific API token.
    study_id
        The Prolific study ID.
    submission_ids
        List of submission IDs to transition.
    action
        Action to perform on all submissions.
    rejection_category
        Required when action is REJECT.
    """

    token: str = Field(description="Prolific API token")
    study_id: str = Field(description="Study ID")
    submission_ids: list[str] = Field(description="Submission IDs to transition")
    action: ParticipantAction = Field(description="Action to take")
    rejection_category: str | None = Field(
        default=None, description="Rejection category (required for REJECT)"
    )


class TransitionResponse(BaseModel):
    """Response from a transition operation.

    Attributes
    ----------
    success
        Whether the operation succeeded.
    submission_id
        The transitioned submission ID.
    new_status
        The new status after transition.
    """

    success: bool = Field(description="Operation success")
    submission_id: str = Field(description="Submission ID")
    new_status: str = Field(description="New status")


class BatchTransitionResponse(BaseModel):
    """Response from a batch transition operation.

    Attributes
    ----------
    success_count
        Number of successful transitions.
    failure_count
        Number of failed transitions.
    """

    success_count: int = Field(ge=0, description="Successful transitions")
    failure_count: int = Field(ge=0, description="Failed transitions")


@router.post("/connect", response_model=ProlificStudyListResponse)
async def connect_and_list_studies(
    config: ProlificConnectionConfig,
) -> ProlificStudyListResponse:
    """Connect to Prolific and list available studies.

    Validates the connection credentials and returns a list of
    studies for the account.

    Parameters
    ----------
    config
        Prolific connection configuration with token.

    Returns
    -------
    ProlificStudyListResponse
        List of available studies.

    Raises
    ------
    HTTPException
        401 if authentication fails.
        502 if Prolific API is unreachable.
    """
    async with ProlificClient(config.token) as client:
        try:
            raw_studies = await client.list_studies()
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "403" in error_msg:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid Prolific API token",
                ) from e
            raise HTTPException(
                status_code=502,
                detail=f"Failed to connect to Prolific: {error_msg}",
            ) from e

        studies: list[ProlificStudySummary] = []
        for raw in raw_studies:
            study_id = raw.get("id")
            name = raw.get("name")
            if study_id is not None and name is not None:
                studies.append(
                    ProlificStudySummary(
                        id=str(study_id),
                        name=str(name),
                        status=_get_str(raw, "status", "UNKNOWN"),
                        total_available_places=_get_int(raw, "total_available_places"),
                        places_taken=_get_int(raw, "places_taken"),
                    )
                )

        return ProlificStudyListResponse(studies=studies)


@router.get(
    "/studies/{study_id}/submissions",
    response_model=ProlificSubmissionListResponse,
)
async def get_study_submissions(
    study_id: str,
    token: str = Query(description="Prolific API token"),
    status: str | None = Query(default=None, description="Filter by status"),
) -> ProlificSubmissionListResponse:
    """Get submissions for a Prolific study.

    Returns all submissions for the specified study, optionally
    filtered by status.

    Parameters
    ----------
    study_id
        The Prolific study ID.
    token
        Prolific API token.
    status
        Optional status filter.

    Returns
    -------
    ProlificSubmissionListResponse
        List of submissions.

    Raises
    ------
    HTTPException
        401 if authentication fails.
        404 if study not found.
        502 if Prolific API is unreachable.
    """
    async with ProlificClient(token) as client:
        try:
            # Convert string status to enum if provided
            status_enum: SubmissionStatus | None = None
            if status is not None:
                with contextlib.suppress(ValueError):
                    status_enum = SubmissionStatus(status)

            raw_submissions = await client.get_submissions(
                study_id, status=status_enum
            )
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "403" in error_msg:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid Prolific API token",
                ) from e
            if "404" in error_msg:
                raise HTTPException(
                    status_code=404,
                    detail=f"Study not found: {study_id}",
                ) from e
            raise HTTPException(
                status_code=502,
                detail=f"Failed to fetch submissions: {error_msg}",
            ) from e

        submissions: list[ProlificSubmissionSummary] = []
        for raw in raw_submissions:
            sub_id = raw.get("id")
            participant_id = raw.get("participant_id")
            if sub_id is not None and participant_id is not None:
                started_at = raw.get("started_at")
                completed_at = raw.get("completed_at")
                submissions.append(
                    ProlificSubmissionSummary(
                        id=str(sub_id),
                        participant_id=str(participant_id),
                        status=_get_str(raw, "status", "UNKNOWN"),
                        started_at=str(started_at) if started_at is not None else None,
                        completed_at=(
                            str(completed_at) if completed_at is not None else None
                        ),
                    )
                )

        return ProlificSubmissionListResponse(
            submissions=submissions,
            total=len(submissions),
        )


@router.post("/submissions/transition", response_model=TransitionResponse)
async def transition_submission(request: TransitionRequest) -> TransitionResponse:
    """Transition a single submission.

    Performs an action (approve, reject, return) on a submission.

    Parameters
    ----------
    request
        Transition request with token, submission ID, and action.

    Returns
    -------
    TransitionResponse
        Result of the transition.

    Raises
    ------
    HTTPException
        400 if rejection_category missing for REJECT.
        401 if authentication fails.
        404 if submission not found.
        502 if Prolific API is unreachable.
    """
    if (
        request.action == ParticipantAction.REJECT
        and request.rejection_category is None
    ):
        raise HTTPException(
            status_code=400,
            detail="rejection_category is required when rejecting",
        )

    async with ProlificClient(request.token) as client:
        try:
            result = await client.transition_submission(
                request.submission_id,
                request.action,
                rejection_category=request.rejection_category,
                message=request.message,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "403" in error_msg:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid Prolific API token",
                ) from e
            if "404" in error_msg:
                raise HTTPException(
                    status_code=404,
                    detail=f"Submission not found: {request.submission_id}",
                ) from e
            raise HTTPException(
                status_code=502,
                detail=f"Failed to transition submission: {error_msg}",
            ) from e

        return TransitionResponse(
            success=True,
            submission_id=request.submission_id,
            new_status=_get_str(result, "status", "UNKNOWN"),
        )


@router.post("/submissions/batch-transition", response_model=BatchTransitionResponse)
async def batch_transition_submissions(
    request: BatchTransitionRequest,
) -> BatchTransitionResponse:
    """Batch transition multiple submissions.

    Performs the same action on multiple submissions efficiently.

    Parameters
    ----------
    request
        Batch transition request with token, study ID, submission IDs, and action.

    Returns
    -------
    BatchTransitionResponse
        Summary of the batch operation.

    Raises
    ------
    HTTPException
        400 if submission_ids is empty or rejection_category missing for REJECT.
        401 if authentication fails.
        404 if study not found.
        502 if Prolific API is unreachable.
    """
    if not request.submission_ids:
        raise HTTPException(
            status_code=400,
            detail="submission_ids cannot be empty",
        )

    if (
        request.action == ParticipantAction.REJECT
        and request.rejection_category is None
    ):
        raise HTTPException(
            status_code=400,
            detail="rejection_category is required when rejecting",
        )

    async with ProlificClient(request.token) as client:
        try:
            result = await client.batch_transition(
                request.study_id,
                request.submission_ids,
                request.action,
                rejection_category=request.rejection_category,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "403" in error_msg:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid Prolific API token",
                ) from e
            if "404" in error_msg:
                raise HTTPException(
                    status_code=404,
                    detail=f"Study not found: {request.study_id}",
                ) from e
            raise HTTPException(
                status_code=502,
                detail=f"Failed to batch transition: {error_msg}",
            ) from e

        # Extract counts from result, defaulting to request count on success
        success_count = _get_int(result, "success_count", len(request.submission_ids))
        failure_count = _get_int(result, "failure_count", 0)

        return BatchTransitionResponse(
            success_count=success_count,
            failure_count=failure_count,
        )


@router.get("/submissions/{submission_id}")
async def get_submission(
    submission_id: str,
    token: str = Query(description="Prolific API token"),
) -> dict[str, JsonValue]:
    """Get details for a specific submission.

    Parameters
    ----------
    submission_id
        The Prolific submission ID.
    token
        Prolific API token.

    Returns
    -------
    dict[str, JsonValue]
        Full submission details.

    Raises
    ------
    HTTPException
        401 if authentication fails.
        404 if submission not found.
        502 if Prolific API is unreachable.
    """
    async with ProlificClient(token) as client:
        try:
            result = await client.get_submission(submission_id)
            return result
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "403" in error_msg:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid Prolific API token",
                ) from e
            if "404" in error_msg:
                raise HTTPException(
                    status_code=404,
                    detail=f"Submission not found: {submission_id}",
                ) from e
            raise HTTPException(
                status_code=502,
                detail=f"Failed to fetch submission: {error_msg}",
            ) from e
