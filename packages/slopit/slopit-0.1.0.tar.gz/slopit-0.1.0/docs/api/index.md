# API Overview

The slopit Python package is organized into four main modules:

## Module Structure

```
slopit/
├── schemas/      # Pydantic data models
├── io/           # Data loaders
├── behavioral/   # Behavioral analyzers
└── pipeline/     # Orchestration and reporting
```

## Core Concepts

### Sessions and Trials

A **session** represents one participant completing an experiment. Each session contains multiple **trials**, where each trial is a single task (e.g., answering a question, writing a response).

```python
from slopit import SlopitSession, SlopitTrial

session: SlopitSession  # Contains metadata, environment info, and trials
trial: SlopitTrial      # Contains stimulus, response, and behavioral data
```

### Behavioral Data

Each trial captures **behavioral data** during task completion:

- **Keystrokes**: Individual key press and release events with timestamps
- **Focus events**: Window blur/focus and visibility changes
- **Paste events**: Clipboard paste operations

```python
from slopit.schemas import BehavioralData, KeystrokeEvent, FocusEvent, PasteEvent
```

### Analyzers

**Analyzers** process behavioral data and produce flags. Each analyzer focuses on a specific type of evidence:

```python
from slopit.behavioral import Analyzer, KeystrokeAnalyzer, FocusAnalyzer
```

### Pipeline

The **pipeline** orchestrates multiple analyzers and combines their results:

```python
from slopit.pipeline import AnalysisPipeline, PipelineConfig
```

## Data Flow

```
                    load_session()
                         |
                         v
+------------------+     +------------------+
| JSON File        | --> | SlopitSession    |
+------------------+     +------------------+
                              |
                              v
                    +------------------+
                    | AnalysisPipeline |
                    +------------------+
                              |
              +---------------+---------------+
              |               |               |
              v               v               v
        +-----------+   +-----------+   +-----------+
        | Keystroke |   |   Focus   |   |   Paste   |
        | Analyzer  |   |  Analyzer |   |  Analyzer |
        +-----------+   +-----------+   +-----------+
              |               |               |
              v               v               v
        +------------+  +------------+  +------------+
        | Analysis   |  | Analysis   |  | Analysis   |
        | Result     |  | Result     |  | Result     |
        +------------+  +------------+  +------------+
              |               |               |
              +-------+-------+-------+-------+
                      |
                      v
              +------------------+
              | PipelineResult   |
              | (aggregated)     |
              +------------------+
```

## Quick Reference

### Loading Data

```python
from slopit import load_session, load_sessions

# Single file
session = load_session("path/to/file.json")

# Directory
sessions = load_sessions("path/to/directory/")
```

### Running Analysis

```python
from slopit.pipeline import AnalysisPipeline
from slopit.behavioral import KeystrokeAnalyzer

pipeline = AnalysisPipeline([KeystrokeAnalyzer()])
result = pipeline.analyze(sessions)
```

### Checking Results

```python
for session_id, verdict in result.verdicts.items():
    print(f"{session_id}: {verdict.status}")
```

### Exporting Results

```python
from slopit.pipeline import CSVExporter

exporter = CSVExporter()
exporter.export(result, "results.csv")
```

## Module Documentation

- [Schemas](schemas.md): Data models (SlopitSession, SlopitTrial, etc.)
- [IO Loaders](io.md): Loading data from various formats
- [Analyzers](analyzers.md): Behavioral analyzers
- [Pipeline](pipeline.md): Orchestration and aggregation
