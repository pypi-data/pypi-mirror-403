"""Tests for reporting functionality."""

from __future__ import annotations

from pathlib import Path

import pytest

from slopit.pipeline import CSVExporter, TextReporter
from slopit.schemas.analysis import AnalysisResult, PipelineResult, SessionVerdict
from slopit.schemas.flags import AnalysisFlag


@pytest.fixture
def clean_pipeline_result() -> PipelineResult:
    """Pipeline result with all clean sessions."""
    return PipelineResult(
        sessions=["session-001", "session-002"],
        analyzer_results={
            "keystroke": [
                AnalysisResult(analyzer="keystroke", session_id="session-001"),
                AnalysisResult(analyzer="keystroke", session_id="session-002"),
            ]
        },
        aggregated_flags={
            "session-001": [],
            "session-002": [],
        },
        verdicts={
            "session-001": SessionVerdict(
                status="clean",
                confidence=1.0,
                flags=[],
                summary="No issues detected",
            ),
            "session-002": SessionVerdict(
                status="clean",
                confidence=1.0,
                flags=[],
                summary="No issues detected",
            ),
        },
    )


@pytest.fixture
def mixed_pipeline_result() -> PipelineResult:
    """Pipeline result with mixed verdicts."""
    flag1 = AnalysisFlag(
        type="low_iki_variance",
        analyzer="keystroke",
        severity="medium",
        message="Keystroke timing too consistent",
        confidence=0.75,
        trial_ids=["trial-001"],
    )
    flag2 = AnalysisFlag(
        type="excessive_blur",
        analyzer="focus",
        severity="medium",
        message="Too many tab switches",
        confidence=0.8,
        trial_ids=["trial-002"],
    )
    flag3 = AnalysisFlag(
        type="large_paste",
        analyzer="paste",
        severity="high",
        message="Large paste detected",
        confidence=0.9,
    )

    return PipelineResult(
        sessions=["session-001", "session-002", "session-003"],
        analyzer_results={
            "keystroke": [
                AnalysisResult(
                    analyzer="keystroke",
                    session_id="session-001",
                    flags=[flag1],
                ),
                AnalysisResult(analyzer="keystroke", session_id="session-002"),
                AnalysisResult(analyzer="keystroke", session_id="session-003"),
            ],
            "focus": [
                AnalysisResult(analyzer="focus", session_id="session-001"),
                AnalysisResult(
                    analyzer="focus",
                    session_id="session-002",
                    flags=[flag2],
                ),
                AnalysisResult(analyzer="focus", session_id="session-003"),
            ],
        },
        aggregated_flags={
            "session-001": [flag1],
            "session-002": [flag2],
            "session-003": [flag3],
        },
        verdicts={
            "session-001": SessionVerdict(
                status="suspicious",
                confidence=0.75,
                flags=[flag1],
                summary="Detected: low_iki_variance",
            ),
            "session-002": SessionVerdict(
                status="suspicious",
                confidence=0.8,
                flags=[flag2],
                summary="Detected: excessive_blur",
            ),
            "session-003": SessionVerdict(
                status="flagged",
                confidence=0.9,
                flags=[flag3],
                summary="Detected: large_paste",
            ),
        },
    )


class TestTextReporter:
    """Tests for TextReporter."""

    def test_generate_clean_report(
        self, clean_pipeline_result: PipelineResult
    ) -> None:
        """Should generate report for clean sessions."""
        reporter = TextReporter()
        report = reporter.generate(clean_pipeline_result)

        assert "slopit Analysis Report" in report
        assert "Sessions Analyzed: 2" in report
        assert "Clean:" in report

    def test_generate_mixed_report(
        self, mixed_pipeline_result: PipelineResult
    ) -> None:
        """Should generate report with flagged and suspicious sessions."""
        reporter = TextReporter()
        report = reporter.generate(mixed_pipeline_result)

        assert "Sessions Analyzed: 3" in report
        assert "Flagged:" in report
        assert "Suspicious:" in report
        assert "session-003" in report  # Flagged session
        assert "large_paste" in report

    def test_generate_includes_flag_details(
        self, mixed_pipeline_result: PipelineResult
    ) -> None:
        """Should include flag details in report."""
        reporter = TextReporter()
        report = reporter.generate(mixed_pipeline_result)

        # Should include flag type and analyzer
        assert "[keystroke]" in report or "keystroke" in report
        assert "low_iki_variance" in report

    def test_generate_empty_result(self) -> None:
        """Should handle empty pipeline result."""
        result = PipelineResult(sessions=[], verdicts={})
        reporter = TextReporter()
        report = reporter.generate(result)

        assert "Sessions Analyzed: 0" in report

    def test_report_structure(
        self, mixed_pipeline_result: PipelineResult
    ) -> None:
        """Should have proper report structure."""
        reporter = TextReporter()
        report = reporter.generate(mixed_pipeline_result)

        # Check for main sections
        assert "=" * 60 in report  # Header divider
        assert "Flagged Sessions" in report
        assert "Suspicious Sessions" in report

    def test_percentages_in_report(
        self, mixed_pipeline_result: PipelineResult
    ) -> None:
        """Should include percentages in summary."""
        reporter = TextReporter()
        report = reporter.generate(mixed_pipeline_result)

        # Should have percentage values
        assert "%" in report


