"""Tests for session schemas: SlopitSession, SlopitTrial, etc."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from slopit.schemas import (
    EnvironmentInfo,
    GlobalEvents,
    PlatformInfo,
    ResponseInfo,
    SessionTiming,
    SlopitSession,
    SlopitTrial,
    StimulusInfo,
)


class TestPlatformInfo:
    """Tests for PlatformInfo schema."""

    def test_valid_platform_info(self) -> None:
        """Should accept valid platform info."""
        info = PlatformInfo(name="jspsych", version="7.3.4", adapter_version="0.1.0")
        assert info.name == "jspsych"
        assert info.version == "7.3.4"
        assert info.adapter_version == "0.1.0"

    def test_minimal_platform_info(self) -> None:
        """Should accept minimal platform info (only name required)."""
        info = PlatformInfo(name="custom")
        assert info.name == "custom"
        assert info.version is None
        assert info.adapter_version is None

    def test_platform_info_missing_name(self) -> None:
        """Should reject platform info without name."""
        with pytest.raises(ValidationError) as exc_info:
            PlatformInfo()  # type: ignore[call-arg]
        assert "name" in str(exc_info.value)

    def test_platform_info_serialization(self) -> None:
        """Should serialize and deserialize correctly."""
        info = PlatformInfo(name="labjs", version="22.2.0")
        data = info.model_dump()
        restored = PlatformInfo.model_validate(data)
        assert restored == info


class TestEnvironmentInfo:
    """Tests for EnvironmentInfo schema."""

    def test_valid_environment_info(self, sample_environment_info: EnvironmentInfo) -> None:
        """Should accept valid environment info."""
        assert sample_environment_info.user_agent.startswith("Mozilla")
        assert sample_environment_info.screen_resolution == (1920, 1080)
        assert sample_environment_info.viewport_size == (1920, 937)
        assert sample_environment_info.device_pixel_ratio == 1.0

    def test_environment_info_with_high_dpi(self) -> None:
        """Should accept high DPI device pixel ratio."""
        info = EnvironmentInfo(
            user_agent="Test Agent",
            screen_resolution=(2880, 1800),
            viewport_size=(1440, 900),
            device_pixel_ratio=2.0,
            timezone="UTC",
            language="en",
            touch_capable=True,
        )
        assert info.device_pixel_ratio == 2.0

    def test_environment_info_missing_required(self) -> None:
        """Should reject environment info with missing required fields."""
        with pytest.raises(ValidationError):
            EnvironmentInfo(
                user_agent="Test",
                # Missing screen_resolution and other required fields
            )  # type: ignore[call-arg]

    def test_environment_info_tuple_validation(self) -> None:
        """Should validate tuple formats for resolution."""
        info = EnvironmentInfo(
            user_agent="Test",
            screen_resolution=(800, 600),
            viewport_size=(800, 550),
            device_pixel_ratio=1.0,
            timezone="UTC",
            language="en",
            touch_capable=False,
        )
        assert len(info.screen_resolution) == 2
        assert len(info.viewport_size) == 2


class TestSessionTiming:
    """Tests for SessionTiming schema."""

    def test_valid_session_timing(self, sample_session_timing: SessionTiming) -> None:
        """Should accept valid session timing."""
        assert sample_session_timing.start_time > 0
        assert sample_session_timing.end_time is not None
        assert sample_session_timing.end_time > sample_session_timing.start_time
        assert sample_session_timing.duration == 300000

    def test_session_timing_incomplete(self) -> None:
        """Should accept incomplete session timing (no end_time)."""
        timing = SessionTiming(start_time=1704067200000)
        assert timing.start_time == 1704067200000
        assert timing.end_time is None
        assert timing.duration is None

    def test_session_timing_only_start_required(self) -> None:
        """Should only require start_time."""
        timing = SessionTiming(start_time=0)
        assert timing.start_time == 0


class TestStimulusInfo:
    """Tests for StimulusInfo schema."""

    def test_text_stimulus(self, sample_stimulus_info: StimulusInfo) -> None:
        """Should accept text stimulus."""
        assert sample_stimulus_info.type == "text"
        assert sample_stimulus_info.content is not None

    def test_image_stimulus(self) -> None:
        """Should accept image stimulus."""
        stimulus = StimulusInfo(
            type="image",
            content="https://example.com/image.jpg",
            content_hash="hash123",
        )
        assert stimulus.type == "image"

    def test_all_stimulus_types(self) -> None:
        """Should accept all valid stimulus types."""
        valid_types = ["text", "image", "audio", "video", "html", "other"]
        for stimulus_type in valid_types:
            stimulus = StimulusInfo(type=stimulus_type)  # type: ignore[arg-type]
            assert stimulus.type == stimulus_type

    def test_invalid_stimulus_type(self) -> None:
        """Should reject invalid stimulus type."""
        with pytest.raises(ValidationError):
            StimulusInfo(type="invalid")  # type: ignore[arg-type]

    def test_stimulus_with_parameters(self) -> None:
        """Should accept stimulus with additional parameters."""
        stimulus = StimulusInfo(
            type="html",
            content="<div>Test</div>",
            parameters={"width": 500, "height": 300, "centered": True},
        )
        assert stimulus.parameters is not None
        assert stimulus.parameters["width"] == 500


class TestResponseInfo:
    """Tests for ResponseInfo schema."""

    def test_text_response(self, sample_response_info: ResponseInfo) -> None:
        """Should accept text response."""
        assert sample_response_info.type == "text"
        assert sample_response_info.value is not None
        assert sample_response_info.character_count == 48
        assert sample_response_info.word_count == 9

    def test_choice_response(self) -> None:
        """Should accept choice response."""
        response = ResponseInfo(type="choice", value="option_a")
        assert response.type == "choice"
        assert response.value == "option_a"

    def test_multi_choice_response(self) -> None:
        """Should accept multi-choice response."""
        response = ResponseInfo(type="multi-choice", value=["option_a", "option_c"])
        assert response.type == "multi-choice"
        assert response.value == ["option_a", "option_c"]

    def test_slider_response(self) -> None:
        """Should accept slider response."""
        response = ResponseInfo(type="slider", value=75)
        assert response.type == "slider"
        assert response.value == 75

    def test_likert_response(self) -> None:
        """Should accept likert response."""
        response = ResponseInfo(type="likert", value=4)
        assert response.type == "likert"

    def test_all_response_types(self) -> None:
        """Should accept all valid response types."""
        valid_types = ["text", "choice", "multi-choice", "slider", "likert", "annotation", "other"]
        for response_type in valid_types:
            response = ResponseInfo(type=response_type, value="test")  # type: ignore[arg-type]
            assert response.type == response_type


class TestSlopitTrial:
    """Tests for SlopitTrial schema."""

    def test_valid_trial(self, sample_trial: SlopitTrial) -> None:
        """Should accept valid trial."""
        assert sample_trial.trial_id == "trial-001"
        assert sample_trial.trial_index == 0
        assert sample_trial.trial_type == "survey-text"
        assert sample_trial.behavioral is not None

    def test_minimal_trial(self, minimal_trial: SlopitTrial) -> None:
        """Should accept minimal trial (only required fields)."""
        assert minimal_trial.trial_id == "trial-minimal"
        assert minimal_trial.behavioral is None
        assert minimal_trial.response is None

    def test_trial_missing_required(self) -> None:
        """Should reject trial missing required fields."""
        with pytest.raises(ValidationError):
            SlopitTrial(
                trial_id="test",
                trial_index=0,
                # Missing start_time and end_time
            )  # type: ignore[call-arg]

    def test_trial_with_capture_flags(self, sample_capture_flag) -> None:
        """Should accept trial with capture flags."""
        trial = SlopitTrial(
            trial_id="trial-flagged",
            trial_index=0,
            start_time=0,
            end_time=5000,
            capture_flags=[sample_capture_flag],
        )
        assert trial.capture_flags is not None
        assert len(trial.capture_flags) == 1

    def test_trial_serialization_roundtrip(self, sample_trial: SlopitTrial) -> None:
        """Should serialize and deserialize correctly."""
        data = sample_trial.model_dump()
        restored = SlopitTrial.model_validate(data)
        assert restored.trial_id == sample_trial.trial_id
        assert restored.behavioral is not None


class TestSlopitSession:
    """Tests for SlopitSession schema."""

    def test_valid_session(self, sample_session: SlopitSession) -> None:
        """Should accept valid session."""
        assert sample_session.schema_version == "1.0"
        assert sample_session.session_id == "session-001"
        assert sample_session.participant_id == "participant-001"
        assert len(sample_session.trials) == 1

    def test_session_schema_version_default(
        self,
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should default to schema version 1.0."""
        session = SlopitSession(
            session_id="test-session",
            platform=sample_platform_info,
            environment=sample_environment_info,
            timing=sample_session_timing,
            global_events=sample_global_events,
        )
        assert session.schema_version == "1.0"

    def test_session_invalid_schema_version(
        self,
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should reject invalid schema version."""
        with pytest.raises(ValidationError):
            SlopitSession(
                schema_version="2.0",  # type: ignore[arg-type]
                session_id="test-session",
                platform=sample_platform_info,
                environment=sample_environment_info,
                timing=sample_session_timing,
                global_events=sample_global_events,
            )

    def test_session_empty_trials(
        self,
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should accept session with empty trials list."""
        session = SlopitSession(
            session_id="empty-session",
            platform=sample_platform_info,
            environment=sample_environment_info,
            timing=sample_session_timing,
            trials=[],
            global_events=sample_global_events,
        )
        assert len(session.trials) == 0

    def test_session_multiple_trials(
        self,
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_trial: SlopitTrial,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should accept session with multiple trials."""
        trial2 = SlopitTrial(
            trial_id="trial-002",
            trial_index=1,
            start_time=1704067260000,
            end_time=1704067320000,
        )
        session = SlopitSession(
            session_id="multi-trial-session",
            platform=sample_platform_info,
            environment=sample_environment_info,
            timing=sample_session_timing,
            trials=[sample_trial, trial2],
            global_events=sample_global_events,
        )
        assert len(session.trials) == 2

    def test_session_with_metadata(
        self,
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should accept session with arbitrary metadata."""
        session = SlopitSession(
            session_id="metadata-session",
            platform=sample_platform_info,
            environment=sample_environment_info,
            timing=sample_session_timing,
            global_events=sample_global_events,
            metadata={
                "condition": "experimental",
                "wave": 2,
                "complete": True,
                "notes": None,
            },
        )
        assert session.metadata is not None
        assert session.metadata["condition"] == "experimental"

    def test_session_serialization_roundtrip(self, sample_session: SlopitSession) -> None:
        """Should serialize and deserialize correctly."""
        data = sample_session.model_dump()
        restored = SlopitSession.model_validate(data)
        assert restored.session_id == sample_session.session_id
        assert len(restored.trials) == len(sample_session.trials)
        assert restored.platform.name == sample_session.platform.name

    def test_session_json_roundtrip(self, sample_session: SlopitSession) -> None:
        """Should convert to JSON and back correctly."""
        json_str = sample_session.model_dump_json()
        restored = SlopitSession.model_validate_json(json_str)
        assert restored.session_id == sample_session.session_id
