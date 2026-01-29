# API Reference

This document provides comprehensive API documentation for the slopit Python package.

## Package Structure

```
slopit/
├── schemas/           # Pydantic data models
│   ├── session.py     # SlopitSession, SlopitTrial
│   ├── behavioral.py  # Behavioral events and metrics
│   ├── flags.py       # CaptureFlag, AnalysisFlag
│   ├── analysis.py    # AnalysisResult, PipelineResult
│   └── types.py       # Type aliases (JsonValue, etc.)
├── behavioral/        # Analysis modules
│   ├── base.py        # Analyzer base class
│   ├── keystroke.py   # KeystrokeAnalyzer
│   ├── focus.py       # FocusAnalyzer
│   ├── paste.py       # PasteAnalyzer
│   └── timing.py      # TimingAnalyzer
├── io/                # Data loading
│   ├── base.py        # BaseLoader
│   ├── native.py      # NativeLoader
│   └── jatos.py       # JATOSLoader
├── pipeline/          # Analysis orchestration
│   ├── pipeline.py    # AnalysisPipeline
│   ├── aggregation.py # Flag aggregation
│   └── reporting.py   # TextReporter, CSVExporter
└── dashboard/         # Web dashboard
    ├── app.py         # FastAPI application
    ├── config.py      # DashboardConfig
    ├── services/      # Business logic
    ├── integrations/  # JATOS, Prolific clients
    └── websocket/     # Real-time updates
```

## slopit.schemas

Data models for sessions, trials, events, and analysis results.

### Session Models

#### SlopitSession

Root container for a participant session.

```python
from slopit.schemas import SlopitSession

class SlopitSession(BaseModel):
    """Root container for a participant session.

    Attributes
    ----------
    schema_version
        Schema version for forward compatibility. Current: "1.0".
    session_id
        Unique session identifier.
    participant_id
        Participant identifier from recruitment platform.
    study_id
        Study identifier.
    platform
        Platform information (PlatformInfo).
    environment
        Client environment information (EnvironmentInfo).
    timing
        Session timing information (SessionTiming).
    trials
        List of trial data (list[SlopitTrial]).
    global_events
        Events not tied to specific trials (GlobalEvents).
    metadata
        Additional session metadata.
    """
```

**Example:**

```python
from slopit.schemas import SlopitSession

# validate from dict
session = SlopitSession.model_validate(raw_data)

# access fields
print(session.session_id)
print(session.participant_id)
print(len(session.trials))

# serialize to JSON
json_str = session.model_dump_json()
```

#### SlopitTrial

Data for a single trial.

```python
from slopit.schemas import SlopitTrial

class SlopitTrial(BaseModel):
    """Data for a single trial.

    Attributes
    ----------
    trial_id
        Unique trial identifier.
    trial_index
        Zero-indexed position in the session.
    trial_type
        Trial type identifier from the platform.
    start_time
        Trial start as Unix timestamp in milliseconds.
    end_time
        Trial end as Unix timestamp in milliseconds.
    rt
        Response time in milliseconds.
    stimulus
        Stimulus information (StimulusInfo).
    response
        Participant response (ResponseInfo).
    behavioral
        Behavioral capture data (BehavioralData).
    platform_data
        Platform-specific trial data.
    capture_flags
        Flags generated during capture.
    """
```

#### PlatformInfo

```python
class PlatformInfo(BaseModel):
    """Information about the experiment platform.

    Attributes
    ----------
    name
        Platform identifier ("jspsych", "labjs", "psychojs", etc.).
    version
        Platform version string.
    adapter_version
        Version of the slopit adapter used.
    """
```

#### EnvironmentInfo

```python
class EnvironmentInfo(BaseModel):
    """Client environment information captured at session start.

    Attributes
    ----------
    user_agent
        Browser user agent string.
    screen_resolution
        Screen dimensions as (width, height) in pixels.
    viewport_size
        Viewport dimensions as (width, height) in pixels.
    device_pixel_ratio
        Device pixel ratio for high-DPI displays.
    timezone
        IANA timezone identifier (e.g., "America/New_York").
    language
        Browser language setting (e.g., "en-US").
    touch_capable
        Whether touch input is available.
    connection_type
        Estimated connection type from Navigator.connection API.
    """
```

### Behavioral Events

#### KeystrokeEvent

```python
from slopit.schemas import KeystrokeEvent

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
        Modifier key states (ModifierState).
    """
```

**Example:**

```python
event = KeystrokeEvent(
    time=150.5,
    key="a",
    code="KeyA",
    event="keydown",
    text_length=5,
)
```

#### FocusEvent

```python
from slopit.schemas import FocusEvent

class FocusEvent(BaseModel):
    """A focus or visibility change event.

    Attributes
    ----------
    time
        Time since trial start in milliseconds.
    event
        Event type: "focus", "blur", or "visibilitychange".
    visibility
        For visibilitychange events, the new visibility state.
    blur_duration
        For blur events, duration until refocus in milliseconds.
    """
```

#### PasteEvent

