"""Tests for AnalysisPipeline."""

from __future__ import annotations

import pytest

from slopit.behavioral import (
    FocusAnalyzer,
    KeystrokeAnalyzer,
    PasteAnalyzer,
    TimingAnalyzer,
)
from slopit.pipeline import AnalysisPipeline, PipelineConfig
from slopit.schemas import SlopitSession


class TestPipelineConfig:
    """Tests for PipelineConfig."""

    def test_default_config(self) -> None:
        """Should have sensible defaults."""
        config = PipelineConfig()
        assert config.aggregation == "weighted"
        assert config.severity_threshold == "low"
        assert config.confidence_threshold == 0.5

    def test_custom_config(self) -> None:
        """Should accept custom values."""
        config = PipelineConfig(
            aggregation="any",
            severity_threshold="medium",
            confidence_threshold=0.7,
        )
        assert config.aggregation == "any"
        assert config.severity_threshold == "medium"
        assert config.confidence_threshold == 0.7


class TestAnalysisPipeline:
    """Tests for AnalysisPipeline."""

    def test_pipeline_with_single_analyzer(
        self, session_with_sufficient_keystrokes: SlopitSession
    ) -> None:
        """Should run with a single analyzer."""
        from slopit.behavioral import KeystrokeAnalyzerConfig

        config = KeystrokeAnalyzerConfig(min_keystrokes=10)
        analyzer = KeystrokeAnalyzer(config)
        pipeline = AnalysisPipeline([analyzer])

        result = pipeline.analyze([session_with_sufficient_keystrokes])

        assert len(result.sessions) == 1
        assert "keystroke" in result.analyzer_results
        assert session_with_sufficient_keystrokes.session_id in result.verdicts

    def test_pipeline_with_multiple_analyzers(
        self, session_with_suspicious_patterns: SlopitSession
    ) -> None:
        """Should run with multiple analyzers."""
        analyzers = [
            KeystrokeAnalyzer(),
            FocusAnalyzer(),
            TimingAnalyzer(),
            PasteAnalyzer(),
        ]
        pipeline = AnalysisPipeline(analyzers)

        result = pipeline.analyze([session_with_suspicious_patterns])

        assert len(result.analyzer_results) == 4
        assert "keystroke" in result.analyzer_results
        assert "focus" in result.analyzer_results
        assert "timing" in result.analyzer_results
        assert "paste" in result.analyzer_results

    def test_pipeline_multiple_sessions(
        self,
        sample_session: SlopitSession,
        session_with_sufficient_keystrokes: SlopitSession,
    ) -> None:
        """Should analyze multiple sessions."""
        pipeline = AnalysisPipeline([TimingAnalyzer()])

        result = pipeline.analyze([sample_session, session_with_sufficient_keystrokes])

        assert len(result.sessions) == 2
        assert len(result.verdicts) == 2

    def test_pipeline_empty_sessions(self) -> None:
        """Should handle empty session list."""
        pipeline = AnalysisPipeline([KeystrokeAnalyzer()])

        result = pipeline.analyze([])

        assert len(result.sessions) == 0
        assert len(result.verdicts) == 0

    def test_pipeline_clean_verdict(self, sample_session: SlopitSession) -> None:
        """Should produce clean verdict when no flags."""
        # sample_session has minimal data that won't trigger flags
        pipeline = AnalysisPipeline([TimingAnalyzer()])

        result = pipeline.analyze([sample_session])
        verdict = result.verdicts[sample_session.session_id]

        assert verdict.status == "clean"
        assert verdict.confidence == 1.0
        assert len(verdict.flags) == 0

    def test_pipeline_flagged_verdict(
        self, session_with_suspicious_patterns: SlopitSession
    ) -> None:
        """Should produce flagged verdict when many issues."""
        from slopit.behavioral import (
            FocusAnalyzerConfig,
            KeystrokeAnalyzerConfig,
            PasteAnalyzerConfig,
        )

        # Configure analyzers with lower thresholds to ensure flags
        analyzers = [
            KeystrokeAnalyzer(KeystrokeAnalyzerConfig(min_keystrokes=20)),
            FocusAnalyzer(FocusAnalyzerConfig(max_blur_count=3)),
            PasteAnalyzer(PasteAnalyzerConfig(large_paste_threshold=50)),
        ]
        pipeline = AnalysisPipeline(analyzers)

        result = pipeline.analyze([session_with_suspicious_patterns])
        verdict = result.verdicts[session_with_suspicious_patterns.session_id]

        # Should have some flags
        assert len(verdict.flags) > 0

    def test_pipeline_custom_config(
        self, session_with_suspicious_patterns: SlopitSession
    ) -> None:
        """Should use custom pipeline config."""
        config = PipelineConfig(
            aggregation="any",
            severity_threshold="high",
            confidence_threshold=0.8,
        )
        pipeline = AnalysisPipeline([KeystrokeAnalyzer()], config)

        result = pipeline.analyze([session_with_suspicious_patterns])

        # Config should be applied
        assert pipeline.config.aggregation == "any"

    def test_filter_flags_by_severity(
        self, session_with_suspicious_patterns: SlopitSession
    ) -> None:
        """Should filter flags by severity threshold."""
        config = PipelineConfig(severity_threshold="high")
        pipeline = AnalysisPipeline([KeystrokeAnalyzer()], config)

        result = pipeline.analyze([session_with_suspicious_patterns])

        # Only high severity flags should remain
        for flag in result.aggregated_flags.get(
            session_with_suspicious_patterns.session_id, []
        ):
            assert flag.severity == "high"

    def test_filter_flags_by_confidence(
        self, session_with_suspicious_patterns: SlopitSession
    ) -> None:
        """Should filter flags by confidence threshold."""
        config = PipelineConfig(confidence_threshold=0.9)
        pipeline = AnalysisPipeline([KeystrokeAnalyzer()], config)

        result = pipeline.analyze([session_with_suspicious_patterns])

        # Only high confidence flags should remain
        for flag in result.aggregated_flags.get(
            session_with_suspicious_patterns.session_id, []
        ):
            assert flag.confidence is None or flag.confidence >= 0.9

    def test_verdict_summary_generation(
        self, session_with_suspicious_patterns: SlopitSession
    ) -> None:
        """Should generate human-readable summary."""
        from slopit.behavioral import FocusAnalyzerConfig

        config = FocusAnalyzerConfig(max_blur_count=3)
        pipeline = AnalysisPipeline([FocusAnalyzer(config)])

        result = pipeline.analyze([session_with_suspicious_patterns])
        verdict = result.verdicts[session_with_suspicious_patterns.session_id]

        if verdict.flags:
            assert "Detected:" in verdict.summary
        else:
            assert verdict.summary == "No flags detected"

    def test_analyzer_results_structure(
        self, sample_session: SlopitSession
    ) -> None:
        """Should organize analyzer results correctly."""
        analyzers = [KeystrokeAnalyzer(), FocusAnalyzer()]
        pipeline = AnalysisPipeline(analyzers)

        result = pipeline.analyze([sample_session])

        # Each analyzer should have a list of results
        for analyzer_name, results in result.analyzer_results.items():
            assert isinstance(results, list)
            for r in results:
                assert r.analyzer == analyzer_name

    def test_aggregated_flags_per_session(
        self,
        sample_session: SlopitSession,
        session_with_suspicious_patterns: SlopitSession,
    ) -> None:
        """Should aggregate flags per session."""
        from slopit.behavioral import FocusAnalyzerConfig

        config = FocusAnalyzerConfig(max_blur_count=3)
        pipeline = AnalysisPipeline([FocusAnalyzer(config)])

        result = pipeline.analyze([sample_session, session_with_suspicious_patterns])

        # Each session should have its own flag list
        assert sample_session.session_id in result.aggregated_flags
        assert session_with_suspicious_patterns.session_id in result.aggregated_flags


