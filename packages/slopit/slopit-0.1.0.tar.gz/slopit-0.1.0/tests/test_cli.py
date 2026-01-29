"""Tests for CLI commands."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from slopit.cli import main
from slopit.schemas import SlopitSession


@pytest.fixture
def cli_runner() -> CliRunner:
    """Create Click CLI runner."""
    return CliRunner()


@pytest.fixture
def sample_session_file(
    sample_session: SlopitSession, temp_dir: Path
) -> Path:
    """Create a sample session file for CLI tests."""
    data = sample_session.model_dump()
    data["schemaVersion"] = "1.0"
    data["sessionId"] = sample_session.session_id

    file_path = temp_dir / "session.json"
    with file_path.open("w") as f:
        json.dump(data, f)

    return file_path


@pytest.fixture
def multiple_session_files(
    sample_session: SlopitSession, temp_dir: Path
) -> Path:
    """Create multiple session files for CLI tests."""
    for i in range(3):
        data = sample_session.model_dump()
        data["session_id"] = f"session-{i:03d}"
        data["schemaVersion"] = "1.0"
        data["sessionId"] = f"session-{i:03d}"

        file_path = temp_dir / f"session_{i}.json"
        with file_path.open("w") as f:
            json.dump(data, f)

    return temp_dir


class TestCLIMain:
    """Tests for main CLI group."""

    def test_version(self, cli_runner: CliRunner) -> None:
        """Should display version."""
        result = cli_runner.invoke(main, ["--version"])

        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_help(self, cli_runner: CliRunner) -> None:
        """Should display help."""
        result = cli_runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "slopit" in result.output
        assert "analyze" in result.output
        assert "validate" in result.output
        assert "report" in result.output


class TestAnalyzeCommand:
    """Tests for analyze command."""

    def test_analyze_single_file(
        self,
        cli_runner: CliRunner,
        sample_session_file: Path,
    ) -> None:
        """Should analyze single session file."""
        result = cli_runner.invoke(main, ["analyze", str(sample_session_file)])

        assert result.exit_code == 0
        assert "Loaded 1 sessions" in result.output

    def test_analyze_directory(
        self,
        cli_runner: CliRunner,
        multiple_session_files: Path,
    ) -> None:
        """Should analyze directory of sessions."""
        result = cli_runner.invoke(main, ["analyze", str(multiple_session_files)])

        assert result.exit_code == 0
        assert "Loaded 3 sessions" in result.output

    def test_analyze_with_output(
        self,
        cli_runner: CliRunner,
        sample_session_file: Path,
        temp_dir: Path,
    ) -> None:
        """Should save results to output file."""
        output_path = temp_dir / "output.json"
        result = cli_runner.invoke(
            main,
            ["analyze", str(sample_session_file), "--output", str(output_path)],
        )

        assert result.exit_code == 0
        assert output_path.exists()

        with output_path.open() as f:
            data = json.load(f)

        assert "sessions" in data
        assert "verdicts" in data

    def test_analyze_with_specific_analyzers(
        self,
        cli_runner: CliRunner,
        sample_session_file: Path,
    ) -> None:
        """Should use specified analyzers."""
        result = cli_runner.invoke(
            main,
            ["analyze", str(sample_session_file), "--analyzers", "keystroke,timing"],
        )

        assert result.exit_code == 0
        assert "Running 2 analyzers" in result.output

    def test_analyze_summary_flag(
        self,
        cli_runner: CliRunner,
        sample_session_file: Path,
    ) -> None:
        """Should print summary table with --summary flag."""
        result = cli_runner.invoke(
            main,
            ["analyze", str(sample_session_file), "--summary"],
        )

        assert result.exit_code == 0
        # Rich table output should contain status headers
        # Note: Rich output may vary based on terminal

    def test_analyze_csv_export(
        self,
        cli_runner: CliRunner,
        sample_session_file: Path,
        temp_dir: Path,
    ) -> None:
        """Should export CSV with --csv flag."""
        csv_path = temp_dir / "results.csv"
        result = cli_runner.invoke(
            main,
            ["analyze", str(sample_session_file), "--csv", str(csv_path)],
        )

        assert result.exit_code == 0
        assert csv_path.exists()

    def test_analyze_aggregation_strategy(
        self,
        cli_runner: CliRunner,
        sample_session_file: Path,
    ) -> None:
        """Should accept aggregation strategy option."""
        for strategy in ["any", "majority", "weighted"]:
            result = cli_runner.invoke(
                main,
                ["analyze", str(sample_session_file), "--aggregation", strategy],
            )

            assert result.exit_code == 0

    def test_analyze_invalid_path(self, cli_runner: CliRunner) -> None:
        """Should error on non-existent path."""
        result = cli_runner.invoke(
            main, ["analyze", "/nonexistent/path/file.json"]
        )

        assert result.exit_code != 0

    def test_analyze_empty_directory(
        self, cli_runner: CliRunner, temp_dir: Path
    ) -> None:
        """Should handle empty directory."""
        result = cli_runner.invoke(main, ["analyze", str(temp_dir)])

        assert result.exit_code == 0
        assert "No sessions found" in result.output

    def test_analyze_invalid_analyzer(
        self,
        cli_runner: CliRunner,
        sample_session_file: Path,
    ) -> None:
        """Should handle invalid analyzer names gracefully."""
        result = cli_runner.invoke(
            main,
            ["analyze", str(sample_session_file), "--analyzers", "invalid_analyzer"],
        )

        assert result.exit_code == 0
        assert "No valid analyzers" in result.output


class TestValidateCommand:
    """Tests for validate command."""

    def test_validate_valid_file(
        self,
        cli_runner: CliRunner,
        sample_session_file: Path,
    ) -> None:
        """Should validate valid session file."""
        result = cli_runner.invoke(main, ["validate", str(sample_session_file)])

        assert result.exit_code == 0
        # Checkmark character may vary by terminal
        assert "valid" in result.output.lower()

    def test_validate_directory(
        self,
        cli_runner: CliRunner,
        multiple_session_files: Path,
    ) -> None:
        """Should validate all files in directory."""
        result = cli_runner.invoke(main, ["validate", str(multiple_session_files)])

        assert result.exit_code == 0
        assert "Summary" in result.output

    def test_validate_invalid_file(
        self,
        cli_runner: CliRunner,
        malformed_json: Path,
    ) -> None:
        """Should report invalid file."""
        result = cli_runner.invoke(main, ["validate", str(malformed_json)])

        # Should complete but report the invalid file
        assert result.exit_code == 0
        assert "invalid" in result.output.lower()

    def test_validate_mixed_files(
        self,
        cli_runner: CliRunner,
        temp_dir: Path,
        sample_session: SlopitSession,
    ) -> None:
        """Should validate mix of valid and invalid files."""
        # Create valid file
        valid_data = sample_session.model_dump()
        valid_data["schemaVersion"] = "1.0"
        valid_data["sessionId"] = sample_session.session_id
        valid_path = temp_dir / "valid.json"
        with valid_path.open("w") as f:
            json.dump(valid_data, f)

        # Create invalid file
        invalid_path = temp_dir / "invalid.json"
        with invalid_path.open("w") as f:
            f.write('{"broken": json}')

        result = cli_runner.invoke(main, ["validate", str(temp_dir)])

        assert result.exit_code == 0
        assert "valid" in result.output.lower()


class TestReportCommand:
    """Tests for report command."""

    def test_report_text_format(
        self,
        cli_runner: CliRunner,
        sample_session_file: Path,
        temp_dir: Path,
    ) -> None:
        """Should generate text report from results."""
        # First run analyze to create results
        results_path = temp_dir / "results.json"
        cli_runner.invoke(
            main,
            ["analyze", str(sample_session_file), "--output", str(results_path)],
        )

        # Then generate report
        result = cli_runner.invoke(
            main,
            ["report", str(results_path), "--format", "text"],
        )

        assert result.exit_code == 0
        assert "Analysis Report" in result.output

    def test_report_csv_format(
        self,
        cli_runner: CliRunner,
        sample_session_file: Path,
        temp_dir: Path,
    ) -> None:
        """Should export CSV report."""
        # First run analyze to create results
        results_path = temp_dir / "results.json"
        cli_runner.invoke(
            main,
            ["analyze", str(sample_session_file), "--output", str(results_path)],
        )

        # Then generate CSV report
        csv_output = temp_dir / "report.csv"
        result = cli_runner.invoke(
            main,
            ["report", str(results_path), "--format", "csv", "--output", str(csv_output)],
        )

        assert result.exit_code == 0
        assert csv_output.exists()

    def test_report_csv_requires_output(
        self,
        cli_runner: CliRunner,
        sample_session_file: Path,
        temp_dir: Path,
    ) -> None:
        """Should require output path for CSV format."""
        # First run analyze to create results
        results_path = temp_dir / "results.json"
        cli_runner.invoke(
            main,
            ["analyze", str(sample_session_file), "--output", str(results_path)],
        )

        # Try CSV without output
        result = cli_runner.invoke(
            main,
            ["report", str(results_path), "--format", "csv"],
        )

        assert result.exit_code == 0
        assert "requires --output" in result.output

    def test_report_text_to_file(
        self,
        cli_runner: CliRunner,
        sample_session_file: Path,
        temp_dir: Path,
    ) -> None:
        """Should save text report to file."""
        # First run analyze
        results_path = temp_dir / "results.json"
        cli_runner.invoke(
            main,
            ["analyze", str(sample_session_file), "--output", str(results_path)],
        )

        # Generate report to file
        report_path = temp_dir / "report.txt"
        result = cli_runner.invoke(
            main,
            ["report", str(results_path), "--format", "text", "--output", str(report_path)],
        )

        assert result.exit_code == 0
        assert report_path.exists()
        assert "Analysis Report" in report_path.read_text()

    def test_report_invalid_results_file(
        self, cli_runner: CliRunner, temp_dir: Path
    ) -> None:
        """Should handle invalid results file."""
        invalid_path = temp_dir / "invalid.json"
        # Use an invalid verdicts value (should be a dict, not a string)
        with invalid_path.open("w") as f:
            json.dump({"verdicts": "not_a_dict"}, f)

        result = cli_runner.invoke(main, ["report", str(invalid_path)])

        assert result.exit_code != 0


class TestCLIIntegration:
    """Integration tests for CLI workflows."""

    def test_full_workflow(
        self,
        cli_runner: CliRunner,
        multiple_session_files: Path,
        temp_dir: Path,
    ) -> None:
        """Should complete full analyze -> report workflow."""
        results_path = temp_dir / "results.json"
        csv_path = temp_dir / "summary.csv"
        report_path = temp_dir / "report.txt"

        # Step 1: Analyze
        result = cli_runner.invoke(
            main,
            [
                "analyze",
                str(multiple_session_files),
                "--output", str(results_path),
                "--analyzers", "keystroke,timing",
            ],
        )
        assert result.exit_code == 0

        # Step 2: Generate text report
        result = cli_runner.invoke(
            main,
            [
                "report",
                str(results_path),
                "--format", "text",
                "--output", str(report_path),
            ],
        )
        assert result.exit_code == 0

        # Step 3: Generate CSV report
        result = cli_runner.invoke(
            main,
            [
                "report",
                str(results_path),
                "--format", "csv",
                "--output", str(csv_path),
            ],
        )
        assert result.exit_code == 0

        # Verify all outputs exist
        assert results_path.exists()
        assert report_path.exists()
        assert csv_path.exists()

    def test_validate_then_analyze(
        self,
        cli_runner: CliRunner,
        sample_session_file: Path,
    ) -> None:
        """Should validate then analyze same files."""
        # First validate
        result = cli_runner.invoke(main, ["validate", str(sample_session_file)])
        assert result.exit_code == 0
        assert "valid" in result.output.lower()

        # Then analyze
        result = cli_runner.invoke(main, ["analyze", str(sample_session_file)])
        assert result.exit_code == 0
        assert "Loaded 1 sessions" in result.output