```python
from slopit.schemas import PasteEvent

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
```

#### MouseEvent

```python
from slopit.schemas import MouseEvent

class MouseEvent(BaseModel):
    """Mouse event with kinematics data.

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
```

#### ScrollEvent

```python
from slopit.schemas import ScrollEvent

class ScrollEvent(BaseModel):
    """Scroll event for reading vs composing detection.

    Attributes
    ----------
    time
        Time since trial start in milliseconds.
    direction
        Scroll direction, either "up" or "down".
    delta_y
        Scroll amount in pixels.
    scroll_top
        Current scroll position from the top in pixels.
    scroll_height
        Total scrollable height in pixels.
    client_height
        Visible viewport height in pixels.
    velocity
        Scroll velocity in pixels per millisecond.
    """
```

### Behavioral Metrics

#### KeystrokeMetrics

```python
from slopit.schemas import KeystrokeMetrics

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
```

#### FocusMetrics

```python
from slopit.schemas import FocusMetrics

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
```

### Flags

#### CaptureFlag

Flags generated during client-side capture.

```python
from slopit.schemas import CaptureFlag

class CaptureFlag(BaseModel):
    """Flag generated during data capture.

    Attributes
    ----------
    type
        Flag type identifier.
    severity
        Severity level: "info", "low", "medium", or "high".
    message
        Human-readable description.
    timestamp
        Unix timestamp in milliseconds when flag was generated.
    details
        Additional details about the flag.
    """
```

#### AnalysisFlag

Flags generated during server-side analysis.

```python
from slopit.schemas.flags import AnalysisFlag

class AnalysisFlag(BaseModel):
    """Flag generated during server-side analysis.

    Attributes
    ----------
    type
        Flag type identifier (e.g., "low_iki_variance").
    analyzer
        Name of the analyzer that generated this flag.
    severity
        Severity level: "info", "low", "medium", or "high".
    message
        Human-readable description.
    confidence
        Confidence score between 0.0 and 1.0.
    evidence
        Evidence supporting this flag.
    trial_ids
        Related trial IDs if trial-specific.
    """
```

### Analysis Results

#### AnalysisResult

```python
from slopit.schemas.analysis import AnalysisResult

class AnalysisResult(BaseModel):
    """Result from a single analyzer.

    Attributes
    ----------
    analyzer
        Name of the analyzer that produced this result.
    session_id
        ID of the analyzed session.
    trials
        Per-trial analysis results.
    flags
        Flags generated by the analyzer.
    session_summary
        Session-level summary statistics.
    """
```

#### SessionVerdict

```python
from slopit.schemas.analysis import SessionVerdict

class SessionVerdict(BaseModel):
    """Final verdict for a session.

    Attributes
    ----------
    status
        Overall status: "clean", "suspicious", or "flagged".
    confidence
        Confidence in the verdict (0.0 to 1.0).
    flags
        All flags contributing to the verdict.
    summary
        Human-readable summary.
    """
```

#### PipelineResult

```python
from slopit.schemas.analysis import PipelineResult

class PipelineResult(BaseModel):
    """Result from the analysis pipeline.

    Attributes
    ----------
    sessions
        List of analyzed session IDs.
    analyzer_results
        Results from each analyzer, keyed by analyzer name.
    aggregated_flags
        Aggregated flags per session.
    verdicts
        Final verdict per session.

    Methods
    -------
    to_dict()
        Convert to dictionary for JSON serialization.
    """
```

### Type Aliases

```python
from slopit.schemas.types import JsonValue, Severity

# recursive JSON type
type JsonPrimitive = str | int | float | bool | None
type JsonValue = JsonPrimitive | list["JsonValue"] | dict[str, "JsonValue"]

# severity levels
type Severity = Literal["info", "low", "medium", "high"]

# verdict statuses
type VerdictStatus = Literal["clean", "suspicious", "flagged"]
```

---

## slopit.behavioral

Behavioral analyzers for detecting AI-assisted responses.

### Base Classes

#### Analyzer

Abstract base class for all analyzers.

```python
from slopit.behavioral import Analyzer

class Analyzer(ABC):
    """Base class for all analyzers.

    Attributes
    ----------
    name : str
        Unique identifier for this analyzer.

    Methods
    -------
    analyze_session(session)
        Analyze a single session.
    analyze_sessions(sessions)
        Analyze multiple sessions.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this analyzer."""
        ...

    @abstractmethod
    def analyze_session(self, session: SlopitSession) -> AnalysisResult:
        """Analyze a single session."""
        ...

    def analyze_sessions(self, sessions: list[SlopitSession]) -> list[AnalysisResult]:
        """Analyze multiple sessions (override for cross-session analysis)."""
        return [self.analyze_session(s) for s in sessions]
```

### KeystrokeAnalyzer

Analyzes keystroke timing patterns to detect transcription.

