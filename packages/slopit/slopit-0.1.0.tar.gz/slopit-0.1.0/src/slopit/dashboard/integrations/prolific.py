"""Prolific API client for participant management.

This module provides an async client for interacting with the Prolific
participant recruitment platform to manage studies and participant
submissions.
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, cast

import httpx

if TYPE_CHECKING:
    from slopit.schemas.types import JsonValue


class ParticipantAction(str, Enum):
    """Actions that can be taken on Prolific participant submissions.

    Attributes
    ----------
    APPROVE
        Approve the submission and pay the participant.
    REJECT
        Reject the submission. Use sparingly and with justification.
    RETURN
        Return the submission to the pool without penalty.
    """

    APPROVE = "APPROVE"
    REJECT = "REJECT"
    RETURN = "RETURN"


class SubmissionStatus(str, Enum):
    """Possible statuses for a Prolific submission.

    Attributes
    ----------
    ACTIVE
        Participant is currently working on the study.
    AWAITING_REVIEW
        Submission is complete and awaiting researcher review.
    APPROVED
        Submission has been approved and participant paid.
    REJECTED
        Submission has been rejected.
    RETURNED
        Submission was returned to the pool.
    TIMED_OUT
        Participant did not complete within the time limit.
    """

    ACTIVE = "ACTIVE"
    AWAITING_REVIEW = "AWAITING REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RETURNED = "RETURNED"
    TIMED_OUT = "TIMED-OUT"


class ProlificClient:
    """Client for Prolific API integration.

    Manages participant submissions and provides functionality for
    approval, rejection, and status tracking based on slopit analysis.

    Parameters
    ----------
    token
        Prolific API token for authentication.

    Examples
    --------
    >>> async with ProlificClient("api-token") as client:
    ...     studies = await client.list_studies()
    ...     submissions = await client.get_submissions("study-123")
    ...     for sub in submissions:
    ...         print(sub["participant_id"], sub["status"])
    """

    BASE_URL = "https://api.prolific.com/api/v1"

    def __init__(self, token: str) -> None:
        self.token = token
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers={"Authorization": f"Token {self.token}"},
                timeout=30.0,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> ProlificClient:
        """Enter async context manager."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Exit async context manager."""
        await self.close()

    async def list_studies(self) -> list[dict[str, JsonValue]]:
        """List all studies for the account.

        Returns
        -------
        list[dict[str, JsonValue]]
            List of study metadata objects containing id, name,
            status, and other Prolific study properties.

        Raises
        ------
        httpx.HTTPStatusError
            If the API request fails.
        """
        client = await self._get_client()
        response = await client.get("/studies/")
        response.raise_for_status()
        data = cast("dict[str, JsonValue]", response.json())
        results = data.get("results")
        if isinstance(results, list):
            return cast("list[dict[str, JsonValue]]", results)
        return []

    async def get_study(self, study_id: str) -> dict[str, JsonValue]:
        """Get details for a specific study.

        Parameters
        ----------
        study_id
            The Prolific study ID.

        Returns
        -------
        dict[str, JsonValue]
            Study metadata object.

        Raises
        ------
        httpx.HTTPStatusError
            If the API request fails or study not found.
        """
        client = await self._get_client()
        response = await client.get(f"/studies/{study_id}/")
        response.raise_for_status()
        return cast("dict[str, JsonValue]", response.json())

    async def get_submissions(
        self,
        study_id: str,
        *,
        status: SubmissionStatus | None = None,
    ) -> list[dict[str, JsonValue]]:
        """Get submissions for a study.

        Parameters
        ----------
        study_id
            The Prolific study ID.
        status
            Filter by submission status. If None, returns all.

        Returns
        -------
        list[dict[str, JsonValue]]
            List of submission objects with participant info,
            status, and timing data.

        Raises
        ------
        httpx.HTTPStatusError
            If the API request fails.
        """
        client = await self._get_client()
        params: dict[str, str] = {}
        if status is not None:
            params["status"] = status.value

        response = await client.get(
            f"/studies/{study_id}/submissions/",
            params=params if params else None,
        )
        response.raise_for_status()
        data = cast("dict[str, JsonValue]", response.json())
        results = data.get("results")
        if isinstance(results, list):
            return cast("list[dict[str, JsonValue]]", results)
        return []

    async def get_submission(
        self,
        submission_id: str,
    ) -> dict[str, JsonValue]:
        """Get a specific submission by ID.

        Parameters
        ----------
        submission_id
            The submission ID.

        Returns
        -------
        dict[str, JsonValue]
            Submission object with full details.

        Raises
        ------
        httpx.HTTPStatusError
            If the API request fails or submission not found.
        """
        client = await self._get_client()
        response = await client.get(f"/submissions/{submission_id}/")
        response.raise_for_status()
        return cast("dict[str, JsonValue]", response.json())

    async def transition_submission(
        self,
        submission_id: str,
        action: ParticipantAction,
        *,
        rejection_category: str | None = None,
        message: str | None = None,
    ) -> dict[str, JsonValue]:
        """Transition a single submission to a new state.

        Parameters
        ----------
        submission_id
            The submission ID.
        action
            The action to take (APPROVE, REJECT, RETURN).
        rejection_category
            Required when action is REJECT. Common values include
            "BAD_CODE", "NO_DATA", "FAILED_ATTENTION".
        message
            Optional message to send to the participant.

        Returns
        -------
        dict[str, JsonValue]
            Updated submission object.

        Raises
        ------
        httpx.HTTPStatusError
            If the API request fails.
        ValueError
            If action is REJECT but rejection_category is not provided.
        """
        if action == ParticipantAction.REJECT and rejection_category is None:
            msg = "rejection_category is required when rejecting a submission"
            raise ValueError(msg)

        client = await self._get_client()
        payload: dict[str, str] = {"action": action.value}

        if rejection_category is not None:
            payload["rejection_category"] = rejection_category
        if message is not None:
            payload["message"] = message

        response = await client.post(
            f"/submissions/{submission_id}/transition/",
            json=payload,
        )
        response.raise_for_status()
        return cast("dict[str, JsonValue]", response.json())

    async def approve_submission(
        self,
        submission_id: str,
        *,
        message: str | None = None,
    ) -> dict[str, JsonValue]:
        """Approve a submission and pay the participant.

        Parameters
        ----------
        submission_id
            The submission ID.
        message
            Optional thank you message to the participant.

        Returns
        -------
        dict[str, JsonValue]
            Updated submission object.
        """
        return await self.transition_submission(
            submission_id,
            ParticipantAction.APPROVE,
            message=message,
        )

    async def reject_submission(
        self,
        submission_id: str,
        rejection_category: str,
        *,
        message: str | None = None,
    ) -> dict[str, JsonValue]:
        """Reject a submission.

        Use this sparingly and only with clear justification.
        Consider using return_submission for borderline cases.

        Parameters
        ----------
        submission_id
            The submission ID.
        rejection_category
            Reason category for rejection (e.g., "NO_DATA").
        message
            Optional explanation message to the participant.

        Returns
        -------
        dict[str, JsonValue]
            Updated submission object.
        """
        return await self.transition_submission(
            submission_id,
            ParticipantAction.REJECT,
            rejection_category=rejection_category,
            message=message,
        )

    async def return_submission(
        self,
        submission_id: str,
        *,
        message: str | None = None,
    ) -> dict[str, JsonValue]:
        """Return a submission to the pool.

        Returns the submission without penalty to the participant.
        The slot becomes available for another participant.

        Parameters
        ----------
        submission_id
            The submission ID.
        message
            Optional message to the participant.

        Returns
        -------
        dict[str, JsonValue]
            Updated submission object.
        """
        return await self.transition_submission(
            submission_id,
            ParticipantAction.RETURN,
            message=message,
        )

    async def batch_transition(
        self,
        study_id: str,
        submission_ids: list[str],
        action: ParticipantAction,
        *,
        rejection_category: str | None = None,
    ) -> dict[str, JsonValue]:
        """Batch transition multiple submissions.

        Performs the same action on multiple submissions in a single
        API call. More efficient than individual transitions.

        Parameters
        ----------
        study_id
            The Prolific study ID.
        submission_ids
            List of submission IDs to transition.
        action
            The action to take on all submissions.
        rejection_category
            Required when action is REJECT.

        Returns
        -------
        dict[str, JsonValue]
            Batch operation result with success/failure counts.

        Raises
        ------
        httpx.HTTPStatusError
            If the API request fails.
        ValueError
            If action is REJECT but rejection_category is not provided.
            If submission_ids is empty.
        """
        if not submission_ids:
            msg = "submission_ids cannot be empty"
            raise ValueError(msg)

        if action == ParticipantAction.REJECT and rejection_category is None:
            msg = "rejection_category is required when rejecting submissions"
            raise ValueError(msg)

        client = await self._get_client()
        payload: dict[str, str | list[str]] = {
            "submission_ids": submission_ids,
            "action": action.value,
        }

        if rejection_category is not None:
            payload["rejection_category"] = rejection_category

        response = await client.post(
            f"/studies/{study_id}/submissions/bulk-transition/",
            json=payload,
        )
        response.raise_for_status()
        return cast("dict[str, JsonValue]", response.json())

    async def batch_approve(
        self,
        study_id: str,
        submission_ids: list[str],
    ) -> dict[str, JsonValue]:
        """Batch approve multiple submissions.

        Parameters
        ----------
        study_id
            The Prolific study ID.
        submission_ids
            List of submission IDs to approve.

        Returns
        -------
        dict[str, JsonValue]
            Batch operation result.
        """
        return await self.batch_transition(
            study_id,
            submission_ids,
            ParticipantAction.APPROVE,
        )

    async def batch_reject(
        self,
        study_id: str,
        submission_ids: list[str],
        rejection_category: str,
    ) -> dict[str, JsonValue]:
        """Batch reject multiple submissions.

        Parameters
        ----------
        study_id
            The Prolific study ID.
        submission_ids
            List of submission IDs to reject.
        rejection_category
            Reason category for rejection.

        Returns
        -------
        dict[str, JsonValue]
            Batch operation result.
        """
        return await self.batch_transition(
            study_id,
            submission_ids,
            ParticipantAction.REJECT,
            rejection_category=rejection_category,
        )

    async def batch_return(
        self,
        study_id: str,
        submission_ids: list[str],
    ) -> dict[str, JsonValue]:
        """Batch return multiple submissions.

        Parameters
        ----------
        study_id
            The Prolific study ID.
        submission_ids
            List of submission IDs to return.

        Returns
        -------
        dict[str, JsonValue]
            Batch operation result.
        """
        return await self.batch_transition(
            study_id,
            submission_ids,
            ParticipantAction.RETURN,
        )
