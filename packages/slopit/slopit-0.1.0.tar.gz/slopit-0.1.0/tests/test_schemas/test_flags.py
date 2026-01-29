"""Tests for flag schemas: CaptureFlag, AnalysisFlag, Severity."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from slopit.schemas import AnalysisFlag, CaptureFlag, Severity


class TestSeverity:
    """Tests for Severity type."""

    def test_valid_severity_values(self) -> None:
        """Should accept all valid severity values."""
        valid: list[Severity] = ["info", "low", "medium", "high"]
        for severity in valid:
            # Create a flag with each severity to validate
            flag = CaptureFlag(
                type="test",
                severity=severity,
                message="Test",
                timestamp=0,
            )
            assert flag.severity == severity


class TestCaptureFlag:
    """Tests for CaptureFlag schema."""

    def test_valid_capture_flag(self, sample_capture_flag: CaptureFlag) -> None:
        """Should accept valid capture flag."""
        assert sample_capture_flag.type == "paste_detected"
        assert sample_capture_flag.severity == "medium"
        assert sample_capture_flag.timestamp > 0

    def test_capture_flag_all_severities(self) -> None:
        """Should accept all severity levels."""
        for severity in ["info", "low", "medium", "high"]:
            flag = CaptureFlag(
                type="test_flag",
                severity=severity,  # type: ignore[arg-type]
                message="Test message",
                timestamp=1704067200000,
            )
            assert flag.severity == severity

    def test_capture_flag_with_details(self) -> None:
        """Should accept capture flag with details."""
        flag = CaptureFlag(
            type="focus_lost",
            severity="low",
            message="Window lost focus for 5 seconds",
            timestamp=1704067200000,
            details={
                "blur_duration_ms": 5000,
                "target_window": "external",
                "is_recurring": True,
            },
        )
        assert flag.details is not None
        assert flag.details["blur_duration_ms"] == 5000

    def test_capture_flag_without_details(self) -> None:
        """Should accept capture flag without details."""
        flag = CaptureFlag(
            type="simple_flag",
            severity="info",
            message="Simple event",
            timestamp=0,
        )
        assert flag.details is None

    def test_capture_flag_invalid_severity(self) -> None:
        """Should reject invalid severity."""
        with pytest.raises(ValidationError):
            CaptureFlag(
                type="test",
                severity="critical",  # type: ignore[arg-type]
                message="Test",
                timestamp=0,
            )

    def test_capture_flag_missing_required(self) -> None:
        """Should reject flag missing required fields."""
        with pytest.raises(ValidationError):
            CaptureFlag(
                type="test",
                # Missing severity, message, timestamp
            )  # type: ignore[call-arg]

    def test_capture_flag_serialization(self, sample_capture_flag: CaptureFlag) -> None:
        """Should serialize and deserialize correctly."""
        data = sample_capture_flag.model_dump()
        restored = CaptureFlag.model_validate(data)
        assert restored.type == sample_capture_flag.type
        assert restored.severity == sample_capture_flag.severity
        assert restored.details == sample_capture_flag.details


class TestAnalysisFlag:
    """Tests for AnalysisFlag schema."""

    def test_valid_analysis_flag(self, sample_analysis_flag: AnalysisFlag) -> None:
        """Should accept valid analysis flag."""
        assert sample_analysis_flag.type == "low_iki_variance"
        assert sample_analysis_flag.analyzer == "keystroke"
        assert sample_analysis_flag.severity == "medium"
        assert sample_analysis_flag.confidence == 0.75

    def test_analysis_flag_all_severities(self) -> None:
        """Should accept all severity levels."""
        for severity in ["info", "low", "medium", "high"]:
            flag = AnalysisFlag(
                type="test_flag",
                analyzer="test_analyzer",
                severity=severity,  # type: ignore[arg-type]
                message="Test message",
            )
            assert flag.severity == severity

    def test_analysis_flag_confidence_bounds(self) -> None:
        """Should accept confidence values between 0 and 1."""
        # Valid confidence values
        for confidence in [0.0, 0.5, 1.0]:
            flag = AnalysisFlag(
                type="test",
                analyzer="test",
                severity="medium",
                message="Test",
                confidence=confidence,
            )
            assert flag.confidence == confidence

    def test_analysis_flag_confidence_below_zero(self) -> None:
        """Should reject confidence below 0."""
        with pytest.raises(ValidationError):
            AnalysisFlag(
                type="test",
                analyzer="test",
                severity="medium",
                message="Test",
                confidence=-0.1,
            )

    def test_analysis_flag_confidence_above_one(self) -> None:
        """Should reject confidence above 1."""
        with pytest.raises(ValidationError):
            AnalysisFlag(
                type="test",
                analyzer="test",
                severity="medium",
                message="Test",
                confidence=1.1,
            )

    def test_analysis_flag_no_confidence(self) -> None:
        """Should accept flag without confidence."""
        flag = AnalysisFlag(
            type="no_confidence",
            analyzer="test",
            severity="low",
            message="No confidence provided",
        )
        assert flag.confidence is None

    def test_analysis_flag_with_evidence(self) -> None:
        """Should accept flag with evidence dictionary."""
        flag = AnalysisFlag(
            type="timing_anomaly",
            analyzer="timing",
            severity="high",
            message="Response too fast",
            confidence=0.9,
            evidence={
                "rt_ms": 500,
                "expected_min_ms": 5000,
                "character_count": 200,
                "words_per_minute": 800,
            },
        )
        assert flag.evidence is not None
        assert flag.evidence["rt_ms"] == 500

    def test_analysis_flag_with_trial_ids(self) -> None:
        """Should accept flag with trial IDs."""
        flag = AnalysisFlag(
            type="multi_trial_issue",
            analyzer="cross_trial",
            severity="medium",
            message="Issue found across trials",
            trial_ids=["trial-001", "trial-003", "trial-007"],
        )
        assert flag.trial_ids is not None
        assert len(flag.trial_ids) == 3

    def test_analysis_flag_session_level(self) -> None:
        """Should accept session-level flag (no trial_ids)."""
        flag = AnalysisFlag(
            type="session_issue",
            analyzer="session",
            severity="medium",
            message="Session-level anomaly",
            trial_ids=None,
        )
        assert flag.trial_ids is None

    def test_analysis_flag_invalid_severity(self) -> None:
        """Should reject invalid severity."""
        with pytest.raises(ValidationError):
            AnalysisFlag(
                type="test",
                analyzer="test",
                severity="invalid",  # type: ignore[arg-type]
                message="Test",
            )

    def test_analysis_flag_missing_required(self) -> None:
        """Should reject flag missing required fields."""
        with pytest.raises(ValidationError):
            AnalysisFlag(
                type="test",
                # Missing analyzer, severity, message
            )  # type: ignore[call-arg]

    def test_analysis_flag_serialization(self, sample_analysis_flag: AnalysisFlag) -> None:
        """Should serialize and deserialize correctly."""
        data = sample_analysis_flag.model_dump()
        restored = AnalysisFlag.model_validate(data)
        assert restored.type == sample_analysis_flag.type
        assert restored.analyzer == sample_analysis_flag.analyzer
        assert restored.confidence == sample_analysis_flag.confidence
        assert restored.trial_ids == sample_analysis_flag.trial_ids

    def test_analysis_flag_json_roundtrip(self) -> None:
        """Should convert to JSON and back correctly."""
        flag = AnalysisFlag(
            type="json_test",
            analyzer="json_analyzer",
            severity="high",
            message="JSON roundtrip test",
            confidence=0.85,
            evidence={"key": "value", "number": 42},
            trial_ids=["t1", "t2"],
        )
        json_str = flag.model_dump_json()
        restored = AnalysisFlag.model_validate_json(json_str)
        assert restored == flag
