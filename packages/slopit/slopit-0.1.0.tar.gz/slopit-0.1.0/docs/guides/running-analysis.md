# Running Analysis

This guide covers configuring and running behavioral analysis with slopit.

## Basic Analysis

The simplest analysis uses default configuration:

```python
from slopit import load_sessions
from slopit.pipeline import AnalysisPipeline
from slopit.behavioral import KeystrokeAnalyzer

sessions = load_sessions("data/")
pipeline = AnalysisPipeline([KeystrokeAnalyzer()])
result = pipeline.analyze(sessions)
```

## Choosing Analyzers

Select analyzers based on your detection needs:

| Analyzer | Detects | Best For |
|----------|---------|----------|
| KeystrokeAnalyzer | Transcription patterns | Free-text responses |
| FocusAnalyzer | Tab switching | Any task |
| TimingAnalyzer | Fast responses | Timed tasks |
| PasteAnalyzer | Copy/paste | Text entry |

### Recommended Configuration

For comprehensive detection, use all analyzers:

```python
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
```

### Minimal Configuration

For basic transcription detection:

```python
pipeline = AnalysisPipeline([KeystrokeAnalyzer()])
```

## Configuring Analyzers

Each analyzer accepts a configuration object:

### Keystroke Analyzer

```python
from slopit.behavioral import KeystrokeAnalyzer, KeystrokeAnalyzerConfig

config = KeystrokeAnalyzerConfig(
    pause_threshold_ms=2000.0,      # What counts as a pause
    burst_threshold_ms=500.0,       # Max IKI within a burst
    min_keystrokes=20,              # Minimum for analysis
    min_iki_std_threshold=100.0,    # Flag if std < this
    max_ppr_threshold=0.95,         # Flag if PPR > this
)

analyzer = KeystrokeAnalyzer(config)
```

**Parameter guidance:**

- **min_iki_std_threshold**: Lower values catch more subtle transcription. 100ms is a good starting point; reduce to 50ms for stricter detection.
- **min_keystrokes**: Increase for longer responses to ensure reliable statistics.
- **max_ppr_threshold**: 0.95 means flag if final text is >95% of total keystrokes (minimal revision).

### Focus Analyzer

```python
from slopit.behavioral import FocusAnalyzer, FocusAnalyzerConfig

config = FocusAnalyzerConfig(
    max_blur_count=5,               # Flag if more blurs than this
    max_hidden_duration_ms=30000,   # Flag if hidden > 30s
    blur_paste_window_ms=5000,      # Detect paste within 5s of refocus
)

analyzer = FocusAnalyzer(config)
```

**Parameter guidance:**

- **max_blur_count**: Normal users occasionally switch tabs. 5 is permissive; reduce to 2-3 for stricter detection.
- **max_hidden_duration_ms**: Long hidden periods may indicate using another tool. 30s is a reasonable threshold.
- **blur_paste_window_ms**: Time window for detecting "copy from AI, paste into task" pattern.

### Timing Analyzer

```python
from slopit.behavioral import TimingAnalyzer, TimingAnalyzerConfig

config = TimingAnalyzerConfig(
    min_rt_per_char_ms=20.0,              # Minimum realistic typing speed
    max_rt_cv_threshold=0.1,              # Flag if CV < 0.1
    instant_response_threshold_ms=2000,   # Instant response threshold
    instant_response_min_chars=100,       # Only for long responses
)

analyzer = TimingAnalyzer(config)
```

**Parameter guidance:**

- **min_rt_per_char_ms**: 20ms/char = 3000 chars/minute, faster than any human typist.
- **instant_response_threshold_ms**: 2 seconds is very fast for composing text.
- **instant_response_min_chars**: Only flag instant responses for substantial text.

### Paste Analyzer

```python
from slopit.behavioral import PasteAnalyzer, PasteAnalyzerConfig

config = PasteAnalyzerConfig(
    large_paste_threshold=50,            # Flag pastes > 50 chars
    suspicious_preceding_keystrokes=5,   # Flag if few keystrokes before
)

analyzer = PasteAnalyzer(config)
```

**Parameter guidance:**

- **large_paste_threshold**: What counts as a "large" paste. 50 chars is about a sentence.
- **suspicious_preceding_keystrokes**: Legitimate paste usually follows some typing. 5 is permissive.

## Pipeline Configuration

### Aggregation Strategies

Choose how flags from multiple analyzers are combined:

```python
from slopit.pipeline import PipelineConfig

# Flag if ANY analyzer flags (most sensitive)
config = PipelineConfig(aggregation="any")

# Flag if MAJORITY of analyzers flag (balanced)
config = PipelineConfig(aggregation="majority")

# Use confidence-weighted voting (recommended)
config = PipelineConfig(aggregation="weighted")
```

**Strategy comparison:**

