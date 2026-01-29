# Analyzers

The `slopit.behavioral` module provides analyzers for detecting AI-assisted responses through behavioral patterns.

## Analyzer Base Class

### Analyzer

Abstract base class that all analyzers inherit from.

::: slopit.behavioral.base.Analyzer
    options:
      show_source: true

### AnalyzerConfig

Base configuration class for analyzers.

::: slopit.behavioral.base.AnalyzerConfig
    options:
      show_source: true

## Keystroke Analyzer

Analyzes keystroke dynamics to detect transcription patterns. Transcription (typing from a pre-written source) produces different keystroke patterns than authentic composition.

### KeystrokeAnalyzer

::: slopit.behavioral.keystroke.KeystrokeAnalyzer
    options:
      show_source: true

### KeystrokeAnalyzerConfig

::: slopit.behavioral.keystroke.KeystrokeAnalyzerConfig
    options:
      show_source: true

### Detection Signals

| Flag Type | Severity | Description |
|-----------|----------|-------------|
| `low_iki_variance` | medium | Keystroke timing unusually consistent |
| `minimal_revision` | low | Very few revisions during composition |
| `no_deletions` | low | No deletion keystrokes in extended response |

### Example

```python
from slopit import load_sessions
from slopit.behavioral import KeystrokeAnalyzer, KeystrokeAnalyzerConfig

# Custom configuration
config = KeystrokeAnalyzerConfig(
    pause_threshold_ms=2000.0,      # Pauses longer than 2s
    burst_threshold_ms=500.0,       # Typing bursts under 500ms IKI
    min_keystrokes=20,              # Minimum keystrokes for analysis
    min_iki_std_threshold=100.0,    # Flag if std IKI < 100ms
    max_ppr_threshold=0.95,         # Flag if product/process ratio > 0.95
)

analyzer = KeystrokeAnalyzer(config)

# Analyze sessions
sessions = load_sessions("data/")
for session in sessions:
    result = analyzer.analyze_session(session)

    for flag in result.flags:
        print(f"{flag.type}: {flag.message}")
```

### Metrics Computed

- **mean_iki**: Mean inter-keystroke interval (milliseconds)
- **std_iki**: Standard deviation of IKI
- **median_iki**: Median IKI
- **total_keystrokes**: Total keydown events
- **printable_keystrokes**: Printable character keystrokes
- **deletions**: Backspace and Delete keystrokes
- **pause_count**: Pauses exceeding threshold
- **product_process_ratio**: Final length / total keystrokes

## Focus Analyzer

Analyzes focus and visibility events to detect patterns suggesting external assistance (tab switching to AI tools).

### FocusAnalyzer

::: slopit.behavioral.focus.FocusAnalyzer
    options:
      show_source: true

### FocusAnalyzerConfig

::: slopit.behavioral.focus.FocusAnalyzerConfig
    options:
      show_source: true

### Detection Signals

| Flag Type | Severity | Description |
|-----------|----------|-------------|
| `excessive_blur` | medium | Many window blur events |
| `extended_hidden` | medium | Long periods with tab hidden |
| `blur_paste_pattern` | high | Paste shortly after tab switch |

### Example

```python
from slopit.behavioral import FocusAnalyzer, FocusAnalyzerConfig

config = FocusAnalyzerConfig(
    max_blur_count=5,               # Flag if more than 5 blur events
    max_hidden_duration_ms=30000,   # Flag if hidden > 30 seconds
    blur_paste_window_ms=5000,      # Detect paste within 5s of refocus
)

analyzer = FocusAnalyzer(config)
result = analyzer.analyze_session(session)
```

### Metrics Computed

- **blur_count**: Number of window blur events
- **total_blur_duration**: Total time with window blurred
- **hidden_count**: Number of visibility hidden events
- **total_hidden_duration**: Total time with document hidden

## Timing Analyzer

Analyzes response timing to detect suspiciously fast responses or unusual consistency.

### TimingAnalyzer

::: slopit.behavioral.timing.TimingAnalyzer
    options:
      show_source: true

### TimingAnalyzerConfig

::: slopit.behavioral.timing.TimingAnalyzerConfig
    options:
      show_source: true

### Detection Signals

| Flag Type | Severity | Description |
|-----------|----------|-------------|
| `instant_response` | high | Very fast response for character count |
| `fast_typing` | medium | Typing speed exceeds human capability |
| `consistent_timing` | medium | Unusually consistent RT across trials |

### Example

```python
from slopit.behavioral import TimingAnalyzer, TimingAnalyzerConfig

config = TimingAnalyzerConfig(
    min_rt_per_char_ms=20.0,              # Minimum 20ms per character
    max_rt_cv_threshold=0.1,              # Flag if CV < 0.1
    instant_response_threshold_ms=2000,   # Instant if < 2s
    instant_response_min_chars=100,       # For responses > 100 chars
)

analyzer = TimingAnalyzer(config)
result = analyzer.analyze_session(session)
```

### Metrics Computed

- **rt**: Response time (milliseconds)
- **character_count**: Characters in response
- **ms_per_char**: Milliseconds per character
- **chars_per_minute**: Characters per minute

## Paste Analyzer

Analyzes paste events to detect copy/paste behavior.

### PasteAnalyzer

::: slopit.behavioral.paste.PasteAnalyzer
    options:
      show_source: true

### PasteAnalyzerConfig

::: slopit.behavioral.paste.PasteAnalyzerConfig
    options:
      show_source: true

### Detection Signals

| Flag Type | Severity | Description |
|-----------|----------|-------------|
| `large_paste` | medium | Pasted substantial text |
| `paste_without_typing` | medium/high | Paste with minimal prior keystrokes |

### Example

```python
from slopit.behavioral import PasteAnalyzer, PasteAnalyzerConfig

config = PasteAnalyzerConfig(
    large_paste_threshold=50,            # Flag pastes > 50 chars
    suspicious_preceding_keystrokes=5,   # Flag if < 5 keystrokes before
)

analyzer = PasteAnalyzer(config)
result = analyzer.analyze_session(session)
```

### Metrics Computed

- **paste_count**: Number of paste events
- **total_pasted_chars**: Total characters pasted
- **blocked_count**: Number of blocked paste events
- **large_paste_count**: Number of large paste events

## Combining Analyzers

Use the pipeline to run multiple analyzers and combine their results:

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
```

See [Pipeline](pipeline.md) for aggregation configuration.

## Writing Custom Analyzers

See [Custom Analyzers Guide](../guides/custom-analyzers.md) for instructions on creating your own analyzers.
