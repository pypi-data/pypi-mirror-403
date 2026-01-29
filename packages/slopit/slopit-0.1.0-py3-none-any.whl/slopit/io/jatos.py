"""JATOS data format loader.

This module provides loading functionality for data exported from
JATOS (Just Another Tool for Online Studies).
"""

import json
from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

from slopit.io.base import BaseLoader
from slopit.schemas import (
    BehavioralData,
    EnvironmentInfo,
    GlobalEvents,
    PlatformInfo,
    ResponseInfo,
    SessionTiming,
    SlopitSession,
    SlopitTrial,
)
from slopit.schemas.types import JsonValue


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


def _get_float(data: dict[str, JsonValue], key: str, default: float = 0.0) -> float:
    """Safely extract a float value from a JSON dictionary."""
    value = data.get(key, default)
    if isinstance(value, float):
        return value
    if isinstance(value, int):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return default
    return default


def _get_str(data: dict[str, JsonValue], key: str, default: str = "") -> str:
    """Safely extract a string value from a JSON dictionary."""
    value = data.get(key, default)
    if value is None:
        return default
    return str(value)


def _get_bool(data: dict[str, JsonValue], key: str, default: bool = False) -> bool:
    """Safely extract a boolean value from a JSON dictionary."""
    value = data.get(key, default)
    if isinstance(value, bool):
        return value
    return default


