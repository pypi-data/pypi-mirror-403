# slopit

A modular Python toolkit for detecting AI-assisted responses in crowdsourced behavioral research.

## Key Features

- **Behavioral Analysis**: Analyze keystroke dynamics, focus patterns, and paste events
- **Multiple Analyzers**: Combine evidence from independent analyzers for robust detection
- **Real-time Dashboard**: Web-based monitoring with JATOS and Prolific integration
- **Pipeline Orchestration**: Configure aggregation strategies and confidence thresholds
- **Multiple Data Formats**: Load data from JATOS, native JSON, and other sources
- **CLI and API**: Command-line tools and Python API for flexible integration

## Installation

### Basic Installation

```bash
pip install slopit
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add slopit
```

### With Dashboard (Recommended)

```bash
pip install slopit[dashboard]
```

This adds the web dashboard with:

- FastAPI-based REST API
- WebSocket real-time updates
- JATOS data synchronization
- Prolific submission management
- React-based UI

### Other Optional Dependencies

```bash
# LLM-based analysis (requires PyTorch)
pip install slopit[llm]

# Documentation building
pip install slopit[docs]

# All optional dependencies
pip install slopit[dashboard,llm,docs]
```

### Development Installation

```bash
git clone https://github.com/slopit/slopit.git
cd slopit/python
pip install -e ".[dev]"
```

## Requirements

- Python 3.13+
- NumPy 2.0+
- pandas 2.2+
- scikit-learn 1.5+
- Pydantic 2.10+

## Quick Start

### Loading and Analyzing Sessions

```python
from slopit import load_session, load_sessions
from slopit.pipeline import AnalysisPipeline
from slopit.behavioral import (
    KeystrokeAnalyzer,
    FocusAnalyzer,
    PasteAnalyzer,
    TimingAnalyzer,
)

# load a single session
session = load_session("data/participant_001.json")

# or load all sessions from a directory
sessions = load_sessions("data/")

# create an analysis pipeline with multiple analyzers
pipeline = AnalysisPipeline([
    KeystrokeAnalyzer(),
    FocusAnalyzer(),
    PasteAnalyzer(),
    TimingAnalyzer(),
])

# run analysis
result = pipeline.analyze(sessions)

# check verdicts for each session
for session_id, verdict in result.verdicts.items():
    print(f"{session_id}: {verdict.status} (confidence: {verdict.confidence:.2f})")
    if verdict.flags:
        for flag in verdict.flags:
            print(f"  - [{flag.analyzer}] {flag.type}: {flag.message}")
```

### Using the CLI

Analyze sessions from the command line:

```bash
# analyze sessions and print report
slopit analyze data/

# analyze with specific analyzers
slopit analyze data/ --analyzers keystroke,focus

# export results to JSON
slopit analyze data/ --output results.json

# export results to CSV
slopit analyze data/ --csv results.csv

# print summary table only
slopit analyze data/ --summary
```

Validate session files:

```bash
slopit validate data/session.json
slopit validate data/
```

Generate reports from previous analysis:

```bash
slopit report results.json
slopit report results.json --format csv --output report.csv
```

Start the dashboard server:

```bash
# default settings (localhost:8000)
slopit dashboard

# custom host and port
slopit dashboard --host 0.0.0.0 --port 8080

# development mode with auto-reload
slopit dashboard --reload
```

## Loading Data

### Native JSON Format

Load sessions in the native slopit format:

```python
from slopit import load_session, load_sessions

# single file
session = load_session("data/session.json")

# directory of files
sessions = load_sessions("data/")

# with glob pattern
sessions = load_sessions("data/", pattern="*.json")
```

### JATOS Export Format

Load data exported from JATOS:

```python
from slopit.io import JATOSLoader

loader = JATOSLoader()

# load a single result file
session = loader.load("study_result_123.txt")

# load all results from a directory
for session in loader.load_many("jatos_results/"):
    print(f"Loaded session {session.session_id}")
```

### Direct JATOS API Access

Connect to a JATOS server to retrieve results:

```python
from slopit.dashboard.integrations import JATOSClient

async with JATOSClient("https://jatos.example.com", "api-token") as client:
    # list available studies
    studies = await client.list_studies()

    # get all sessions for a study
    sessions = await client.get_sessions("study-123")

    # or stream sessions one at a time
    async for session in client.stream_results("study-123"):
        print(f"Session: {session.session_id}")
```

