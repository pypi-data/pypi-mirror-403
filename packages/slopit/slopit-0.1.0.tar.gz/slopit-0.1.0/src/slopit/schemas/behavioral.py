"""Behavioral data schemas for slopit.

This module defines types for keystroke events, focus events,
paste events, mouse events, scroll events, clipboard events,
input duration events, and computed behavioral metrics.
"""

from typing import Literal

from pydantic import BaseModel, Field


class ModifierState(BaseModel):
    """Modifier key states at the time of a keystroke.

    Attributes
    ----------
    shift
        Whether Shift was pressed.
    ctrl
        Whether Ctrl was pressed.
    alt
        Whether Alt was pressed.
    meta
        Whether Meta (Cmd on Mac, Win on Windows) was pressed.
    """

    shift: bool
    ctrl: bool
    alt: bool
    meta: bool


class KeystrokeEvent(BaseModel):
    """A single keystroke event.

    Attributes
    ----------
    time
        Time since trial start in milliseconds.
    key
        Key value from KeyboardEvent.key (e.g., "a", "Enter").
    code
        Physical key code from KeyboardEvent.code (e.g., "KeyA").
    event
        Event type, either "keydown" or "keyup".
    text_length
        Current text length at this moment.
    modifiers
        Modifier key states.
    """

    time: float
    key: str
    code: str
    event: Literal["keydown", "keyup"]
    text_length: int | None = None
    modifiers: ModifierState | None = None


class FocusEvent(BaseModel):
    """A focus or visibility change event.

    Attributes
    ----------
    time
        Time since trial start in milliseconds.
    event
        Event type.
    visibility
        For visibilitychange events, the new visibility state.
    blur_duration
        For blur events, duration until refocus in milliseconds.
    """

    time: float
    event: Literal["focus", "blur", "visibilitychange"]
    visibility: Literal["visible", "hidden"] | None = None
    blur_duration: float | None = None


class PasteEvent(BaseModel):
    """A paste event.

    Attributes
    ----------
    time
        Time since trial start in milliseconds.
    text_length
        Length of pasted text in characters.
    text_preview
        First N characters of pasted text.
    text_hash
        SHA-256 hash of full pasted text.
    preceding_keystrokes
        Number of keystrokes in preceding 2 seconds.
    blocked
        Whether paste was blocked by configuration.
    """

    time: float
    text_length: int
    text_preview: str | None = None
    text_hash: str | None = None
    preceding_keystrokes: int
    blocked: bool


class MouseEvent(BaseModel):
    """Mouse event with kinematics data.

    Captures mouse movements, clicks, and drag operations with
    computed velocity and distance metrics for behavioral analysis.

    Attributes
    ----------
    time
        Time since trial start in milliseconds.
    event
        Event type (mousemove, mousedown, mouseup, or click).
    x
        X coordinate relative to the viewport.
    y
        Y coordinate relative to the viewport.
    velocity
        Mouse velocity in pixels per millisecond.
    distance
        Distance traveled from previous event in pixels.
    delta_time
        Time since previous mouse event in milliseconds.
    is_dragging
        Whether the mouse button is held down during movement.
    """

    time: float
    event: Literal["mousemove", "mousedown", "mouseup", "click"]
    x: float
    y: float
    velocity: float | None = None
    distance: float | None = None
    delta_time: float | None = None
    is_dragging: bool | None = None


class ScrollEvent(BaseModel):
    """Scroll event for reading vs composing detection.

    Captures scroll patterns to distinguish between reading behavior
    (scrolling through existing content) and composing behavior
    (typing new content).

    Attributes
    ----------
    time
        Time since trial start in milliseconds.
    direction
        Scroll direction, either "up" or "down".
    delta_y
        Scroll amount in pixels (positive for down, negative for up).
    scroll_top
        Current scroll position from the top in pixels.
    scroll_height
        Total scrollable height in pixels.
    client_height
        Visible viewport height in pixels.
    velocity
        Scroll velocity in pixels per millisecond.
    """

    time: float
    direction: Literal["up", "down"]
    delta_y: float
    scroll_top: float
    scroll_height: float
    client_height: float
    velocity: float | None = None