class JATOSLoader(BaseLoader):
    """Loader for JATOS export format.

    JATOS exports data as JSON, either as a single array of trials
    or as newline-delimited JSON (one trial per line). This loader
    handles both formats.

    Examples
    --------
    >>> loader = JATOSLoader()
    >>> session = loader.load(Path("jatos_results/study_result_123.txt"))
    >>> print(f"Loaded {len(session.trials)} trials")
    """

    def load(self, path: Path) -> SlopitSession:
        """Load a JATOS result file.

        Parameters
        ----------
        path
            Path to the JATOS result file (.txt or .json).

        Returns
        -------
        SlopitSession
            Converted session data.
        """
        if not path.exists():
            msg = f"File not found: {path}"
            raise FileNotFoundError(msg)

        raw_data = self._read_jatos_file(path)
        return self._convert_to_session(raw_data, path.stem)

    def load_result(
        self,
        trials: list[dict[str, JsonValue]],
        result_id: str = "unknown",
    ) -> SlopitSession:
        """Load a session from raw trial data.

        This method is useful for converting JATOS API results directly
        without writing to a file first.

        Parameters
        ----------
        trials
            List of raw trial dictionaries from JATOS.
        result_id
            Optional identifier for the result (for logging/debugging).

        Returns
        -------
        SlopitSession
            Converted session data.

        Examples
        --------
        >>> loader = JATOSLoader()
        >>> trials = [{"trial_type": "survey", "response": "..."}]
        >>> session = loader.load_result(trials, result_id="api-123")
        """
        return self._convert_to_session(trials, result_id)

    def load_many(self, path: Path, pattern: str = "*.txt") -> Iterator[SlopitSession]:
        """Load multiple JATOS result files.

        Parameters
        ----------
        path
            Path to directory containing result files.
        pattern
            Glob pattern for file matching.

        Yields
        ------
        SlopitSession
            Session data for each file.
        """
        if path.is_file():
            yield self.load(path)
            return

        for file_path in sorted(path.glob(pattern)):
            if file_path.is_file():
                try:
                    yield self.load(file_path)
                except (ValueError, json.JSONDecodeError):
                    continue

    @classmethod
    def can_load(cls, path: Path) -> bool:
        """Check if path appears to be JATOS format.

        Parameters
        ----------
        path
            Path to check.

        Returns
        -------
        bool
            True if the path appears to be JATOS format.
        """
        if path.is_dir():
            return any(path.glob("study_result_*.txt")) or any(path.glob("*.txt"))

        if path.suffix not in {".txt", ".json"}:
            return False

        # Check for JATOS markers in content
        try:
            content = path.read_text(encoding="utf-8")[:1000]
            return "trial_type" in content or "jsPsych" in content.lower()
        except Exception:
            return False

    def _read_jatos_file(self, path: Path) -> list[dict[str, JsonValue]]:
        """Read and parse a JATOS result file.

        Handles both array format and newline-delimited JSON.

        Parameters
        ----------
        path
            Path to the file.

        Returns
        -------
        list[dict[str, JsonValue]]
            List of trial data dictionaries.

        Raises
        ------
        json.JSONDecodeError
            If the file does not contain valid JSON.
        """
        content = path.read_text(encoding="utf-8").strip()

        # Try parsing as JSON array first
        if content.startswith("["):
            parsed: list[dict[str, JsonValue]] | dict[str, JsonValue] | JsonValue
            parsed = json.loads(content)
            if isinstance(parsed, list):
                result: list[dict[str, JsonValue]] = []
                for raw_item in parsed:
                    item: JsonValue = raw_item
                    if isinstance(item, dict):
                        # Cast to appropriate type for type checker
                        typed_item: dict[str, JsonValue] = item  # type: ignore[assignment]
                        result.append(typed_item)
                return result
            return []

        # Try newline-delimited JSON
        trials: list[dict[str, JsonValue]] = []
        parsed_any = False
        for line in content.split("\n"):
            line = line.strip()
            if line:
                try:
                    data: JsonValue = json.loads(line)
                    parsed_any = True
                    if isinstance(data, list):
                        for raw_item in data:
                            item: JsonValue = raw_item
                            if isinstance(item, dict):
                                typed_item: dict[str, JsonValue] = item  # type: ignore[assignment]
                                trials.append(typed_item)
                    elif isinstance(data, dict):
                        typed_data: dict[str, JsonValue] = data  # type: ignore[assignment]
                        trials.append(typed_data)
                except json.JSONDecodeError:
                    continue

        if not parsed_any and content:
            # No valid JSON was parsed, raise an error
            msg = "Could not parse any valid JSON from file"
            raise json.JSONDecodeError(msg, content, 0)

        return trials

    def _convert_to_session(
        self,
        trials: list[dict[str, JsonValue]],
        file_id: str,  # noqa: ARG002
    ) -> SlopitSession:
        """Convert raw JATOS trial data to SlopitSession.

        Parameters
        ----------
        trials
            List of raw trial dictionaries.
        file_id
            Identifier derived from filename (reserved for future use).

        Returns
        -------
        SlopitSession
            Converted session.
        """
        # Extract metadata from first trial or use defaults
        first_trial = trials[0] if trials else {}
        last_trial = trials[-1] if trials else {}

        # Determine timing
        if trials:
            time_elapsed = _get_int(first_trial, "time_elapsed", 0)
            rt = _get_int(first_trial, "rt", 0)
            start_time = time_elapsed - rt
            end_time = _get_int(last_trial, "time_elapsed", 0)
        else:
            start_time = end_time = 0

        return SlopitSession(
            schema_version="1.0",
            session_id=str(uuid4()),
            participant_id=self._extract_participant_id(first_trial),
            study_id=self._extract_study_id(first_trial),
            platform=PlatformInfo(
                name="jspsych",
                version=self._detect_jspsych_version(first_trial),
                adapter_version="0.1.0",
            ),
            environment=self._extract_environment(first_trial),
            timing=SessionTiming(
                start_time=start_time,
                end_time=end_time,
                duration=end_time - start_time if end_time > start_time else None,
            ),
            trials=[self._convert_trial(t, i) for i, t in enumerate(trials)],
            global_events=GlobalEvents(),
        )

    def _convert_trial(self, trial: dict[str, JsonValue], index: int) -> SlopitTrial:
        """Convert a single JATOS trial to SlopitTrial.

        Parameters
        ----------
        trial
            Raw trial dictionary.
        index
            Trial index in session.

        Returns
        -------
        SlopitTrial
            Converted trial.
        """
        time_elapsed = _get_int(trial, "time_elapsed", 0)
        rt = _get_int(trial, "rt", 0)

        trial_id_value = trial.get("trial_id")
        trial_id = str(trial_id_value) if trial_id_value is not None else f"trial-{index}"

        trial_type_value = trial.get("trial_type")
        trial_type = str(trial_type_value) if trial_type_value is not None else "unknown"

        converted = SlopitTrial(
            trial_id=trial_id,
            trial_index=index,
            trial_type=trial_type,
            start_time=time_elapsed - rt,
            end_time=time_elapsed,
            rt=rt,
        )

        # Extract response
        if "response" in trial:
            response = trial["response"]
            converted.response = ResponseInfo(
                type="text" if isinstance(response, str) else "other",
                value=response,
                character_count=len(response) if isinstance(response, str) else None,
                word_count=len(response.split()) if isinstance(response, str) else None,
            )

        # Extract slopit data
        sd_data = trial.get("slopit")
        if isinstance(sd_data, dict):
            behavioral_data = sd_data.get("behavioral")
            if isinstance(behavioral_data, dict):
                converted.behavioral = BehavioralData.model_validate(behavioral_data)
            flags_data = sd_data.get("flags")
            if isinstance(flags_data, list):
                converted.capture_flags = flags_data  # type: ignore[assignment]

        # Store platform data
        platform_data = {k: v for k, v in trial.items() if k != "slopit"}
        converted.platform_data = platform_data

        return converted

    def _extract_participant_id(self, trial: dict[str, JsonValue]) -> str | None:
        """Extract participant ID from trial data."""
        for key in ["PROLIFIC_PID", "workerId", "participant_id", "subject"]:
            if key in trial:
                value = trial[key]
                if value is not None:
                    return str(value)
        return None

    def _extract_study_id(self, trial: dict[str, JsonValue]) -> str | None:
        """Extract study ID from trial data."""
        for key in ["STUDY_ID", "study_id", "experiment_id"]:
            if key in trial:
                value = trial[key]
                if value is not None:
                    return str(value)
        return None

    def _detect_jspsych_version(self, trial: dict[str, JsonValue]) -> str | None:
        """Attempt to detect jsPsych version."""
        version = trial.get("jspsych_version")
        if version is not None:
            return str(version)
        return None

    def _extract_environment(self, trial: dict[str, JsonValue]) -> EnvironmentInfo:
        """Extract environment info from trial data."""
        return EnvironmentInfo(
            user_agent=_get_str(trial, "user_agent", "unknown"),
            screen_resolution=(
                _get_int(trial, "screen_width", 0),
                _get_int(trial, "screen_height", 0),
            ),
            viewport_size=(
                _get_int(trial, "viewport_width", 0),
                _get_int(trial, "viewport_height", 0),
            ),
            device_pixel_ratio=_get_float(trial, "device_pixel_ratio", 1.0),
            timezone=_get_str(trial, "timezone", "unknown"),
            language=_get_str(trial, "language", "unknown"),
            touch_capable=_get_bool(trial, "touch_capable", False),
        )