```python
from slopit.behavioral import KeystrokeAnalyzer, KeystrokeAnalyzerConfig

class KeystrokeAnalyzerConfig:
    """Configuration for keystroke analysis.

    Attributes
    ----------
    pause_threshold_ms : float
        Minimum IKI to count as a pause (default: 2000.0).
    burst_threshold_ms : float
        Maximum IKI within a typing burst (default: 500.0).
    min_keystrokes : int
        Minimum keystrokes required for analysis (default: 20).
    min_iki_std_threshold : float
        Minimum IKI std for authentic typing (default: 100.0).
    max_ppr_threshold : float
        Maximum product-process ratio (default: 0.95).
    """

class KeystrokeAnalyzer(Analyzer):
    """Analyzer for keystroke dynamics.

    Detects transcription patterns by analyzing inter-keystroke intervals,
    revision behavior, and typing burst characteristics.

    Flags Generated
    ---------------
    low_iki_variance
        Keystroke timing unusually consistent (severity: medium).
    minimal_revision
        Very few revisions during composition (severity: low).
    no_deletions
        No deletion keystrokes in extended response (severity: low).
    """
```

**Example:**

```python
from slopit.behavioral import KeystrokeAnalyzer, KeystrokeAnalyzerConfig

# with default config
analyzer = KeystrokeAnalyzer()

# with custom config
config = KeystrokeAnalyzerConfig(
    min_keystrokes=30,
    min_iki_std_threshold=80.0,
)
analyzer = KeystrokeAnalyzer(config)

# analyze
result = analyzer.analyze_session(session)
print(f"Flags: {len(result.flags)}")
```

### FocusAnalyzer

Analyzes focus and visibility patterns to detect external assistance.

```python
from slopit.behavioral import FocusAnalyzer, FocusAnalyzerConfig

class FocusAnalyzerConfig:
    """Configuration for focus analysis.

    Attributes
    ----------
    max_blur_count : int
        Maximum blur events before flagging (default: 5).
    max_hidden_duration_ms : float
        Maximum hidden duration in ms (default: 30000.0).
    blur_paste_window_ms : float
        Window for blur-paste pattern detection (default: 5000.0).
    """

class FocusAnalyzer(Analyzer):
    """Analyzer for focus and visibility patterns.

    Detects patterns that suggest external assistance such as
    excessive tab switching or extended hidden periods.

    Flags Generated
    ---------------
    excessive_blur
        Excessive window switches detected (severity: medium).
    extended_hidden
        Extended tab switch detected (severity: medium).
    blur_paste_pattern
        Paste event detected shortly after tab switch (severity: high).
    """
```

**Example:**

```python
from slopit.behavioral import FocusAnalyzer, FocusAnalyzerConfig

config = FocusAnalyzerConfig(
    max_blur_count=3,
    blur_paste_window_ms=3000.0,
)
analyzer = FocusAnalyzer(config)
result = analyzer.analyze_session(session)
```

### PasteAnalyzer

Analyzes paste events and clipboard usage.

```python
from slopit.behavioral import PasteAnalyzer, PasteAnalyzerConfig

class PasteAnalyzerConfig:
    """Configuration for paste analysis.

    Attributes
    ----------
    large_paste_threshold : int
        Minimum characters to flag as large paste (default: 50).
    suspicious_preceding_keystrokes : int
        Max keystrokes before paste to flag (default: 5).
    """

class PasteAnalyzer(Analyzer):
    """Analyzer for paste events and clipboard usage.

    Detects suspicious paste patterns such as large pastes
    without prior typing.

    Flags Generated
    ---------------
    large_paste
        Large paste detected (severity: medium).
    paste_without_typing
        Paste with minimal prior typing (severity: medium/high).
    """
```

**Example:**

```python
from slopit.behavioral import PasteAnalyzer, PasteAnalyzerConfig

config = PasteAnalyzerConfig(
    large_paste_threshold=100,
    suspicious_preceding_keystrokes=10,
)
analyzer = PasteAnalyzer(config)
result = analyzer.analyze_session(session)
```

### TimingAnalyzer

Analyzes response timing patterns.

```python
from slopit.behavioral import TimingAnalyzer, TimingAnalyzerConfig

class TimingAnalyzerConfig:
    """Configuration for timing analysis.

    Attributes
    ----------
    min_rt_per_char_ms : float
        Minimum expected ms per character (default: 20.0).
    max_rt_cv_threshold : float
        Maximum CV for response times (default: 0.1).
    instant_response_threshold_ms : float
        Threshold for instant response (default: 2000.0).
    instant_response_min_chars : int
        Minimum chars for instant response flag (default: 100).
    """

class TimingAnalyzer(Analyzer):
    """Analyzer for response timing patterns.

    Detects suspiciously fast responses or unusually consistent
    timing across trials.

    Flags Generated
    ---------------
    instant_response
        Suspiciously fast response (severity: high).
    fast_typing
        Typing speed exceeds human capability (severity: medium).
    consistent_timing
        Unusually consistent response times (severity: medium).
    """
```

---

## slopit.io

Data loaders for various formats.

### load_session

