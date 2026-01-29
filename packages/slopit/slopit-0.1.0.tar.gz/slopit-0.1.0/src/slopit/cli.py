"""Command-line interface for slopit.

This module provides the CLI for running analysis on session data.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import click
from rich.console import Console

from slopit import load_sessions
from slopit.behavioral import (
    Analyzer,
    FocusAnalyzer,
    KeystrokeAnalyzer,
    PasteAnalyzer,
    TimingAnalyzer,
)
from slopit.pipeline import AnalysisPipeline, CSVExporter, PipelineConfig, TextReporter

if TYPE_CHECKING:
    from collections.abc import Sequence

ANALYZERS = {
    "keystroke": KeystrokeAnalyzer,
    "focus": FocusAnalyzer,
    "timing": TimingAnalyzer,
    "paste": PasteAnalyzer,
}

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="slopit")
def main() -> None:
    """slopit: AI response detection for crowdsourced research."""
    pass


@main.command()
@click.argument("input_path", type=click.Path(exists=True))
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file for results (JSON format)",
)
@click.option(
    "--analyzers",
    "-a",
    default="keystroke,focus,timing,paste",
    help="Comma-separated list of analyzers to run",
)
@click.option(
    "--aggregation",
    type=click.Choice(["any", "majority", "weighted"]),
    default="weighted",
    help="Flag aggregation strategy",
)
@click.option(
    "--summary",
    "-s",
    is_flag=True,
    help="Print summary table only",
)
@click.option(
    "--csv",
    type=click.Path(),
    help="Export results to CSV file",
)
def analyze(
    input_path: str,
    output: str | None,
    analyzers: str,
    aggregation: str,
    summary: bool,
    csv: str | None,
) -> None:
    """Analyze sessions for AI-assisted responses.

    INPUT_PATH can be a single file or a directory of session files.
    """
    # Load sessions
    sessions = load_sessions(Path(input_path))
    console.print(f"[green]Loaded {len(sessions)} sessions[/green]")

    if not sessions:
        console.print("[yellow]No sessions found to analyze[/yellow]")
        return

    # Create analyzers
    analyzer_names = [a.strip() for a in analyzers.split(",")]
    analyzer_instances: Sequence[Analyzer] = [
        ANALYZERS[name]() for name in analyzer_names if name in ANALYZERS
    ]

    if not analyzer_instances:
        console.print("[red]No valid analyzers specified[/red]")
        return

    console.print(f"[blue]Running {len(analyzer_instances)} analyzers...[/blue]")

    # Run pipeline
    config = PipelineConfig(aggregation=aggregation)  # type: ignore[arg-type]
    pipeline = AnalysisPipeline(list(analyzer_instances), config)
    result = pipeline.analyze(sessions)

    # Output results
    if summary:
        reporter = TextReporter()
        reporter.print_summary(result)
    elif output:
        output_path = Path(output)
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2, default=str)
        console.print(f"[green]Results saved to {output}[/green]")
    else:
        reporter = TextReporter()
        console.print(reporter.generate(result))

    # Export to CSV if requested
    if csv:
        exporter = CSVExporter()
        exporter.export(result, csv)
        console.print(f"[green]CSV exported to {csv}[/green]")


@main.command()
@click.argument("input_path", type=click.Path(exists=True))
def validate(input_path: str) -> None:
    """Validate session files against the slopit schema.

    INPUT_PATH can be a single file or a directory.
    """
    path = Path(input_path)

    files = [path] if path.is_file() else list(path.glob("**/*.json"))

    valid_count = 0
    invalid_count = 0

    for file_path in files:
        try:
            sessions = load_sessions(file_path)
            console.print(f"[green]\u2713[/green] {file_path}: {len(sessions)} session(s) valid")
            valid_count += len(sessions)
        except Exception as e:
            console.print(f"[red]\u2717[/red] {file_path}: {e}")
            invalid_count += 1

    console.print()
    console.print(f"[bold]Summary:[/bold] {valid_count} valid, {invalid_count} invalid")


@main.command()
@click.argument("results_path", type=click.Path(exists=True))
@click.option(
    "--format",
    "-f",
    type=click.Choice(["text", "csv"]),
    default="text",
    help="Output format",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output file path",
)
def report(results_path: str, format: str, output: str | None) -> None:
    """Generate a report from analysis results.

    RESULTS_PATH should be a JSON file from the analyze command.
    """
    from slopit.schemas.analysis import PipelineResult

    path = Path(results_path)
    with path.open(encoding="utf-8") as f:
        data = json.load(f)

    result = PipelineResult.model_validate(data)

    if format == "text":
        reporter = TextReporter()
        report_text = reporter.generate(result)

        if output:
            Path(output).write_text(report_text, encoding="utf-8")
            console.print(f"[green]Report saved to {output}[/green]")
        else:
            console.print(report_text)

    elif format == "csv":
        if not output:
            console.print("[red]CSV format requires --output path[/red]")
            return

        exporter = CSVExporter()
        exporter.export(result, output)
        console.print(f"[green]CSV exported to {output}[/green]")


@main.command()
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", default=8000, type=int, help="Port to bind to")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
@click.option("--data-dir", type=click.Path(), default="./data", help="Data directory path")
def dashboard(host: str, port: int, reload: bool, data_dir: str) -> None:
    """Start the slopit analytics dashboard server.

    Launches a FastAPI server with real-time analysis, JATOS/Prolific
    integration, and a web-based dashboard UI.

    Examples
    --------
    Start dashboard on default port:

        $ slopit dashboard

    Start with custom settings:

        $ slopit dashboard --host 0.0.0.0 --port 8080 --reload
    """
    try:
        import uvicorn

        from slopit.dashboard.app import create_app
        from slopit.dashboard.config import DashboardConfig
    except ImportError as e:
        click.echo(
            "Dashboard dependencies not installed. "
            "Install with: pip install slopit[dashboard]",
            err=True,
        )
        raise SystemExit(1) from e

    config = DashboardConfig(
        host=host,
        port=port,
        reload=reload,
        data_dir=Path(data_dir),
    )

    app = create_app(config)

    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        reload=config.reload,
    )


if __name__ == "__main__":
    main()
