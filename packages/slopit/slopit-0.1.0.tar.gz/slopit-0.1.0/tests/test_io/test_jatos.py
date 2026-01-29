"""Tests for JATOSLoader."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from slopit.io import load_session, load_sessions
from slopit.io.jatos import JATOSLoader
from slopit.schemas import SlopitSession


class TestJATOSLoader:
    """Tests for JATOSLoader class."""

    def test_load_jatos_array_format(self, sample_jatos_json: Path) -> None:
        """Should load JATOS array format."""
        loader = JATOSLoader()
        session = loader.load(sample_jatos_json)

        assert isinstance(session, SlopitSession)
        assert session.platform.name == "jspsych"
        assert len(session.trials) == 2

    def test_load_jatos_ndjson_format(self, temp_dir: Path) -> None:
        """Should load JATOS newline-delimited JSON format."""
        trials = [
            {"trial_type": "instructions", "trial_index": 0, "time_elapsed": 1000, "rt": 500},
            {"trial_type": "survey-text", "trial_index": 1, "time_elapsed": 5000, "rt": 3000},
        ]

        file_path = temp_dir / "ndjson_results.txt"
        with file_path.open("w") as f:
            for trial in trials:
                f.write(json.dumps(trial) + "\n")

        loader = JATOSLoader()
        session = loader.load(file_path)

        assert len(session.trials) == 2

    def test_load_jatos_nested_array_ndjson(self, temp_dir: Path) -> None:
        """Should handle JATOS format with arrays on each line."""
        # Some JATOS exports have the entire trial array on one line
        trials = [
            {"trial_type": "trial1", "trial_index": 0, "time_elapsed": 1000, "rt": 500},
            {"trial_type": "trial2", "trial_index": 1, "time_elapsed": 2000, "rt": 800},
        ]

        file_path = temp_dir / "array_line.txt"
        with file_path.open("w") as f:
            f.write(json.dumps(trials))

        loader = JATOSLoader()
        session = loader.load(file_path)

        assert len(session.trials) == 2

    def test_load_file_not_found(self, temp_dir: Path) -> None:
        """Should raise FileNotFoundError for missing file."""
        loader = JATOSLoader()
        with pytest.raises(FileNotFoundError):
            loader.load(temp_dir / "nonexistent.txt")

    def test_load_extracts_participant_id(self, temp_dir: Path) -> None:
        """Should extract participant ID from trial data."""
        trials = [
            {
                "trial_type": "survey",
                "time_elapsed": 1000,
                "rt": 500,
                "PROLIFIC_PID": "prolific-abc123",
            }
        ]

        file_path = temp_dir / "results.txt"
        with file_path.open("w") as f:
            json.dump(trials, f)

        loader = JATOSLoader()
        session = loader.load(file_path)

        assert session.participant_id == "prolific-abc123"

    def test_load_extracts_study_id(self, temp_dir: Path) -> None:
        """Should extract study ID from trial data."""
        trials = [
            {
                "trial_type": "survey",
                "time_elapsed": 1000,
                "rt": 500,
                "STUDY_ID": "study-xyz789",
            }
        ]

        file_path = temp_dir / "results.txt"
        with file_path.open("w") as f:
            json.dump(trials, f)

        loader = JATOSLoader()
        session = loader.load(file_path)

        assert session.study_id == "study-xyz789"

    def test_load_extracts_response(self, temp_dir: Path) -> None:
        """Should extract response from trial data."""
        trials = [
            {
                "trial_type": "survey-text",
                "time_elapsed": 5000,
                "rt": 4000,
                "response": "This is my thoughtful response.",
            }
        ]

        file_path = temp_dir / "results.txt"
        with file_path.open("w") as f:
            json.dump(trials, f)

        loader = JATOSLoader()
        session = loader.load(file_path)

        assert session.trials[0].response is not None
        assert session.trials[0].response.value == "This is my thoughtful response."
        assert session.trials[0].response.character_count == 31

    def test_load_extracts_slopit_data(self, temp_dir: Path) -> None:
        """Should extract slopit behavioral data if present."""
        trials = [
            {
                "trial_type": "survey-text",
                "time_elapsed": 5000,
                "rt": 4000,
                "slopit": {
                    "behavioral": {
                        "keystrokes": [
                            {"time": 100, "key": "h", "code": "KeyH", "event": "keydown"},
                            {"time": 200, "key": "i", "code": "KeyI", "event": "keydown"},
                        ],
                        "focus": [],
                        "paste": [],
                    }
                },
            }
        ]

        file_path = temp_dir / "results.txt"
        with file_path.open("w") as f:
            json.dump(trials, f)

        loader = JATOSLoader()
        session = loader.load(file_path)

        assert session.trials[0].behavioral is not None
        assert len(session.trials[0].behavioral.keystrokes) == 2

    def test_load_many_from_directory(self, temp_dir: Path) -> None:
        """Should load multiple JATOS files from directory."""
        for i in range(3):
            trials = [
                {"trial_type": "survey", "time_elapsed": 1000, "rt": 500, "trial_index": 0}
            ]
            file_path = temp_dir / f"study_result_{i}.txt"
            with file_path.open("w") as f:
                json.dump(trials, f)

        loader = JATOSLoader()
        sessions = list(loader.load_many(temp_dir))

        assert len(sessions) == 3

    def test_load_many_skips_invalid(self, temp_dir: Path) -> None:
        """Should skip files that cannot be parsed."""
        # Valid file
        valid_trials = [{"trial_type": "survey", "time_elapsed": 1000, "rt": 500}]
        valid_path = temp_dir / "valid.txt"
        with valid_path.open("w") as f:
            json.dump(valid_trials, f)

        # Invalid file
        invalid_path = temp_dir / "invalid.txt"
        invalid_path.write_text("not json at all {{{")

        loader = JATOSLoader()
        sessions = list(loader.load_many(temp_dir))

        assert len(sessions) == 1

    def test_can_load_jatos_file(self, sample_jatos_json: Path) -> None:
        """Should detect JATOS format file."""
        assert JATOSLoader.can_load(sample_jatos_json) is True

    def test_can_load_jatos_directory(self, temp_dir: Path) -> None:
        """Should detect directory with JATOS files."""
        file_path = temp_dir / "study_result_1.txt"
        file_path.write_text('[{"trial_type": "test"}]')

        assert JATOSLoader.can_load(temp_dir) is True

    def test_can_load_txt_files(self, temp_dir: Path) -> None:
        """Should recognize .txt files with trial_type as JATOS."""
        file_path = temp_dir / "results.txt"
        file_path.write_text('[{"trial_type": "survey"}]')

        assert JATOSLoader.can_load(file_path) is True

    def test_can_load_rejects_non_jatos(self, temp_dir: Path) -> None:
        """Should reject files without JATOS markers."""
        file_path = temp_dir / "other.json"
        with file_path.open("w") as f:
            json.dump({"data": "something else"}, f)

        assert JATOSLoader.can_load(file_path) is False

    def test_can_load_rejects_unsupported_extension(self, temp_dir: Path) -> None:
        """Should reject files with unsupported extensions."""
        file_path = temp_dir / "data.csv"
        file_path.write_text("col1,col2\nval1,val2")

        assert JATOSLoader.can_load(file_path) is False

    def test_empty_trials_array(self, temp_dir: Path) -> None:
        """Should handle empty trials array."""
        file_path = temp_dir / "empty.txt"
        with file_path.open("w") as f:
            json.dump([], f)

        loader = JATOSLoader()
        session = loader.load(file_path)

        assert len(session.trials) == 0

    def test_timing_calculation(self, temp_dir: Path) -> None:
        """Should calculate session timing from trials."""
        trials = [
            {"trial_type": "t1", "time_elapsed": 2000, "rt": 1000, "trial_index": 0},
            {"trial_type": "t2", "time_elapsed": 5000, "rt": 2000, "trial_index": 1},
            {"trial_type": "t3", "time_elapsed": 10000, "rt": 3000, "trial_index": 2},
        ]

        file_path = temp_dir / "results.txt"
        with file_path.open("w") as f:
            json.dump(trials, f)

        loader = JATOSLoader()
        session = loader.load(file_path)

        # First trial: time_elapsed=2000, rt=1000 -> start_time=1000
        # Last trial: time_elapsed=10000 -> end_time=10000
        assert session.timing.start_time == 1000
        assert session.timing.end_time == 10000

    def test_environment_extraction(self, temp_dir: Path) -> None:
        """Should extract environment info from trial data."""
        trials = [
            {
                "trial_type": "survey",
                "time_elapsed": 1000,
                "rt": 500,
                "user_agent": "Mozilla/5.0 Test Browser",
                "screen_width": 1920,
                "screen_height": 1080,
                "viewport_width": 1920,
                "viewport_height": 900,
                "device_pixel_ratio": 2.0,
                "timezone": "America/New_York",
                "language": "en-US",
                "touch_capable": True,
            }
        ]

        file_path = temp_dir / "results.txt"
        with file_path.open("w") as f:
            json.dump(trials, f)

        loader = JATOSLoader()
        session = loader.load(file_path)

        assert session.environment.user_agent == "Mozilla/5.0 Test Browser"
        assert session.environment.screen_resolution == (1920, 1080)
        assert session.environment.device_pixel_ratio == 2.0

    def test_jspsych_version_detection(self, temp_dir: Path) -> None:
        """Should detect jsPsych version if present."""
        trials = [
            {
                "trial_type": "survey",
                "time_elapsed": 1000,
                "rt": 500,
                "jspsych_version": "7.3.4",
            }
        ]

        file_path = temp_dir / "results.txt"
        with file_path.open("w") as f:
            json.dump(trials, f)

        loader = JATOSLoader()
        session = loader.load(file_path)

        assert session.platform.version == "7.3.4"

    def test_platform_data_passthrough(self, temp_dir: Path) -> None:
        """Should pass through platform-specific data."""
        trials = [
            {
                "trial_type": "custom-plugin",
                "time_elapsed": 1000,
                "rt": 500,
                "custom_field": "custom_value",
                "another_field": 42,
            }
        ]

        file_path = temp_dir / "results.txt"
        with file_path.open("w") as f:
            json.dump(trials, f)

        loader = JATOSLoader()
        session = loader.load(file_path)

        assert session.trials[0].platform_data is not None
        assert session.trials[0].platform_data["custom_field"] == "custom_value"
        assert session.trials[0].platform_data["another_field"] == 42


class TestJATOSIntegration:
    """Integration tests using load_session/load_sessions with JATOS files."""

    def test_load_session_jatos(self, sample_jatos_json: Path) -> None:
        """Should load JATOS file via load_session."""
        session = load_session(sample_jatos_json)

        assert isinstance(session, SlopitSession)
        assert session.participant_id == "prolific-123"

    def test_load_sessions_jatos_directory(self, temp_dir: Path) -> None:
        """Should load JATOS files from directory via load_sessions."""
        for i in range(2):
            trials = [
                {
                    "trial_type": "survey",
                    "time_elapsed": 1000,
                    "rt": 500,
                    "PROLIFIC_PID": f"participant-{i}",
                }
            ]
            file_path = temp_dir / f"study_result_{i}.txt"
            with file_path.open("w") as f:
                json.dump(trials, f)

        sessions = load_sessions(temp_dir)

        assert len(sessions) == 2
        participant_ids = {s.participant_id for s in sessions}
        assert "participant-0" in participant_ids
        assert "participant-1" in participant_ids
