"""JATOS API client for syncing study results.

This module provides an async client for interacting with JATOS
(Just Another Tool for Online Studies) servers to retrieve and
synchronize experiment data.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast

import httpx

from slopit.io import JATOSLoader

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from slopit.schemas import SlopitSession
    from slopit.schemas.types import JsonValue


class JATOSClient:
    """Client for JATOS API integration.

    Connects to a JATOS server to retrieve study results and
    convert them to SlopitSession format.

    Parameters
    ----------
    base_url
        JATOS server URL (e.g., "https://jatos.example.com").
    token
        JATOS API token for authentication.

    Examples
    --------
    >>> client = JATOSClient("https://jatos.example.com", "api-token")
    >>> studies = await client.list_studies()
    >>> async for session in client.stream_results("study-123"):
    ...     print(session.session_id)
    """

    def __init__(self, base_url: str, token: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self._client: httpx.AsyncClient | None = None
        self._loader = JATOSLoader()

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=30.0,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> JATOSClient:
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
        """List all studies accessible with the API token.

        Returns
        -------
        list[dict[str, JsonValue]]
            List of study metadata objects containing id, title,
            description, and other JATOS study properties.

        Raises
        ------
        httpx.HTTPStatusError
            If the API request fails.
        """
        client = await self._get_client()
        response = await client.get("/jatos/api/v1/admin/studies")
        response.raise_for_status()
        return cast("list[dict[str, JsonValue]]", response.json())

    async def get_study(self, study_id: str) -> dict[str, JsonValue]:
        """Get metadata for a specific study.

        Parameters
        ----------
        study_id
            The JATOS study ID.

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
        response = await client.get(f"/jatos/api/v1/admin/studies/{study_id}")
        response.raise_for_status()
        return cast("dict[str, JsonValue]", response.json())

    async def get_study_results(self, study_id: str) -> list[dict[str, JsonValue]]:
        """Get all results for a study.

        Parameters
        ----------
        study_id
            The JATOS study ID.

        Returns
        -------
        list[dict[str, JsonValue]]
            List of result data objects, each containing the raw
            trial data from a participant session.

        Raises
        ------
        httpx.HTTPStatusError
            If the API request fails.
        """
        client = await self._get_client()
        response = await client.get(f"/jatos/api/v1/results/{study_id}")
        response.raise_for_status()
        return cast("list[dict[str, JsonValue]]", response.json())

    async def get_result(
        self,
        study_id: str,
        result_id: str,
    ) -> dict[str, JsonValue]:
        """Get a specific result by ID.

        Parameters
        ----------
        study_id
            The JATOS study ID.
        result_id
            The result ID to retrieve.

        Returns
        -------
        dict[str, JsonValue]
            Result data object.

        Raises
        ------
        httpx.HTTPStatusError
            If the API request fails or result not found.
        """
        client = await self._get_client()
        response = await client.get(
            f"/jatos/api/v1/results/{study_id}/{result_id}"
        )
        response.raise_for_status()
        return cast("dict[str, JsonValue]", response.json())

    def _parse_result(self, result: dict[str, JsonValue]) -> SlopitSession | None:
        """Parse a JATOS result into a SlopitSession.

        Parameters
        ----------
        result
            Raw result data from JATOS API.

        Returns
        -------
        SlopitSession | None
            Parsed session, or None if parsing fails.
        """
        try:
            # Extract the data field which contains the trial array
            data = result.get("data")
            trials: list[dict[str, JsonValue]]
            if isinstance(data, str):
                # Data may be JSON-encoded string
                trials = cast("list[dict[str, JsonValue]]", json.loads(data))
            elif isinstance(data, list):
                trials = cast("list[dict[str, JsonValue]]", data)
            else:
                return None

            # Use the existing loader's conversion logic
            result_id = result.get("id")
            file_id = str(result_id) if result_id is not None else "unknown"
            return self._loader.load_result(trials, file_id)
        except Exception:
            return None

    async def stream_results(self, study_id: str) -> AsyncIterator[SlopitSession]:
        """Stream results as SlopitSession objects.

        Retrieves all results for a study and yields them as parsed
        SlopitSession objects. Malformed results are silently skipped.

        Parameters
        ----------
        study_id
            The JATOS study ID.

        Yields
        ------
        SlopitSession
            Parsed session objects.

        Raises
        ------
        httpx.HTTPStatusError
            If the API request fails.
        """
        results = await self.get_study_results(study_id)
        for result in results:
            session = self._parse_result(result)
            if session is not None:
                yield session

    async def get_sessions(self, study_id: str) -> list[SlopitSession]:
        """Get all results as a list of SlopitSession objects.

        Convenience method that collects all streamed sessions into a list.

        Parameters
        ----------
        study_id
            The JATOS study ID.

        Returns
        -------
        list[SlopitSession]
            List of parsed session objects.
        """
        sessions: list[SlopitSession] = []
        async for session in self.stream_results(study_id):
            sessions.append(session)
        return sessions