```python
from slopit import load_session

def load_session(path: str | Path) -> SlopitSession:
    """Load a single session from a file.

    Automatically detects the file format and uses the appropriate loader.

    Parameters
    ----------
    path
        Path to the session file.

    Returns
    -------
    SlopitSession
        The loaded session data.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    ValueError
        If the file format cannot be determined.
    """
```

### load_sessions

```python
from slopit import load_sessions

def load_sessions(path: str | Path, pattern: str = "*") -> list[SlopitSession]:
    """Load multiple sessions from a directory.

    Parameters
    ----------
    path
        Path to directory containing session files.
    pattern
        Glob pattern for file matching.

    Returns
    -------
    list[SlopitSession]
        List of loaded sessions.
    """
```

### NativeLoader

```python
from slopit.io import NativeLoader

class NativeLoader(BaseLoader):
    """Loader for native slopit JSON format.

    The native format is a JSON file that directly contains a SlopitSession
    object with schema_version field.

    Methods
    -------
    load(path)
        Load a single native JSON file.
    load_many(path, pattern="*.json")
        Load multiple native JSON files.
    can_load(path)
        Check if path is native format.
    """
```

**Example:**

```python
from pathlib import Path
from slopit.io import NativeLoader

loader = NativeLoader()
session = loader.load(Path("data/session.json"))

for session in loader.load_many(Path("data/"), pattern="*.json"):
    print(session.session_id)
```

### JATOSLoader

```python
from slopit.io import JATOSLoader

class JATOSLoader(BaseLoader):
    """Loader for JATOS export format.

    JATOS exports data as JSON arrays or newline-delimited JSON.
    This loader handles both formats.

    Methods
    -------
    load(path)
        Load a JATOS result file.
    load_result(trials, result_id)
        Load from raw trial data (useful for API results).
    load_many(path, pattern="*.txt")
        Load multiple JATOS result files.
    can_load(path)
        Check if path is JATOS format.
    """
```

**Example:**

```python
from pathlib import Path
from slopit.io import JATOSLoader

loader = JATOSLoader()

# from file
session = loader.load(Path("study_result_123.txt"))

# from raw data (e.g., from API)
trials = [{"trial_type": "survey", "response": "..."}]
session = loader.load_result(trials, result_id="api-result-1")
```

---

## slopit.pipeline

Analysis orchestration and reporting.

### AnalysisPipeline

```python
from slopit.pipeline import AnalysisPipeline, PipelineConfig

class PipelineConfig:
    """Configuration for the analysis pipeline.

    Attributes
    ----------
    aggregation : Literal["any", "majority", "weighted"]
        Strategy for combining flags (default: "weighted").
    severity_threshold : Literal["info", "low", "medium", "high"]
        Minimum severity to include (default: "low").
    confidence_threshold : float
        Minimum confidence to include (default: 0.5).
    """

class AnalysisPipeline:
    """Orchestrates multiple analyzers and aggregates results.

    Parameters
    ----------
    analyzers
        List of analyzers to run.
    config
        Pipeline configuration.

    Methods
    -------
    analyze(sessions)
        Run all analyzers and aggregate results.
    """
```

**Example:**

```python
from slopit.pipeline import AnalysisPipeline, PipelineConfig
from slopit.behavioral import KeystrokeAnalyzer, FocusAnalyzer

config = PipelineConfig(
    aggregation="weighted",
    severity_threshold="medium",
    confidence_threshold=0.6,
)

pipeline = AnalysisPipeline(
    [KeystrokeAnalyzer(), FocusAnalyzer()],
    config,
)

result = pipeline.analyze(sessions)
```

### Aggregation Strategies

```python
from slopit.pipeline import AggregationStrategy, aggregate_flags

type AggregationStrategy = Literal["any", "majority", "weighted"]

def aggregate_flags(
    flags: list[AnalysisFlag],
    strategy: AggregationStrategy,
    total_analyzers: int,
) -> tuple[VerdictStatus, float]:
    """Aggregate flags using the specified strategy.

    Strategies
    ----------
    any
        Flag if any analyzer produces a flag. Most sensitive.
    majority
        Flag if majority of analyzers flag. Balanced.
    weighted
        Use confidence-weighted voting. Recommended.

    Returns
    -------
    tuple[VerdictStatus, float]
        Verdict status ("clean", "suspicious", "flagged") and confidence.
    """
```

### TextReporter

```python
from slopit.pipeline import TextReporter

class TextReporter:
    """Generate text reports from analysis results.

    Methods
    -------
    generate(result)
        Generate a text report string.
    print_summary(result)
        Print a summary table using Rich.
    """
```

**Example:**

```python
from slopit.pipeline import TextReporter

reporter = TextReporter()

# full text report
report = reporter.generate(result)
print(report)

# summary table
reporter.print_summary(result)
```

### CSVExporter

```python
from slopit.pipeline import CSVExporter

class CSVExporter:
    """Export analysis results to CSV format.

    Methods
    -------
    export(result, path)
        Export session verdicts to CSV.
    export_flags(result, path)
        Export individual flags to CSV.
    """
```

**Example:**

