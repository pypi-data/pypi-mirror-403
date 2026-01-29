# Integrations Guide

This guide covers integrating slopit with external services including JATOS and Prolific.

## JATOS Integration

JATOS (Just Another Tool for Online Studies) is a popular server for running online experiments. slopit provides two methods for working with JATOS data:

1. **File-based loading**: Load exported result files
2. **API-based streaming**: Connect directly to a JATOS server

### Loading JATOS Export Files

JATOS exports study results as text files containing JSON data. These can be in two formats:

- JSON array format: `[{trial1}, {trial2}, ...]`
- Newline-delimited JSON: one JSON object per line

The `JATOSLoader` handles both formats automatically.

```python
from pathlib import Path
from slopit.io import JATOSLoader

loader = JATOSLoader()

# load a single result file
session = loader.load(Path("study_result_123.txt"))
print(f"Session ID: {session.session_id}")
print(f"Trials: {len(session.trials)}")

# load all results from a directory
for session in loader.load_many(Path("jatos_results/")):
    print(f"Loaded: {session.session_id}")
```

### Format Detection

The loader checks for JATOS-specific markers in the file content:

```python
from pathlib import Path
from slopit.io import JATOSLoader

# check if a path is JATOS format
if JATOSLoader.can_load(Path("data/")):
    loader = JATOSLoader()
    sessions = list(loader.load_many(Path("data/")))
```

### Converting Raw Trial Data

When receiving data from the JATOS API directly, use `load_result()` to convert raw trial arrays:

```python
from slopit.io import JATOSLoader

loader = JATOSLoader()

# raw trial data from JATOS
trials = [
    {
        "trial_type": "survey-text",
        "rt": 15000,
        "response": "This is my answer...",
        "time_elapsed": 45000,
        "slopit": {
            "behavioral": {
                "keystrokes": [...],
                "focus": [...],
            }
        }
    },
    # more trials...
]

session = loader.load_result(trials, result_id="jatos-result-456")
```

### JATOS API Client

For direct integration with a JATOS server, use the `JATOSClient`:

```python
from slopit.dashboard.integrations import JATOSClient

async def sync_from_jatos():
    async with JATOSClient("https://jatos.example.com", "api-token") as client:
        # list all accessible studies
        studies = await client.list_studies()
        for study in studies:
            print(f"Study: {study['title']} (ID: {study['id']})")

        # get metadata for a specific study
        study = await client.get_study("study-123")
        print(f"Description: {study.get('description')}")

        # get all results for a study
        results = await client.get_study_results("study-123")
        print(f"Total results: {len(results)}")

        # stream results as SlopitSession objects
        async for session in client.stream_results("study-123"):
            print(f"Session: {session.session_id}")
            print(f"  Trials: {len(session.trials)}")

        # or collect all sessions at once
        sessions = await client.get_sessions("study-123")
        print(f"Loaded {len(sessions)} sessions")
```

### JATOS API Authentication

The JATOS API uses token-based authentication. Generate a token in the JATOS admin interface:

1. Log in to JATOS as admin
2. Go to Admin > API Tokens
3. Generate a new token with appropriate permissions

Store the token securely (e.g., environment variables):

```python
import os
from slopit.dashboard.integrations import JATOSClient

jatos_url = os.environ["JATOS_URL"]
jatos_token = os.environ["JATOS_TOKEN"]

async with JATOSClient(jatos_url, jatos_token) as client:
    sessions = await client.get_sessions("study-123")
```

### Error Handling

The client raises `httpx.HTTPStatusError` for API errors:

```python
import httpx
from slopit.dashboard.integrations import JATOSClient

async def safe_sync():
    async with JATOSClient(url, token) as client:
        try:
            sessions = await client.get_sessions("study-123")
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                print("Authentication failed; check your API token")
            elif e.response.status_code == 404:
                print("Study not found")
            else:
                print(f"API error: {e.response.status_code}")
```

---

## Prolific Integration

Prolific is a participant recruitment platform. slopit provides a client for managing submissions based on analysis results.

### Setting Up the Client

```python
import os
from slopit.dashboard.integrations import ProlificClient

# use environment variable for token
token = os.environ["PROLIFIC_TOKEN"]

async with ProlificClient(token) as client:
    studies = await client.list_studies()
```

### Listing Studies and Submissions

```python
from slopit.dashboard.integrations import ProlificClient, SubmissionStatus

async with ProlificClient(token) as client:
    # list all studies
    studies = await client.list_studies()
    for study in studies:
        print(f"{study['name']}: {study['status']}")

    # get submissions for a study
    submissions = await client.get_submissions("study-id-123")
    for sub in submissions:
        print(f"  {sub['participant_id']}: {sub['status']}")

    # filter by status
    pending = await client.get_submissions(
        "study-id-123",
        status=SubmissionStatus.AWAITING_REVIEW,
    )
    print(f"Awaiting review: {len(pending)}")
```

