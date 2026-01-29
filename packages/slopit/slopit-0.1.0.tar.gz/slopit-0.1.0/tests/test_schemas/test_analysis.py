"""Tests for analysis result schemas: AnalysisResult, SessionVerdict, PipelineResult."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from slopit.schemas.analysis import AnalysisResult, PipelineResult, SessionVerdict
from slopit.schemas.flags import AnalysisFlag


class TestAnalysisResult:
    """Tests for AnalysisResult schema."""

    def test_valid_analysis_result(self, sample_analysis_result: AnalysisResult) -> None:
        """Should accept valid analysis result."""
        assert sample_analysis_result.analyzer == "keystroke"
        assert sample_analysis_result.session_id == "session-001"
        assert len(sample_analysis_result.trials) == 1
        assert len(sample_analysis_result.flags) == 1

    def test_analysis_result_empty_trials(self) -> None:
        """Should accept result with no analyzed trials."""
        result = AnalysisResult(
            analyzer="focus",
            session_id="empty-session",
        )
        assert len(result.trials) == 0
        assert len(result.flags) == 0
        assert result.session_summary == {}

    def test_analysis_result_multiple_trials(self, sample_analysis_flag: AnalysisFlag) -> None:
        """Should accept result with multiple trials."""
        result = AnalysisResult(
            analyzer="timing",
            session_id="multi-trial",
            trials=[
                {"trial_id": "t1", "metrics": {"rt": 5000}},
                {"trial_id": "t2", "metrics": {"rt": 8000}},
                {"trial_id": "t3", "metrics": {"rt": 3000}},
            ],
            flags=[sample_analysis_flag],
            session_summary={
                "trials_analyzed": 3,
                "mean_rt": 5333.33,
            },
        )
        assert len(result.trials) == 3

    def test_analysis_result_session_summary(self) -> None:
        """Should accept result with session summary."""
        result = AnalysisResult(
            analyzer="keystroke",
            session_id="summary-session",
            session_summary={
                "trials_analyzed": 5,
                "mean_iki_across_trials": 150.5,
                "total_flags": 2,
                "suspicious_trial_ratio": 0.4,
            },
        )
        assert result.session_summary["trials_analyzed"] == 5

    def test_analysis_result_serialization(
        self, sample_analysis_result: AnalysisResult
    ) -> None:
        """Should serialize and deserialize correctly."""
        data = sample_analysis_result.model_dump()
        restored = AnalysisResult.model_validate(data)
        assert restored.analyzer == sample_analysis_result.analyzer
        assert restored.session_id == sample_analysis_result.session_id


class TestSessionVerdict:
    """Tests for SessionVerdict schema."""

    def test_clean_verdict(self) -> None:
        """Should accept clean verdict."""
        verdict = SessionVerdict(
            status="clean",
            confidence=1.0,
            flags=[],
            summary="No issues detected",
        )
        assert verdict.status == "clean"
        assert verdict.confidence == 1.0
        assert len(verdict.flags) == 0

    def test_suspicious_verdict(self, sample_session_verdict: SessionVerdict) -> None:
        """Should accept suspicious verdict."""
        assert sample_session_verdict.status == "suspicious"
        assert 0.0 <= sample_session_verdict.confidence <= 1.0

    def test_flagged_verdict(self, sample_analysis_flag: AnalysisFlag) -> None:
        """Should accept flagged verdict."""
        verdict = SessionVerdict(
            status="flagged",
            confidence=0.9,
            flags=[sample_analysis_flag],
            summary="High confidence AI assistance detected",
        )
        assert verdict.status == "flagged"
        assert len(verdict.flags) == 1

    def test_verdict_all_statuses(self) -> None:
        """Should accept all valid status values."""
        for status in ["clean", "suspicious", "flagged"]:
            verdict = SessionVerdict(
                status=status,  # type: ignore[arg-type]
                confidence=0.5,
                summary="Test",
            )
            assert verdict.status == status

    def test_verdict_invalid_status(self) -> None:
        """Should reject invalid status."""
        with pytest.raises(ValidationError):
            SessionVerdict(
                status="invalid",  # type: ignore[arg-type]
                confidence=0.5,
                summary="Test",
            )

    def test_verdict_confidence_bounds(self) -> None:
        """Should validate confidence is between 0 and 1."""
        # Valid bounds
        for confidence in [0.0, 0.5, 1.0]:
            verdict = SessionVerdict(
                status="suspicious",
                confidence=confidence,
                summary="Test",
            )
            assert verdict.confidence == confidence

    def test_verdict_confidence_below_zero(self) -> None:
        """Should reject confidence below 0."""
        with pytest.raises(ValidationError):
            SessionVerdict(
                status="flagged",
                confidence=-0.1,
                summary="Test",
            )

    def test_verdict_confidence_above_one(self) -> None:
        """Should reject confidence above 1."""
        with pytest.raises(ValidationError):
            SessionVerdict(
                status="flagged",
                confidence=1.1,
                summary="Test",
            )

    def test_verdict_with_multiple_flags(self) -> None:
        """Should accept verdict with multiple flags."""
        flags = [
            AnalysisFlag(
                type="flag1",
                analyzer="analyzer1",
                severity="medium",
                message="First flag",
            ),
            AnalysisFlag(
                type="flag2",
                analyzer="analyzer2",
                severity="high",
                message="Second flag",
            ),
        ]
        verdict = SessionVerdict(
            status="flagged",
            confidence=0.85,
            flags=flags,
            summary="Multiple issues detected",
        )
        assert len(verdict.flags) == 2

    def test_verdict_serialization(self, sample_session_verdict: SessionVerdict) -> None:
        """Should serialize and deserialize correctly."""
        data = sample_session_verdict.model_dump()
        restored = SessionVerdict.model_validate(data)
        assert restored.status == sample_session_verdict.status
        assert restored.confidence == sample_session_verdict.confidence


class TestPipelineResult:
    """Tests for PipelineResult schema."""

    def test_valid_pipeline_result(self, sample_pipeline_result: PipelineResult) -> None:
        """Should accept valid pipeline result."""
        assert len(sample_pipeline_result.sessions) == 1
        assert "keystroke" in sample_pipeline_result.analyzer_results
        assert "session-001" in sample_pipeline_result.verdicts

    def test_empty_pipeline_result(self) -> None:
        """Should accept empty pipeline result."""
        result = PipelineResult()
        assert len(result.sessions) == 0
        assert len(result.analyzer_results) == 0
        assert len(result.verdicts) == 0

    def test_pipeline_result_multiple_sessions(
        self, sample_analysis_flag: AnalysisFlag
    ) -> None:
        """Should accept result with multiple sessions."""
        result = PipelineResult(
            sessions=["session-001", "session-002", "session-003"],
            analyzer_results={
                "keystroke": [
                    AnalysisResult(analyzer="keystroke", session_id="session-001"),
                    AnalysisResult(analyzer="keystroke", session_id="session-002"),
                    AnalysisResult(analyzer="keystroke", session_id="session-003"),
                ]
            },
            aggregated_flags={
                "session-001": [],
                "session-002": [sample_analysis_flag],
                "session-003": [],
            },
            verdicts={
                "session-001": SessionVerdict(
                    status="clean", confidence=1.0, summary="Clean"
                ),
                "session-002": SessionVerdict(
                    status="suspicious",
                    confidence=0.7,
                    flags=[sample_analysis_flag],
                    summary="Suspicious",
                ),
                "session-003": SessionVerdict(
                    status="clean", confidence=1.0, summary="Clean"
                ),
            },
        )
        assert len(result.sessions) == 3
        assert len(result.verdicts) == 3

    def test_pipeline_result_multiple_analyzers(self) -> None:
        """Should accept result with multiple analyzers."""
        result = PipelineResult(
            sessions=["session-001"],
            analyzer_results={
                "keystroke": [
                    AnalysisResult(analyzer="keystroke", session_id="session-001")
                ],
                "focus": [AnalysisResult(analyzer="focus", session_id="session-001")],
                "timing": [
                    AnalysisResult(analyzer="timing", session_id="session-001")
                ],
                "paste": [AnalysisResult(analyzer="paste", session_id="session-001")],
            },
            verdicts={
                "session-001": SessionVerdict(
                    status="clean", confidence=1.0, summary="Clean"
                )
            },
        )
        assert len(result.analyzer_results) == 4

    def test_pipeline_result_to_dict(self, sample_pipeline_result: PipelineResult) -> None:
        """Should convert to dictionary correctly."""
        data = sample_pipeline_result.to_dict()
        assert "sessions" in data
        assert "analyzer_results" in data
        assert "verdicts" in data

    def test_pipeline_result_serialization(
        self, sample_pipeline_result: PipelineResult
    ) -> None:
        """Should serialize and deserialize correctly."""
        data = sample_pipeline_result.model_dump()
        restored = PipelineResult.model_validate(data)
        assert restored.sessions == sample_pipeline_result.sessions
        assert len(restored.analyzer_results) == len(
            sample_pipeline_result.analyzer_results
        )

    def test_pipeline_result_json_roundtrip(
        self, sample_pipeline_result: PipelineResult
    ) -> None:
        """Should convert to JSON and back correctly."""
        json_str = sample_pipeline_result.model_dump_json()
        restored = PipelineResult.model_validate_json(json_str)
        assert restored.sessions == sample_pipeline_result.sessions
