"""Shared fixtures for slopit tests."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from slopit.schemas import (
    BehavioralData,
    CaptureFlag,
    EnvironmentInfo,
    FocusEvent,
    GlobalEvents,
    KeystrokeEvent,
    ModifierState,
    PasteEvent,
    PlatformInfo,
    ResponseInfo,
    SessionTiming,
    SlopitSession,
    SlopitTrial,
    StimulusInfo,
)
from slopit.schemas.analysis import AnalysisFlag, AnalysisResult, PipelineResult, SessionVerdict


# --- Basic Data Fixtures ---


@pytest.fixture
def modifier_state_default() -> ModifierState:
    """Default modifier state with no modifiers pressed."""
    return ModifierState(shift=False, ctrl=False, alt=False, meta=False)


@pytest.fixture
def modifier_state_shift() -> ModifierState:
    """Modifier state with shift pressed."""
    return ModifierState(shift=True, ctrl=False, alt=False, meta=False)


@pytest.fixture
def modifier_state_ctrl() -> ModifierState:
    """Modifier state with ctrl pressed (for paste)."""
    return ModifierState(shift=False, ctrl=True, alt=False, meta=False)


# --- Keystroke Event Fixtures ---


@pytest.fixture
def sample_keystroke_events(modifier_state_default: ModifierState) -> list[KeystrokeEvent]:
    """Sample keystroke events simulating typing 'hello'."""
    events: list[KeystrokeEvent] = []
    keys = ["h", "e", "l", "l", "o"]
    time = 0.0

    for i, key in enumerate(keys):
        # keydown
        events.append(
            KeystrokeEvent(
                time=time,
                key=key,
                code=f"Key{key.upper()}",
                event="keydown",
                text_length=i + 1,
                modifiers=modifier_state_default,
            )
        )
        time += 50.0  # 50ms hold
        # keyup
        events.append(
            KeystrokeEvent(
                time=time,
                key=key,
                code=f"Key{key.upper()}",
                event="keyup",
                text_length=i + 1,
                modifiers=modifier_state_default,
            )
        )
        time += 100.0  # 100ms between keys

    return events


@pytest.fixture
def keystroke_events_with_deletions(
    modifier_state_default: ModifierState,
) -> list[KeystrokeEvent]:
    """Keystroke events with backspace deletions."""
    events: list[KeystrokeEvent] = []
    # Type "hello", delete "lo", type "p" -> "help"
    sequence = [
        ("h", "KeyH", 1),
        ("e", "KeyE", 2),
        ("l", "KeyL", 3),
        ("l", "KeyL", 4),
        ("o", "KeyO", 5),
        ("Backspace", "Backspace", 4),
        ("Backspace", "Backspace", 3),
        ("p", "KeyP", 4),
    ]

    time = 0.0
    for key, code, text_len in sequence:
        events.append(
            KeystrokeEvent(
                time=time,
                key=key,
                code=code,
                event="keydown",
                text_length=text_len,
                modifiers=modifier_state_default,
            )
        )
        time += 150.0  # Variable timing

    return events


@pytest.fixture
def keystroke_events_uniform_timing(
    modifier_state_default: ModifierState,
) -> list[KeystrokeEvent]:
    """Keystroke events with suspiciously uniform timing (suggests transcription)."""
    events: list[KeystrokeEvent] = []
    text = "The quick brown fox jumps over the lazy dog"

    time = 0.0
    for i, char in enumerate(text):
        if char == " ":
            key, code = " ", "Space"
        else:
            key, code = char, f"Key{char.upper()}"

        events.append(
            KeystrokeEvent(
                time=time,
                key=key,
                code=code,
                event="keydown",
                text_length=i + 1,
                modifiers=modifier_state_default,
            )
        )
        time += 100.0  # Exactly 100ms between every key

    return events


@pytest.fixture
def keystroke_events_natural_timing(
    modifier_state_default: ModifierState,
) -> list[KeystrokeEvent]:
    """Keystroke events with natural variable timing."""
    events: list[KeystrokeEvent] = []
    text = "The quick brown fox"

    # Variable intervals simulating natural typing with std > 100ms
    intervals = [
        120, 80, 320, 90, 50, 450, 130, 60, 280, 400,
        150, 70, 350, 85, 55, 500, 125, 65, 300,
    ]

    time = 0.0
    for i, char in enumerate(text):
        if char == " ":
            key, code = " ", "Space"
        else:
            key, code = char, f"Key{char.upper()}"

        events.append(
            KeystrokeEvent(
                time=time,
                key=key,
                code=code,
                event="keydown",
                text_length=i + 1,
                modifiers=modifier_state_default,
            )
        )
        if i < len(intervals):
            time += intervals[i]

    return events


# --- Focus Event Fixtures ---


@pytest.fixture
def sample_focus_events() -> list[FocusEvent]:
    """Sample focus events with a brief tab switch."""
    return [
        FocusEvent(time=1000.0, event="blur", blur_duration=2000.0),
        FocusEvent(time=3000.0, event="focus"),
    ]


@pytest.fixture
def focus_events_excessive_blur() -> list[FocusEvent]:
    """Focus events with excessive tab switching."""
    events: list[FocusEvent] = []
    time = 1000.0

    for _ in range(10):  # 10 blur/focus cycles
        events.append(FocusEvent(time=time, event="blur", blur_duration=500.0))
        time += 500.0
        events.append(FocusEvent(time=time, event="focus"))
        time += 5000.0

    return events


@pytest.fixture
def focus_events_long_hidden() -> list[FocusEvent]:
    """Focus events with extended hidden duration."""
    return [
        FocusEvent(time=1000.0, event="visibilitychange", visibility="hidden"),
        FocusEvent(time=61000.0, event="visibilitychange", visibility="visible"),
    ]


# --- Paste Event Fixtures ---


@pytest.fixture
def sample_paste_event() -> PasteEvent:
    """A single paste event."""
    return PasteEvent(
        time=5000.0,
        text_length=50,
        text_preview="This is pasted text...",
        text_hash="abc123",
        preceding_keystrokes=10,
        blocked=False,
    )


@pytest.fixture
def large_paste_event() -> PasteEvent:
    """A large paste event (suspicious)."""
    return PasteEvent(
        time=1000.0,
        text_length=500,
        text_preview="Lorem ipsum dolor sit amet...",
        text_hash="def456",
        preceding_keystrokes=2,
        blocked=False,
    )


@pytest.fixture
def paste_without_typing() -> PasteEvent:
    """Paste event with no prior typing."""
    return PasteEvent(
        time=500.0,
        text_length=200,
        text_preview="Entire response was pasted...",
        text_hash="ghi789",
        preceding_keystrokes=0,
        blocked=False,
    )


# --- Behavioral Data Fixtures ---


@pytest.fixture
def sample_behavioral_data(
    sample_keystroke_events: list[KeystrokeEvent],
    sample_focus_events: list[FocusEvent],
) -> BehavioralData:
    """Sample behavioral data with keystrokes and focus events."""
    return BehavioralData(
        keystrokes=sample_keystroke_events,
        focus=sample_focus_events,
        paste=[],
    )


@pytest.fixture
def behavioral_data_with_paste(
    sample_keystroke_events: list[KeystrokeEvent],
    sample_focus_events: list[FocusEvent],
    sample_paste_event: PasteEvent,
) -> BehavioralData:
    """Behavioral data including a paste event."""
    return BehavioralData(
        keystrokes=sample_keystroke_events,
        focus=sample_focus_events,
        paste=[sample_paste_event],
    )


@pytest.fixture
def behavioral_data_suspicious(
    keystroke_events_uniform_timing: list[KeystrokeEvent],
    focus_events_excessive_blur: list[FocusEvent],
    large_paste_event: PasteEvent,
) -> BehavioralData:
    """Behavioral data with suspicious patterns."""
    return BehavioralData(
        keystrokes=keystroke_events_uniform_timing,
        focus=focus_events_excessive_blur,
        paste=[large_paste_event],
    )


# --- Session/Trial Fixtures ---


@pytest.fixture
def sample_platform_info() -> PlatformInfo:
    """Sample platform info for jsPsych."""
    return PlatformInfo(
        name="jspsych",
        version="7.3.4",
        adapter_version="0.1.0",
    )


@pytest.fixture
def sample_environment_info() -> EnvironmentInfo:
    """Sample environment info."""
    return EnvironmentInfo(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
        screen_resolution=(1920, 1080),
        viewport_size=(1920, 937),
        device_pixel_ratio=1.0,
        timezone="America/New_York",
        language="en-US",
        touch_capable=False,
        connection_type="4g",
    )


@pytest.fixture
def sample_session_timing() -> SessionTiming:
    """Sample session timing."""
    return SessionTiming(
        start_time=1704067200000,  # 2024-01-01 00:00:00 UTC
        end_time=1704067500000,  # 5 minutes later
        duration=300000,
    )


@pytest.fixture
def sample_stimulus_info() -> StimulusInfo:
    """Sample stimulus info for a text prompt."""
    return StimulusInfo(
        type="text",
        content="Please describe your ideal vacation destination.",
        content_hash="stimulus_hash_123",
    )


@pytest.fixture
def sample_response_info() -> ResponseInfo:
    """Sample response info."""
    return ResponseInfo(
        type="text",
        value="I would love to visit the mountains in Colorado.",
        character_count=48,
        word_count=9,
    )


@pytest.fixture
def sample_trial(
    sample_behavioral_data: BehavioralData,
    sample_stimulus_info: StimulusInfo,
    sample_response_info: ResponseInfo,
) -> SlopitTrial:
    """Sample trial with behavioral data."""
    return SlopitTrial(
        trial_id="trial-001",
        trial_index=0,
        trial_type="survey-text",
        start_time=1704067200000,
        end_time=1704067260000,
        rt=60000,
        stimulus=sample_stimulus_info,
        response=sample_response_info,
        behavioral=sample_behavioral_data,
    )


@pytest.fixture
def minimal_trial() -> SlopitTrial:
    """Minimal trial with no behavioral data."""
    return SlopitTrial(
        trial_id="trial-minimal",
        trial_index=0,
        start_time=0,
        end_time=1000,
    )


@pytest.fixture
def sample_global_events() -> GlobalEvents:
    """Sample global events."""
    return GlobalEvents(focus=[], errors=[])


@pytest.fixture
def sample_session(
    sample_platform_info: PlatformInfo,
    sample_environment_info: EnvironmentInfo,
    sample_session_timing: SessionTiming,
    sample_trial: SlopitTrial,
    sample_global_events: GlobalEvents,
) -> SlopitSession:
    """Sample complete session."""
    return SlopitSession(
        schema_version="1.0",
        session_id="session-001",
        participant_id="participant-001",
        study_id="study-001",
        platform=sample_platform_info,
        environment=sample_environment_info,
        timing=sample_session_timing,
        trials=[sample_trial],
        global_events=sample_global_events,
    )


@pytest.fixture
def session_with_sufficient_keystrokes(
    sample_platform_info: PlatformInfo,
    sample_environment_info: EnvironmentInfo,
    sample_session_timing: SessionTiming,
    sample_global_events: GlobalEvents,
    keystroke_events_natural_timing: list[KeystrokeEvent],
) -> SlopitSession:
    """Session with enough keystrokes for analysis."""
    behavioral = BehavioralData(keystrokes=keystroke_events_natural_timing, focus=[], paste=[])
    trial = SlopitTrial(
        trial_id="trial-sufficient",
        trial_index=0,
        trial_type="survey-text",
        start_time=0,
        end_time=30000,
        rt=30000,
        behavioral=behavioral,
        response=ResponseInfo(type="text", value="The quick brown fox", character_count=19),
    )
    return SlopitSession(
        schema_version="1.0",
        session_id="session-sufficient",
        platform=sample_platform_info,
        environment=sample_environment_info,
        timing=sample_session_timing,
        trials=[trial],
        global_events=sample_global_events,
    )


@pytest.fixture
def session_with_suspicious_patterns(
    sample_platform_info: PlatformInfo,
    sample_environment_info: EnvironmentInfo,
    sample_session_timing: SessionTiming,
    sample_global_events: GlobalEvents,
    behavioral_data_suspicious: BehavioralData,
) -> SlopitSession:
    """Session with suspicious behavioral patterns."""
    trial = SlopitTrial(
        trial_id="trial-suspicious",
        trial_index=0,
        trial_type="survey-text",
        start_time=0,
        end_time=5000,
        rt=5000,
        behavioral=behavioral_data_suspicious,
        response=ResponseInfo(
            type="text",
            value="The quick brown fox jumps over the lazy dog",
            character_count=43,
        ),
    )
    return SlopitSession(
        schema_version="1.0",
        session_id="session-suspicious",
        platform=sample_platform_info,
        environment=sample_environment_info,
        timing=sample_session_timing,
        trials=[trial],
        global_events=sample_global_events,
    )


# --- Flag Fixtures ---


@pytest.fixture
def sample_capture_flag() -> CaptureFlag:
    """Sample capture flag."""
    return CaptureFlag(
        type="paste_detected",
        severity="medium",
        message="Paste event detected during trial",
        timestamp=1704067230000,
        details={"text_length": 50},
    )


@pytest.fixture
def sample_analysis_flag() -> AnalysisFlag:
    """Sample analysis flag."""
    return AnalysisFlag(
        type="low_iki_variance",
        analyzer="keystroke",
        severity="medium",
        message="Keystroke timing unusually consistent",
        confidence=0.75,
        evidence={"std_iki": 50.0},
        trial_ids=["trial-001"],
    )


# --- Analysis Result Fixtures ---


@pytest.fixture
def sample_analysis_result(sample_analysis_flag: AnalysisFlag) -> AnalysisResult:
    """Sample analysis result."""
    return AnalysisResult(
        analyzer="keystroke",
        session_id="session-001",
        trials=[{"trial_id": "trial-001", "metrics": {}, "flags": []}],
        flags=[sample_analysis_flag],
        session_summary={"trials_analyzed": 1},
    )


@pytest.fixture
def sample_session_verdict(sample_analysis_flag: AnalysisFlag) -> SessionVerdict:
    """Sample session verdict."""
    return SessionVerdict(
        status="suspicious",
        confidence=0.75,
        flags=[sample_analysis_flag],
        summary="Detected: low_iki_variance",
    )


@pytest.fixture
def sample_pipeline_result(
    sample_analysis_result: AnalysisResult,
    sample_session_verdict: SessionVerdict,
    sample_analysis_flag: AnalysisFlag,
) -> PipelineResult:
    """Sample pipeline result."""
    return PipelineResult(
        sessions=["session-001"],
        analyzer_results={"keystroke": [sample_analysis_result]},
        aggregated_flags={"session-001": [sample_analysis_flag]},
        verdicts={"session-001": sample_session_verdict},
    )


# --- File Fixtures ---


@pytest.fixture
def temp_dir() -> Path:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_session_json(sample_session: SlopitSession, temp_dir: Path) -> Path:
    """Write sample session to a JSON file and return path."""
    # Convert to dict with schemaVersion and sessionId for native format detection
    data = sample_session.model_dump(by_alias=True)
    # Ensure the native format markers are present
    data["schemaVersion"] = "1.0"
    data["sessionId"] = sample_session.session_id

    file_path = temp_dir / "session.json"
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(data, f)

    return file_path


@pytest.fixture
def sample_jatos_json(temp_dir: Path) -> Path:
    """Create a sample JATOS-format file."""
    trials = [
        {
            "trial_type": "survey-text",
            "trial_index": 0,
            "time_elapsed": 10000,
            "rt": 5000,
            "response": "This is my response to the question.",
            "PROLIFIC_PID": "prolific-123",
            "STUDY_ID": "study-456",
        },
        {
            "trial_type": "survey-text",
            "trial_index": 1,
            "time_elapsed": 25000,
            "rt": 8000,
            "response": "Another thoughtful response here.",
        },
    ]

    file_path = temp_dir / "jatos_results.txt"
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(trials, f)

    return file_path


@pytest.fixture
def malformed_json(temp_dir: Path) -> Path:
    """Create a malformed JSON file."""
    file_path = temp_dir / "malformed.json"
    with file_path.open("w", encoding="utf-8") as f:
        f.write('{"incomplete": ')

    return file_path


@pytest.fixture
def empty_json(temp_dir: Path) -> Path:
    """Create an empty JSON array file."""
    file_path = temp_dir / "empty.json"
    with file_path.open("w", encoding="utf-8") as f:
        f.write("[]")

    return file_path