### Submission Statuses

```python
from slopit.dashboard.integrations import SubmissionStatus

# available statuses
SubmissionStatus.ACTIVE           # participant is working
SubmissionStatus.AWAITING_REVIEW  # complete, needs review
SubmissionStatus.APPROVED         # approved and paid
SubmissionStatus.REJECTED         # rejected
SubmissionStatus.RETURNED         # returned to pool
SubmissionStatus.TIMED_OUT        # participant timed out
```

### Approving Submissions

```python
from slopit.dashboard.integrations import ProlificClient

async with ProlificClient(token) as client:
    # approve a single submission
    result = await client.approve_submission("submission-id")

    # approve with a thank you message
    result = await client.approve_submission(
        "submission-id",
        message="Thank you for your participation!",
    )
```

### Rejecting Submissions

Rejections require a category and should be used sparingly:

```python
from slopit.dashboard.integrations import ProlificClient

async with ProlificClient(token) as client:
    # reject with required category
    result = await client.reject_submission(
        "submission-id",
        rejection_category="NO_DATA",
        message="We were unable to record your responses.",
    )
```

Common rejection categories:

- `NO_DATA`: No data was submitted
- `BAD_CODE`: Invalid completion code
- `FAILED_ATTENTION`: Failed attention checks
- `INCOMP_LONGITUDINAL`: Incomplete longitudinal study
- `TOO_QUICKLY`: Completed too quickly
- `TOO_SLOWLY`: Completed too slowly
- `OTHER`: Other reason (requires message)

### Returning Submissions

Returns release the slot without penalty to the participant:

```python
from slopit.dashboard.integrations import ProlificClient

async with ProlificClient(token) as client:
    # return a submission
    result = await client.return_submission(
        "submission-id",
        message="Thank you, but we need to re-run this study.",
    )
```

### Batch Operations

For efficiency, use batch operations when processing multiple submissions:

```python
from slopit.dashboard.integrations import ProlificClient

async with ProlificClient(token) as client:
    # batch approve
    result = await client.batch_approve(
        "study-id",
        ["sub-1", "sub-2", "sub-3"],
    )
    print(f"Approved: {result}")

    # batch reject
    result = await client.batch_reject(
        "study-id",
        ["sub-4", "sub-5"],
        rejection_category="NO_DATA",
    )

    # batch return
    result = await client.batch_return(
        "study-id",
        ["sub-6", "sub-7"],
    )
```

### Automated Review Workflow

Combine slopit analysis with Prolific submission management:

```python
from slopit import load_sessions
from slopit.pipeline import AnalysisPipeline
from slopit.behavioral import KeystrokeAnalyzer, FocusAnalyzer
from slopit.dashboard.integrations import ProlificClient, SubmissionStatus

async def review_submissions(study_id: str, data_dir: str) -> None:
    """Review Prolific submissions using slopit analysis."""
    # load and analyze sessions
    sessions = load_sessions(data_dir)
    pipeline = AnalysisPipeline([KeystrokeAnalyzer(), FocusAnalyzer()])
    result = pipeline.analyze(sessions)

    # map participant IDs to verdicts
    participant_verdicts: dict[str, str] = {}
    for session in sessions:
        if session.participant_id:
            verdict = result.verdicts.get(session.session_id)
            if verdict:
                participant_verdicts[session.participant_id] = verdict.status

    # process Prolific submissions
    async with ProlificClient(token) as client:
        submissions = await client.get_submissions(
            study_id,
            status=SubmissionStatus.AWAITING_REVIEW,
        )

        approve_ids: list[str] = []
        review_ids: list[str] = []

        for sub in submissions:
            participant_id = sub["participant_id"]
            submission_id = sub["id"]

            verdict = participant_verdicts.get(participant_id)

            if verdict == "clean":
                approve_ids.append(submission_id)
            elif verdict in ("suspicious", "flagged"):
                review_ids.append(submission_id)
            # else: no data, skip

        # batch approve clean submissions
        if approve_ids:
            await client.batch_approve(study_id, approve_ids)
            print(f"Approved {len(approve_ids)} submissions")

        # flag submissions for manual review
        print(f"Flagged for review: {len(review_ids)} submissions")
        for sub_id in review_ids:
            print(f"  - {sub_id}")
```

---

## Dashboard WebSocket Events

The dashboard uses WebSockets for real-time updates. Clients can connect and receive events as sessions are processed.

### Event Types

