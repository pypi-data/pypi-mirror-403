"""Native slopit JSON format loader.

This module provides loading functionality for the native slopit JSON format.
"""

import json
from collections.abc import Iterator
from pathlib import Path

from slopit.io.base import BaseLoader
from slopit.schemas import SlopitSession


class NativeLoader(BaseLoader):
    """Loader for native slopit JSON format.

    The native format is a JSON file that directly contains a SlopitSession
    object with schemaVersion field.

    Examples
    --------
    >>> loader = NativeLoader()
    >>> session = loader.load(Path("data/session.json"))
    >>> print(f"Loaded session {session.session_id}")
    """

    def load(self, path: Path) -> SlopitSession:
        """Load a native slopit JSON file.

        Parameters
        ----------
        path
            Path to the JSON file.

        Returns
        -------
        SlopitSession
            The loaded session data.
        """
        if not path.exists():
            msg = f"File not found: {path}"
            raise FileNotFoundError(msg)

        content = path.read_text(encoding="utf-8")
        data = json.loads(content)

        return SlopitSession.model_validate(data)

    def load_many(self, path: Path, pattern: str = "*.json") -> Iterator[SlopitSession]:
        """Load multiple native JSON files.

        Parameters
        ----------
        path
            Path to directory containing JSON files.
        pattern
            Glob pattern for file matching.

        Yields
        ------
        SlopitSession
            Session data for each matching file.
        """
        if path.is_file():
            yield self.load(path)
            return

        for file_path in sorted(path.glob(pattern)):
            if file_path.is_file() and self._is_native_format(file_path):
                yield self.load(file_path)

    @classmethod
    def can_load(cls, path: Path) -> bool:
        """Check if path appears to be native slopit format.

        Parameters
        ----------
        path
            Path to check.

        Returns
        -------
        bool
            True if the path appears to be native format.
        """
        if path.is_dir():
            # Check if any JSON files look like native format
            return any(cls._is_native_format(json_file) for json_file in path.glob("*.json"))

        return cls._is_native_format(path)

    @classmethod
    def _is_native_format(cls, path: Path) -> bool:
        """Check if a file is in native slopit format."""
        if path.suffix != ".json":
            return False

        try:
            content = path.read_text(encoding="utf-8")[:1000]
            # Check for both camelCase (JS convention) and snake_case (Python convention)
            has_schema = '"schemaVersion"' in content or '"schema_version"' in content
            has_session = '"sessionId"' in content or '"session_id"' in content
            return has_schema and has_session
        except Exception:
            return False