## Analysis Pipeline

### Creating a Pipeline

```python
from slopit.pipeline import AnalysisPipeline, PipelineConfig
from slopit.behavioral import KeystrokeAnalyzer, FocusAnalyzer

# basic pipeline
pipeline = AnalysisPipeline([
    KeystrokeAnalyzer(),
    FocusAnalyzer(),
])

# pipeline with custom configuration
config = PipelineConfig(
    aggregation="weighted",      # "any", "majority", or "weighted"
    severity_threshold="low",    # minimum severity to include
    confidence_threshold=0.5,    # minimum confidence to include
)
pipeline = AnalysisPipeline([KeystrokeAnalyzer()], config)
```

### Configuring Analyzers

Each analyzer accepts a configuration object:

```python
from slopit.behavioral import (
    KeystrokeAnalyzer,
    KeystrokeAnalyzerConfig,
    FocusAnalyzer,
    FocusAnalyzerConfig,
    PasteAnalyzer,
    PasteAnalyzerConfig,
    TimingAnalyzer,
    TimingAnalyzerConfig,
)

# keystroke analyzer configuration
keystroke_config = KeystrokeAnalyzerConfig(
    pause_threshold_ms=2000.0,      # minimum IKI to count as pause
    burst_threshold_ms=500.0,       # maximum IKI within typing burst
    min_keystrokes=20,              # minimum keystrokes for analysis
    min_iki_std_threshold=100.0,    # threshold for low variance flag
    max_ppr_threshold=0.95,         # threshold for minimal revision flag
)
keystroke_analyzer = KeystrokeAnalyzer(keystroke_config)

# focus analyzer configuration
focus_config = FocusAnalyzerConfig(
    max_blur_count=5,               # blur events before flagging
    max_hidden_duration_ms=30000.0, # hidden duration before flagging
    blur_paste_window_ms=5000.0,    # window for blur-paste detection
)
focus_analyzer = FocusAnalyzer(focus_config)

# paste analyzer configuration
paste_config = PasteAnalyzerConfig(
    large_paste_threshold=50,           # characters for large paste flag
    suspicious_preceding_keystrokes=5,  # max keystrokes before paste
)
paste_analyzer = PasteAnalyzer(paste_config)

# timing analyzer configuration
timing_config = TimingAnalyzerConfig(
    min_rt_per_char_ms=20.0,            # minimum ms per character
    max_rt_cv_threshold=0.1,            # CV threshold for consistent timing
    instant_response_threshold_ms=2000.0,
    instant_response_min_chars=100,
)
timing_analyzer = TimingAnalyzer(timing_config)
```

### Processing Results

```python
result = pipeline.analyze(sessions)

# access per-session verdicts
for session_id, verdict in result.verdicts.items():
    print(f"Session: {session_id}")
    print(f"  Status: {verdict.status}")
    print(f"  Confidence: {verdict.confidence:.2f}")
    print(f"  Summary: {verdict.summary}")

# access aggregated flags per session
for session_id, flags in result.aggregated_flags.items():
    for flag in flags:
        print(f"{session_id}: {flag.type} ({flag.severity})")

# access raw analyzer results
for analyzer_name, results in result.analyzer_results.items():
    for analysis_result in results:
        print(f"{analyzer_name}: {len(analysis_result.flags)} flags")
```

### Generating Reports

```python
from slopit.pipeline import TextReporter, CSVExporter

# text report
reporter = TextReporter()
report_text = reporter.generate(result)
print(report_text)

# summary table (using Rich)
reporter.print_summary(result)

# CSV export
exporter = CSVExporter()
exporter.export(result, "results.csv")

# export individual flags
exporter.export_flags(result, "flags.csv")
```

## Dashboard Server

The dashboard provides a web interface for real-time analysis and monitoring.

### Starting the Server

**CLI (recommended):**

```bash
# default settings (localhost:8000)
slopit dashboard

# custom host and port
slopit dashboard --host 0.0.0.0 --port 8080

# development mode with auto-reload
slopit dashboard --reload

# custom data directory
slopit dashboard --data-dir ./sessions
```

**Python API:**