```python
from slopit.pipeline import CSVExporter

exporter = CSVExporter()
exporter.export(result, "verdicts.csv")
exporter.export_flags(result, "flags.csv")
```

---

## slopit.dashboard

Web dashboard for real-time session analysis and monitoring.

The dashboard module provides:

- FastAPI-based REST API for session and verdict management
- WebSocket support for real-time updates
- File-based JSON storage service
- Background analysis processing
- JATOS and Prolific integration clients
- React frontend embedding support

### Module Structure

```
dashboard/
├── app.py              # FastAPI application factory
├── config.py           # DashboardConfig model
├── dependencies.py     # Dependency injection
├── api/                # REST API endpoints
│   ├── sessions.py     # Session CRUD
│   ├── trials.py       # Trial data access
│   ├── analysis.py     # Verdicts and flags
│   ├── export.py       # CSV/JSON export
│   ├── jatos.py        # JATOS sync endpoints
│   └── prolific.py     # Prolific submission management
├── services/           # Business logic
│   ├── storage_service.py   # File-based storage
│   ├── analysis_service.py  # Background analysis
│   ├── session_service.py   # Session management
│   └── export_service.py    # Export generation
├── websocket/          # Real-time updates
│   ├── events.py       # Event type definitions
│   ├── manager.py      # Connection management
│   └── handlers.py     # Message handlers
└── integrations/       # External services
    ├── jatos.py        # JATOS API client
    └── prolific.py     # Prolific API client
```

### DashboardConfig

```python
from slopit.dashboard import DashboardConfig

class DashboardConfig(BaseModel):
    """Dashboard configuration.

    Attributes
    ----------
    host
        Host address to bind the server to. Default: "127.0.0.1".
    port
        Port number to listen on. Default: 8000.
    data_dir
        Directory for storing session data files. Default: "./data".
    cors_origins
        List of allowed CORS origins for API requests. Default: ["*"].
    reload
        Enable auto-reload for development. Default: False.
    jatos_url
        URL of the JATOS server for data synchronization.
    jatos_token
        Authentication token for JATOS API access.
    prolific_token
        Authentication token for Prolific API access.
    """
```

**Example:**

```python
from pathlib import Path
from slopit.dashboard import DashboardConfig

config = DashboardConfig(
    host="0.0.0.0",
    port=8080,
    data_dir=Path("./sessions"),
    cors_origins=["http://localhost:3000"],
    reload=True,
    jatos_url="https://jatos.example.com",
    jatos_token="your-jatos-api-token",
    prolific_token="your-prolific-api-token",
)
```

### create_app

```python
from slopit.dashboard.app import create_app

def create_app(config: DashboardConfig | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Parameters
    ----------
    config
        Dashboard configuration. Uses defaults if not provided.

    Returns
    -------
    FastAPI
        Configured FastAPI application instance with:
        - CORS middleware
        - Session, trial, analysis, and export API routes
        - WebSocket endpoint at /ws
        - Static file serving for React frontend (if present)
    """
```

**Example:**

```python
from slopit.dashboard import DashboardConfig
from slopit.dashboard.app import create_app
import uvicorn

config = DashboardConfig(port=8080)
app = create_app(config)

# run the server
uvicorn.run(app, host=config.host, port=config.port)
```

### Services

#### StorageService

File-based persistent storage for sessions and analysis verdicts.

```python
from pathlib import Path
from slopit.dashboard.services import StorageService, SessionIndex

class SessionIndex(BaseModel):
    """Index entry for a session.

    Attributes
    ----------
    session_id
        Unique identifier for the session.
    created_at
        ISO 8601 timestamp or Unix timestamp string.
    trial_count
        Number of trials in the session.
    has_verdict
        Whether a verdict has been computed.
    """

class StorageService:
    """File-based storage for sessions and verdicts.

    Stores data in a directory structure:

        data/
        ├── sessions/
        │   ├── {session_id}.json
        │   └── index.json
        ├── verdicts/
        │   └── {session_id}.json
        └── exports/
            └── {timestamp}.csv

    Parameters
    ----------
    data_dir
        Root directory for data storage.
    """
```

**Methods:**

| Method | Description |
|--------|-------------|
| `save_session(session)` | Save a SlopitSession to storage |
| `get_session(session_id)` | Retrieve session by ID (returns None if not found) |
| `list_sessions(page, page_size, has_verdict)` | Paginated session listing with optional filter |
| `iter_sessions()` | Iterate over all stored sessions |
| `save_verdict(session_id, verdict)` | Save analysis verdict for a session |
| `get_verdict(session_id)` | Retrieve verdict by session ID |

**Example:**

```python
from pathlib import Path
from slopit.dashboard.services import StorageService
from slopit.schemas import SlopitSession

storage = StorageService(Path("./data"))

# save a session
storage.save_session(session)

# retrieve it
retrieved = storage.get_session(session.session_id)

# list sessions with pagination
sessions, total = storage.list_sessions(page=1, page_size=20, has_verdict=True)
print(f"Page 1 of {total // 20 + 1}")

# iterate all sessions
for session in storage.iter_sessions():
    print(session.session_id)

# save and retrieve verdict
storage.save_verdict("session-123", {
    "status": "flagged",
    "confidence": 0.85,
    "flags": ["low_iki_variance"],
    "summary": "Detected: low_iki_variance",
})

verdict = storage.get_verdict("session-123")
print(f"Status: {verdict['status']}")
```

