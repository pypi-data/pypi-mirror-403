"""IO module for loading slopit session data.

This module provides loaders for various data formats including
native JSON, JATOS exports, and others.
"""

from pathlib import Path

from slopit.io.base import BaseLoader
from slopit.io.jatos import JATOSLoader
from slopit.io.native import NativeLoader
from slopit.schemas import SlopitSession

__all__ = [
    "BaseLoader",
    "JATOSLoader",
    "NativeLoader",
    "load_session",
    "load_sessions",
]


def load_session(path: str | Path) -> SlopitSession:
    """Load a single session from a file.

    Automatically detects the file format and uses the appropriate loader.

    Parameters
    ----------
    path
        Path to the session file.

    Returns
    -------
    SlopitSession
        The loaded session data.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    ValueError
        If the file format cannot be determined or is invalid.

    Examples
    --------
    >>> session = load_session("data/participant_001.json")
    >>> print(f"Session {session.session_id} has {len(session.trials)} trials")
    """
    path = Path(path)

    if not path.exists():
        msg = f"File not found: {path}"
        raise FileNotFoundError(msg)

    # Try native format first
    if NativeLoader.can_load(path):
        return NativeLoader().load(path)

    # Try JATOS format
    if JATOSLoader.can_load(path):
        return JATOSLoader().load(path)

    msg = f"Unable to determine file format: {path}"
    raise ValueError(msg)


def load_sessions(path: str | Path, pattern: str = "*") -> list[SlopitSession]:
    """Load multiple sessions from a directory.

    Parameters
    ----------
    path
        Path to directory containing session files.
    pattern
        Glob pattern for file matching.

    Returns
    -------
    list[SlopitSession]
        List of loaded sessions.

    Examples
    --------
    >>> sessions = load_sessions("data/")
    >>> print(f"Loaded {len(sessions)} sessions")
    """
    path = Path(path)

    if path.is_file():
        return [load_session(path)]

    sessions: list[SlopitSession] = []

    # Try each loader
    for loader_cls in [NativeLoader, JATOSLoader]:
        if loader_cls.can_load(path):
            loader = loader_cls()
            for session in loader.load_many(path, pattern):
                sessions.append(session)
            return sessions

    # Fallback: try loading each file individually
    for file_path in sorted(path.glob(pattern)):
        if file_path.is_file():
            try:
                sessions.append(load_session(file_path))
            except ValueError:
                continue

    return sessions
