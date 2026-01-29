"""Tests for flag aggregation strategies."""

from __future__ import annotations

import pytest

from slopit.pipeline.aggregation import (
    aggregate_flags,
    _aggregate_any,
    _aggregate_majority,
    _aggregate_weighted,
)
from slopit.schemas.flags import AnalysisFlag


@pytest.fixture
def single_flag() -> list[AnalysisFlag]:
    """Single flag with medium confidence."""
    return [
        AnalysisFlag(
            type="test_flag",
            analyzer="test",
            severity="medium",
            message="Test flag",
            confidence=0.6,
        )
    ]


@pytest.fixture
def multiple_flags_same_analyzer() -> list[AnalysisFlag]:
    """Multiple flags from same analyzer."""
    return [
        AnalysisFlag(
            type="flag1",
            analyzer="keystroke",
            severity="medium",
            message="Flag 1",
            confidence=0.7,
        ),
        AnalysisFlag(
            type="flag2",
            analyzer="keystroke",
            severity="high",
            message="Flag 2",
            confidence=0.9,
        ),
    ]


@pytest.fixture
def multiple_flags_different_analyzers() -> list[AnalysisFlag]:
    """Flags from different analyzers."""
    return [
        AnalysisFlag(
            type="flag1",
            analyzer="keystroke",
            severity="medium",
            message="Keystroke flag",
            confidence=0.7,
        ),
        AnalysisFlag(
            type="flag2",
            analyzer="focus",
            severity="high",
            message="Focus flag",
            confidence=0.8,
        ),
        AnalysisFlag(
            type="flag3",
            analyzer="timing",
            severity="medium",
            message="Timing flag",
            confidence=0.6,
        ),
    ]


@pytest.fixture
def low_confidence_flags() -> list[AnalysisFlag]:
    """Flags with low confidence scores."""
    return [
        AnalysisFlag(
            type="flag1",
            analyzer="test",
            severity="medium",
            message="Low confidence flag",
            confidence=0.3,
        ),
        AnalysisFlag(
            type="flag2",
            analyzer="test2",
            severity="low",
            message="Another low confidence",
            confidence=0.2,
        ),
    ]


class TestAggregateFlags:
    """Tests for aggregate_flags function."""

    def test_empty_flags(self) -> None:
        """Should return clean status for no flags."""
        status, confidence = aggregate_flags([], "any", 4)

        assert status == "clean"
        assert confidence == 1.0

    def test_any_strategy(self, single_flag: list[AnalysisFlag]) -> None:
        """Should use 'any' strategy."""
        status, confidence = aggregate_flags(single_flag, "any", 4)

        assert status == "flagged"
        assert confidence == 0.6

    def test_majority_strategy(
        self, multiple_flags_different_analyzers: list[AnalysisFlag]
    ) -> None:
        """Should use 'majority' strategy."""
        # 3 analyzers flagged out of 4 total (majority)
        status, confidence = aggregate_flags(
            multiple_flags_different_analyzers, "majority", 4
        )

        assert status == "flagged"

    def test_weighted_strategy(
        self, multiple_flags_different_analyzers: list[AnalysisFlag]
    ) -> None:
        """Should use 'weighted' strategy."""
        status, confidence = aggregate_flags(
            multiple_flags_different_analyzers, "weighted", 4
        )

        # Average confidence: (0.7 + 0.8 + 0.6) / 3 = 0.7
        assert confidence == pytest.approx(0.7, rel=0.01)


class TestAggregateAny:
    """Tests for _aggregate_any function."""

    def test_any_with_flags(self, single_flag: list[AnalysisFlag]) -> None:
        """Should return flagged with max confidence."""
        status, confidence = _aggregate_any(single_flag)

        assert status == "flagged"
        assert confidence == 0.6

    def test_any_max_confidence(
        self, multiple_flags_different_analyzers: list[AnalysisFlag]
    ) -> None:
        """Should use maximum confidence value."""
        status, confidence = _aggregate_any(multiple_flags_different_analyzers)

        assert status == "flagged"
        assert confidence == 0.8  # Max of 0.7, 0.8, 0.6

    def test_any_with_none_confidence(self) -> None:
        """Should use default 0.5 for None confidence."""
        flags = [
            AnalysisFlag(
                type="test",
                analyzer="test",
                severity="medium",
                message="No confidence",
                confidence=None,
            )
        ]
        status, confidence = _aggregate_any(flags)

        assert confidence == 0.5