#### AnalysisService

Background analysis worker for processing sessions asynchronously.

```python
from slopit.dashboard.services import AnalysisService

class AnalysisService:
    """Background analysis service.

    Provides real-time analysis of sessions using the standard
    slopit analysis pipeline. Sessions can be queued for background
    processing or analyzed synchronously.

    The service runs all four behavioral analyzers:
    - KeystrokeAnalyzer
    - FocusAnalyzer
    - PasteAnalyzer
    - TimingAnalyzer
    """
```

**Methods:**

| Method | Description |
|--------|-------------|
| `start()` | Start the background worker task |
| `stop()` | Stop the background worker |
| `enqueue_session(session)` | Add session to processing queue |
| `analyze_session(session)` | Analyze synchronously (returns verdict dict) |
| `on_complete(callback)` | Register callback for completed analysis |

**Example:**

```python
import asyncio
from slopit.dashboard.services import AnalysisService, StorageService
from pathlib import Path

storage = StorageService(Path("./data"))
service = AnalysisService()

# register callback to save verdicts
def save_verdict(session_id: str, verdict: dict) -> None:
    storage.save_verdict(session_id, verdict)
    print(f"Saved verdict for {session_id}: {verdict['status']}")

service.on_complete(save_verdict)

async def main() -> None:
    # start the background worker
    await service.start()

    # enqueue sessions for background processing
    for session in storage.iter_sessions():
        await service.enqueue_session(session)

    # wait for processing
    await asyncio.sleep(5)

    # stop the worker
    await service.stop()

asyncio.run(main())
```

**Synchronous analysis:**

```python
async def analyze_single(session: SlopitSession) -> None:
    service = AnalysisService()
    verdict = await service.analyze_session(session)
    print(f"Status: {verdict['status']}")
    print(f"Confidence: {verdict['confidence']}")
    print(f"Flags: {verdict['flags']}")
```

### Integrations

#### JATOSClient

Async client for syncing data from JATOS (Just Another Tool for Online Studies).

```python
from slopit.dashboard.integrations import JATOSClient

class JATOSClient:
    """Client for JATOS API integration.

    Parameters
    ----------
    base_url
        JATOS server URL (e.g., "https://jatos.example.com").
    token
        JATOS API token for authentication.
    """
```

**Methods:**

| Method | Description |
|--------|-------------|
| `list_studies()` | List all accessible studies |
| `get_study(study_id)` | Get metadata for a study |
| `get_study_results(study_id)` | Get raw result data for a study |
| `get_result(study_id, result_id)` | Get a specific result |
| `stream_results(study_id)` | Async generator yielding SlopitSession objects |
| `get_sessions(study_id)` | Get all results as SlopitSession list |
| `close()` | Close the HTTP client |

**Example:**

```python
from slopit.dashboard.integrations import JATOSClient
from slopit.dashboard.services import StorageService
from pathlib import Path

storage = StorageService(Path("./data"))

async def sync_from_jatos() -> None:
    async with JATOSClient("https://jatos.example.com", "api-token") as client:
        # list available studies
        studies = await client.list_studies()
        for study in studies:
            print(f"Study: {study['title']} (ID: {study['id']})")

        # sync all sessions from a study
        async for session in client.stream_results("study-123"):
            storage.save_session(session)
            print(f"Synced: {session.session_id}")

        # or get all at once
        sessions = await client.get_sessions("study-456")
        print(f"Retrieved {len(sessions)} sessions")
```

#### ProlificClient

Async client for managing Prolific participant submissions.

```python
from slopit.dashboard.integrations import (
    ProlificClient,
    ParticipantAction,
    SubmissionStatus,
)

class ParticipantAction(str, Enum):
    """Actions for Prolific submissions."""
    APPROVE = "APPROVE"   # approve and pay participant
    REJECT = "REJECT"     # reject submission (use sparingly)
    RETURN = "RETURN"     # return to pool without penalty

class SubmissionStatus(str, Enum):
    """Prolific submission statuses."""
    ACTIVE = "ACTIVE"
    AWAITING_REVIEW = "AWAITING REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RETURNED = "RETURNED"
    TIMED_OUT = "TIMED-OUT"

class ProlificClient:
    """Client for Prolific API integration.

    Parameters
    ----------
    token
        Prolific API token for authentication.
    """
```

**Methods:**

