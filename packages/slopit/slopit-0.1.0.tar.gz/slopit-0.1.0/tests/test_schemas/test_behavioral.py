"""Tests for behavioral data schemas: KeystrokeEvent, FocusEvent, etc."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from slopit.schemas import (
    BehavioralData,
    BehavioralMetrics,
    ClipboardCopyEvent,
    FocusEvent,
    FocusMetrics,
    GlobalEvents,
    InputDurationEvent,
    InputDurationMetrics,
    KeystrokeEvent,
    KeystrokeMetrics,
    ModifierState,
    MouseEvent,
    MouseMetrics,
    PasteEvent,
    ScrollEvent,
    ScrollMetrics,
    SessionFocusEvent,
    TimingMetrics,
)
from slopit.schemas.behavioral import ErrorEvent


class TestModifierState:
    """Tests for ModifierState schema."""

    def test_default_modifiers(self, modifier_state_default: ModifierState) -> None:
        """Should create modifier state with all false."""
        assert modifier_state_default.shift is False
        assert modifier_state_default.ctrl is False
        assert modifier_state_default.alt is False
        assert modifier_state_default.meta is False

    def test_shift_modifier(self, modifier_state_shift: ModifierState) -> None:
        """Should create modifier state with shift pressed."""
        assert modifier_state_shift.shift is True
        assert modifier_state_shift.ctrl is False

    def test_all_modifiers_pressed(self) -> None:
        """Should accept all modifiers pressed."""
        state = ModifierState(shift=True, ctrl=True, alt=True, meta=True)
        assert all([state.shift, state.ctrl, state.alt, state.meta])

    def test_modifier_missing_fields(self) -> None:
        """Should reject modifier state missing required fields."""
        with pytest.raises(ValidationError):
            ModifierState(shift=True)  # type: ignore[call-arg]


class TestKeystrokeEvent:
    """Tests for KeystrokeEvent schema."""

    def test_valid_keydown(self, modifier_state_default: ModifierState) -> None:
        """Should accept valid keydown event."""
        event = KeystrokeEvent(
            time=100.0,
            key="a",
            code="KeyA",
            event="keydown",
            text_length=5,
            modifiers=modifier_state_default,
        )
        assert event.time == 100.0
        assert event.key == "a"
        assert event.event == "keydown"

    def test_valid_keyup(self) -> None:
        """Should accept valid keyup event."""
        event = KeystrokeEvent(time=150.0, key="a", code="KeyA", event="keyup")
        assert event.event == "keyup"

    def test_special_keys(self) -> None:
        """Should accept special key events."""
        special_keys = [
            ("Enter", "Enter"),
            ("Backspace", "Backspace"),
            ("Tab", "Tab"),
            ("Shift", "ShiftLeft"),
            (" ", "Space"),
        ]
        for key, code in special_keys:
            event = KeystrokeEvent(time=0.0, key=key, code=code, event="keydown")
            assert event.key == key

    def test_invalid_event_type(self) -> None:
        """Should reject invalid event type."""
        with pytest.raises(ValidationError):
            KeystrokeEvent(time=0.0, key="a", code="KeyA", event="invalid")  # type: ignore[arg-type]

    def test_optional_fields(self) -> None:
        """Should accept event without optional fields."""
        event = KeystrokeEvent(time=0.0, key="x", code="KeyX", event="keydown")
        assert event.text_length is None
        assert event.modifiers is None

    def test_keystroke_serialization(
        self, sample_keystroke_events: list[KeystrokeEvent]
    ) -> None:
        """Should serialize and deserialize keystroke events."""
        for event in sample_keystroke_events:
            data = event.model_dump()
            restored = KeystrokeEvent.model_validate(data)
            assert restored.time == event.time
            assert restored.key == event.key


class TestFocusEvent:
    """Tests for FocusEvent schema."""

    def test_blur_event(self) -> None:
        """Should accept blur event with duration."""
        event = FocusEvent(time=1000.0, event="blur", blur_duration=5000.0)
        assert event.event == "blur"
        assert event.blur_duration == 5000.0

    def test_focus_event(self) -> None:
        """Should accept focus event."""
        event = FocusEvent(time=6000.0, event="focus")
        assert event.event == "focus"

    def test_visibility_hidden(self) -> None:
        """Should accept visibilitychange to hidden."""
        event = FocusEvent(time=2000.0, event="visibilitychange", visibility="hidden")
        assert event.visibility == "hidden"

    def test_visibility_visible(self) -> None:
        """Should accept visibilitychange to visible."""
        event = FocusEvent(time=8000.0, event="visibilitychange", visibility="visible")
        assert event.visibility == "visible"

    def test_invalid_event_type(self) -> None:
        """Should reject invalid focus event type."""
        with pytest.raises(ValidationError):
            FocusEvent(time=0.0, event="invalid")  # type: ignore[arg-type]

    def test_invalid_visibility(self) -> None:
        """Should reject invalid visibility state."""
        with pytest.raises(ValidationError):
            FocusEvent(
                time=0.0,
                event="visibilitychange",
                visibility="invalid",  # type: ignore[arg-type]
            )


class TestPasteEvent:
    """Tests for PasteEvent schema."""

    def test_valid_paste(self, sample_paste_event: PasteEvent) -> None:
        """Should accept valid paste event."""
        assert sample_paste_event.text_length == 50
        assert sample_paste_event.preceding_keystrokes == 10
        assert sample_paste_event.blocked is False

    def test_blocked_paste(self) -> None:
        """Should accept blocked paste event."""
        event = PasteEvent(
            time=100.0,
            text_length=100,
            preceding_keystrokes=0,
            blocked=True,
        )
        assert event.blocked is True

    def test_paste_with_preview(self) -> None:
        """Should accept paste with text preview."""
        event = PasteEvent(
            time=200.0,
            text_length=500,
            text_preview="Lorem ipsum dolor sit amet...",
            text_hash="abc123def456",
            preceding_keystrokes=5,
            blocked=False,
        )
        assert event.text_preview is not None
        assert event.text_hash is not None

    def test_paste_missing_required(self) -> None:
        """Should reject paste event missing required fields."""
        with pytest.raises(ValidationError):
            PasteEvent(
                time=0.0,
                text_length=10,
                # Missing preceding_keystrokes and blocked
            )  # type: ignore[call-arg]


class TestKeystrokeMetrics:
    """Tests for KeystrokeMetrics schema."""

    def test_valid_metrics(self) -> None:
        """Should accept valid keystroke metrics."""
        metrics = KeystrokeMetrics(
            total_keystrokes=100,
            printable_keystrokes=85,
            deletions=15,
            mean_iki=120.5,
            std_iki=45.2,
            median_iki=110.0,
            pause_count=3,
            product_process_ratio=0.85,
        )
        assert metrics.total_keystrokes == 100
        assert metrics.deletions == 15

    def test_zero_metrics(self) -> None:
        """Should accept zero metrics (empty trial)."""
        metrics = KeystrokeMetrics(
            total_keystrokes=0,
            printable_keystrokes=0,
            deletions=0,
            mean_iki=0.0,
            std_iki=0.0,
            median_iki=0.0,
            pause_count=0,
            product_process_ratio=0.0,
        )
        assert metrics.total_keystrokes == 0


class TestFocusMetrics:
    """Tests for FocusMetrics schema."""

    def test_valid_focus_metrics(self) -> None:
        """Should accept valid focus metrics."""
        metrics = FocusMetrics(
            blur_count=5,
            total_blur_duration=15000.0,
            hidden_count=2,
            total_hidden_duration=8000.0,
        )
        assert metrics.blur_count == 5
        assert metrics.total_hidden_duration == 8000.0


class TestTimingMetrics:
    """Tests for TimingMetrics schema."""

    def test_valid_timing_metrics(self) -> None:
        """Should accept valid timing metrics."""
        metrics = TimingMetrics(
            first_keystroke_latency=500.0,
            total_response_time=30000.0,
            characters_per_minute=250.0,
        )
        assert metrics.first_keystroke_latency == 500.0
        assert metrics.total_response_time == 30000.0

    def test_timing_metrics_optional_fields(self) -> None:
        """Should accept timing metrics with only required field."""
        metrics = TimingMetrics(total_response_time=10000.0)
        assert metrics.first_keystroke_latency is None
        assert metrics.characters_per_minute is None


class TestBehavioralMetrics:
    """Tests for BehavioralMetrics schema."""

    def test_full_metrics(self) -> None:
        """Should accept full behavioral metrics."""
        metrics = BehavioralMetrics(
            keystroke=KeystrokeMetrics(
                total_keystrokes=50,
                printable_keystrokes=45,
                deletions=5,
                mean_iki=100.0,
                std_iki=30.0,
                median_iki=95.0,
                pause_count=2,
                product_process_ratio=0.9,
            ),
            focus=FocusMetrics(
                blur_count=1,
                total_blur_duration=2000.0,
                hidden_count=0,
                total_hidden_duration=0.0,
            ),
            timing=TimingMetrics(total_response_time=20000.0),
        )
        assert metrics.keystroke is not None
        assert metrics.focus is not None
        assert metrics.timing is not None

    def test_partial_metrics(self) -> None:
        """Should accept partial behavioral metrics."""
        metrics = BehavioralMetrics(keystroke=None, focus=None, timing=None)
        assert metrics.keystroke is None


class TestBehavioralData:
    """Tests for BehavioralData schema."""

    def test_full_behavioral_data(
        self, sample_behavioral_data: BehavioralData
    ) -> None:
        """Should accept full behavioral data."""
        assert sample_behavioral_data.keystrokes is not None
        assert len(sample_behavioral_data.keystrokes) > 0
        assert sample_behavioral_data.focus is not None
        assert len(sample_behavioral_data.focus) > 0

    def test_empty_behavioral_data(self) -> None:
        """Should accept empty behavioral data with None fields."""
        data = BehavioralData()
        assert data.keystrokes is None
        assert data.focus is None
        assert data.paste is None
        assert data.mouse is None
        assert data.scroll is None
        assert data.clipboard is None
        assert data.input_duration is None

    def test_behavioral_data_with_empty_lists(self) -> None:
        """Should accept behavioral data with explicit empty lists."""
        data = BehavioralData(
            keystrokes=[],
            focus=[],
            paste=[],
            mouse=[],
            scroll=[],
            clipboard=[],
            input_duration=[],
        )
        assert data.keystrokes is not None
        assert len(data.keystrokes) == 0
        assert data.focus is not None
        assert len(data.focus) == 0

    def test_behavioral_data_with_metrics(
        self,
        sample_keystroke_events: list[KeystrokeEvent],
    ) -> None:
        """Should accept behavioral data with computed metrics."""
        metrics = BehavioralMetrics(
            keystroke=KeystrokeMetrics(
                total_keystrokes=len(sample_keystroke_events),
                printable_keystrokes=5,
                deletions=0,
                mean_iki=150.0,
                std_iki=25.0,
                median_iki=150.0,
                pause_count=0,
                product_process_ratio=1.0,
            )
        )
        data = BehavioralData(
            keystrokes=sample_keystroke_events,
            metrics=metrics,
        )
        assert data.metrics is not None
        assert data.metrics.keystroke is not None


class TestMouseEvent:
    """Tests for MouseEvent schema."""

    def test_valid_mousemove(self) -> None:
        """Should accept valid mousemove event."""
        event = MouseEvent(
            time=100.0,
            event="mousemove",
            x=150.0,
            y=200.0,
            velocity=5.0,
            distance=10.0,
            delta_time=16.0,
            is_dragging=False,
        )
        assert event.event == "mousemove"
        assert event.x == 150.0
        assert event.velocity == 5.0

    def test_valid_click(self) -> None:
        """Should accept valid click event."""
        event = MouseEvent(
            time=200.0,
            event="click",
            x=300.0,
            y=400.0,
        )
        assert event.event == "click"

    def test_mousedown_with_dragging(self) -> None:
        """Should accept mousedown event with dragging flag."""
        event = MouseEvent(
            time=150.0,
            event="mousedown",
            x=100.0,
            y=100.0,
            is_dragging=True,
        )
        assert event.is_dragging is True

    def test_mouse_optional_fields(self) -> None:
        """Should accept mouse event without optional fields."""
        event = MouseEvent(time=0.0, event="mouseup", x=0.0, y=0.0)
        assert event.velocity is None
        assert event.distance is None
        assert event.delta_time is None
        assert event.is_dragging is None

    def test_invalid_event_type(self) -> None:
        """Should reject invalid mouse event type."""
        with pytest.raises(ValidationError):
            MouseEvent(time=0.0, event="invalid", x=0.0, y=0.0)  # type: ignore[arg-type]


class TestScrollEvent:
    """Tests for ScrollEvent schema."""

    def test_valid_scroll_down(self) -> None:
        """Should accept valid scroll down event."""
        event = ScrollEvent(
            time=1000.0,
            direction="down",
            delta_y=100.0,
            scroll_top=200.0,
            scroll_height=1000.0,
            client_height=500.0,
            velocity=2.5,
        )
        assert event.direction == "down"
        assert event.delta_y == 100.0
        assert event.velocity == 2.5

    def test_valid_scroll_up(self) -> None:
        """Should accept valid scroll up event."""
        event = ScrollEvent(
            time=2000.0,
            direction="up",
            delta_y=-50.0,
            scroll_top=150.0,
            scroll_height=1000.0,
            client_height=500.0,
        )
        assert event.direction == "up"
        assert event.delta_y == -50.0

    def test_scroll_optional_velocity(self) -> None:
        """Should accept scroll event without velocity."""
        event = ScrollEvent(
            time=0.0,
            direction="down",
            delta_y=10.0,
            scroll_top=0.0,
            scroll_height=100.0,
            client_height=50.0,
        )
        assert event.velocity is None

    def test_invalid_direction(self) -> None:
        """Should reject invalid scroll direction."""
        with pytest.raises(ValidationError):
            ScrollEvent(
                time=0.0,
                direction="left",  # type: ignore[arg-type]
                delta_y=0.0,
                scroll_top=0.0,
                scroll_height=100.0,
                client_height=50.0,
            )


class TestClipboardCopyEvent:
    """Tests for ClipboardCopyEvent schema."""

    def test_valid_copy_event(self) -> None:
        """Should accept valid copy event."""
        event = ClipboardCopyEvent(
            time=500.0,
            event="copy",
            text_length=100,
            text_preview="Lorem ipsum...",
            text_hash="abc123",
            selection_start=0,
            selection_end=100,
        )
        assert event.event == "copy"
        assert event.text_length == 100
        assert event.selection_start == 0

    def test_valid_cut_event(self) -> None:
        """Should accept valid cut event."""
        event = ClipboardCopyEvent(
            time=600.0,
            event="cut",
            text_length=50,
        )
        assert event.event == "cut"
        assert event.text_length == 50

    def test_copy_optional_fields(self) -> None:
        """Should accept copy event without optional fields."""
        event = ClipboardCopyEvent(time=0.0, event="copy", text_length=10)
        assert event.text_preview is None
        assert event.text_hash is None
        assert event.selection_start is None
        assert event.selection_end is None

    def test_invalid_event_type(self) -> None:
        """Should reject invalid clipboard event type."""
        with pytest.raises(ValidationError):
            ClipboardCopyEvent(time=0.0, event="paste", text_length=10)  # type: ignore[arg-type]


class TestInputDurationEvent:
    """Tests for InputDurationEvent schema."""

    def test_valid_input_duration(self) -> None:
        """Should accept valid input duration event."""
        event = InputDurationEvent(
            focus_time=1000.0,
            blur_time=5000.0,
            duration=4000.0,
            element_id="response-input",
            keystrokes_during_focus=50,
            pastes_during_focus=1,
        )
        assert event.duration == 4000.0
        assert event.element_id == "response-input"
        assert event.keystrokes_during_focus == 50

    def test_input_duration_optional_fields(self) -> None:
        """Should accept input duration without optional fields."""
        event = InputDurationEvent(
            focus_time=0.0,
            blur_time=1000.0,
            duration=1000.0,
        )
        assert event.element_id is None
        assert event.keystrokes_during_focus is None
        assert event.pastes_during_focus is None


class TestMouseMetrics:
    """Tests for MouseMetrics schema."""

    def test_valid_mouse_metrics(self) -> None:
        """Should accept valid mouse metrics."""
        metrics = MouseMetrics(
            total_events=500,
            total_distance=15000.0,
            mean_velocity=3.5,
            max_velocity=25.0,
            click_count=10,
            drag_count=2,
            total_drag_distance=500.0,
        )
        assert metrics.total_events == 500
        assert metrics.mean_velocity == 3.5

    def test_mouse_metrics_optional_velocities(self) -> None:
        """Should accept mouse metrics without velocity fields."""
        metrics = MouseMetrics(
            total_events=0,
            total_distance=0.0,
            click_count=0,
            drag_count=0,
            total_drag_distance=0.0,
        )
        assert metrics.mean_velocity is None
        assert metrics.max_velocity is None


class TestScrollMetrics:
    """Tests for ScrollMetrics schema."""

    def test_valid_scroll_metrics(self) -> None:
        """Should accept valid scroll metrics."""
        metrics = ScrollMetrics(
            total_events=100,
            total_distance=5000.0,
            up_distance=1500.0,
            down_distance=3500.0,
            direction_changes=15,
            mean_velocity=2.0,
            max_velocity=10.0,
        )
        assert metrics.total_events == 100
        assert metrics.direction_changes == 15

    def test_scroll_metrics_optional_velocities(self) -> None:
        """Should accept scroll metrics without velocity fields."""
        metrics = ScrollMetrics(
            total_events=0,
            total_distance=0.0,
            up_distance=0.0,
            down_distance=0.0,
            direction_changes=0,
        )
        assert metrics.mean_velocity is None
        assert metrics.max_velocity is None


class TestInputDurationMetrics:
    """Tests for InputDurationMetrics schema."""

    def test_valid_input_duration_metrics(self) -> None:
        """Should accept valid input duration metrics."""
        metrics = InputDurationMetrics(
            total_focus_events=5,
            total_focus_duration=30000.0,
            mean_focus_duration=6000.0,
            max_focus_duration=15000.0,
            total_keystrokes_during_focus=250,
            total_pastes_during_focus=2,
        )
        assert metrics.total_focus_events == 5
        assert metrics.mean_focus_duration == 6000.0

    def test_input_duration_metrics_optional_fields(self) -> None:
        """Should accept input duration metrics without optional fields."""
        metrics = InputDurationMetrics(
            total_focus_events=0,
            total_focus_duration=0.0,
        )
        assert metrics.mean_focus_duration is None
        assert metrics.max_focus_duration is None
        assert metrics.total_keystrokes_during_focus is None
        assert metrics.total_pastes_during_focus is None


class TestSessionFocusEvent:
    """Tests for SessionFocusEvent schema."""

    def test_session_focus_event(self) -> None:
        """Should accept session-level focus event."""
        event = SessionFocusEvent(
            timestamp=1704067200000,
            event="blur",
        )
        assert event.timestamp == 1704067200000
        assert event.event == "blur"

    def test_session_visibility_event(self) -> None:
        """Should accept session-level visibility event."""
        event = SessionFocusEvent(
            timestamp=1704067205000,
            event="visibilitychange",
            visibility="hidden",
        )
        assert event.visibility == "hidden"


class TestErrorEvent:
    """Tests for ErrorEvent schema."""

    def test_error_event(self) -> None:
        """Should accept error event."""
        error = ErrorEvent(
            timestamp=1704067200000,
            message="TypeError: Cannot read property 'foo' of undefined",
            stack="at Object.foo (app.js:123:45)",
            source="app.js:123:45",
        )
        assert "TypeError" in error.message
        assert error.stack is not None

    def test_error_event_minimal(self) -> None:
        """Should accept error event with only required fields."""
        error = ErrorEvent(
            timestamp=1704067200000,
            message="Unknown error",
        )
        assert error.stack is None
        assert error.source is None


class TestGlobalEvents:
    """Tests for GlobalEvents schema."""

    def test_empty_global_events(self, sample_global_events: GlobalEvents) -> None:
        """Should accept empty global events."""
        assert len(sample_global_events.focus) == 0
        assert len(sample_global_events.errors) == 0

    def test_global_events_with_focus(self) -> None:
        """Should accept global events with focus events."""
        events = GlobalEvents(
            focus=[
                SessionFocusEvent(timestamp=1000, event="blur"),
                SessionFocusEvent(timestamp=3000, event="focus"),
            ],
            errors=[],
        )
        assert len(events.focus) == 2

    def test_global_events_with_errors(self) -> None:
        """Should accept global events with error events."""
        events = GlobalEvents(
            focus=[],
            errors=[
                ErrorEvent(timestamp=5000, message="Network error"),
            ],
        )
        assert len(events.errors) == 1
