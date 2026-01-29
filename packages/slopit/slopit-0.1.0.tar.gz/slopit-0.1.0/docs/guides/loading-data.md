# Loading Data

This guide covers loading session data from various formats into slopit.

## Quick Start

The simplest way to load data:

```python
from slopit import load_session, load_sessions

# Single file
session = load_session("data/participant_001.json")

# Directory of files
sessions = load_sessions("data/")
```

slopit automatically detects the file format and uses the appropriate loader.

## Supported Formats

### Native slopit Format

The native format is a JSON file that directly matches the `SlopitSession` schema. Files are detected by the presence of `schemaVersion` and `sessionId` fields.

```python
from slopit import load_session

session = load_session("data/session.json")
```

Expected file structure:

```json
{
  "schemaVersion": "1.0",
  "sessionId": "abc123",
  "participantId": "P001",
  "platform": {"name": "jspsych", "version": "7.3.0"},
  "environment": {...},
  "timing": {...},
  "trials": [...],
  "globalEvents": {...}
}
```

### JATOS Format

slopit can load data exported from JATOS (Just Another Tool for Online Studies). JATOS exports are detected by the presence of `trial_type` or "jsPsych" in the file content.

```python
from slopit import load_session

# JATOS result file
session = load_session("jatos_results/study_result_123.txt")
```

JATOS exports can be:

- JSON array: `[{trial1}, {trial2}, ...]`
- Newline-delimited JSON: One trial object per line

The JATOS loader extracts participant and study IDs from common fields:

| Field | Source |
|-------|--------|
| participant_id | `PROLIFIC_PID`, `workerId`, `participant_id`, `subject` |
| study_id | `STUDY_ID`, `study_id`, `experiment_id` |

Behavioral data is extracted from the `slopit` field added by slopit adapters.

## Loading Multiple Sessions

### From a Directory

```python
from slopit import load_sessions

# Load all files
sessions = load_sessions("data/")

# Filter by pattern
sessions = load_sessions("data/", pattern="participant_*.json")
```

### From Multiple Directories

```python
from slopit import load_sessions

all_sessions = []
for directory in ["data/batch1/", "data/batch2/", "data/batch3/"]:
    sessions = load_sessions(directory)
    all_sessions.extend(sessions)

print(f"Loaded {len(all_sessions)} sessions total")
```

### Handling Errors

By default, `load_sessions` skips files that fail to parse. To handle errors explicitly:

```python
from pathlib import Path
from slopit import load_session

sessions = []
errors = []

for path in Path("data/").glob("*.json"):
    try:
        session = load_session(path)
        sessions.append(session)
    except ValueError as e:
        errors.append((path, str(e)))
    except FileNotFoundError as e:
        errors.append((path, str(e)))

print(f"Loaded {len(sessions)} sessions")
print(f"Errors: {len(errors)}")
```

## Using Specific Loaders

For more control, use loaders directly:

```python
from pathlib import Path
from slopit.io import NativeLoader, JATOSLoader

# Native format
native_loader = NativeLoader()
session = native_loader.load(Path("data/session.json"))

# JATOS format
jatos_loader = JATOSLoader()
session = jatos_loader.load(Path("jatos_results/result.txt"))
```

### Checking Format Support

```python
from pathlib import Path
from slopit.io import NativeLoader, JATOSLoader

path = Path("data/unknown.json")

if NativeLoader.can_load(path):
    loader = NativeLoader()
elif JATOSLoader.can_load(path):
    loader = JATOSLoader()
else:
    raise ValueError(f"Unknown format: {path}")

session = loader.load(path)
```

## Working with Session Data

### Accessing Session Metadata

```python
session = load_session("data/session.json")

print(f"Session ID: {session.session_id}")
print(f"Participant: {session.participant_id}")
print(f"Study: {session.study_id}")
print(f"Platform: {session.platform.name} {session.platform.version}")
print(f"Duration: {session.timing.duration / 1000:.1f} seconds")
```

### Accessing Environment Info

```python
env = session.environment

print(f"User Agent: {env.user_agent}")
print(f"Screen: {env.screen_resolution[0]}x{env.screen_resolution[1]}")
print(f"Viewport: {env.viewport_size[0]}x{env.viewport_size[1]}")
print(f"Timezone: {env.timezone}")
print(f"Language: {env.language}")
print(f"Touch: {env.touch_capable}")
```