class TestPipelineIntegration:
    """Integration tests for the analysis pipeline."""

    def test_full_pipeline_workflow(
        self, session_with_suspicious_patterns: SlopitSession
    ) -> None:
        """Should run complete analysis workflow."""
        from slopit.behavioral import FocusAnalyzerConfig

        # Set up pipeline with all analyzers
        analyzers = [
            KeystrokeAnalyzer(),
            FocusAnalyzer(FocusAnalyzerConfig(max_blur_count=3)),
            TimingAnalyzer(),
            PasteAnalyzer(),
        ]
        config = PipelineConfig(
            aggregation="weighted",
            severity_threshold="low",
            confidence_threshold=0.5,
        )
        pipeline = AnalysisPipeline(analyzers, config)

        # Run analysis
        result = pipeline.analyze([session_with_suspicious_patterns])

        # Verify complete result structure
        assert len(result.sessions) == 1
        assert len(result.analyzer_results) == 4
        assert session_with_suspicious_patterns.session_id in result.verdicts

        # Verify verdict structure
        verdict = result.verdicts[session_with_suspicious_patterns.session_id]
        assert verdict.status in ["clean", "suspicious", "flagged"]
        assert 0.0 <= verdict.confidence <= 1.0
        assert isinstance(verdict.summary, str)

    def test_pipeline_result_to_dict(
        self, sample_session: SlopitSession
    ) -> None:
        """Should convert result to dictionary."""
        pipeline = AnalysisPipeline([TimingAnalyzer()])
        result = pipeline.analyze([sample_session])

        data = result.to_dict()

        assert "sessions" in data
        assert "analyzer_results" in data
        assert "aggregated_flags" in data
        assert "verdicts" in data
