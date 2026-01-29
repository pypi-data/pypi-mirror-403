"""Tests for TimingAnalyzer."""

from __future__ import annotations

import pytest

from slopit.behavioral import TimingAnalyzer, TimingAnalyzerConfig
from slopit.schemas import (
    BehavioralData,
    EnvironmentInfo,
    GlobalEvents,
    PlatformInfo,
    ResponseInfo,
    SessionTiming,
    SlopitSession,
    SlopitTrial,
)


class TestTimingAnalyzerConfig:
    """Tests for TimingAnalyzerConfig."""

    def test_default_config(self) -> None:
        """Should have sensible defaults."""
        config = TimingAnalyzerConfig()
        assert config.min_rt_per_char_ms == 20.0
        assert config.max_rt_cv_threshold == 0.1
        assert config.instant_response_threshold_ms == 2000.0
        assert config.instant_response_min_chars == 100

    def test_custom_config(self) -> None:
        """Should accept custom values."""
        config = TimingAnalyzerConfig(
            min_rt_per_char_ms=30.0,
            instant_response_threshold_ms=3000.0,
        )
        assert config.min_rt_per_char_ms == 30.0
        assert config.instant_response_threshold_ms == 3000.0


class TestTimingAnalyzer:
    """Tests for TimingAnalyzer."""

    def test_analyzer_name(self) -> None:
        """Should have correct name."""
        analyzer = TimingAnalyzer()
        assert analyzer.name == "timing"

    def test_default_config(self) -> None:
        """Should use default config when none provided."""
        analyzer = TimingAnalyzer()
        assert analyzer.config.min_rt_per_char_ms == 20.0

    def test_custom_config(self) -> None:
        """Should accept custom config."""
        config = TimingAnalyzerConfig(min_rt_per_char_ms=50.0)
        analyzer = TimingAnalyzer(config)
        assert analyzer.config.min_rt_per_char_ms == 50.0

    def test_analyze_session_no_rt(
        self,
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should skip trials without RT."""
        trial = SlopitTrial(
            trial_id="no-rt",
            trial_index=0,
            start_time=0,
            end_time=5000,
            rt=None,  # No RT
        )
        session = SlopitSession(
            session_id="no-rt-session",
            platform=sample_platform_info,
            environment=sample_environment_info,
            timing=sample_session_timing,
            trials=[trial],
            global_events=sample_global_events,
        )

        analyzer = TimingAnalyzer()
        result = analyzer.analyze_session(session)

        assert len(result.trials) == 0

    def test_analyze_session_with_rt(
        self,
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should analyze trials with RT."""
        trial = SlopitTrial(
            trial_id="with-rt",
            trial_index=0,
            start_time=0,
            end_time=5000,
            rt=5000,
            response=ResponseInfo(type="text", value="Test response", character_count=13),
        )
        session = SlopitSession(
            session_id="rt-session",
            platform=sample_platform_info,
            environment=sample_environment_info,
            timing=sample_session_timing,
            trials=[trial],
            global_events=sample_global_events,
        )

        analyzer = TimingAnalyzer()
        result = analyzer.analyze_session(session)

        assert len(result.trials) == 1
        assert "metrics" in result.trials[0]

    def test_compute_trial_metrics(
        self,
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should compute trial metrics correctly."""
        trial = SlopitTrial(
            trial_id="metrics-trial",
            trial_index=0,
            start_time=0,
            end_time=30000,
            rt=30000,
            response=ResponseInfo(
                type="text",
                value="This is a test response with some words",
                character_count=40,
            ),
        )

        analyzer = TimingAnalyzer()
        metrics = analyzer._compute_trial_metrics(trial)

        assert metrics.rt == 30000
        assert metrics.character_count == 40
        assert metrics.ms_per_char == pytest.approx(750.0)  # 30000 / 40
        assert metrics.chars_per_minute == pytest.approx(80.0)  # 40 / 0.5 min

    def test_instant_response_flag(
        self,
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should flag instant response with many characters."""
        trial = SlopitTrial(
            trial_id="instant-trial",
            trial_index=0,
            start_time=0,
            end_time=1500,
            rt=1500,  # 1.5 seconds
            response=ResponseInfo(
                type="text",
                value="x" * 150,  # 150 characters in 1.5 seconds
                character_count=150,
            ),
        )
        session = SlopitSession(
            session_id="instant-session",
            platform=sample_platform_info,
            environment=sample_environment_info,
            timing=sample_session_timing,
            trials=[trial],
            global_events=sample_global_events,
        )

        config = TimingAnalyzerConfig(
            instant_response_threshold_ms=2000.0,
            instant_response_min_chars=100,
        )
        analyzer = TimingAnalyzer(config)
        result = analyzer.analyze_session(session)

        flag_types = {f.type for f in result.flags}
        assert "instant_response" in flag_types

    def test_fast_typing_flag(
        self,
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should flag unrealistically fast typing speed."""
        trial = SlopitTrial(
            trial_id="fast-trial",
            trial_index=0,
            start_time=0,
            end_time=1000,
            rt=1000,  # 1 second
            response=ResponseInfo(
                type="text",
                value="x" * 100,  # 100 chars in 1 second = 10ms/char
                character_count=100,
            ),
        )
        session = SlopitSession(
            session_id="fast-session",
            platform=sample_platform_info,
            environment=sample_environment_info,
            timing=sample_session_timing,
            trials=[trial],
            global_events=sample_global_events,
        )

        config = TimingAnalyzerConfig(min_rt_per_char_ms=20.0)
        analyzer = TimingAnalyzer(config)
        result = analyzer.analyze_session(session)

        flag_types = {f.type for f in result.flags}
        assert "fast_typing" in flag_types

    def test_consistent_timing_flag(
        self,
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should flag suspiciously consistent timing across trials."""
        # Create multiple trials with very similar RT
        trials = [
            SlopitTrial(
                trial_id=f"consistent-{i}",
                trial_index=i,
                start_time=i * 10000,
                end_time=(i + 1) * 10000,
                rt=10000 + (i % 2) * 50,  # RT varies by only 50ms (0.5% CV)
            )
            for i in range(5)
        ]

        session = SlopitSession(
            session_id="consistent-session",
            platform=sample_platform_info,
            environment=sample_environment_info,
            timing=sample_session_timing,
            trials=trials,
            global_events=sample_global_events,
        )

        config = TimingAnalyzerConfig(max_rt_cv_threshold=0.1)
        analyzer = TimingAnalyzer(config)
        result = analyzer.analyze_session(session)

        flag_types = {f.type for f in result.flags}
        assert "consistent_timing" in flag_types

    def test_variable_timing_no_flag(
        self,
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should not flag naturally variable timing."""
        # Create trials with variable RT
        trials = [
            SlopitTrial(
                trial_id=f"variable-{i}",
                trial_index=i,
                start_time=i * 20000,
                end_time=(i + 1) * 20000,
                rt=rt,
            )
            for i, rt in enumerate([5000, 15000, 8000, 25000, 12000])
        ]

        session = SlopitSession(
            session_id="variable-session",
            platform=sample_platform_info,
            environment=sample_environment_info,
            timing=sample_session_timing,
            trials=trials,
            global_events=sample_global_events,
        )

        analyzer = TimingAnalyzer()
        result = analyzer.analyze_session(session)

        flag_types = {f.type for f in result.flags}
        assert "consistent_timing" not in flag_types

    def test_no_consistency_check_few_trials(
        self,
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should not check consistency with fewer than 3 trials."""
        trials = [
            SlopitTrial(
                trial_id=f"few-{i}",
                trial_index=i,
                start_time=i * 10000,
                end_time=(i + 1) * 10000,
                rt=10000,  # Identical RT
            )
            for i in range(2)  # Only 2 trials
        ]

        session = SlopitSession(
            session_id="few-trials-session",
            platform=sample_platform_info,
            environment=sample_environment_info,
            timing=sample_session_timing,
            trials=trials,
            global_events=sample_global_events,
        )

        analyzer = TimingAnalyzer()
        result = analyzer.analyze_session(session)

        flag_types = {f.type for f in result.flags}
        assert "consistent_timing" not in flag_types

    def test_normal_response_no_flags(
        self,
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should not flag normal response timing."""
        trial = SlopitTrial(
            trial_id="normal-trial",
            trial_index=0,
            start_time=0,
            end_time=60000,
            rt=60000,  # 60 seconds for response
            response=ResponseInfo(
                type="text",
                value="This is a normal thoughtful response.",
                character_count=37,
            ),
        )
        session = SlopitSession(
            session_id="normal-session",
            platform=sample_platform_info,
            environment=sample_environment_info,
            timing=sample_session_timing,
            trials=[trial],
            global_events=sample_global_events,
        )

        analyzer = TimingAnalyzer()
        result = analyzer.analyze_session(session)

        assert len(result.flags) == 0

    def test_session_summary(
        self,
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should compute session summary correctly."""
        trials = [
            SlopitTrial(
                trial_id=f"summary-{i}",
                trial_index=i,
                start_time=i * 10000,
                end_time=(i + 1) * 10000,
                rt=rt,
            )
            for i, rt in enumerate([5000, 10000, 15000])
        ]

        session = SlopitSession(
            session_id="summary-session",
            platform=sample_platform_info,
            environment=sample_environment_info,
            timing=sample_session_timing,
            trials=trials,
            global_events=sample_global_events,
        )

        analyzer = TimingAnalyzer()
        result = analyzer.analyze_session(session)

        assert result.session_summary["trials_analyzed"] == 3
        assert result.session_summary["mean_rt"] == pytest.approx(10000.0)
        assert "std_rt" in result.session_summary
        assert result.session_summary["min_rt"] == 5000
        assert result.session_summary["max_rt"] == 15000

    def test_empty_session(
        self,
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should handle session with no trials."""
        session = SlopitSession(
            session_id="empty-session",
            platform=sample_platform_info,
            environment=sample_environment_info,
            timing=sample_session_timing,
            trials=[],
            global_events=sample_global_events,
        )

        analyzer = TimingAnalyzer()
        result = analyzer.analyze_session(session)

        assert result.session_summary == {"trials_analyzed": 0}
        assert len(result.flags) == 0

    def test_no_response_character_count(
        self,
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should handle trials without response character count."""
        trial = SlopitTrial(
            trial_id="no-chars",
            trial_index=0,
            start_time=0,
            end_time=5000,
            rt=5000,
            response=None,
        )
        session = SlopitSession(
            session_id="no-chars-session",
            platform=sample_platform_info,
            environment=sample_environment_info,
            timing=sample_session_timing,
            trials=[trial],
            global_events=sample_global_events,
        )

        analyzer = TimingAnalyzer()
        result = analyzer.analyze_session(session)

        # Should analyze but not compute per-char metrics
        assert len(result.trials) == 1
        metrics = result.trials[0]["metrics"]
        assert metrics["ms_per_char"] is None

    def test_analyze_sessions_multiple(
        self,
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should analyze multiple sessions."""
        trial = SlopitTrial(
            trial_id="multi-trial",
            trial_index=0,
            start_time=0,
            end_time=5000,
            rt=5000,
        )
        session = SlopitSession(
            session_id="multi-session",
            platform=sample_platform_info,
            environment=sample_environment_info,
            timing=sample_session_timing,
            trials=[trial],
            global_events=sample_global_events,
        )

        analyzer = TimingAnalyzer()
        results = analyzer.analyze_sessions([session, session])

        assert len(results) == 2