```python
from slopit.dashboard import DashboardConfig
from slopit.dashboard.app import create_app
import uvicorn

config = DashboardConfig(
    host="127.0.0.1",
    port=8000,
    data_dir="./data",
    jatos_url="https://jatos.example.com",
    jatos_token="your-api-token",
    prolific_token="your-prolific-token",
)

app = create_app(config)
uvicorn.run(app, host=config.host, port=config.port)
```

### Dashboard Features

The dashboard provides:

- **Session Management**: Upload, browse, and inspect session data
- **Real-time Analysis**: Automatic background processing with live updates
- **JATOS Sync**: Import data directly from JATOS experiment servers
- **Prolific Integration**: Approve, reject, or return submissions based on analysis
- **Export**: Download sessions, trials, and verdicts as CSV

### REST API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/sessions/` | List sessions with pagination |
| GET | `/api/v1/sessions/{id}` | Get session details |
| GET | `/api/v1/trials/` | List trials with pagination |
| GET | `/api/v1/trials/{session_id}/{index}` | Get trial details |
| GET | `/api/v1/analysis/summary` | Get analysis statistics |
| GET | `/api/v1/analysis/verdicts` | List verdicts with pagination |
| POST | `/api/v1/analysis/batch` | Start batch analysis |
| GET | `/api/v1/export/sessions/csv` | Export sessions as CSV |
| GET | `/api/v1/export/verdicts/csv` | Export verdicts as CSV |
| POST | `/api/v1/jatos/sync` | Sync from JATOS study |
| POST | `/api/v1/prolific/submissions/batch-transition` | Batch approve/reject |

### WebSocket Events

Connect to `/ws` for real-time updates:

```python
import asyncio
import json
import websockets

async def listen_for_updates():
    async with websockets.connect("ws://localhost:8000/ws") as ws:
        async for message in ws:
            event = json.loads(message)
            if event["type"] == "session.new":
                print(f"New session: {event['data']['session_id']}")
            elif event["type"] == "verdict.computed":
                print(f"Verdict ready: {event['data']['session_id']}")
                print(f"  Status: {event['data']['status']}")
            elif event["type"] == "sync.progress":
                print(f"Sync: {event['data']['progress']}/{event['data']['total']}")

asyncio.run(listen_for_updates())
```

### Services

**StorageService** provides file-based persistence:

```python
from pathlib import Path
from slopit.dashboard.services import StorageService

storage = StorageService(Path("./data"))

# save and retrieve sessions
storage.save_session(session)
retrieved = storage.get_session(session.session_id)

# list with pagination
sessions, total = storage.list_sessions(page=1, page_size=20, has_verdict=True)

# save and retrieve verdicts
storage.save_verdict("session-123", {"status": "flagged", "confidence": 0.85})
verdict = storage.get_verdict("session-123")
```

**AnalysisService** provides background processing:

```python
from slopit.dashboard.services import AnalysisService

service = AnalysisService()

# register callback for completed analysis
def on_verdict(session_id: str, verdict: dict) -> None:
    storage.save_verdict(session_id, verdict)

service.on_complete(on_verdict)

# start worker and enqueue sessions
await service.start()
await service.enqueue_session(session)

# or analyze synchronously
verdict = await service.analyze_session(session)
```

## Prolific Integration

Manage participant submissions based on analysis results:

```python
from slopit.dashboard.integrations import ProlificClient, ParticipantAction

async with ProlificClient("your-api-token") as client:
    # list studies
    studies = await client.list_studies()

    # get submissions awaiting review
    from slopit.dashboard.integrations import SubmissionStatus
    submissions = await client.get_submissions(
        "study-123",
        status=SubmissionStatus.AWAITING_REVIEW,
    )

    # approve a submission
    await client.approve_submission("submission-456")

    # reject with category
    await client.reject_submission(
        "submission-789",
        rejection_category="NO_DATA",
        message="Data validation failed",
    )

    # return submission to pool
    await client.return_submission("submission-012")

    # batch operations
    await client.batch_approve("study-123", ["sub-1", "sub-2", "sub-3"])
```

## Schemas

### Session Data

```python
from slopit.schemas import SlopitSession, SlopitTrial

# validate session data
session = SlopitSession.model_validate(raw_dict)

# access session properties
print(f"Session ID: {session.session_id}")
print(f"Participant: {session.participant_id}")
print(f"Platform: {session.platform.name}")
print(f"Trials: {len(session.trials)}")

# iterate trials
for trial in session.trials:
    print(f"Trial {trial.trial_index}: {trial.trial_type}")
    if trial.behavioral:
        keystrokes = trial.behavioral.keystrokes or []
        print(f"  Keystrokes: {len(keystrokes)}")
```

