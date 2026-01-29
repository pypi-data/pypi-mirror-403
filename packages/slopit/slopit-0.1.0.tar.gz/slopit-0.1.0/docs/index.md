# slopit

**AI response detection for crowdsourced behavioral research.**

slopit is a modular toolkit for detecting AI-assisted responses in online behavioral studies. It provides client-side behavioral capture (TypeScript) and server-side analysis (Python) to identify participants who may be using ChatGPT, Claude, or other AI assistants to complete tasks.

## Key Features

- **Behavioral Analysis**: Analyze keystroke dynamics, focus patterns, and paste events
- **Multiple Analyzers**: Combine evidence from independent analyzers for robust detection
- **Real-time Dashboard**: Web-based monitoring with JATOS and Prolific integration
- **Pipeline Orchestration**: Configure aggregation strategies and confidence thresholds
- **Multiple Data Formats**: Load data from JATOS, native JSON, and other sources
- **Extensible Architecture**: Write custom analyzers for domain-specific detection

## Architecture Overview

slopit consists of two main components:

```
                    +-----------------+
                    |   Browser       |
                    |   TypeScript    |
                    |   @slopit/core  |
                    +-----------------+
                            |
                            | SlopitSession (JSON)
                            v
                    +-----------------+
                    |   Server        |
                    |   Python        |
                    |   slopit        |
                    +-----------------+
```

**Client-side (TypeScript)**: Captures behavioral data during task completion, including keystrokes, focus/visibility events, and paste operations. Works with jsPsych, lab.js, PsychoJS, or standalone.

**Server-side (Python)**: Analyzes captured data using multiple independent analyzers. Produces flags with confidence scores and combines them into session-level verdicts.

## Detection Signals

slopit detects several behavioral patterns associated with AI-assisted responses:

| Signal | Description | Analyzer |
|--------|-------------|----------|
| Low IKI variance | Consistent keystroke timing suggests transcription | Keystroke |
| Minimal revision | Few deletions suggests copy/paste rather than composition | Keystroke |
| Instant response | Fast response relative to character count | Timing |
| Excessive blur | Many tab switches may indicate external assistance | Focus |
| Blur-paste pattern | Paste shortly after refocus suggests copy from AI | Focus |
| Large paste | Pasting substantial text without prior typing | Paste |

## Quick Example

```python
from slopit import load_sessions
from slopit.pipeline import AnalysisPipeline
from slopit.behavioral import KeystrokeAnalyzer, FocusAnalyzer

# Load session data
sessions = load_sessions("data/")

# Create analysis pipeline
pipeline = AnalysisPipeline([
    KeystrokeAnalyzer(),
    FocusAnalyzer(),
])

# Analyze sessions
result = pipeline.analyze(sessions)

# Check verdicts
for session_id, verdict in result.verdicts.items():
    if verdict.status == "flagged":
        print(f"{session_id}: {verdict.summary}")
```

## Getting Started

- [Installation](installation.md): Install slopit and its dependencies
- [Quick Start](quickstart.md): Run your first analysis in minutes
- [CLI Reference](cli.md): Use the command-line interface
- [Integrations](integrations.md): JATOS and Prolific integration

## API Reference

- [Schemas](api/schemas.md): Data models for sessions, trials, and events
- [IO Loaders](api/io.md): Load data from various formats
- [Analyzers](api/analyzers.md): Available behavioral analyzers
- [Pipeline](api/pipeline.md): Orchestration and aggregation
- [Dashboard](api.md#slopitdashboard): Web dashboard and REST API

## Research Background

slopit is based on research into behavioral signatures of AI-assisted writing. Key findings include:

- AI-assisted responses show lower keystroke timing variance (consistent typing speed suggests transcription)
- Authentic composition includes pauses, revisions, and variable timing
- Focus patterns reveal tab-switching to external tools
- Combining multiple signals improves detection accuracy

For more details, see:

- Kundu et al. (2025). "Detecting AI-Assisted Responses in Crowdsourced Research." arXiv:2511.12468.

## License

slopit is released under the MIT License.
