# Schemas

The `slopit.schemas` module contains Pydantic models for all data structures. These schemas mirror the TypeScript schemas in `@slopit/core` and provide validation and type safety.

## Session Types

### SlopitSession

The root container for a participant session. This is the primary data structure consumed by all analyzers.

::: slopit.schemas.session.SlopitSession
    options:
      show_source: true
      members: []

#### Example

```python
from slopit import load_session
from slopit.schemas import SlopitSession

# Load from file
session = load_session("data/participant_001.json")

# Validate raw data
raw_data = {"sessionId": "abc123", ...}
session = SlopitSession.model_validate(raw_data)

# Access attributes
print(f"Session: {session.session_id}")
print(f"Participant: {session.participant_id}")
print(f"Trials: {len(session.trials)}")
```

### SlopitTrial

Data for a single trial within a session.

::: slopit.schemas.session.SlopitTrial
    options:
      show_source: true
      members: []

#### Example

```python
for trial in session.trials:
    print(f"Trial {trial.trial_index}: {trial.trial_type}")

    if trial.response:
        print(f"  Response: {trial.response.value}")

    if trial.behavioral:
        print(f"  Keystrokes: {len(trial.behavioral.keystrokes)}")
```

### SessionTiming

Session-level timing information.

::: slopit.schemas.session.SessionTiming
    options:
      show_source: true
      members: []

### EnvironmentInfo

Client environment information captured at session start.

::: slopit.schemas.session.EnvironmentInfo
    options:
      show_source: true
      members: []

### PlatformInfo

Information about the experiment platform (jsPsych, lab.js, etc.).

::: slopit.schemas.session.PlatformInfo
    options:
      show_source: true
      members: []

### StimulusInfo

Information about a trial stimulus.

::: slopit.schemas.session.StimulusInfo
    options:
      show_source: true
      members: []

### ResponseInfo

Participant response information.

::: slopit.schemas.session.ResponseInfo
    options:
      show_source: true
      members: []

## Behavioral Types

### BehavioralData

Container for all behavioral capture data within a trial.

::: slopit.schemas.behavioral.BehavioralData
    options:
      show_source: true
      members: []

#### Example

```python
for trial in session.trials:
    if trial.behavioral is None:
        continue

    behavioral = trial.behavioral

    # Access keystroke data
    for ks in behavioral.keystrokes:
        if ks.event == "keydown":
            print(f"  {ks.time}ms: {ks.key}")

    # Access focus events
    for focus in behavioral.focus:
        print(f"  {focus.time}ms: {focus.event}")

    # Access paste events
    for paste in behavioral.paste:
        print(f"  {paste.time}ms: pasted {paste.text_length} chars")
```

### KeystrokeEvent

A single keystroke event (keydown or keyup).

::: slopit.schemas.behavioral.KeystrokeEvent
    options:
      show_source: true
      members: []

#### Example

```python
from slopit.schemas import KeystrokeEvent

# KeystrokeEvent fields
event = KeystrokeEvent(
    time=1234.5,           # ms since trial start
    key="a",               # KeyboardEvent.key
    code="KeyA",           # KeyboardEvent.code
    event="keydown",       # "keydown" or "keyup"
    text_length=42,        # current text length
    modifiers=None,        # modifier key states
)
```

### FocusEvent

A focus or visibility change event.

::: slopit.schemas.behavioral.FocusEvent
    options:
      show_source: true
      members: []

### PasteEvent

A paste event from clipboard.

::: slopit.schemas.behavioral.PasteEvent
    options:
      show_source: true
      members: []

### ModifierState

Modifier key states at the time of a keystroke.

::: slopit.schemas.behavioral.ModifierState
    options:
      show_source: true
      members: []

## Metric Types

### KeystrokeMetrics

Computed metrics from keystroke data.

::: slopit.schemas.behavioral.KeystrokeMetrics
    options:
      show_source: true
      members: []

### FocusMetrics

Computed metrics from focus data.

::: slopit.schemas.behavioral.FocusMetrics
    options:
      show_source: true
      members: []

### TimingMetrics

Timing metrics for a trial.

::: slopit.schemas.behavioral.TimingMetrics
    options:
      show_source: true
      members: []

### BehavioralMetrics

Container for all computed behavioral metrics.

::: slopit.schemas.behavioral.BehavioralMetrics
    options:
      show_source: true
      members: []

## Flag Types

### AnalysisFlag

Flag generated during server-side analysis.

::: slopit.schemas.flags.AnalysisFlag
    options:
      show_source: true
      members: []

#### Example

```python
from slopit.schemas.flags import AnalysisFlag

flag = AnalysisFlag(
    type="low_iki_variance",
    analyzer="keystroke",
    severity="medium",
    message="Keystroke timing unusually consistent",
    confidence=0.75,
    evidence={"std_iki": 45.2},
    trial_ids=["trial-0", "trial-1"],
)
```

### CaptureFlag

Flag generated during client-side data capture.

::: slopit.schemas.flags.CaptureFlag
    options:
      show_source: true
      members: []

### Severity

Flag severity levels: `"info"`, `"low"`, `"medium"`, `"high"`.

## Analysis Result Types

### AnalysisResult

Result from a single analyzer.

::: slopit.schemas.analysis.AnalysisResult
    options:
      show_source: true
      members: []

### SessionVerdict

Final verdict for a session.

::: slopit.schemas.analysis.SessionVerdict
    options:
      show_source: true
      members: []

### PipelineResult

Result from the analysis pipeline.

::: slopit.schemas.analysis.PipelineResult
    options:
      show_source: true
      members: []

## Global Event Types

### GlobalEvents

Container for session-level events not tied to specific trials.

::: slopit.schemas.behavioral.GlobalEvents
    options:
      show_source: true
      members: []

### SessionFocusEvent

Session-level focus event.

::: slopit.schemas.behavioral.SessionFocusEvent
    options:
      show_source: true
      members: []

## Type Aliases

The `slopit.schemas.types` module defines type aliases used throughout the package:

```python
from slopit.schemas.types import (
    JsonPrimitive,      # str | int | float | bool | None
    JsonValue,          # JSON-compatible value
    Severity,           # "info" | "low" | "medium" | "high"
    EventType,          # "keydown" | "keyup"
    FocusEventType,     # "focus" | "blur" | "visibilitychange"
    VisibilityState,    # "visible" | "hidden"
    VerdictStatus,      # "clean" | "suspicious" | "flagged"
    Milliseconds,       # float
    UnixTimestamp,      # int
    SessionId,          # str
    TrialId,            # str
    ParticipantId,      # str
    StudyId,            # str
)
```