class ClipboardCopyEvent(BaseModel):
    """Clipboard copy/cut event with selection context.

    Captures when users copy or cut text from the input area,
    which may indicate reference to external sources or internal
    text manipulation patterns.

    Attributes
    ----------
    time
        Time since trial start in milliseconds.
    event
        Event type, either "copy" or "cut".
    text_length
        Length of copied/cut text in characters.
    text_preview
        First N characters of the copied/cut text.
    text_hash
        SHA-256 hash of the full copied/cut text.
    selection_start
        Start index of the selection in the text.
    selection_end
        End index of the selection in the text.
    """

    time: float
    event: Literal["copy", "cut"]
    text_length: int
    text_preview: str | None = None
    text_hash: str | None = None
    selection_start: int | None = None
    selection_end: int | None = None


class InputDurationEvent(BaseModel):
    """Input duration event for per-field focus tracking.

    Captures focus duration on input elements to analyze
    time spent in specific fields and activity during focus.

    Attributes
    ----------
    focus_time
        Time when the element received focus, in milliseconds since trial start.
    blur_time
        Time when the element lost focus, in milliseconds since trial start.
    duration
        Duration of focus in milliseconds (blur_time - focus_time).
    element_id
        ID attribute of the focused element, if available.
    keystrokes_during_focus
        Number of keystrokes recorded while this element had focus.
    pastes_during_focus
        Number of paste events recorded while this element had focus.
    """

    focus_time: float
    blur_time: float
    duration: float
    element_id: str | None = None
    keystrokes_during_focus: int | None = None
    pastes_during_focus: int | None = None


class KeystrokeMetrics(BaseModel):
    """Computed metrics from keystroke data.

    Attributes
    ----------
    total_keystrokes
        Total number of keystroke events.
    printable_keystrokes
        Number of printable character keystrokes.
    deletions
        Number of deletion keystrokes (Backspace, Delete).
    mean_iki
        Mean inter-keystroke interval in milliseconds.
    std_iki
        Standard deviation of inter-keystroke intervals.
    median_iki
        Median inter-keystroke interval.
    pause_count
        Number of pauses exceeding threshold.
    product_process_ratio
        Ratio of final characters to total keystrokes.
    """

    total_keystrokes: int
    printable_keystrokes: int
    deletions: int
    mean_iki: float
    std_iki: float
    median_iki: float
    pause_count: int
    product_process_ratio: float


class FocusMetrics(BaseModel):
    """Computed metrics from focus data.

    Attributes
    ----------
    blur_count
        Number of window blur events.
    total_blur_duration
        Total time with window blurred in milliseconds.
    hidden_count
        Number of visibility hidden events.
    total_hidden_duration
        Total time with document hidden in milliseconds.
    """

    blur_count: int
    total_blur_duration: float
    hidden_count: int
    total_hidden_duration: float


class TimingMetrics(BaseModel):
    """Timing metrics for a trial.

    Attributes
    ----------
    first_keystroke_latency
        Time from trial start to first keystroke in milliseconds.
    total_response_time
        Time from trial start to submission in milliseconds.
    characters_per_minute
        Typing speed in characters per minute.
    """

    first_keystroke_latency: float | None = None
    total_response_time: float
    characters_per_minute: float | None = None


class MouseMetrics(BaseModel):
    """Computed metrics from mouse event data.

    Attributes
    ----------
    total_events
        Total number of mouse events captured.
    total_distance
        Total distance traveled by the mouse in pixels.
    mean_velocity
        Mean mouse velocity in pixels per millisecond.
    max_velocity
        Maximum mouse velocity recorded.
    click_count
        Number of click events.
    drag_count
        Number of drag operations (mousedown followed by movement).
    total_drag_distance
        Total distance traveled while dragging in pixels.
    """

    total_events: int
    total_distance: float
    mean_velocity: float | None = None
    max_velocity: float | None = None
    click_count: int
    drag_count: int
    total_drag_distance: float


