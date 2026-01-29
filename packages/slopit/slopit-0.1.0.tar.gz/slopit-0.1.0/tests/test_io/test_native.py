"""Tests for NativeLoader."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from slopit.io import load_session, load_sessions
from slopit.io.native import NativeLoader
from slopit.schemas import SlopitSession


class TestNativeLoader:
    """Tests for NativeLoader class."""

    def test_load_valid_session(self, sample_session_json: Path) -> None:
        """Should load a valid native JSON file."""
        loader = NativeLoader()
        session = loader.load(sample_session_json)

        assert isinstance(session, SlopitSession)
        assert session.session_id == "session-001"

    def test_load_file_not_found(self, temp_dir: Path) -> None:
        """Should raise FileNotFoundError for missing file."""
        loader = NativeLoader()
        with pytest.raises(FileNotFoundError):
            loader.load(temp_dir / "nonexistent.json")

    def test_load_invalid_json(self, malformed_json: Path) -> None:
        """Should raise error for malformed JSON."""
        loader = NativeLoader()
        with pytest.raises(json.JSONDecodeError):
            loader.load(malformed_json)

    def test_load_many_from_directory(
        self,
        temp_dir: Path,
        sample_session: SlopitSession,
    ) -> None:
        """Should load multiple sessions from directory."""
        # Create multiple session files
        for i in range(3):
            session_data = sample_session.model_dump()
            session_data["session_id"] = f"session-{i:03d}"
            session_data["schemaVersion"] = "1.0"
            session_data["sessionId"] = f"session-{i:03d}"

            file_path = temp_dir / f"session_{i}.json"
            with file_path.open("w") as f:
                json.dump(session_data, f)

        loader = NativeLoader()
        sessions = list(loader.load_many(temp_dir))

        assert len(sessions) == 3
        session_ids = {s.session_id for s in sessions}
        assert "session-000" in session_ids
        assert "session-001" in session_ids
        assert "session-002" in session_ids

    def test_load_many_from_single_file(self, sample_session_json: Path) -> None:
        """Should handle single file passed to load_many."""
        loader = NativeLoader()
        sessions = list(loader.load_many(sample_session_json))

        assert len(sessions) == 1

    def test_load_many_with_pattern(
        self,
        temp_dir: Path,
        sample_session: SlopitSession,
    ) -> None:
        """Should filter files by pattern."""
        # Create files with different patterns
        for i, suffix in enumerate(["_data.json", "_meta.json", "_data.json"]):
            session_data = sample_session.model_dump()
            session_data["session_id"] = f"session-{i:03d}"
            session_data["schemaVersion"] = "1.0"
            session_data["sessionId"] = f"session-{i:03d}"

            file_path = temp_dir / f"file{i}{suffix}"
            with file_path.open("w") as f:
                json.dump(session_data, f)

        loader = NativeLoader()
        sessions = list(loader.load_many(temp_dir, pattern="*_data.json"))

        assert len(sessions) == 2

    def test_can_load_native_file(self, sample_session_json: Path) -> None:
        """Should detect native format file."""
        assert NativeLoader.can_load(sample_session_json) is True

    def test_can_load_native_directory(
        self,
        temp_dir: Path,
        sample_session: SlopitSession,
    ) -> None:
        """Should detect directory with native files."""
        session_data = sample_session.model_dump()
        session_data["schemaVersion"] = "1.0"
        session_data["sessionId"] = sample_session.session_id

        file_path = temp_dir / "session.json"
        with file_path.open("w") as f:
            json.dump(session_data, f)

        assert NativeLoader.can_load(temp_dir) is True

    def test_can_load_non_native_file(self, temp_dir: Path) -> None:
        """Should reject non-native format."""
        # Create a file without native markers
        file_path = temp_dir / "other.json"
        with file_path.open("w") as f:
            json.dump({"type": "other_format"}, f)

        assert NativeLoader.can_load(file_path) is False

    def test_can_load_non_json_file(self, temp_dir: Path) -> None:
        """Should reject non-JSON file."""
        file_path = temp_dir / "data.txt"
        file_path.write_text("This is not JSON")

        assert NativeLoader.can_load(file_path) is False

    def test_is_native_format_detection(
        self,
        temp_dir: Path,
        sample_session: SlopitSession,
    ) -> None:
        """Should correctly identify native format."""
        # Native format file
        native_data = sample_session.model_dump()
        native_data["schemaVersion"] = "1.0"
        native_data["sessionId"] = sample_session.session_id

        native_path = temp_dir / "native.json"
        with native_path.open("w") as f:
            json.dump(native_data, f)

        assert NativeLoader._is_native_format(native_path) is True

        # Non-native format file
        other_path = temp_dir / "other.json"
        with other_path.open("w") as f:
            json.dump({"data": "other"}, f)

        assert NativeLoader._is_native_format(other_path) is False


class TestLoadSessionFunction:
    """Tests for load_session convenience function."""

    def test_load_session_native(self, sample_session_json: Path) -> None:
        """Should load native format session."""
        session = load_session(sample_session_json)

        assert isinstance(session, SlopitSession)
        assert session.session_id == "session-001"

    def test_load_session_file_not_found(self) -> None:
        """Should raise FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_session("/nonexistent/path/session.json")

    def test_load_session_unknown_format(self, temp_dir: Path) -> None:
        """Should raise ValueError for unknown format."""
        file_path = temp_dir / "unknown.json"
        with file_path.open("w") as f:
            json.dump({"unknown": "format"}, f)

        with pytest.raises(ValueError, match="Unable to determine file format"):
            load_session(file_path)

    def test_load_session_accepts_string_path(self, sample_session_json: Path) -> None:
        """Should accept string path."""
        session = load_session(str(sample_session_json))

        assert isinstance(session, SlopitSession)