| Method | Description |
|--------|-------------|
| `list_studies()` | List all studies for the account |
| `get_study(study_id)` | Get study details |
| `get_submissions(study_id, status)` | Get submissions (optionally filtered) |
| `get_submission(submission_id)` | Get a specific submission |
| `approve_submission(submission_id, message)` | Approve and pay |
| `reject_submission(submission_id, category, message)` | Reject with reason |
| `return_submission(submission_id, message)` | Return to pool |
| `batch_approve(study_id, submission_ids)` | Approve multiple |
| `batch_reject(study_id, submission_ids, category)` | Reject multiple |
| `batch_return(study_id, submission_ids)` | Return multiple |
| `close()` | Close the HTTP client |

**Example:**

```python
from slopit.dashboard.integrations import ProlificClient, SubmissionStatus

async def manage_submissions() -> None:
    async with ProlificClient("api-token") as client:
        # list studies
        studies = await client.list_studies()

        # get submissions awaiting review
        submissions = await client.get_submissions(
            "study-123",
            status=SubmissionStatus.AWAITING_REVIEW,
        )

        # approve clean submissions
        clean_ids = ["sub-1", "sub-2"]
        await client.batch_approve("study-123", clean_ids)

        # reject with category
        await client.reject_submission(
            "sub-3",
            rejection_category="NO_DATA",
            message="No response data recorded.",
        )

        # return submission to pool
        await client.return_submission(
            "sub-4",
            message="Technical issue; please try again.",
        )
```

### WebSocket Events

Real-time event system for live dashboard updates.

```python
from slopit.dashboard.websocket import (
    WebSocketEvent,
    SessionNewEvent,
    VerdictComputedEvent,
    SyncProgressEvent,
    ConnectionManager,
)
```

#### Event Types

**SessionNewEvent:** Sent when a new session is stored.

```python
class SessionNewEvent(BaseModel):
    type: Literal["session.new"] = "session.new"
    data: dict[str, object]  # session_id, timestamp, trial_count
```

**VerdictComputedEvent:** Sent when analysis completes.

```python
class VerdictComputedEvent(BaseModel):
    type: Literal["verdict.computed"] = "verdict.computed"
    data: dict[str, object]  # session_id, status, confidence, flags
```

**SyncProgressEvent:** Sent during JATOS/Prolific sync.

```python
class SyncProgressEvent(BaseModel):
    type: Literal["sync.progress"] = "sync.progress"
    data: dict[str, object]  # source, progress, total, status
```

#### ConnectionManager

```python
class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and register a connection."""

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a connection."""

    async def broadcast(self, event: WebSocketEvent) -> None:
        """Send event to all connected clients."""

    async def send_personal(self, websocket: WebSocket, event: WebSocketEvent) -> None:
        """Send event to a specific client."""

    @property
    def connection_count(self) -> int:
        """Number of active connections."""
```

**Server-side example:**

```python
from slopit.dashboard.websocket import (
    ConnectionManager,
    SessionNewEvent,
    VerdictComputedEvent,
)

manager = ConnectionManager()

# broadcast new session to all clients
await manager.broadcast(
    SessionNewEvent(data={
        "session_id": "abc123",
        "timestamp": 1706000000000,
        "trial_count": 5,
    })
)

# broadcast verdict
await manager.broadcast(
    VerdictComputedEvent(data={
        "session_id": "abc123",
        "status": "flagged",
        "confidence": 0.85,
        "flags": ["low_iki_variance"],
    })
)
```

### REST API Endpoints

The dashboard exposes REST endpoints under `/api/v1/`.

#### Sessions API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/sessions/` | List sessions with pagination |
| GET | `/api/v1/sessions/{id}` | Get session details |
| GET | `/api/v1/sessions/{id}/trials` | Get trials for a session |
| GET | `/api/v1/sessions/{id}/verdict` | Get verdict for a session |

**List sessions request:**

```bash
curl "http://localhost:8000/api/v1/sessions/?page=1&page_size=20&has_verdict=true"
```

**Response:**

```json
{
  "sessions": [
    {
      "session_id": "abc123",
      "created_at": "1706000000000",
      "trial_count": 5,
      "has_verdict": true
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 20
}
```

#### Trials API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/trials/` | List all trials with pagination |
| GET | `/api/v1/trials/{session_id}/{index}` | Get trial details |
| GET | `/api/v1/trials/{session_id}/{index}/keystrokes` | Get keystroke events |
| GET | `/api/v1/trials/{session_id}/{index}/metrics` | Get computed metrics |

**Get trial keystrokes:**

```bash
curl "http://localhost:8000/api/v1/trials/abc123/0/keystrokes?limit=100"
```

#### Analysis API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/analysis/summary` | Get aggregate statistics |
| GET | `/api/v1/analysis/flags` | List available flag types |
| GET | `/api/v1/analysis/verdicts` | List verdicts with pagination |
| GET | `/api/v1/analysis/verdicts/{id}` | Get detailed verdict |
| POST | `/api/v1/analysis/batch` | Start batch analysis |
| GET | `/api/v1/analysis/batch/{task_id}` | Get batch task status |

**Batch analysis request:**

```bash
curl -X POST http://localhost:8000/api/v1/analysis/batch \
  -H "Content-Type: application/json" \
  -d '{"session_ids": ["abc123", "def456"], "force_reanalyze": false}'
```