```python
from slopit.dashboard.websocket import (
    SessionNewEvent,
    VerdictComputedEvent,
    SyncProgressEvent,
)

# new session received
SessionNewEvent(
    type="session.new",
    data={
        "session_id": "abc123",
        "timestamp": 1706000000000,
        "trial_count": 5,
    }
)

# analysis complete
VerdictComputedEvent(
    type="verdict.computed",
    data={
        "session_id": "abc123",
        "status": "flagged",
        "confidence": 0.85,
        "flags": ["low_iki_variance", "blur_paste_pattern"],
    }
)

# sync progress (JATOS/Prolific)
SyncProgressEvent(
    type="sync.progress",
    data={
        "source": "jatos",
        "study_id": "study-123",
        "progress": 50,
        "total": 100,
        "status": "syncing",
    }
)
```

### JavaScript Client Example

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  console.log('Connected to slopit dashboard');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch (data.type) {
    case 'session.new':
      console.log(`New session: ${data.data.session_id}`);
      refreshSessionList();
      break;

    case 'verdict.computed':
      console.log(`Verdict for ${data.data.session_id}: ${data.data.status}`);
      updateSessionStatus(data.data.session_id, data.data.status);
      break;

    case 'sync.progress':
      console.log(`Sync: ${data.data.progress}/${data.data.total}`);
      updateProgressBar(data.data.progress, data.data.total);
      break;
  }
};

ws.onclose = () => {
  console.log('Disconnected from dashboard');
};
```

### Python Client Example

```python
import asyncio
import json
import websockets

async def listen_for_events():
    """Listen for real-time dashboard events."""
    uri = "ws://localhost:8000/ws"

    async with websockets.connect(uri) as websocket:
        print("Connected to dashboard")

        async for message in websocket:
            event = json.loads(message)

            if event["type"] == "session.new":
                session_id = event["data"]["session_id"]
                print(f"New session received: {session_id}")

            elif event["type"] == "verdict.computed":
                session_id = event["data"]["session_id"]
                status = event["data"]["status"]
                print(f"Verdict for {session_id}: {status}")

            elif event["type"] == "sync.progress":
                progress = event["data"]["progress"]
                total = event["data"]["total"]
                print(f"Sync progress: {progress}/{total}")


if __name__ == "__main__":
    asyncio.run(listen_for_events())
```

### Broadcasting Events

The `ConnectionManager` handles event broadcasting:

```python
from slopit.dashboard.websocket import (
    ConnectionManager,
    SessionNewEvent,
    VerdictComputedEvent,
)

manager = ConnectionManager()

# broadcast to all connected clients
await manager.broadcast(
    SessionNewEvent(data={"session_id": "abc123"})
)

# send to specific client
await manager.send_personal(
    websocket,
    VerdictComputedEvent(data={"session_id": "abc123", "status": "clean"})
)
```

---

## Export Formats

### CSV Export

Export analysis results to CSV for use in spreadsheets or statistical software:

```python
from slopit.pipeline import CSVExporter

exporter = CSVExporter()

# export session verdicts
exporter.export(result, "verdicts.csv")
# columns: session_id, status, confidence, flag_count, summary, flag_*

# export individual flags
exporter.export_flags(result, "flags.csv")
# columns: session_id, analyzer, type, severity, message, confidence, trial_ids
```

**verdicts.csv format:**

| session_id | status | confidence | flag_count | summary | flag_low_iki_variance | flag_excessive_blur |
|------------|--------|------------|------------|---------|----------------------|---------------------|
| abc123 | flagged | 0.85 | 2 | Detected: low_iki_variance, excessive_blur | True | True |
| def456 | clean | 1.0 | 0 | No flags detected | | |

**flags.csv format:**

| session_id | analyzer | type | severity | message | confidence | trial_ids |
|------------|----------|------|----------|---------|------------|-----------|
| abc123 | keystroke | low_iki_variance | medium | Keystroke timing unusually consistent | 0.8 | trial-1 |
| abc123 | focus | excessive_blur | medium | Excessive window switches | 0.7 | trial-1,trial-2 |

### JSON Export

Export full results to JSON:

```python
import json
from pathlib import Path
from slopit.pipeline import AnalysisPipeline

result = pipeline.analyze(sessions)

# convert to dict
data = result.to_dict()

# write to file
Path("results.json").write_text(json.dumps(data, indent=2, default=str))
```

### Loading Previous Results

Load results from a previous analysis:

```python
import json
from pathlib import Path
from slopit.schemas.analysis import PipelineResult

# load from JSON
data = json.loads(Path("results.json").read_text())
result = PipelineResult.model_validate(data)

# access verdicts
for session_id, verdict in result.verdicts.items():
    print(f"{session_id}: {verdict.status}")