class TestLoadSessionsFunction:
    """Tests for load_sessions convenience function."""

    def test_load_sessions_from_directory(
        self,
        temp_dir: Path,
        sample_session: SlopitSession,
    ) -> None:
        """Should load all sessions from directory."""
        # Create multiple session files
        for i in range(3):
            session_data = sample_session.model_dump()
            session_data["session_id"] = f"session-{i:03d}"
            session_data["schemaVersion"] = "1.0"
            session_data["sessionId"] = f"session-{i:03d}"

            file_path = temp_dir / f"session_{i}.json"
            with file_path.open("w") as f:
                json.dump(session_data, f)

        sessions = load_sessions(temp_dir)

        assert len(sessions) == 3

    def test_load_sessions_from_single_file(self, sample_session_json: Path) -> None:
        """Should load from single file."""
        sessions = load_sessions(sample_session_json)

        assert len(sessions) == 1
        assert sessions[0].session_id == "session-001"

    def test_load_sessions_empty_directory(self, temp_dir: Path) -> None:
        """Should return empty list for empty directory."""
        sessions = load_sessions(temp_dir)

        assert sessions == []

    def test_load_sessions_with_pattern(
        self,
        temp_dir: Path,
        sample_session: SlopitSession,
    ) -> None:
        """Should filter by pattern."""
        # Create files with different extensions
        for ext in [".json", ".txt"]:
            session_data = sample_session.model_dump()
            session_data["schemaVersion"] = "1.0"
            session_data["sessionId"] = sample_session.session_id

            file_path = temp_dir / f"session{ext}"
            with file_path.open("w") as f:
                json.dump(session_data, f)

        sessions = load_sessions(temp_dir, pattern="*.json")

        assert len(sessions) == 1

    def test_load_sessions_skips_invalid_files(
        self,
        temp_dir: Path,
        sample_session: SlopitSession,
    ) -> None:
        """Should skip files that cannot be loaded."""
        # Create one valid file
        session_data = sample_session.model_dump()
        session_data["schemaVersion"] = "1.0"
        session_data["sessionId"] = sample_session.session_id

        valid_path = temp_dir / "valid.json"
        with valid_path.open("w") as f:
            json.dump(session_data, f)

        # Create one invalid file (unknown format)
        invalid_path = temp_dir / "invalid.json"
        with invalid_path.open("w") as f:
            json.dump({"unknown": "format"}, f)

        sessions = load_sessions(temp_dir)

        # Should load only the valid file
        assert len(sessions) == 1