### Behavioral Data

```python
from slopit.schemas import (
    BehavioralData,
    KeystrokeEvent,
    FocusEvent,
    PasteEvent,
)

# access behavioral data from a trial
behavioral: BehavioralData = trial.behavioral

# keystroke events
for event in behavioral.keystrokes or []:
    print(f"{event.time}ms: {event.key} ({event.event})")

# focus events
for event in behavioral.focus or []:
    print(f"{event.time}ms: {event.event}")

# paste events
for event in behavioral.paste or []:
    print(f"{event.time}ms: pasted {event.text_length} chars")
```

### Analysis Results

```python
from slopit.schemas.analysis import (
    AnalysisResult,
    PipelineResult,
    SessionVerdict,
)
from slopit.schemas.flags import AnalysisFlag, Severity

# verdicts are "clean", "suspicious", or "flagged"
verdict: SessionVerdict = result.verdicts["session-123"]
print(f"Status: {verdict.status}")

# flags have type, analyzer, severity, message, and confidence
for flag in verdict.flags:
    flag_info: AnalysisFlag = flag
    print(f"{flag_info.analyzer}: {flag_info.type}")
    print(f"  Severity: {flag_info.severity}")
    print(f"  Confidence: {flag_info.confidence}")
    print(f"  Message: {flag_info.message}")
```

## Examples

### Batch Processing

```python
from pathlib import Path
from slopit import load_sessions
from slopit.pipeline import AnalysisPipeline, CSVExporter
from slopit.behavioral import (
    KeystrokeAnalyzer,
    FocusAnalyzer,
    PasteAnalyzer,
    TimingAnalyzer,
)

def process_study(data_dir: Path, output_dir: Path) -> None:
    """Process all sessions in a study directory."""
    sessions = load_sessions(data_dir)
    print(f"Loaded {len(sessions)} sessions")

    pipeline = AnalysisPipeline([
        KeystrokeAnalyzer(),
        FocusAnalyzer(),
        PasteAnalyzer(),
        TimingAnalyzer(),
    ])

    result = pipeline.analyze(sessions)

    # count by status
    counts = {"clean": 0, "suspicious": 0, "flagged": 0}
    for verdict in result.verdicts.values():
        counts[verdict.status] += 1

    print(f"Results: {counts}")

    # export to CSV
    exporter = CSVExporter()
    exporter.export(result, output_dir / "verdicts.csv")
    exporter.export_flags(result, output_dir / "flags.csv")

# usage
process_study(Path("data/study1"), Path("output"))
```

### Custom Aggregation

```python
from slopit.pipeline import AnalysisPipeline, PipelineConfig

# flag if ANY analyzer detects an issue (most sensitive)
config_any = PipelineConfig(aggregation="any")

# flag if MAJORITY of analyzers detect issues
config_majority = PipelineConfig(aggregation="majority")

# use confidence-weighted voting (recommended)
config_weighted = PipelineConfig(
    aggregation="weighted",
    confidence_threshold=0.6,  # require 60% confidence
    severity_threshold="medium",  # ignore "info" and "low" flags
)
```

### Real-time Analysis with Dashboard

```python
from pathlib import Path
from slopit.dashboard import DashboardConfig
from slopit.dashboard.app import create_app
from slopit.dashboard.services import AnalysisService, StorageService

# create services
storage = StorageService(Path("./data"))
analysis = AnalysisService()

# register callback for completed analysis
def on_verdict(session_id: str, verdict: dict) -> None:
    print(f"Analysis complete for {session_id}: {verdict['status']}")
    storage.save_verdict(session_id, verdict)

analysis.on_complete(on_verdict)

# start the service
import asyncio
asyncio.run(analysis.start())
```

## API Reference

For complete API documentation, see:

- [Schemas](docs/api/schemas.md): Data models
- [IO Loaders](docs/api/io.md): Data loading
- [Analyzers](docs/api/analyzers.md): Behavioral analyzers
- [Pipeline](docs/api/pipeline.md): Analysis orchestration

## License

MIT