class TestAggregateMajority:
    """Tests for _aggregate_majority function."""

    def test_majority_flagged(
        self, multiple_flags_different_analyzers: list[AnalysisFlag]
    ) -> None:
        """Should return flagged when majority of analyzers flag."""
        # 3 unique analyzers out of 4 total
        status, confidence = _aggregate_majority(
            multiple_flags_different_analyzers, 4
        )

        assert status == "flagged"
        assert confidence == 0.75  # 3/4 = 0.75

    def test_minority_suspicious(
        self, single_flag: list[AnalysisFlag]
    ) -> None:
        """Should return suspicious when minority flag."""
        # 1 analyzer out of 4 total
        status, confidence = _aggregate_majority(single_flag, 4)

        assert status == "suspicious"
        assert confidence == 0.25  # 1/4 = 0.25

    def test_no_analyzers(self, single_flag: list[AnalysisFlag]) -> None:
        """Should handle zero total analyzers."""
        status, confidence = _aggregate_majority(single_flag, 0)

        assert status == "suspicious"
        assert confidence == 0

    def test_exactly_half(self) -> None:
        """Should return suspicious when exactly half flag."""
        flags = [
            AnalysisFlag(
                type="flag1",
                analyzer="analyzer1",
                severity="medium",
                message="Flag 1",
            ),
            AnalysisFlag(
                type="flag2",
                analyzer="analyzer2",
                severity="medium",
                message="Flag 2",
            ),
        ]
        # 2 analyzers out of 4 = exactly half
        status, confidence = _aggregate_majority(flags, 4)

        assert status == "suspicious"  # Half is not majority

    def test_more_than_half(self) -> None:
        """Should return flagged when more than half flag."""
        flags = [
            AnalysisFlag(
                type="flag1",
                analyzer="analyzer1",
                severity="medium",
                message="Flag 1",
            ),
            AnalysisFlag(
                type="flag2",
                analyzer="analyzer2",
                severity="medium",
                message="Flag 2",
            ),
            AnalysisFlag(
                type="flag3",
                analyzer="analyzer3",
                severity="medium",
                message="Flag 3",
            ),
        ]
        # 3 analyzers out of 4 = more than half
        status, confidence = _aggregate_majority(flags, 4)

        assert status == "flagged"

    def test_same_analyzer_multiple_flags(
        self, multiple_flags_same_analyzer: list[AnalysisFlag]
    ) -> None:
        """Should count unique analyzers, not total flags."""
        # 2 flags from same analyzer = 1 unique analyzer
        status, confidence = _aggregate_majority(
            multiple_flags_same_analyzer, 4
        )

        assert status == "suspicious"
        assert confidence == 0.25  # 1/4


class TestAggregateWeighted:
    """Tests for _aggregate_weighted function."""

    def test_high_confidence_flagged(
        self, multiple_flags_different_analyzers: list[AnalysisFlag]
    ) -> None:
        """Should return flagged for high average confidence."""
        status, confidence = _aggregate_weighted(multiple_flags_different_analyzers)

        # Average: (0.7 + 0.8 + 0.6) / 3 = 0.7
        assert status == "flagged"  # >= 0.7
        assert confidence == pytest.approx(0.7, rel=0.01)

    def test_medium_confidence_suspicious(
        self, low_confidence_flags: list[AnalysisFlag]
    ) -> None:
        """Should return suspicious for medium average confidence."""
        # Create flags with medium confidence
        flags = [
            AnalysisFlag(
                type="flag1",
                analyzer="test1",
                severity="medium",
                message="Flag 1",
                confidence=0.5,
            ),
            AnalysisFlag(
                type="flag2",
                analyzer="test2",
                severity="medium",
                message="Flag 2",
                confidence=0.5,
            ),
        ]
        status, confidence = _aggregate_weighted(flags)

        # Average: 0.5, which is >= 0.4 but < 0.7
        assert status == "suspicious"
        assert confidence == 0.5

    def test_low_confidence_clean(
        self, low_confidence_flags: list[AnalysisFlag]
    ) -> None:
        """Should return clean for low average confidence."""
        status, confidence = _aggregate_weighted(low_confidence_flags)

        # Average: (0.3 + 0.2) / 2 = 0.25
        assert status == "clean"  # < 0.4
        assert confidence == pytest.approx(0.75, rel=0.01)  # 1 - 0.25

    def test_none_confidence_default(self) -> None:
        """Should use 0.5 default for None confidence."""
        flags = [
            AnalysisFlag(
                type="flag1",
                analyzer="test",
                severity="medium",
                message="No confidence",
                confidence=None,
            ),
            AnalysisFlag(
                type="flag2",
                analyzer="test2",
                severity="medium",
                message="Has confidence",
                confidence=0.9,
            ),
        ]
        status, confidence = _aggregate_weighted(flags)

        # Average: (0.5 + 0.9) / 2 = 0.7
        assert status == "flagged"
        assert confidence == pytest.approx(0.7, rel=0.01)

    def test_threshold_boundaries(self) -> None:
        """Should handle threshold boundaries correctly."""
        # Exactly 0.7 should be flagged
        flags_70 = [
            AnalysisFlag(
                type="flag1",
                analyzer="test",
                severity="medium",
                message="70% confidence",
                confidence=0.7,
            )
        ]
        status, _ = _aggregate_weighted(flags_70)
        assert status == "flagged"

        # Exactly 0.4 should be suspicious
        flags_40 = [
            AnalysisFlag(
                type="flag1",
                analyzer="test",
                severity="medium",
                message="40% confidence",
                confidence=0.4,
            )
        ]
        status, _ = _aggregate_weighted(flags_40)
        assert status == "suspicious"

        # Just below 0.4 should be clean
        flags_39 = [
            AnalysisFlag(
                type="flag1",
                analyzer="test",
                severity="medium",
                message="39% confidence",
                confidence=0.39,
            )
        ]
        status, _ = _aggregate_weighted(flags_39)
        assert status == "clean"
