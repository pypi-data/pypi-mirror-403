"""Tests for FocusAnalyzer."""

from __future__ import annotations

import pytest

from slopit.behavioral import FocusAnalyzer, FocusAnalyzerConfig
from slopit.schemas import (
    BehavioralData,
    EnvironmentInfo,
    FocusEvent,
    GlobalEvents,
    PasteEvent,
    PlatformInfo,
    SessionTiming,
    SlopitSession,
    SlopitTrial,
)


class TestFocusAnalyzerConfig:
    """Tests for FocusAnalyzerConfig."""

    def test_default_config(self) -> None:
        """Should have sensible defaults."""
        config = FocusAnalyzerConfig()
        assert config.max_blur_count == 5
        assert config.max_hidden_duration_ms == 30000.0
        assert config.blur_paste_window_ms == 5000.0

    def test_custom_config(self) -> None:
        """Should accept custom values."""
        config = FocusAnalyzerConfig(
            max_blur_count=10,
            max_hidden_duration_ms=60000.0,
        )
        assert config.max_blur_count == 10
        assert config.max_hidden_duration_ms == 60000.0


class TestFocusAnalyzer:
    """Tests for FocusAnalyzer."""

    def test_analyzer_name(self) -> None:
        """Should have correct name."""
        analyzer = FocusAnalyzer()
        assert analyzer.name == "focus"

    def test_default_config(self) -> None:
        """Should use default config when none provided."""
        analyzer = FocusAnalyzer()
        assert analyzer.config.max_blur_count == 5

    def test_custom_config(self) -> None:
        """Should accept custom config."""
        config = FocusAnalyzerConfig(max_blur_count=10)
        analyzer = FocusAnalyzer(config)
        assert analyzer.config.max_blur_count == 10

    def test_analyze_session_no_focus_data(
        self,
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should skip trials without focus data."""
        trial = SlopitTrial(
            trial_id="no-focus",
            trial_index=0,
            start_time=0,
            end_time=5000,
            behavioral=BehavioralData(keystrokes=[], focus=[], paste=[]),
        )
        session = SlopitSession(
            session_id="no-focus-session",
            platform=sample_platform_info,
            environment=sample_environment_info,
            timing=sample_session_timing,
            trials=[trial],
            global_events=sample_global_events,
        )

        analyzer = FocusAnalyzer()
        result = analyzer.analyze_session(session)

        assert len(result.trials) == 0

    def test_analyze_session_with_focus_data(
        self,
        sample_focus_events: list[FocusEvent],
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should analyze trials with focus data."""
        trial = SlopitTrial(
            trial_id="with-focus",
            trial_index=0,
            start_time=0,
            end_time=10000,
            behavioral=BehavioralData(
                keystrokes=[],
                focus=sample_focus_events,
                paste=[],
            ),
        )
        session = SlopitSession(
            session_id="focus-session",
            platform=sample_platform_info,
            environment=sample_environment_info,
            timing=sample_session_timing,
            trials=[trial],
            global_events=sample_global_events,
        )

        analyzer = FocusAnalyzer()
        result = analyzer.analyze_session(session)

        assert len(result.trials) == 1
        assert "metrics" in result.trials[0]

    def test_compute_metrics_blur(self) -> None:
        """Should compute blur metrics correctly."""
        events = [
            FocusEvent(time=1000.0, event="blur", blur_duration=2000.0),
            FocusEvent(time=3000.0, event="focus"),
            FocusEvent(time=5000.0, event="blur", blur_duration=1500.0),
            FocusEvent(time=6500.0, event="focus"),
        ]

        analyzer = FocusAnalyzer()
        metrics = analyzer._compute_metrics(events)

        assert metrics.blur_count == 2
        assert metrics.total_blur_duration == 3500.0

    def test_compute_metrics_visibility(self) -> None:
        """Should compute visibility metrics correctly."""
        events = [
            FocusEvent(time=1000.0, event="visibilitychange", visibility="hidden"),
            FocusEvent(time=5000.0, event="visibilitychange", visibility="visible"),
            FocusEvent(time=8000.0, event="visibilitychange", visibility="hidden"),
            FocusEvent(time=10000.0, event="visibilitychange", visibility="visible"),
        ]

        analyzer = FocusAnalyzer()
        metrics = analyzer._compute_metrics(events)

        assert metrics.hidden_count == 2
        assert metrics.total_hidden_duration == 6000.0  # 4000 + 2000

    def test_excessive_blur_flag(
        self,
        focus_events_excessive_blur: list[FocusEvent],
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should flag excessive blur events."""
        trial = SlopitTrial(
            trial_id="excess-blur",
            trial_index=0,
            start_time=0,
            end_time=100000,
            behavioral=BehavioralData(
                keystrokes=[],
                focus=focus_events_excessive_blur,
                paste=[],
            ),
        )
        session = SlopitSession(
            session_id="excess-blur-session",
            platform=sample_platform_info,
            environment=sample_environment_info,
            timing=sample_session_timing,
            trials=[trial],
            global_events=sample_global_events,
        )

        config = FocusAnalyzerConfig(max_blur_count=5)
        analyzer = FocusAnalyzer(config)
        result = analyzer.analyze_session(session)

        flag_types = {f.type for f in result.flags}
        assert "excessive_blur" in flag_types

    def test_extended_hidden_flag(
        self,
        focus_events_long_hidden: list[FocusEvent],
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should flag extended hidden duration."""
        trial = SlopitTrial(
            trial_id="long-hidden",
            trial_index=0,
            start_time=0,
            end_time=70000,
            behavioral=BehavioralData(
                keystrokes=[],
                focus=focus_events_long_hidden,
                paste=[],
            ),
        )
        session = SlopitSession(
            session_id="long-hidden-session",
            platform=sample_platform_info,
            environment=sample_environment_info,
            timing=sample_session_timing,
            trials=[trial],
            global_events=sample_global_events,
        )

        config = FocusAnalyzerConfig(max_hidden_duration_ms=30000.0)
        analyzer = FocusAnalyzer(config)
        result = analyzer.analyze_session(session)

        flag_types = {f.type for f in result.flags}
        assert "extended_hidden" in flag_types

    def test_blur_paste_pattern_flag(
        self,
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should flag blur followed by paste pattern."""
        focus_events = [
            FocusEvent(time=1000.0, event="blur", blur_duration=3000.0),
            FocusEvent(time=4000.0, event="focus"),
        ]
        paste_events = [
            PasteEvent(
                time=4500.0,  # 500ms after refocus
                text_length=100,
                preceding_keystrokes=0,
                blocked=False,
            )
        ]

        trial = SlopitTrial(
            trial_id="blur-paste",
            trial_index=0,
            start_time=0,
            end_time=10000,
            behavioral=BehavioralData(
                keystrokes=[],
                focus=focus_events,
                paste=paste_events,
            ),
        )
        session = SlopitSession(
            session_id="blur-paste-session",
            platform=sample_platform_info,
            environment=sample_environment_info,
            timing=sample_session_timing,
            trials=[trial],
            global_events=sample_global_events,
        )

        config = FocusAnalyzerConfig(blur_paste_window_ms=5000.0)
        analyzer = FocusAnalyzer(config)
        result = analyzer.analyze_session(session)

        flag_types = {f.type for f in result.flags}
        assert "blur_paste_pattern" in flag_types

    def test_no_blur_paste_pattern_outside_window(
        self,
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should not flag paste outside blur window."""
        focus_events = [
            FocusEvent(time=1000.0, event="blur", blur_duration=3000.0),
            FocusEvent(time=4000.0, event="focus"),
        ]
        paste_events = [
            PasteEvent(
                time=15000.0,  # 11 seconds after refocus
                text_length=100,
                preceding_keystrokes=0,
                blocked=False,
            )
        ]

        trial = SlopitTrial(
            trial_id="no-blur-paste",
            trial_index=0,
            start_time=0,
            end_time=20000,
            behavioral=BehavioralData(
                keystrokes=[],
                focus=focus_events,
                paste=paste_events,
            ),
        )
        session = SlopitSession(
            session_id="no-blur-paste-session",
            platform=sample_platform_info,
            environment=sample_environment_info,
            timing=sample_session_timing,
            trials=[trial],
            global_events=sample_global_events,
        )

        config = FocusAnalyzerConfig(blur_paste_window_ms=5000.0)
        analyzer = FocusAnalyzer(config)
        result = analyzer.analyze_session(session)

        flag_types = {f.type for f in result.flags}
        assert "blur_paste_pattern" not in flag_types

    def test_normal_focus_no_flags(
        self,
        sample_focus_events: list[FocusEvent],
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should not flag normal focus behavior."""
        trial = SlopitTrial(
            trial_id="normal-focus",
            trial_index=0,
            start_time=0,
            end_time=10000,
            behavioral=BehavioralData(
                keystrokes=[],
                focus=sample_focus_events,
                paste=[],
            ),
        )
        session = SlopitSession(
            session_id="normal-focus-session",
            platform=sample_platform_info,
            environment=sample_environment_info,
            timing=sample_session_timing,
            trials=[trial],
            global_events=sample_global_events,
        )

        analyzer = FocusAnalyzer()
        result = analyzer.analyze_session(session)

        assert len(result.flags) == 0

    def test_session_summary(
        self,
        focus_events_excessive_blur: list[FocusEvent],
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should compute session summary correctly."""
        trial = SlopitTrial(
            trial_id="summary-trial",
            trial_index=0,
            start_time=0,
            end_time=100000,
            behavioral=BehavioralData(
                keystrokes=[],
                focus=focus_events_excessive_blur,
                paste=[],
            ),
        )
        session = SlopitSession(
            session_id="summary-session",
            platform=sample_platform_info,
            environment=sample_environment_info,
            timing=sample_session_timing,
            trials=[trial],
            global_events=sample_global_events,
        )

        analyzer = FocusAnalyzer()
        result = analyzer.analyze_session(session)

        assert "trials_analyzed" in result.session_summary
        assert "total_blur_events" in result.session_summary
        assert result.session_summary["trials_analyzed"] == 1

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

        analyzer = FocusAnalyzer()
        result = analyzer.analyze_session(session)

        assert result.session_summary == {"trials_analyzed": 0}
        assert len(result.flags) == 0

    def test_analyze_sessions_multiple(
        self,
        sample_focus_events: list[FocusEvent],
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
            end_time=10000,
            behavioral=BehavioralData(keystrokes=[], focus=sample_focus_events, paste=[]),
        )
        session = SlopitSession(
            session_id="multi-session",
            platform=sample_platform_info,
            environment=sample_environment_info,
            timing=sample_session_timing,
            trials=[trial],
            global_events=sample_global_events,
        )

        analyzer = FocusAnalyzer()
        results = analyzer.analyze_sessions([session, session])

        assert len(results) == 2
