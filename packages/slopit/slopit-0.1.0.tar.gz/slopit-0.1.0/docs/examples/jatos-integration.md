# JATOS Integration Example

This example demonstrates processing data exported from JATOS (Just Another Tool for Online Studies).

## Scenario

You ran a jsPsych experiment on JATOS with the slopit adapter capturing behavioral data. You have downloaded the study results and want to analyze them for potential AI assistance.

## JATOS Data Structure

JATOS exports study results as `.txt` files containing JSON data. Each file represents one participant session and contains all trial data from jsPsych.

### File Location

When you export results from JATOS:

1. Go to your study in JATOS
2. Click "Results"
3. Select the component results you want
4. Export as "JSON Results"

Files are named like `study_result_123.txt` or `component_result_456.txt`.

### Data Format

JATOS exports can be in two formats:

**Array format** (all trials in one JSON array):

```json
[
  {
    "trial_type": "html-keyboard-response",
    "rt": 2345,
    "response": "j",
    "time_elapsed": 5678
  },
  {
    "trial_type": "survey-text",
    "rt": 45000,
    "response": "The participant's written response...",
    "slopit": {
      "behavioral": {
        "keystrokes": [...],
        "focus": [...],
        "paste": [...]
      },
      "flags": []
    },
    "time_elapsed": 50678
  }
]
```

**Newline-delimited format** (one trial per line):

```
{"trial_type": "html-keyboard-response", "rt": 2345, ...}
{"trial_type": "survey-text", "rt": 45000, "slopit": {...}, ...}
```

## Loading JATOS Data

slopit automatically detects JATOS format:

```python
from slopit import load_session, load_sessions

# Single file
session = load_session("jatos_results/study_result_123.txt")

# Directory of results
sessions = load_sessions("jatos_results/")
```

## Extracting Participant Information

The JATOS loader extracts participant and study IDs from common fields:

```python
session = load_session("jatos_results/study_result_123.txt")

# These are extracted from trial data if present
print(f"Participant: {session.participant_id}")  # From PROLIFIC_PID, workerId, etc.
print(f"Study: {session.study_id}")              # From STUDY_ID, study_id, etc.
```

If you use Prolific, the participant ID is extracted from `PROLIFIC_PID`. For MTurk, it uses `workerId`.

## Complete Workflow

### Step 1: Download Results from JATOS

Export your study results from the JATOS web interface and save them to a directory.

### Step 2: Load and Validate

```python
from pathlib import Path
from slopit import load_session

results_dir = Path("jatos_results/")

# List available result files
result_files = list(results_dir.glob("*.txt"))
print(f"Found {len(result_files)} result files")

# Load and validate each
sessions = []
errors = []

for path in result_files:
    try:
        session = load_session(path)
        sessions.append(session)
        print(f"Loaded {path.name}: {len(session.trials)} trials")
    except Exception as e:
        errors.append((path, str(e)))
        print(f"Error loading {path.name}: {e}")

print(f"\nLoaded {len(sessions)} sessions, {len(errors)} errors")
```

### Step 3: Filter Relevant Trials

JATOS exports include all trials, but you may only want to analyze specific ones:

```python
# Find trials with behavioral data
for session in sessions:
    behavioral_trials = [
        t for t in session.trials
        if t.behavioral and t.behavioral.keystrokes
    ]
    print(f"{session.participant_id}: {len(behavioral_trials)} trials with behavioral data")
```

### Step 4: Run Analysis

```python
from slopit.pipeline import AnalysisPipeline
from slopit.behavioral import (
    KeystrokeAnalyzer,
    FocusAnalyzer,
    TimingAnalyzer,
    PasteAnalyzer,
)

pipeline = AnalysisPipeline([
    KeystrokeAnalyzer(),
    FocusAnalyzer(),
    TimingAnalyzer(),
    PasteAnalyzer(),
])

result = pipeline.analyze(sessions)

# Summary
flagged = sum(1 for v in result.verdicts.values() if v.status == "flagged")
print(f"\nFlagged: {flagged}/{len(sessions)} sessions")
```

### Step 5: Export Results

```python
from slopit.pipeline import CSVExporter

exporter = CSVExporter()

# Export for review
exporter.export(result, "jatos_analysis.csv")
exporter.export_flags(result, "jatos_flags.csv")
```

## Complete Script

