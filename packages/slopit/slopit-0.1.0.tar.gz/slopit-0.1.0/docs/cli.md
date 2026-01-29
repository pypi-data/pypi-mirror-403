# CLI Reference

slopit provides a command-line interface for running analysis without writing Python code.

## Installation

The CLI is installed automatically with the slopit package:

```bash
pip install slopit
```

Verify installation:

```bash
slopit --version
```

## Commands

### slopit analyze

Analyze sessions for AI-assisted responses.

```bash
slopit analyze INPUT_PATH [OPTIONS]
```

**Arguments:**

- `INPUT_PATH`: Path to a session file or directory of files

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--output` | `-o` | None | Output file for JSON results |
| `--analyzers` | `-a` | `keystroke,focus,timing,paste` | Comma-separated list of analyzers |
| `--aggregation` | | `weighted` | Flag aggregation strategy |
| `--summary` | `-s` | False | Print summary table only |
| `--csv` | | None | Export results to CSV file |

**Examples:**

```bash
# Analyze all files in a directory
slopit analyze data/

# Print summary only
slopit analyze data/ --summary

# Save results to JSON
slopit analyze data/ --output results.json

# Export to CSV
slopit analyze data/ --csv results.csv

# Use specific analyzers
slopit analyze data/ --analyzers keystroke,focus

# Change aggregation strategy
slopit analyze data/ --aggregation majority

# Combine options
slopit analyze data/ \
  --analyzers keystroke,focus,timing \
  --aggregation weighted \
  --output results.json \
  --csv summary.csv
```

**Output:**

Without `--summary`, prints a full report:

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
    - [keystroke] low_iki_variance: Keystroke timing unusually consistent
    - [focus] blur_paste_pattern: Paste event detected shortly after tab switch
```

With `--summary`, prints a compact table:

```
         Analysis Summary
┏━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━┓
┃ Status     ┃ Count ┃ Percentage ┃
┡━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━┩
│ Flagged    │    12 │      12.0% │
│ Suspicious │     8 │       8.0% │
│ Clean      │    80 │      80.0% │
└────────────┴───────┴────────────┘
```

### slopit validate

Validate session files against the slopit schema.

```bash
slopit validate INPUT_PATH
```

**Arguments:**

- `INPUT_PATH`: Path to a session file or directory of files

**Examples:**

```bash
# Validate a single file
slopit validate data/session.json

# Validate all files in a directory
slopit validate data/
```

**Output:**

```
✓ data/session_001.json: 1 session(s) valid
✓ data/session_002.json: 1 session(s) valid
✗ data/session_003.json: Invalid schemaVersion: expected "1.0"

Summary: 2 valid, 1 invalid
```

### slopit report

Generate a report from previously saved analysis results.

```bash
slopit report RESULTS_PATH [OPTIONS]
```

**Arguments:**

- `RESULTS_PATH`: Path to a JSON results file from `slopit analyze --output`

**Options:**

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--format` | `-f` | `text` | Output format: `text` or `csv` |
| `--output` | `-o` | None | Output file path |

**Examples:**

```bash
# Print text report to console
slopit report results.json

# Save text report to file
slopit report results.json --output report.txt

# Export to CSV (requires --output)
slopit report results.json --format csv --output summary.csv
```

### slopit dashboard

Start the slopit analytics dashboard server.

```bash
slopit dashboard [OPTIONS]
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--host` | `127.0.0.1` | Host address to bind to |
| `--port` | `8000` | Port number to listen on |
| `--reload` | False | Enable auto-reload for development |
| `--data-dir` | `./data` | Directory for session data storage |

**Examples:**

```bash
# Start on default port (localhost:8000)
slopit dashboard

# Start on all interfaces, custom port
slopit dashboard --host 0.0.0.0 --port 8080

# Development mode with auto-reload
slopit dashboard --reload

# Custom data directory
slopit dashboard --data-dir ./sessions

# Combined options
slopit dashboard --host 0.0.0.0 --port 8080 --reload --data-dir ./sessions
```

**Requirements:**

The dashboard requires optional dependencies. Install with:

```bash
pip install slopit[dashboard]
```

**Features:**

When running, the dashboard provides:

- **REST API** at `http://localhost:8000/api/v1/`
- **WebSocket** at `ws://localhost:8000/ws` for real-time updates
- **Web UI** at `http://localhost:8000/` (if React frontend is built)

**API Endpoints:**

| Endpoint | Description |
|----------|-------------|
| `/api/v1/sessions/` | List and manage sessions |
| `/api/v1/trials/` | Access trial data |
| `/api/v1/analysis/` | Verdicts, flags, batch analysis |
| `/api/v1/export/` | CSV and JSON exports |
| `/api/v1/jatos/` | JATOS synchronization |
| `/api/v1/prolific/` | Prolific submission management |

**Environment Variables:**

For JATOS and Prolific integration, set API tokens via environment variables or pass them in API requests:

```bash
export JATOS_URL="https://jatos.example.com"
export JATOS_TOKEN="your-jatos-api-token"
export PROLIFIC_TOKEN="your-prolific-api-token"

slopit dashboard
```

---

## Analyzers

Available analyzers for the `--analyzers` option:

| Name | Description |
|------|-------------|
| `keystroke` | Keystroke dynamics analysis (IKI variance, revision patterns) |
| `focus` | Focus and visibility analysis (tab switching, hidden periods) |
| `timing` | Response timing analysis (fast responses, consistent timing) |
| `paste` | Paste event analysis (large pastes, paste without typing) |

**Default:** All four analyzers are used.

## Aggregation Strategies

Available strategies for the `--aggregation` option:

| Strategy | Description |
|----------|-------------|
| `any` | Flag if any analyzer produces a flag (most sensitive) |
| `majority` | Flag if majority of analyzers produce flags |
| `weighted` | Use confidence-weighted voting (recommended) |

**Default:** `weighted`

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error (file not found, invalid format, etc.) |

## Environment Variables

The dashboard command can use environment variables for API integration:

| Variable | Description |
|----------|-------------|
| `JATOS_URL` | JATOS server URL for data synchronization |
| `JATOS_TOKEN` | JATOS API authentication token |
| `PROLIFIC_TOKEN` | Prolific API authentication token |

These are optional; credentials can also be passed via the REST API.

## Examples

### Basic Workflow

```bash
# 1. Validate data files
slopit validate data/

# 2. Run analysis
slopit analyze data/ --output results.json

# 3. Generate report
slopit report results.json
```

### Screening Large Datasets

```bash
# Quick summary of flagged sessions
slopit analyze data/ --summary

# Export for further analysis
slopit analyze data/ --csv results.csv
```

### Focused Analysis

```bash
# Only keystroke analysis
slopit analyze data/ --analyzers keystroke

# Keystroke and focus only
slopit analyze data/ --analyzers keystroke,focus
```

### High Sensitivity Mode

```bash
# Use "any" aggregation to catch more potential issues
slopit analyze data/ --aggregation any --summary
```

### Batch Processing

Process multiple directories:

```bash
for dir in batch1 batch2 batch3; do
  slopit analyze "data/$dir" --output "results_$dir.json" --csv "results_$dir.csv"
done
```

### Integration with Other Tools

```bash
# Pipe to jq for JSON processing
slopit analyze data/ --output /dev/stdout | jq '.verdicts | to_entries | map(select(.value.status == "flagged"))'

# Extract flagged session IDs
slopit analyze data/ --output results.json
jq -r '.verdicts | to_entries[] | select(.value.status == "flagged") | .key' results.json
```