class TestCSVExporter:
    """Tests for CSVExporter."""

    def test_export_creates_file(
        self, mixed_pipeline_result: PipelineResult, temp_dir: Path
    ) -> None:
        """Should create CSV file."""
        output_path = temp_dir / "results.csv"
        exporter = CSVExporter()

        exporter.export(mixed_pipeline_result, output_path)

        assert output_path.exists()

    def test_export_content(
        self, mixed_pipeline_result: PipelineResult, temp_dir: Path
    ) -> None:
        """Should export correct content."""
        output_path = temp_dir / "results.csv"
        exporter = CSVExporter()

        exporter.export(mixed_pipeline_result, output_path)

        content = output_path.read_text()
        lines = content.strip().split("\n")

        # Header row
        assert "session_id" in lines[0]
        assert "status" in lines[0]
        assert "confidence" in lines[0]

        # Data rows
        assert len(lines) == 4  # Header + 3 sessions

    def test_export_includes_flag_columns(
        self, mixed_pipeline_result: PipelineResult, temp_dir: Path
    ) -> None:
        """Should include flag type columns."""
        output_path = temp_dir / "results.csv"
        exporter = CSVExporter()

        exporter.export(mixed_pipeline_result, output_path)

        content = output_path.read_text()
        header = content.split("\n")[0]

        # Should have flag_* columns
        assert "flag_" in header

    def test_export_empty_result(self, temp_dir: Path) -> None:
        """Should handle empty result (no file created)."""
        result = PipelineResult(sessions=[], verdicts={})
        output_path = temp_dir / "empty.csv"
        exporter = CSVExporter()

        exporter.export(result, output_path)

        # File should not be created for empty results
        assert not output_path.exists()

    def test_export_flags_separate_file(
        self, mixed_pipeline_result: PipelineResult, temp_dir: Path
    ) -> None:
        """Should export individual flags to separate file."""
        output_path = temp_dir / "flags.csv"
        exporter = CSVExporter()

        exporter.export_flags(mixed_pipeline_result, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        lines = content.strip().split("\n")

        # Header
        assert "session_id" in lines[0]
        assert "analyzer" in lines[0]
        assert "type" in lines[0]
        assert "severity" in lines[0]

        # Should have rows for each flag
        assert len(lines) == 4  # Header + 3 flags

    def test_export_flags_content(
        self, mixed_pipeline_result: PipelineResult, temp_dir: Path
    ) -> None:
        """Should export correct flag content."""
        output_path = temp_dir / "flags.csv"
        exporter = CSVExporter()

        exporter.export_flags(mixed_pipeline_result, output_path)

        content = output_path.read_text()

        assert "keystroke" in content
        assert "low_iki_variance" in content
        assert "focus" in content
        assert "excessive_blur" in content

    def test_export_flags_with_trial_ids(
        self, mixed_pipeline_result: PipelineResult, temp_dir: Path
    ) -> None:
        """Should include trial IDs in export."""
        output_path = temp_dir / "flags.csv"
        exporter = CSVExporter()

        exporter.export_flags(mixed_pipeline_result, output_path)

        content = output_path.read_text()

        assert "trial_ids" in content
        assert "trial-001" in content

    def test_export_flags_empty(self, temp_dir: Path) -> None:
        """Should handle result with no flags."""
        result = PipelineResult(
            sessions=["session-001"],
            verdicts={
                "session-001": SessionVerdict(
                    status="clean",
                    confidence=1.0,
                    flags=[],
                    summary="Clean",
                )
            },
        )
        output_path = temp_dir / "no_flags.csv"
        exporter = CSVExporter()

        exporter.export_flags(result, output_path)

        # Should not create file if no flags
        assert not output_path.exists()

    def test_export_accepts_string_path(
        self, mixed_pipeline_result: PipelineResult, temp_dir: Path
    ) -> None:
        """Should accept string path."""
        output_path = str(temp_dir / "string_path.csv")
        exporter = CSVExporter()

        exporter.export(mixed_pipeline_result, output_path)

        assert Path(output_path).exists()

    def test_export_clean_sessions(
        self, clean_pipeline_result: PipelineResult, temp_dir: Path
    ) -> None:
        """Should export clean sessions correctly."""
        output_path = temp_dir / "clean.csv"
        exporter = CSVExporter()

        exporter.export(clean_pipeline_result, output_path)

        content = output_path.read_text()
        lines = content.strip().split("\n")

        assert len(lines) == 3  # Header + 2 sessions

        # Both should have clean status
        for line in lines[1:]:
            assert "clean" in line


class TestReporterIntegration:
    """Integration tests for reporting."""

    def test_report_and_export_workflow(
        self, mixed_pipeline_result: PipelineResult, temp_dir: Path
    ) -> None:
        """Should generate text report and CSV exports together."""
        text_reporter = TextReporter()
        csv_exporter = CSVExporter()

        # Generate text report
        report = text_reporter.generate(mixed_pipeline_result)

        # Export CSVs
        csv_exporter.export(mixed_pipeline_result, temp_dir / "summary.csv")
        csv_exporter.export_flags(mixed_pipeline_result, temp_dir / "flags.csv")

        # All outputs should be valid
        assert len(report) > 0
        assert (temp_dir / "summary.csv").exists()
        assert (temp_dir / "flags.csv").exists()