```

---

## Dashboard API

The dashboard exposes REST endpoints for programmatic access.

### Sessions API

```bash
# list sessions
curl http://localhost:8000/api/v1/sessions

# list with pagination and filters
curl "http://localhost:8000/api/v1/sessions?page=1&page_size=20&has_verdict=true"

# get single session
curl http://localhost:8000/api/v1/sessions/abc123

# upload session
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d @session.json
```

### Trials API

```bash
# list trials for a session
curl http://localhost:8000/api/v1/trials/abc123
```

### Analysis API

```bash
# run analysis on sessions
curl -X POST http://localhost:8000/api/v1/analysis/run \
  -H "Content-Type: application/json" \
  -d '{"session_ids": ["abc123", "def456"]}'

# get verdict for a session
curl http://localhost:8000/api/v1/analysis/verdict/abc123
```

### Export API

```bash
# export to CSV
curl http://localhost:8000/api/v1/export/csv -o results.csv

# export with filters
curl "http://localhost:8000/api/v1/export/csv?status=flagged" -o flagged.csv
```

---

## Complete Integration Example

```python
"""Complete workflow: JATOS sync, analysis, Prolific management."""

import asyncio
import os
from pathlib import Path

from slopit.pipeline import AnalysisPipeline, CSVExporter
from slopit.behavioral import (
    KeystrokeAnalyzer,
    FocusAnalyzer,
    PasteAnalyzer,
    TimingAnalyzer,
)
from slopit.dashboard.integrations import (
    JATOSClient,
    ProlificClient,
    SubmissionStatus,
)
from slopit.dashboard.services import StorageService


async def main() -> None:
    # configuration from environment
    jatos_url = os.environ["JATOS_URL"]
    jatos_token = os.environ["JATOS_TOKEN"]
    prolific_token = os.environ["PROLIFIC_TOKEN"]
    study_id = os.environ["STUDY_ID"]
    prolific_study_id = os.environ["PROLIFIC_STUDY_ID"]

    # storage
    storage = StorageService(Path("./data"))

    # step 1: sync data from JATOS
    print("Syncing from JATOS...")
    async with JATOSClient(jatos_url, jatos_token) as jatos:
        async for session in jatos.stream_results(study_id):
            storage.save_session(session)
            print(f"  Saved: {session.session_id}")

    # step 2: run analysis
    print("\nRunning analysis...")
    sessions = list(storage.iter_sessions())
    print(f"Analyzing {len(sessions)} sessions")

    pipeline = AnalysisPipeline([
        KeystrokeAnalyzer(),
        FocusAnalyzer(),
        PasteAnalyzer(),
        TimingAnalyzer(),
    ])

    result = pipeline.analyze(sessions)

    # save verdicts
    for session_id, verdict in result.verdicts.items():
        storage.save_verdict(session_id, {
            "status": verdict.status,
            "confidence": verdict.confidence,
            "flags": [f.type for f in verdict.flags],
            "summary": verdict.summary,
        })

    # export results
    exporter = CSVExporter()
    exporter.export(result, "verdicts.csv")
    exporter.export_flags(result, "flags.csv")

    # step 3: manage Prolific submissions
    print("\nProcessing Prolific submissions...")

    # map participant IDs to verdicts
    participant_verdicts: dict[str, str] = {}
    for session in sessions:
        if session.participant_id:
            verdict = result.verdicts.get(session.session_id)
            if verdict:
                participant_verdicts[session.participant_id] = verdict.status

    async with ProlificClient(prolific_token) as prolific:
        submissions = await prolific.get_submissions(
            prolific_study_id,
            status=SubmissionStatus.AWAITING_REVIEW,
        )

        approve_ids: list[str] = []
        flag_ids: list[str] = []

        for sub in submissions:
            participant_id = sub["participant_id"]
            submission_id = sub["id"]

            verdict = participant_verdicts.get(participant_id)

            if verdict == "clean":
                approve_ids.append(submission_id)
            elif verdict in ("suspicious", "flagged"):
                flag_ids.append(submission_id)

        # auto-approve clean submissions
        if approve_ids:
            await prolific.batch_approve(prolific_study_id, approve_ids)
            print(f"  Approved: {len(approve_ids)}")

        # report flagged for manual review
        if flag_ids:
            print(f"  Flagged for review: {len(flag_ids)}")

    # summary
    print("\nSummary:")
    counts = {"clean": 0, "suspicious": 0, "flagged": 0}
    for verdict in result.verdicts.values():
        counts[verdict.status] += 1
    print(f"  Clean: {counts['clean']}")
    print(f"  Suspicious: {counts['suspicious']}")
    print(f"  Flagged: {counts['flagged']}")


if __name__ == "__main__":
    asyncio.run(main())
```
