"""File-based JSON storage service.

This module provides persistent storage for sessions and verdicts using
a simple file-based approach with JSON serialization.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from pydantic import BaseModel

from slopit.schemas import SlopitSession

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path


class SessionIndex(BaseModel):
    """Index entry for a session.

    Attributes
    ----------
    session_id
        Unique identifier for the session.
    created_at
        ISO 8601 timestamp or Unix timestamp string when session was created.
    trial_count
        Number of trials in the session.
    has_verdict
        Whether a verdict has been computed for this session.
    """

    session_id: str
    created_at: str
    trial_count: int
    has_verdict: bool


class StorageService:
    """File-based storage for sessions and verdicts.

    Stores data in a configurable directory with structure::

        data/
        ├── sessions/
        │   ├── {session_id}.json
        │   └── index.json
        ├── verdicts/
        │   └── {session_id}.json
        └── exports/
            └── {timestamp}.csv

    Parameters
    ----------
    data_dir
        Root directory for data storage.

    Examples
    --------
    >>> from pathlib import Path
    >>> storage = StorageService(Path("./data"))
    >>> storage.save_session(session)
    >>> retrieved = storage.get_session(session.session_id)
    """

    def __init__(self, data_dir: Path) -> None:
        from pathlib import Path as PathLib

        # Accept Path from caller but convert to ensure pathlib.Path
        self.data_dir = PathLib(data_dir)
        self.sessions_dir = self.data_dir / "sessions"
        self.verdicts_dir = self.data_dir / "verdicts"
        self.exports_dir = self.data_dir / "exports"

        # Ensure directories exist
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.verdicts_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)

    def save_session(self, session: SlopitSession) -> None:
        """Save a session to storage.

        Parameters
        ----------
        session
            Session to save. Uses session_id as the filename.
        """
        path = self.sessions_dir / f"{session.session_id}.json"
        path.write_text(session.model_dump_json(indent=2))
        self._update_index(session)

    def get_session(self, session_id: str) -> SlopitSession | None:
        """Get a session by ID.

        Parameters
        ----------
        session_id
            Unique identifier of the session to retrieve.

        Returns
        -------
        SlopitSession | None
            The session if found, None otherwise.
        """
        path = self.sessions_dir / f"{session_id}.json"
        if not path.exists():
            return None
        return SlopitSession.model_validate_json(path.read_text())

    def list_sessions(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        has_verdict: bool | None = None,
    ) -> tuple[list[SessionIndex], int]:
        """List sessions with pagination.

        Parameters
        ----------
        page
            Page number (1-indexed).
        page_size
            Number of sessions per page.
        has_verdict
            Filter by verdict status. None returns all sessions.

        Returns
        -------
        tuple[list[SessionIndex], int]
            Tuple of (sessions on current page, total count after filtering).
        """
        index = self._load_index()

        # Filter
        if has_verdict is not None:
            index = [s for s in index if s.has_verdict == has_verdict]

        total = len(index)
        start = (page - 1) * page_size
        end = start + page_size

        return index[start:end], total

    def iter_sessions(self) -> Iterator[SlopitSession]:
        """Iterate over all sessions.

        Yields
        ------
        SlopitSession
            Each session stored in the sessions directory.
        """
        for path in self.sessions_dir.glob("*.json"):
            if path.name != "index.json":
                yield SlopitSession.model_validate_json(path.read_text())

    def save_verdict(
        self,
        session_id: str,
        verdict: dict[str, str | int | float | bool | list[str] | None],
    ) -> None:
        """Save a verdict for a session.

        Parameters
        ----------
        session_id
            ID of the session this verdict belongs to.
        verdict
            Verdict data to save.
        """
        path = self.verdicts_dir / f"{session_id}.json"
        path.write_text(json.dumps(verdict, indent=2))
        self._mark_has_verdict(session_id)

    def get_verdict(
        self,
        session_id: str,
    ) -> dict[str, str | int | float | bool | list[str] | None] | None:
        """Get verdict for a session.

        Parameters
        ----------
        session_id
            ID of the session to get the verdict for.

        Returns
        -------
        dict[str, str | int | float | bool | list[str] | None] | None
            Verdict data if found, None otherwise.
        """
        path = self.verdicts_dir / f"{session_id}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text())  # type: ignore[no-any-return]

    def _load_index(self) -> list[SessionIndex]:
        """Load session index from disk."""
        path = self.sessions_dir / "index.json"
        if not path.exists():
            return []
        data = json.loads(path.read_text())
        return [SessionIndex.model_validate(s) for s in data]

    def _save_index(self, index: list[SessionIndex]) -> None:
        """Save session index to disk."""
        path = self.sessions_dir / "index.json"
        data = [s.model_dump() for s in index]
        path.write_text(json.dumps(data, indent=2))

    def _update_index(self, session: SlopitSession) -> None:
        """Add or update session in index."""
        index = self._load_index()
        existing = next(
            (i for i, s in enumerate(index) if s.session_id == session.session_id),
            None,
        )

        # Convert Unix timestamp (int) to string for storage
        created_at = str(session.timing.start_time) if session.timing else ""

        entry = SessionIndex(
            session_id=session.session_id,
            created_at=created_at,
            trial_count=len(session.trials),
            has_verdict=False,
        )

        if existing is not None:
            entry.has_verdict = index[existing].has_verdict
            index[existing] = entry
        else:
            index.append(entry)

        self._save_index(index)

    def _mark_has_verdict(self, session_id: str) -> None:
        """Mark session as having a verdict."""
        index = self._load_index()
        for entry in index:
            if entry.session_id == session_id:
                entry.has_verdict = True
                break
        self._save_index(index)
