"""Report generation for analysis results.

This module provides various reporters and exporters for
analysis results.
"""

import csv
from pathlib import Path

from rich.console import Console
from rich.table import Table

from slopit.schemas.analysis import PipelineResult

# Type alias for CSV row data (values can be string, int, float, bool, or None)
type CSVValue = str | int | float | bool | None


class TextReporter:
    """Generate text reports from analysis results.

    Examples
    --------
    >>> reporter = TextReporter()
    >>> report = reporter.generate(pipeline_result)
    >>> print(report)
    """

    def generate(self, result: PipelineResult) -> str:
        """Generate a text report.

        Parameters
        ----------
        result
            Pipeline result to report on.

        Returns
        -------
        str
            Formatted text report.
        """
        lines: list[str] = []

        lines.append("=" * 60)
        lines.append("slopit Analysis Report")
        lines.append("=" * 60)
        lines.append("")

        # Summary statistics
        total = len(result.sessions)
        flagged = sum(1 for v in result.verdicts.values() if v.status == "flagged")
        suspicious = sum(1 for v in result.verdicts.values() if v.status == "suspicious")
        clean = sum(1 for v in result.verdicts.values() if v.status == "clean")

        lines.append(f"Sessions Analyzed: {total}")
        lines.append(f"  Flagged:    {flagged} ({flagged / total * 100:.1f}%)" if total else "")
        lines.append(
            f"  Suspicious: {suspicious} ({suspicious / total * 100:.1f}%)" if total else ""
        )
        lines.append(f"  Clean:      {clean} ({clean / total * 100:.1f}%)" if total else "")
        lines.append("")

        # Flagged sessions
        if flagged > 0:
            lines.append("-" * 60)
            lines.append("Flagged Sessions")
            lines.append("-" * 60)
            lines.append("")

            for session_id, verdict in result.verdicts.items():
                if verdict.status != "flagged":
                    continue

                lines.append(f"Session: {session_id}")
                lines.append(f"  Status: {verdict.status} (confidence: {verdict.confidence:.2f})")
                lines.append("  Flags:")

                for flag in verdict.flags:
                    lines.append(f"    - [{flag.analyzer}] {flag.type}: {flag.message}")

                lines.append("")

        # Suspicious sessions
        if suspicious > 0:
            lines.append("-" * 60)
            lines.append("Suspicious Sessions")
            lines.append("-" * 60)
            lines.append("")

            for session_id, verdict in result.verdicts.items():
                if verdict.status != "suspicious":
                    continue

                lines.append(f"Session: {session_id}")
                lines.append(f"  Status: {verdict.status} (confidence: {verdict.confidence:.2f})")
                lines.append(f"  Summary: {verdict.summary}")

                if verdict.flags:
                    lines.append("  Flags:")
                    for flag in verdict.flags:
                        lines.append(f"    - [{flag.analyzer}] {flag.type}: {flag.message}")

                lines.append("")

        return "\n".join(lines)

    def print_summary(self, result: PipelineResult) -> None:
        """Print a summary table using Rich.

        Parameters
        ----------
        result
            Pipeline result to summarize.
        """
        console = Console()

        table = Table(title="Analysis Summary")
        table.add_column("Status", style="bold")
        table.add_column("Count", justify="right")
        table.add_column("Percentage", justify="right")

        total = len(result.sessions)
        if total == 0:
            console.print("[yellow]No sessions analyzed[/yellow]")
            return

        flagged = sum(1 for v in result.verdicts.values() if v.status == "flagged")
        suspicious = sum(1 for v in result.verdicts.values() if v.status == "suspicious")
        clean = sum(1 for v in result.verdicts.values() if v.status == "clean")

        table.add_row("Flagged", str(flagged), f"{flagged / total * 100:.1f}%", style="red")
        table.add_row(
            "Suspicious", str(suspicious), f"{suspicious / total * 100:.1f}%", style="yellow"
        )
        table.add_row("Clean", str(clean), f"{clean / total * 100:.1f}%", style="green")

        console.print(table)


class CSVExporter:
    """Export analysis results to CSV format.

    Examples
    --------
    >>> exporter = CSVExporter()
    >>> exporter.export(pipeline_result, "results.csv")
    """

    def export(self, result: PipelineResult, path: str | Path) -> None:
        """Export results to a CSV file.

        Parameters
        ----------
        result
            Pipeline result to export.
        path
            Output file path.
        """
        path = Path(path)

        rows: list[dict[str, CSVValue]] = []

        for session_id, verdict in result.verdicts.items():
            row: dict[str, CSVValue] = {
                "session_id": session_id,
                "status": verdict.status,
                "confidence": verdict.confidence,
                "flag_count": len(verdict.flags),
                "summary": verdict.summary,
            }

            # Add flag type columns
            flag_types = {f.type for f in verdict.flags}
            for flag_type in flag_types:
                row[f"flag_{flag_type}"] = True

            rows.append(row)

        if not rows:
            return

        # Get all column names
        all_columns: set[str] = set()
        for row in rows:
            all_columns.update(row.keys())

        fieldnames = ["session_id", "status", "confidence", "flag_count", "summary"]
        fieldnames.extend(sorted(c for c in all_columns if c.startswith("flag_")))

        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)

    def export_flags(self, result: PipelineResult, path: str | Path) -> None:
        """Export individual flags to a CSV file.

        Parameters
        ----------
        result
            Pipeline result to export.
        path
            Output file path.
        """
        path = Path(path)

        rows: list[dict[str, CSVValue]] = []

        for session_id, verdict in result.verdicts.items():
            for flag in verdict.flags:
                rows.append(
                    {
                        "session_id": session_id,
                        "analyzer": flag.analyzer,
                        "type": flag.type,
                        "severity": flag.severity,
                        "message": flag.message,
                        "confidence": flag.confidence,
                        "trial_ids": ",".join(flag.trial_ids) if flag.trial_ids else "",
                    }
                )

        if not rows:
            return

        fieldnames = [
            "session_id",
            "analyzer",
            "type",
            "severity",
            "message",
            "confidence",
            "trial_ids",
        ]

        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