class ScrollMetrics(BaseModel):
    """Computed metrics from scroll event data.

    Attributes
    ----------
    total_events
        Total number of scroll events captured.
    total_distance
        Total scroll distance in pixels (absolute value).
    up_distance
        Total distance scrolled upward in pixels.
    down_distance
        Total distance scrolled downward in pixels.
    direction_changes
        Number of times scroll direction changed.
    mean_velocity
        Mean scroll velocity in pixels per millisecond.
    max_velocity
        Maximum scroll velocity recorded.
    """

    total_events: int
    total_distance: float
    up_distance: float
    down_distance: float
    direction_changes: int
    mean_velocity: float | None = None
    max_velocity: float | None = None


class InputDurationMetrics(BaseModel):
    """Computed metrics from input duration events.

    Attributes
    ----------
    total_focus_events
        Total number of focus/blur cycles recorded.
    total_focus_duration
        Total time spent with input elements focused in milliseconds.
    mean_focus_duration
        Mean duration of focus events in milliseconds.
    max_focus_duration
        Maximum single focus duration in milliseconds.
    total_keystrokes_during_focus
        Total keystrokes across all focus events.
    total_pastes_during_focus
        Total paste events across all focus events.
    """

    total_focus_events: int
    total_focus_duration: float
    mean_focus_duration: float | None = None
    max_focus_duration: float | None = None
    total_keystrokes_during_focus: int | None = None
    total_pastes_during_focus: int | None = None


class BehavioralMetrics(BaseModel):
    """Container for all computed behavioral metrics.

    Attributes
    ----------
    keystroke
        Keystroke-derived metrics.
    focus
        Focus-derived metrics.
    timing
        Timing metrics.
    mouse
        Mouse movement and click metrics.
    scroll
        Scroll behavior metrics.
    input_duration
        Per-field input duration metrics.
    """

    keystroke: KeystrokeMetrics | None = None
    focus: FocusMetrics | None = None
    timing: TimingMetrics | None = None
    mouse: MouseMetrics | None = None
    scroll: ScrollMetrics | None = None
    input_duration: InputDurationMetrics | None = None


class BehavioralData(BaseModel):
    """Container for all behavioral capture data.

    Attributes
    ----------
    keystrokes
        List of keystroke events.
    focus
        List of focus/visibility events.
    paste
        List of paste events.
    mouse
        List of mouse events with kinematics data.
    scroll
        List of scroll events for reading pattern detection.
    clipboard
        List of clipboard copy/cut events.
    input_duration
        List of input duration events for per-field tracking.
    metrics
        Computed metrics from the behavioral data.
    """

    keystrokes: list[KeystrokeEvent] | None = None
    focus: list[FocusEvent] | None = None
    paste: list[PasteEvent] | None = None
    mouse: list[MouseEvent] | None = None
    scroll: list[ScrollEvent] | None = None
    clipboard: list[ClipboardCopyEvent] | None = None
    input_duration: list[InputDurationEvent] | None = None
    metrics: BehavioralMetrics | None = None


class SessionFocusEvent(BaseModel):
    """Session-level focus event (not tied to a specific trial).

    Attributes
    ----------
    timestamp
        Unix timestamp in milliseconds.
    event
        Event type.
    visibility
        Visibility state if applicable.
    """

    timestamp: int
    event: Literal["focus", "blur", "visibilitychange"]
    visibility: Literal["visible", "hidden"] | None = None


class ErrorEvent(BaseModel):
    """Error event during session.

    Attributes
    ----------
    timestamp
        Unix timestamp in milliseconds.
    message
        Error message.
    stack
        Stack trace if available.
    source
        Error source (filename, line, column).
    """

    timestamp: int
    message: str
    stack: str | None = None
    source: str | None = None


class GlobalEvents(BaseModel):
    """Container for session-level events.

    Attributes
    ----------
    focus
        Focus events at session level.
    errors
        Error events.
    """

    focus: list[SessionFocusEvent] = Field(default_factory=lambda: list[SessionFocusEvent]())
    errors: list[ErrorEvent] = Field(default_factory=lambda: list[ErrorEvent]())