| Strategy | Sensitivity | Specificity | Use Case |
|----------|-------------|-------------|----------|
| any | High | Low | Screening, when false positives are acceptable |
| majority | Medium | Medium | Balanced detection |
| weighted | Adaptive | Adaptive | General purpose, production use |

### Filtering Thresholds

Control which flags are included in aggregation:

```python
config = PipelineConfig(
    aggregation="weighted",
    severity_threshold="low",      # Include low, medium, high
    confidence_threshold=0.5,      # Only flags with >= 50% confidence
)
```

**Severity levels:**

- **info**: Informational, not necessarily problematic
- **low**: Minor indicator, may be false positive
- **medium**: Moderate concern
- **high**: Strong indicator of AI assistance

### Example Configurations

**High sensitivity** (catch more, accept more false positives):

```python
config = PipelineConfig(
    aggregation="any",
    severity_threshold="info",
    confidence_threshold=0.3,
)
```

**Balanced** (recommended default):

```python
config = PipelineConfig(
    aggregation="weighted",
    severity_threshold="low",
    confidence_threshold=0.5,
)
```

**High specificity** (fewer false positives, may miss some):

```python
config = PipelineConfig(
    aggregation="majority",
    severity_threshold="medium",
    confidence_threshold=0.7,
)
```

## Interpreting Results

### Verdict Status

```python
result = pipeline.analyze(sessions)

for session_id, verdict in result.verdicts.items():
    if verdict.status == "flagged":
        # Strong evidence of AI assistance
        print(f"{session_id}: FLAGGED (confidence: {verdict.confidence:.2f})")
    elif verdict.status == "suspicious":
        # Some evidence, requires review
        print(f"{session_id}: SUSPICIOUS")
    else:
        # No significant evidence
        print(f"{session_id}: Clean")
```

### Understanding Flags

Each flag provides:

- **type**: The detection signal (e.g., "low_iki_variance")
- **analyzer**: Which analyzer produced it
- **severity**: How serious the signal is
- **message**: Human-readable description
- **confidence**: How confident the analyzer is (0.0 to 1.0)
- **evidence**: Data supporting the flag
- **trial_ids**: Which trials triggered the flag

```python
for flag in verdict.flags:
    print(f"\n{flag.type} ({flag.severity})")
    print(f"  Analyzer: {flag.analyzer}")
    print(f"  Message: {flag.message}")
    print(f"  Confidence: {flag.confidence:.2f}")
    print(f"  Evidence: {flag.evidence}")
    print(f"  Trials: {flag.trial_ids}")
```

### Per-Trial Analysis

For detailed per-trial results:

```python
for analyzer_name, results in result.analyzer_results.items():
    print(f"\n{analyzer_name}:")
    for analysis in results:
        for trial_data in analysis.trials:
            trial_id = trial_data["trial_id"]
            metrics = trial_data["metrics"]
            flags = trial_data["flags"]
            print(f"  {trial_id}: {len(flags)} flags")
```

## Exporting Results

### To JSON

```python
import json

with open("results.json", "w") as f:
    json.dump(result.to_dict(), f, indent=2, default=str)
```

### To CSV

```python
from slopit.pipeline import CSVExporter

exporter = CSVExporter()

# Session-level results
exporter.export(result, "results.csv")

# Individual flags
exporter.export_flags(result, "flags.csv")
```

### Text Report

```python
from slopit.pipeline import TextReporter

reporter = TextReporter()

# Full report
print(reporter.generate(result))

# Summary table
reporter.print_summary(result)
```

## Batch Processing

For large datasets:

```python
from pathlib import Path
from slopit import load_session
from slopit.pipeline import AnalysisPipeline, CSVExporter

pipeline = AnalysisPipeline([...])
exporter = CSVExporter()

# Process in batches
batch_size = 100
paths = list(Path("data/").glob("*.json"))

for i in range(0, len(paths), batch_size):
    batch_paths = paths[i:i + batch_size]
    sessions = [load_session(p) for p in batch_paths]

    result = pipeline.analyze(sessions)

    # Append to CSV
    exporter.export(result, f"results_batch_{i//batch_size}.csv")

    print(f"Processed batch {i//batch_size + 1}")
```

## Using the CLI

For quick analysis without writing code:

```bash
# Basic analysis
slopit analyze data/

# Summary only
slopit analyze data/ --summary

# Save to JSON
slopit analyze data/ --output results.json

# Export to CSV
slopit analyze data/ --csv results.csv

# Specific analyzers
slopit analyze data/ --analyzers keystroke,focus

# Different aggregation
slopit analyze data/ --aggregation majority
```

## Best Practices

1. **Start with default configuration** and adjust based on results
2. **Use weighted aggregation** for production
3. **Review suspicious sessions** manually before exclusion
4. **Combine multiple analyzers** for robust detection
5. **Consider your population** when setting thresholds
6. **Document your configuration** for reproducibility
