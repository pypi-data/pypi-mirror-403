# Basic Analysis Example

This example demonstrates a complete workflow for analyzing session data with slopit.

## Scenario

You have collected behavioral data from an online study using jsPsych with the slopit adapter. The data is stored in a directory of JSON files, one per participant. You want to identify participants who may have used AI assistance.

## Setup

First, install slopit:

```bash
pip install slopit
```

## Loading Data

Load all session files from a directory:

```python
from slopit import load_sessions

# Load all sessions
sessions = load_sessions("data/")
print(f"Loaded {len(sessions)} sessions")

# Quick overview
for session in sessions[:3]:  # First 3 sessions
    trial_count = len(session.trials)
    has_behavioral = any(t.behavioral for t in session.trials)
    print(f"  {session.session_id}: {trial_count} trials, behavioral={has_behavioral}")
```

Output:

```
Loaded 50 sessions
  abc123: 10 trials, behavioral=True
  def456: 10 trials, behavioral=True
  ghi789: 10 trials, behavioral=True
```

## Creating the Pipeline

Set up an analysis pipeline with all available analyzers:

```python
from slopit.pipeline import AnalysisPipeline, PipelineConfig
from slopit.behavioral import (
    KeystrokeAnalyzer,
    FocusAnalyzer,
    TimingAnalyzer,
    PasteAnalyzer,
)

# Configure the pipeline
config = PipelineConfig(
    aggregation="weighted",      # Confidence-weighted voting
    severity_threshold="low",    # Include low, medium, and high severity flags
    confidence_threshold=0.5,    # Only flags with >= 50% confidence
)

# Create pipeline with all analyzers
pipeline = AnalysisPipeline(
    analyzers=[
        KeystrokeAnalyzer(),
        FocusAnalyzer(),
        TimingAnalyzer(),
        PasteAnalyzer(),
    ],
    config=config,
)
```

## Running Analysis

Analyze all sessions:

```python
result = pipeline.analyze(sessions)
```

## Reviewing Results

### Summary Statistics

```python
total = len(result.sessions)
flagged = sum(1 for v in result.verdicts.values() if v.status == "flagged")
suspicious = sum(1 for v in result.verdicts.values() if v.status == "suspicious")
clean = sum(1 for v in result.verdicts.values() if v.status == "clean")

print(f"Analysis Results:")
print(f"  Total sessions:  {total}")
print(f"  Flagged:         {flagged} ({flagged/total*100:.1f}%)")
print(f"  Suspicious:      {suspicious} ({suspicious/total*100:.1f}%)")
print(f"  Clean:           {clean} ({clean/total*100:.1f}%)")
```

Output:

```
Analysis Results:
  Total sessions:  50
  Flagged:         6 (12.0%)
  Suspicious:      4 (8.0%)
  Clean:           40 (80.0%)
```

### Detailed Flagged Sessions

```python
print("\nFlagged Sessions:")
print("-" * 60)

for session_id, verdict in result.verdicts.items():
    if verdict.status != "flagged":
        continue

    print(f"\nSession: {session_id}")
    print(f"  Confidence: {verdict.confidence:.2f}")
    print(f"  Summary: {verdict.summary}")
    print("  Flags:")

    for flag in verdict.flags:
        print(f"    - [{flag.analyzer}] {flag.type}")
        print(f"      {flag.message}")
        if flag.evidence:
            for key, value in flag.evidence.items():
                print(f"      {key}: {value}")
```

Output:

```
Flagged Sessions:
------------------------------------------------------------

Session: participant_007
  Confidence: 0.85
  Summary: Detected: low_iki_variance, blur_paste_pattern
  Flags:
    - [keystroke] low_iki_variance
      Keystroke timing unusually consistent (std=42.3ms)
      std_iki: 42.3
    - [focus] blur_paste_pattern
      Paste event detected shortly after tab switch

Session: participant_023
  Confidence: 0.92
  Summary: Detected: instant_response, large_paste
  Flags:
    - [timing] instant_response
      Suspiciously fast response (1500ms for 250 chars)
      rt: 1500
      character_count: 250
    - [paste] large_paste
      Large paste detected (245 characters)
      text_length: 245
```

### Suspicious Sessions

```python
print("\nSuspicious Sessions (require manual review):")
print("-" * 60)

for session_id, verdict in result.verdicts.items():
    if verdict.status != "suspicious":
        continue

    print(f"\n{session_id}: {verdict.summary}")
```

## Exporting Results

### To CSV

```python
from slopit.pipeline import CSVExporter

exporter = CSVExporter()

# Session-level results
exporter.export(result, "analysis_results.csv")
print("Exported to analysis_results.csv")

# Individual flags for detailed review
exporter.export_flags(result, "analysis_flags.csv")
print("Exported to analysis_flags.csv")
```

### To JSON

```python
import json

with open("analysis_results.json", "w") as f:
    json.dump(result.to_dict(), f, indent=2, default=str)

print("Exported to analysis_results.json")
```

### Text Report

```python
from slopit.pipeline import TextReporter

reporter = TextReporter()

# Generate and save report
report = reporter.generate(result)
with open("analysis_report.txt", "w") as f:
    f.write(report)

print("Exported to analysis_report.txt")

# Or print to console
print(report)
```

## Complete Script

Here is the complete analysis script:

```python
#!/usr/bin/env python
"""Basic slopit analysis example."""

from slopit import load_sessions
from slopit.pipeline import (
    AnalysisPipeline,
    PipelineConfig,
    CSVExporter,
    TextReporter,
)
from slopit.behavioral import (
    KeystrokeAnalyzer,
    FocusAnalyzer,
    TimingAnalyzer,
    PasteAnalyzer,
)


def main():
    # Load data
    print("Loading sessions...")
    sessions = load_sessions("data/")
    print(f"Loaded {len(sessions)} sessions")

    # Configure pipeline
    config = PipelineConfig(
        aggregation="weighted",
        severity_threshold="low",
        confidence_threshold=0.5,
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
    print("Running analysis...")
    result = pipeline.analyze(sessions)

    # Print summary
    reporter = TextReporter()
    reporter.print_summary(result)

    # Export results
    exporter = CSVExporter()
    exporter.export(result, "results.csv")
    exporter.export_flags(result, "flags.csv")
    print("\nResults exported to results.csv and flags.csv")

    # Print flagged sessions
    flagged = [
        (sid, v) for sid, v in result.verdicts.items()
        if v.status == "flagged"
    ]

    if flagged:
        print(f"\n{len(flagged)} flagged sessions:")
        for session_id, verdict in flagged:
            print(f"  {session_id}: {verdict.summary}")
    else:
        print("\nNo sessions flagged.")


if __name__ == "__main__":
    main()
```

## Using the CLI

The same analysis can be done from the command line:

```bash
# Run analysis and print summary
slopit analyze data/ --summary

# Save results to files
slopit analyze data/ --output results.json --csv results.csv

# Generate report from saved results
slopit report results.json
```

## Next Steps

- [Running Analysis Guide](../guides/running-analysis.md): Learn about analyzer configuration
- [Custom Analyzers Guide](../guides/custom-analyzers.md): Write your own analyzers
- [JATOS Integration Example](jatos-integration.md): Process JATOS exports