### Iterating Over Trials

```python
for trial in session.trials:
    print(f"\nTrial {trial.trial_index}: {trial.trial_type}")

    # Response
    if trial.response:
        print(f"  Response type: {trial.response.type}")
        if trial.response.character_count:
            print(f"  Characters: {trial.response.character_count}")

    # Timing
    print(f"  RT: {trial.rt}ms" if trial.rt else "  RT: N/A")

    # Behavioral data
    if trial.behavioral:
        ks = len(trial.behavioral.keystrokes)
        focus = len(trial.behavioral.focus)
        paste = len(trial.behavioral.paste)
        print(f"  Events: {ks} keystrokes, {focus} focus, {paste} paste")
```

### Accessing Behavioral Data

```python
for trial in session.trials:
    if trial.behavioral is None:
        continue

    # Keystroke analysis
    keydowns = [k for k in trial.behavioral.keystrokes if k.event == "keydown"]
    print(f"Trial {trial.trial_index}: {len(keydowns)} keydowns")

    # Calculate IKI
    if len(keydowns) >= 2:
        times = [k.time for k in keydowns]
        ikis = [times[i+1] - times[i] for i in range(len(times)-1)]
        mean_iki = sum(ikis) / len(ikis)
        print(f"  Mean IKI: {mean_iki:.1f}ms")

    # Focus events
    blurs = [f for f in trial.behavioral.focus if f.event == "blur"]
    print(f"  Blur events: {len(blurs)}")

    # Paste events
    for paste in trial.behavioral.paste:
        print(f"  Paste at {paste.time}ms: {paste.text_length} chars")
```

## Data Validation

### Validating Raw Data

```python
from slopit.schemas import SlopitSession

raw_data = {
    "schemaVersion": "1.0",
    "sessionId": "test",
    # ... other fields
}

try:
    session = SlopitSession.model_validate(raw_data)
    print("Data is valid")
except Exception as e:
    print(f"Validation error: {e}")
```

### Using the CLI

Validate files from the command line:

```bash
# Validate single file
slopit validate data/session.json

# Validate directory
slopit validate data/
```

Output:

```
✓ data/session_001.json: 1 session(s) valid
✓ data/session_002.json: 1 session(s) valid
✗ data/session_003.json: Invalid schema version

Summary: 2 valid, 1 invalid
```

## Filtering Sessions

### By Participant

```python
sessions = load_sessions("data/")

# Filter to specific participants
participant_ids = {"P001", "P002", "P003"}
filtered = [s for s in sessions if s.participant_id in participant_ids]
```

### By Trial Count

```python
# Sessions with at least 5 trials
filtered = [s for s in sessions if len(s.trials) >= 5]
```

### By Behavioral Data Availability

```python
# Sessions with keystroke data
filtered = [
    s for s in sessions
    if any(t.behavioral and t.behavioral.keystrokes for t in s.trials)
]
```

### By Date Range

```python
from datetime import datetime

start = datetime(2024, 1, 1).timestamp() * 1000  # Unix ms
end = datetime(2024, 6, 30).timestamp() * 1000

filtered = [
    s for s in sessions
    if start <= s.timing.start_time <= end
]
```

## Performance Tips

### Memory Management

For large datasets, process sessions in batches:

```python
from pathlib import Path
from slopit import load_session
from slopit.pipeline import AnalysisPipeline

pipeline = AnalysisPipeline([...])

# Process files one at a time
for path in Path("data/").glob("*.json"):
    session = load_session(path)
    result = pipeline.analyze([session])
    # Process result...
    # Session is garbage collected after each iteration
```

### Parallel Loading

For I/O-bound loading, use concurrent processing:

```python
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from slopit import load_session

paths = list(Path("data/").glob("*.json"))

with ThreadPoolExecutor(max_workers=4) as executor:
    sessions = list(executor.map(load_session, paths))

print(f"Loaded {len(sessions)} sessions")
```

## Troubleshooting

### "Unable to determine file format"

The file does not match any known format. Check:

1. Is it valid JSON?
2. Does it have `schemaVersion` (native) or `trial_type` (JATOS)?
3. Is the file encoding UTF-8?

### "File not found"

Ensure the path is correct. Use absolute paths or paths relative to the current working directory.

### "Validation error"

The file structure does not match the schema. Use `model_validate` with `strict=False` for more lenient parsing, or check the file contents against the schema documentation.
