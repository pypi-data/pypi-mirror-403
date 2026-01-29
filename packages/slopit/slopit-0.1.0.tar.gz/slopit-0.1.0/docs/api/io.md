# IO Loaders

The `slopit.io` module provides loaders for various data formats. Loaders convert platform-specific formats into the standardized `SlopitSession` schema.

## High-Level Functions

### load_session

Load a single session from a file with automatic format detection.

::: slopit.io.load_session
    options:
      show_source: false

#### Example

```python
from slopit import load_session

# Load native slopit format
session = load_session("data/participant_001.json")

# Load JATOS format
session = load_session("jatos_results/study_result_123.txt")
```

### load_sessions

Load multiple sessions from a directory.

::: slopit.io.load_sessions
    options:
      show_source: false

#### Example

```python
from slopit import load_sessions

# Load all sessions from a directory
sessions = load_sessions("data/")
print(f"Loaded {len(sessions)} sessions")

# Filter by pattern
sessions = load_sessions("data/", pattern="*.json")
```

## Base Loader Class

### BaseLoader

Abstract base class that all format-specific loaders inherit from.

::: slopit.io.base.BaseLoader
    options:
      show_source: true
      members:
        - load
        - load_many
        - can_load

## Native Format Loader

### NativeLoader

Loader for native slopit JSON format. The native format is a JSON file that directly contains a `SlopitSession` object.

::: slopit.io.native.NativeLoader
    options:
      show_source: true

#### Native Format Structure

```json
{
  "schemaVersion": "1.0",
  "sessionId": "abc123",
  "participantId": "P001",
  "studyId": "study_001",
  "platform": {
    "name": "jspsych",
    "version": "7.3.0",
    "adapterVersion": "0.1.0"
  },
  "environment": {
    "userAgent": "Mozilla/5.0...",
    "screenResolution": [1920, 1080],
    "viewportSize": [1200, 800],
    "devicePixelRatio": 2.0,
    "timezone": "America/New_York",
    "language": "en-US",
    "touchCapable": false
  },
  "timing": {
    "startTime": 1705000000000,
    "endTime": 1705000600000,
    "duration": 600000
  },
  "trials": [
    {
      "trialId": "trial-0",
      "trialIndex": 0,
      "trialType": "survey-text",
      "startTime": 1705000000000,
      "endTime": 1705000060000,
      "rt": 60000,
      "stimulus": {...},
      "response": {...},
      "behavioral": {...}
    }
  ],
  "globalEvents": {
    "focus": [],
    "errors": []
  }
}
```

#### Example

```python
from slopit.io import NativeLoader
from pathlib import Path

loader = NativeLoader()

# Check if file is native format
if NativeLoader.can_load(Path("data/session.json")):
    session = loader.load(Path("data/session.json"))

# Load multiple files
for session in loader.load_many(Path("data/"), pattern="*.json"):
    print(f"Loaded {session.session_id}")
```

## JATOS Loader

### JATOSLoader

Loader for data exported from JATOS (Just Another Tool for Online Studies). JATOS exports data as JSON arrays or newline-delimited JSON.

::: slopit.io.jatos.JATOSLoader
    options:
      show_source: true

#### JATOS Format

JATOS exports come in two formats:

**Array format** (single JSON array):

```json
[
  {"trial_type": "html-keyboard-response", "rt": 1234, ...},
  {"trial_type": "survey-text", "response": "...", "slopit": {...}, ...}
]
```

**Newline-delimited format** (one trial per line):

```
{"trial_type": "html-keyboard-response", "rt": 1234, ...}
{"trial_type": "survey-text", "response": "...", "slopit": {...}, ...}
```

#### Extracted Fields

The JATOS loader extracts:

- **participant_id**: From `PROLIFIC_PID`, `workerId`, `participant_id`, or `subject`
- **study_id**: From `STUDY_ID`, `study_id`, or `experiment_id`
- **environment**: From standard jsPsych fields (`user_agent`, `screen_width`, etc.)
- **behavioral data**: From the `slopit` field added by slopit adapters

#### Example

```python
from slopit.io import JATOSLoader
from pathlib import Path

loader = JATOSLoader()

# Load JATOS result file
session = loader.load(Path("jatos_results/study_result_123.txt"))
print(f"Loaded {len(session.trials)} trials")

# Load all results from a directory
for session in loader.load_many(Path("jatos_results/")):
    print(f"Session: {session.session_id}")
    print(f"  Participant: {session.participant_id}")
    print(f"  Trials: {len(session.trials)}")
```

## Writing Custom Loaders

To support a new data format, subclass `BaseLoader`:

```python
from pathlib import Path
from collections.abc import Iterator
from slopit.io.base import BaseLoader
from slopit.schemas import SlopitSession

class MyCustomLoader(BaseLoader):
    """Loader for my custom format."""

    def load(self, path: Path) -> SlopitSession:
        """Load a single session."""
        # Parse your format
        raw_data = self._parse_file(path)

        # Convert to SlopitSession
        return SlopitSession(
            schema_version="1.0",
            session_id=raw_data["id"],
            # ... map other fields
        )

    def load_many(self, path: Path, pattern: str = "*") -> Iterator[SlopitSession]:
        """Load multiple sessions."""
        if path.is_file():
            yield self.load(path)
            return

        for file_path in sorted(path.glob(pattern)):
            if self._is_my_format(file_path):
                yield self.load(file_path)

    @classmethod
    def can_load(cls, path: Path) -> bool:
        """Check if this loader can handle the path."""
        if path.is_dir():
            return any(cls._is_my_format(f) for f in path.glob("*"))
        return cls._is_my_format(path)

    @classmethod
    def _is_my_format(cls, path: Path) -> bool:
        """Check if file is in my custom format."""
        # Implement format detection
        return path.suffix == ".myformat"

    def _parse_file(self, path: Path) -> dict:
        """Parse file contents."""
        # Implement parsing logic
        pass
```

### Registering Custom Loaders

Currently, custom loaders must be used directly:

```python
loader = MyCustomLoader()
session = loader.load(Path("data/file.myformat"))
```

Future versions will support registering loaders for automatic format detection.