```python
#!/usr/bin/env python
"""Analyze JATOS study results with slopit."""

from pathlib import Path
from slopit import load_session
from slopit.pipeline import AnalysisPipeline, PipelineConfig, CSVExporter
from slopit.behavioral import (
    KeystrokeAnalyzer,
    FocusAnalyzer,
    TimingAnalyzer,
    PasteAnalyzer,
)


def load_jatos_results(directory: str | Path) -> list:
    """Load all JATOS result files from a directory."""
    results_dir = Path(directory)
    sessions = []
    errors = []

    for path in sorted(results_dir.glob("*.txt")):
        try:
            session = load_session(path)
            sessions.append(session)
        except Exception as e:
            errors.append((path.name, str(e)))

    if errors:
        print(f"Warning: {len(errors)} files failed to load:")
        for filename, error in errors[:5]:
            print(f"  {filename}: {error}")
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more")

    return sessions


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python jatos_analysis.py <results_directory>")
        sys.exit(1)

    results_dir = sys.argv[1]

    # Load data
    print(f"Loading JATOS results from {results_dir}...")
    sessions = load_jatos_results(results_dir)
    print(f"Loaded {len(sessions)} sessions")

    if not sessions:
        print("No sessions to analyze.")
        sys.exit(1)

    # Show data summary
    print("\nData summary:")
    trials_with_behavioral = sum(
        sum(1 for t in s.trials if t.behavioral and t.behavioral.keystrokes)
        for s in sessions
    )
    print(f"  Total trials with behavioral data: {trials_with_behavioral}")

    # Configure and run analysis
    config = PipelineConfig(
        aggregation="weighted",
        severity_threshold="low",
        confidence_threshold=0.5,
    )

    pipeline = AnalysisPipeline(
        analyzers=[
            KeystrokeAnalyzer(),
            FocusAnalyzer(),
            TimingAnalyzer(),
            PasteAnalyzer(),
        ],
        config=config,
    )

    print("\nRunning analysis...")
    result = pipeline.analyze(sessions)

    # Print summary
    total = len(result.sessions)
    flagged = sum(1 for v in result.verdicts.values() if v.status == "flagged")
    suspicious = sum(1 for v in result.verdicts.values() if v.status == "suspicious")
    clean = total - flagged - suspicious

    print(f"\nResults:")
    print(f"  Flagged:    {flagged} ({flagged/total*100:.1f}%)")
    print(f"  Suspicious: {suspicious} ({suspicious/total*100:.1f}%)")
    print(f"  Clean:      {clean} ({clean/total*100:.1f}%)")

    # Export results
    exporter = CSVExporter()
    exporter.export(result, "jatos_analysis.csv")
    exporter.export_flags(result, "jatos_flags.csv")
    print("\nResults exported to jatos_analysis.csv and jatos_flags.csv")

    # List flagged participants
    if flagged > 0:
        print("\nFlagged participants:")
        for session_id, verdict in result.verdicts.items():
            if verdict.status == "flagged":
                # Find participant ID
                session = next(s for s in sessions if s.session_id == session_id)
                participant = session.participant_id or "unknown"
                print(f"  {participant}: {verdict.summary}")


if __name__ == "__main__":
    main()
```

## Command Line Usage

```bash
# Run the script
python jatos_analysis.py jatos_results/

# Or use the slopit CLI directly
slopit analyze jatos_results/ --summary
slopit analyze jatos_results/ --csv jatos_analysis.csv
```

## Matching Results to Prolific/MTurk

To match flagged sessions back to your recruitment platform:

```python
# Get participant IDs for flagged sessions
flagged_participants = []

for session_id, verdict in result.verdicts.items():
    if verdict.status == "flagged":
        session = next(s for s in sessions if s.session_id == session_id)
        if session.participant_id:
            flagged_participants.append(session.participant_id)

print("Flagged participant IDs:")
for pid in flagged_participants:
    print(f"  {pid}")

# Save to file for Prolific/MTurk
with open("flagged_participants.txt", "w") as f:
    for pid in flagged_participants:
        f.write(f"{pid}\n")
```

## Troubleshooting

### "Unable to determine file format"

The file may not be in standard JATOS format. Check:

1. Is the file valid JSON?
2. Does it contain jsPsych trial data with `trial_type` fields?

### No behavioral data found

Make sure your jsPsych experiment includes the slopit adapter. The behavioral data should be in a `slopit` field within each trial.

### Participant ID is None

The loader looks for common field names. If your experiment uses a different field name, you can extract it manually:

```python
for session in sessions:
    if session.participant_id is None:
        # Check first trial for custom field
        first_trial = session.trials[0] if session.trials else None
        if first_trial and first_trial.platform_data:
            custom_id = first_trial.platform_data.get("my_custom_pid_field")
            if custom_id:
                print(f"Found custom ID: {custom_id}")
```
