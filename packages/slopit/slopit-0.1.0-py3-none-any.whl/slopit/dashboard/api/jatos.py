"""JATOS integration endpoints.

This module provides API endpoints for synchronizing data
with JATOS experiment servers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from slopit.dashboard.integrations import JATOSClient

if TYPE_CHECKING:
    from slopit.schemas.types import JsonValue

router = APIRouter()


class JATOSConnectionConfig(BaseModel):
    """Configuration for connecting to a JATOS server.

    Attributes
    ----------
    base_url
        JATOS server URL (e.g., "https://jatos.example.com").
    token
        JATOS API token for authentication.
    """

    base_url: str = Field(description="JATOS server URL")
    token: str = Field(description="JATOS API token")


class JATOSStudySummary(BaseModel):
    """Summary of a JATOS study.

    Attributes
    ----------
    id
        JATOS study ID.
    title
        Study title.
    description
        Study description.
    active
        Whether the study is currently active.
    """

    id: str = Field(description="Study ID")
    title: str = Field(description="Study title")
    description: str | None = Field(default=None, description="Study description")
    active: bool = Field(default=True, description="Whether study is active")


class JATOSSyncRequest(BaseModel):
    """Request to sync results from a JATOS study.

    Attributes
    ----------
    connection
        JATOS connection configuration.
    study_id
        ID of the study to sync.
    """

    connection: JATOSConnectionConfig = Field(description="JATOS connection config")
    study_id: str = Field(description="Study ID to sync")


class JATOSSyncResponse(BaseModel):
    """Response from a JATOS sync operation.

    Attributes
    ----------
    sessions_synced
        Number of sessions successfully synced.
    sessions_failed
        Number of sessions that failed to sync.
    session_ids
        List of synced session IDs.
    """

    sessions_synced: int = Field(ge=0, description="Number of sessions synced")
    sessions_failed: int = Field(ge=0, description="Number of sessions failed")
    session_ids: list[str] = Field(default_factory=list, description="Synced session IDs")


class JATOSStudyListResponse(BaseModel):
    """Response containing list of JATOS studies.

    Attributes
    ----------
    studies
        List of study summaries.
    """

    studies: list[JATOSStudySummary] = Field(description="List of studies")


@router.post("/connect", response_model=JATOSStudyListResponse)
async def connect_and_list_studies(
    config: JATOSConnectionConfig,
) -> JATOSStudyListResponse:
    """Connect to JATOS and list available studies.

    Validates the connection credentials and returns a list of
    studies accessible with the provided API token.

    Parameters
    ----------
    config
        JATOS connection configuration with base_url and token.

    Returns
    -------
    JATOSStudyListResponse
        List of available studies.

    Raises
    ------
    HTTPException
        401 if authentication fails.
        502 if JATOS server is unreachable.
    """
    async with JATOSClient(config.base_url, config.token) as client:
        try:
            raw_studies = await client.list_studies()
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "403" in error_msg:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid JATOS API token",
                ) from e
            raise HTTPException(
                status_code=502,
                detail=f"Failed to connect to JATOS server: {error_msg}",
            ) from e

        studies: list[JATOSStudySummary] = []
        for raw in raw_studies:
            study_id = raw.get("id")
            title = raw.get("title")
            if study_id is not None and title is not None:
                studies.append(
                    JATOSStudySummary(
                        id=str(study_id),
                        title=str(title),
                        description=str(raw.get("description", "")) or None,
                        active=bool(raw.get("active", True)),
                    )
                )

        return JATOSStudyListResponse(studies=studies)


@router.post("/sync", response_model=JATOSSyncResponse)
async def sync_study_results(request: JATOSSyncRequest) -> JATOSSyncResponse:
    """Sync results from a JATOS study.

    Retrieves all results from the specified JATOS study and
    imports them as slopit sessions.

    Parameters
    ----------
    request
        Sync request containing connection config and study ID.

    Returns
    -------
    JATOSSyncResponse
        Summary of the sync operation.

    Raises
    ------
    HTTPException
        401 if authentication fails.
        404 if study not found.
        502 if JATOS server is unreachable.
    """
    config = request.connection
    async with JATOSClient(config.base_url, config.token) as client:
        try:
            sessions = await client.get_sessions(request.study_id)
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "403" in error_msg:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid JATOS API token",
                ) from e
            if "404" in error_msg:
                raise HTTPException(
                    status_code=404,
                    detail=f"Study not found: {request.study_id}",
                ) from e
            raise HTTPException(
                status_code=502,
                detail=f"Failed to sync from JATOS: {error_msg}",
            ) from e

        # TODO: Store sessions in database
        session_ids = [s.session_id for s in sessions]

        return JATOSSyncResponse(
            sessions_synced=len(sessions),
            sessions_failed=0,
            session_ids=session_ids,
        )


@router.get("/studies/{study_id}/results")
async def get_study_results(
    study_id: str,
    base_url: str = Query(description="JATOS server URL"),
    token: str = Query(description="JATOS API token"),
) -> list[dict[str, JsonValue]]:
    """Get raw results for a JATOS study.

    Retrieves raw result data directly from JATOS without
    converting to slopit sessions.

    Parameters
    ----------
    study_id
        The JATOS study ID.
    base_url
        JATOS server URL.
    token
        JATOS API token.

    Returns
    -------
    list[dict[str, JsonValue]]
        List of raw result objects.

    Raises
    ------
    HTTPException
        401 if authentication fails.
        404 if study not found.
        502 if JATOS server is unreachable.
    """
    async with JATOSClient(base_url, token) as client:
        try:
            results = await client.get_study_results(study_id)
            return results
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "403" in error_msg:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid JATOS API token",
                ) from e
            if "404" in error_msg:
                raise HTTPException(
                    status_code=404,
                    detail=f"Study not found: {study_id}",
                ) from e
            raise HTTPException(
                status_code=502,
                detail=f"Failed to fetch results: {error_msg}",
            ) from e
