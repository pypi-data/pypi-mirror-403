# Pipeline

The `slopit.pipeline` module provides orchestration for running multiple analyzers and aggregating their results.

## AnalysisPipeline

The main class for orchestrating analysis.

::: slopit.pipeline.pipeline.AnalysisPipeline
    options:
      show_source: true

### Example

```python
from slopit import load_sessions
from slopit.pipeline import AnalysisPipeline, PipelineConfig
from slopit.behavioral import KeystrokeAnalyzer, FocusAnalyzer

# Load data
sessions = load_sessions("data/")

# Configure pipeline
config = PipelineConfig(
    aggregation="weighted",
    severity_threshold="low",
    confidence_threshold=0.5,
)

# Create pipeline
pipeline = AnalysisPipeline(
    analyzers=[KeystrokeAnalyzer(), FocusAnalyzer()],
    config=config,
)

# Run analysis
result = pipeline.analyze(sessions)
```

## PipelineConfig

Configuration for the analysis pipeline.

::: slopit.pipeline.pipeline.PipelineConfig
    options:
      show_source: true

### Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `aggregation` | `"any"` \| `"majority"` \| `"weighted"` | `"weighted"` | Strategy for combining flags |
| `severity_threshold` | `"info"` \| `"low"` \| `"medium"` \| `"high"` | `"low"` | Minimum severity to include |
| `confidence_threshold` | `float` | `0.5` | Minimum confidence to include |

### Example Configurations

**High sensitivity** (flag on any evidence):

```python
config = PipelineConfig(
    aggregation="any",
    severity_threshold="info",
    confidence_threshold=0.3,
)
```

**Balanced** (recommended for most use cases):

```python
config = PipelineConfig(
    aggregation="weighted",
    severity_threshold="low",
    confidence_threshold=0.5,
)
```

**High specificity** (require strong evidence):

```python
config = PipelineConfig(
    aggregation="majority",
    severity_threshold="medium",
    confidence_threshold=0.7,
)
```

## Aggregation Strategies

### aggregate_flags

::: slopit.pipeline.aggregation.aggregate_flags
    options:
      show_source: true

### Strategy Details

**"any"** (most sensitive):

- Flags the session if any analyzer produces a flag
- Highest sensitivity, highest false positive rate
- Returns the maximum confidence among all flags

**"majority"** (balanced):

- Flags if more than half of analyzers produce flags
- Returns "suspicious" if some but not majority flag
- Confidence is the proportion of flagging analyzers

**"weighted"** (recommended):

- Uses confidence-weighted voting
- Computes average confidence across all flags
- `flagged` if average >= 0.7
- `suspicious` if average >= 0.4
- `clean` otherwise

### Example

```python
from slopit.pipeline.aggregation import aggregate_flags

flags = [...]  # List of AnalysisFlag objects
status, confidence = aggregate_flags(
    flags=flags,
    strategy="weighted",
    total_analyzers=4,
)

print(f"Status: {status}, Confidence: {confidence:.2f}")
```

## Result Types

See [Schemas > Analysis Result Types](schemas.md#analysis-result-types) for the full API reference.

### Working with PipelineResult

```python
result = pipeline.analyze(sessions)

# List of analyzed session IDs
print(result.sessions)

# Results from each analyzer
for analyzer_name, results in result.analyzer_results.items():
    print(f"{analyzer_name}: {len(results)} results")

# Aggregated flags per session
for session_id, flags in result.aggregated_flags.items():
    print(f"{session_id}: {len(flags)} flags")

# Final verdicts
for session_id, verdict in result.verdicts.items():
    print(f"{session_id}: {verdict.status}")
```

### Verdict Status Values

| Status | Description |
|--------|-------------|
| `clean` | No flags detected, or all flags below threshold |
| `suspicious` | Some evidence of AI assistance, requires review |
| `flagged` | Strong evidence of AI assistance |

## Reporting

### TextReporter

Generate text reports from analysis results.

::: slopit.pipeline.reporting.TextReporter
    options:
      show_source: true

#### Example

```python
from slopit.pipeline import TextReporter

reporter = TextReporter()

# Generate full report
report = reporter.generate(result)
print(report)

# Print summary table (uses Rich)
reporter.print_summary(result)
```

#### Sample Output

```
============================================================
slopit Analysis Report
============================================================

Sessions Analyzed: 100
  Flagged:    12 (12.0%)
  Suspicious: 8 (8.0%)
  Clean:      80 (80.0%)

------------------------------------------------------------
Flagged Sessions
------------------------------------------------------------

Session: session_042
  Status: flagged (confidence: 0.85)
  Flags:
    - [keystroke] low_iki_variance: Keystroke timing unusually consistent (std=45.2ms)
    - [focus] blur_paste_pattern: Paste event detected shortly after tab switch
```

### CSVExporter

Export analysis results to CSV format.

::: slopit.pipeline.reporting.CSVExporter
    options:
      show_source: true

#### Example

```python
from slopit.pipeline import CSVExporter

exporter = CSVExporter()

# Export session-level results
exporter.export(result, "results.csv")

# Export individual flags
exporter.export_flags(result, "flags.csv")
```

#### Output Format

**results.csv**:

| session_id | status | confidence | flag_count | summary | flag_low_iki_variance | flag_excessive_blur |
|------------|--------|------------|------------|---------|----------------------|---------------------|
| session_001 | clean | 1.00 | 0 | No flags detected | | |
| session_002 | flagged | 0.85 | 2 | Detected: low_iki_variance, excessive_blur | True | True |

**flags.csv**:

| session_id | analyzer | type | severity | message | confidence | trial_ids |
|------------|----------|------|----------|---------|------------|-----------|
| session_002 | keystroke | low_iki_variance | medium | Keystroke timing unusually consistent | 0.75 | trial-0,trial-1 |
| session_002 | focus | excessive_blur | medium | Excessive window switches detected | 0.70 | trial-0 |

## Complete Pipeline Example

```python
from slopit import load_sessions
from slopit.pipeline import (
    AnalysisPipeline,
    PipelineConfig,
    TextReporter,
    CSVExporter,
)
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
    aggregation="weighted",
    severity_threshold="low",
    confidence_threshold=0.5,
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

# Run analysis
result = pipeline.analyze(sessions)

# Print summary
reporter = TextReporter()
reporter.print_summary(result)

# Export results
exporter = CSVExporter()
exporter.export(result, "results.csv")
exporter.export_flags(result, "flags.csv")

# Print flagged sessions
print("\nFlagged Sessions:")
for session_id, verdict in result.verdicts.items():
    if verdict.status == "flagged":
        print(f"\n{session_id}:")
        print(f"  Confidence: {verdict.confidence:.2f}")
        for flag in verdict.flags:
            print(f"  - [{flag.analyzer}] {flag.message}")
```
