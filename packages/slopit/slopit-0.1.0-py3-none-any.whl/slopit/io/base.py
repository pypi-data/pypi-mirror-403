"""Base classes for data loaders.

This module defines the interface that all format-specific loaders
must implement.
"""

from abc import ABC, abstractmethod
from collections.abc import Iterator
from pathlib import Path

from slopit.schemas import SlopitSession


class BaseLoader(ABC):
    """Abstract base class for data loaders.

    Subclasses implement loading logic for specific data formats
    (JATOS, Pavlovia, Gorilla, etc.).
    """

    @abstractmethod
    def load(self, path: Path) -> SlopitSession:
        """Load a single session from a file.

        Parameters
        ----------
        path
            Path to the data file.

        Returns
        -------
        SlopitSession
            The loaded session data.

        Raises
        ------
        FileNotFoundError
            If the file does not exist.
        ValueError
            If the file format is invalid.
        """
        ...

    @abstractmethod
    def load_many(self, path: Path, pattern: str = "*") -> Iterator[SlopitSession]:
        """Load multiple sessions from a directory or archive.

        Parameters
        ----------
        path
            Path to directory or archive file.
        pattern
            Glob pattern for file matching.

        Yields
        ------
        SlopitSession
            Session data for each matching file.
        """
        ...

    @classmethod
    @abstractmethod
    def can_load(cls, path: Path) -> bool:
        """Check if this loader can handle the given path.

        Parameters
        ----------
        path
            Path to check.

        Returns
        -------
        bool
            True if this loader can handle the format.
        """
        ...
