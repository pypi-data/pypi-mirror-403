# Quick Start

This guide walks through a basic slopit analysis workflow.

## Prerequisites

Make sure slopit is installed:

```bash
pip install slopit
```

## Step 1: Load Session Data

slopit reads session data from JSON files. Each file contains behavioral data captured during a participant session.

```python
from slopit import load_session, load_sessions

# Load a single session
session = load_session("data/participant_001.json")
print(f"Session {session.session_id} has {len(session.trials)} trials")

# Load all sessions from a directory
sessions = load_sessions("data/")
print(f"Loaded {len(sessions)} sessions")
```

### Supported Formats

slopit automatically detects the file format:

- **Native format**: JSON files with `schemaVersion` and `sessionId` fields
- **JATOS format**: Study results exported from JATOS

## Step 2: Create Analyzers

Analyzers examine behavioral data and produce flags. Choose analyzers based on your detection needs:

```python
from slopit.behavioral import (
    KeystrokeAnalyzer,
    FocusAnalyzer,
    TimingAnalyzer,
    PasteAnalyzer,
)

# Create analyzers with default configuration
keystroke = KeystrokeAnalyzer()
focus = FocusAnalyzer()
timing = TimingAnalyzer()
paste = PasteAnalyzer()
```

### Analyzer Overview

| Analyzer | Detects |
|----------|---------|
| KeystrokeAnalyzer | Low IKI variance, minimal revision, no deletions |
| FocusAnalyzer | Excessive blur events, extended hidden periods, blur-paste patterns |
| TimingAnalyzer | Instant responses, fast typing, consistent timing |
| PasteAnalyzer | Large pastes, paste without prior typing |

## Step 3: Run the Pipeline

The analysis pipeline runs all analyzers and aggregates their results:

```python
from slopit.pipeline import AnalysisPipeline

# Create pipeline with all analyzers
pipeline = AnalysisPipeline([
    KeystrokeAnalyzer(),
    FocusAnalyzer(),
    TimingAnalyzer(),
    PasteAnalyzer(),
])

# Analyze sessions
result = pipeline.analyze(sessions)
```

## Step 4: Interpret Results

The pipeline produces verdicts for each session:

```python
# Check session verdicts
for session_id, verdict in result.verdicts.items():
    print(f"{session_id}: {verdict.status} (confidence: {verdict.confidence:.2f})")

    if verdict.status != "clean":
        print(f"  Summary: {verdict.summary}")
        for flag in verdict.flags:
            print(f"  - [{flag.analyzer}] {flag.type}: {flag.message}")
```

### Verdict Status

| Status | Meaning |
|--------|---------|
| `clean` | No flags detected, or flags below threshold |
| `suspicious` | Some flags detected, requires review |
| `flagged` | Strong evidence of AI assistance |

### Example Output

```
session_001: clean (confidence: 1.00)
session_002: flagged (confidence: 0.85)
  Summary: Detected: low_iki_variance, blur_paste_pattern
  - [keystroke] low_iki_variance: Keystroke timing unusually consistent (std=45.2ms)
  - [focus] blur_paste_pattern: Paste event detected shortly after tab switch
session_003: suspicious (confidence: 0.52)
  Summary: Detected: excessive_blur
  - [focus] excessive_blur: Excessive window switches detected (7 blur events)
```

## Complete Example

Here is a complete working example:

```python
from slopit import load_sessions
from slopit.pipeline import AnalysisPipeline, PipelineConfig
from slopit.behavioral import (
    KeystrokeAnalyzer,
    FocusAnalyzer,
    TimingAnalyzer,
    PasteAnalyzer,
)

# Load data
sessions = load_sessions("data/")
print(f"Loaded {len(sessions)} sessions")

# Configure pipeline
config = PipelineConfig(
    aggregation="weighted",      # Use confidence-weighted voting
    severity_threshold="low",    # Include low, medium, and high severity flags
    confidence_threshold=0.5,    # Only include flags with >= 50% confidence
)

# Create pipeline
pipeline = AnalysisPipeline(
    analyzers=[
        KeystrokeAnalyzer(),
        FocusAnalyzer(),
        TimingAnalyzer(),
        PasteAnalyzer(),
    ],
    config=config,
)

# Run analysis
result = pipeline.analyze(sessions)

# Print summary statistics
total = len(result.sessions)
flagged = sum(1 for v in result.verdicts.values() if v.status == "flagged")
suspicious = sum(1 for v in result.verdicts.values() if v.status == "suspicious")
clean = sum(1 for v in result.verdicts.values() if v.status == "clean")

print(f"\nResults:")
print(f"  Total:      {total}")
print(f"  Flagged:    {flagged} ({flagged/total*100:.1f}%)")
print(f"  Suspicious: {suspicious} ({suspicious/total*100:.1f}%)")
print(f"  Clean:      {clean} ({clean/total*100:.1f}%)")

# Export results
from slopit.pipeline import CSVExporter

exporter = CSVExporter()
exporter.export(result, "results.csv")
print("\nResults exported to results.csv")
```

## Using the CLI

For quick analysis, use the command-line interface:

```bash
# Analyze a directory of sessions
slopit analyze data/ --summary

# Save results to JSON
slopit analyze data/ --output results.json

# Export to CSV
slopit analyze data/ --csv results.csv

# Use specific analyzers
slopit analyze data/ --analyzers keystroke,focus
```

See [CLI Reference](cli.md) for all options.

## Next Steps

- [Loading Data](guides/loading-data.md): Details on supported formats and custom loaders
- [Running Analysis](guides/running-analysis.md): Configuring analyzers and pipelines
- [Custom Analyzers](guides/custom-analyzers.md): Writing your own analyzers
- [API Reference](api/index.md): Full API documentation