**Response:**

```json
{
  "task_id": "task-789",
  "queued_count": 2,
  "skipped_count": 0
}
```

#### Export API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/export/sessions/csv` | Export sessions as CSV |
| GET | `/api/v1/export/trials/csv` | Export trials as CSV |
| GET | `/api/v1/export/keystrokes/csv` | Export keystrokes as CSV |
| GET | `/api/v1/export/verdicts/csv` | Export verdicts as CSV |
| POST | `/api/v1/export/json` | Start JSON export task |
| GET | `/api/v1/export/status/{task_id}` | Get export task status |

**Export verdicts:**

```bash
curl "http://localhost:8000/api/v1/export/verdicts/csv?verdict_filter=flagged" \
  -o flagged_verdicts.csv
```

#### JATOS Integration API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/jatos/connect` | Test connection and list studies |
| POST | `/api/v1/jatos/sync` | Sync results from a study |
| GET | `/api/v1/jatos/studies/{id}/results` | Get raw study results |

**Connect and list studies:**

```bash
curl -X POST http://localhost:8000/api/v1/jatos/connect \
  -H "Content-Type: application/json" \
  -d '{"base_url": "https://jatos.example.com", "token": "api-token"}'
```

**Sync study results:**

```bash
curl -X POST http://localhost:8000/api/v1/jatos/sync \
  -H "Content-Type: application/json" \
  -d '{
    "connection": {"base_url": "https://jatos.example.com", "token": "api-token"},
    "study_id": "study-123"
  }'
```

#### Prolific Integration API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/prolific/connect` | Test connection and list studies |
| GET | `/api/v1/prolific/studies/{id}/submissions` | Get study submissions |
| GET | `/api/v1/prolific/submissions/{id}` | Get submission details |
| POST | `/api/v1/prolific/submissions/transition` | Transition single submission |
| POST | `/api/v1/prolific/submissions/batch-transition` | Batch transition |

**Get submissions:**

```bash
curl "http://localhost:8000/api/v1/prolific/studies/study-123/submissions?token=api-token&status=AWAITING%20REVIEW"
```

**Batch approve:**

```bash
curl -X POST http://localhost:8000/api/v1/prolific/submissions/batch-transition \
  -H "Content-Type: application/json" \
  -d '{
    "token": "api-token",
    "study_id": "study-123",
    "submission_ids": ["sub-1", "sub-2"],
    "action": "APPROVE"
  }'
```

### React Frontend Integration

The dashboard serves a React frontend from the `static/` directory when present. To embed the dashboard UI:

1. Build the React app from `packages/dashboard-ui`
2. Copy build output to `python/src/slopit/dashboard/static/`
3. The app mounts at `/` and communicates via the REST API and WebSocket

**Manual setup:**

```bash
# from project root
cd packages/dashboard-ui
npm run build

# copy to Python package
cp -r dist/* ../python/src/slopit/dashboard/static/
```

The React app connects to:

- REST API: `http://localhost:8000/api/v1/`
- WebSocket: `ws://localhost:8000/ws`

---

## Complete Example

```python
"""Complete example of slopit analysis workflow."""

from pathlib import Path

from slopit import load_sessions
from slopit.pipeline import AnalysisPipeline, PipelineConfig, TextReporter, CSVExporter
from slopit.behavioral import (
    KeystrokeAnalyzer,
    KeystrokeAnalyzerConfig,
    FocusAnalyzer,
    FocusAnalyzerConfig,
    PasteAnalyzer,
    TimingAnalyzer,
)


def main() -> None:
    # load data
    sessions = load_sessions(Path("data/study1"))
    print(f"Loaded {len(sessions)} sessions")

    # configure analyzers
    keystroke_config = KeystrokeAnalyzerConfig(
        min_keystrokes=25,
        min_iki_std_threshold=90.0,
    )
    focus_config = FocusAnalyzerConfig(
        max_blur_count=3,
    )

    # create pipeline
    pipeline = AnalysisPipeline(
        analyzers=[
            KeystrokeAnalyzer(keystroke_config),
            FocusAnalyzer(focus_config),
            PasteAnalyzer(),
            TimingAnalyzer(),
        ],
        config=PipelineConfig(
            aggregation="weighted",
            severity_threshold="low",
            confidence_threshold=0.5,
        ),
    )

    # run analysis
    result = pipeline.analyze(sessions)

    # print summary
    reporter = TextReporter()
    reporter.print_summary(result)

    # detailed report
    report = reporter.generate(result)
    Path("report.txt").write_text(report)

    # export to CSV
    exporter = CSVExporter()
    exporter.export(result, "verdicts.csv")
    exporter.export_flags(result, "flags.csv")

    # print flagged sessions
    for session_id, verdict in result.verdicts.items():
        if verdict.status == "flagged":
            print(f"\n{session_id}: {verdict.summary}")
            for flag in verdict.flags:
                print(f"  - {flag.type}: {flag.message}")


if __name__ == "__main__":
    main()
```
