"""Tests for PasteAnalyzer."""

from __future__ import annotations

import pytest

from slopit.behavioral import PasteAnalyzer, PasteAnalyzerConfig
from slopit.schemas import (
    BehavioralData,
    EnvironmentInfo,
    GlobalEvents,
    PasteEvent,
    PlatformInfo,
    SessionTiming,
    SlopitSession,
    SlopitTrial,
)


class TestPasteAnalyzerConfig:
    """Tests for PasteAnalyzerConfig."""

    def test_default_config(self) -> None:
        """Should have sensible defaults."""
        config = PasteAnalyzerConfig()
        assert config.large_paste_threshold == 50
        assert config.suspicious_preceding_keystrokes == 5

    def test_custom_config(self) -> None:
        """Should accept custom values."""
        config = PasteAnalyzerConfig(
            large_paste_threshold=100,
            suspicious_preceding_keystrokes=10,
        )
        assert config.large_paste_threshold == 100
        assert config.suspicious_preceding_keystrokes == 10


class TestPasteAnalyzer:
    """Tests for PasteAnalyzer."""

    def test_analyzer_name(self) -> None:
        """Should have correct name."""
        analyzer = PasteAnalyzer()
        assert analyzer.name == "paste"

    def test_default_config(self) -> None:
        """Should use default config when none provided."""
        analyzer = PasteAnalyzer()
        assert analyzer.config.large_paste_threshold == 50

    def test_custom_config(self) -> None:
        """Should accept custom config."""
        config = PasteAnalyzerConfig(large_paste_threshold=100)
        analyzer = PasteAnalyzer(config)
        assert analyzer.config.large_paste_threshold == 100

    def test_analyze_session_no_paste_data(
        self,
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should skip trials without paste data."""
        trial = SlopitTrial(
            trial_id="no-paste",
            trial_index=0,
            start_time=0,
            end_time=5000,
            behavioral=BehavioralData(keystrokes=[], focus=[], paste=[]),
        )
        session = SlopitSession(
            session_id="no-paste-session",
            platform=sample_platform_info,
            environment=sample_environment_info,
            timing=sample_session_timing,
            trials=[trial],
            global_events=sample_global_events,
        )

        analyzer = PasteAnalyzer()
        result = analyzer.analyze_session(session)

        assert len(result.trials) == 0

    def test_analyze_session_with_paste_data(
        self,
        sample_paste_event: PasteEvent,
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should analyze trials with paste data."""
        trial = SlopitTrial(
            trial_id="with-paste",
            trial_index=0,
            start_time=0,
            end_time=10000,
            behavioral=BehavioralData(
                keystrokes=[],
                focus=[],
                paste=[sample_paste_event],
            ),
        )
        session = SlopitSession(
            session_id="paste-session",
            platform=sample_platform_info,
            environment=sample_environment_info,
            timing=sample_session_timing,
            trials=[trial],
            global_events=sample_global_events,
        )

        analyzer = PasteAnalyzer()
        result = analyzer.analyze_session(session)

        assert len(result.trials) == 1
        assert "metrics" in result.trials[0]

    def test_compute_metrics(self) -> None:
        """Should compute paste metrics correctly."""
        events = [
            PasteEvent(time=1000, text_length=50, preceding_keystrokes=10, blocked=False),
            PasteEvent(time=2000, text_length=100, preceding_keystrokes=5, blocked=False),
            PasteEvent(time=3000, text_length=30, preceding_keystrokes=20, blocked=True),
        ]

        config = PasteAnalyzerConfig(large_paste_threshold=40)
        analyzer = PasteAnalyzer(config)
        metrics = analyzer._compute_metrics(events)

        assert metrics.paste_count == 3
        assert metrics.total_pasted_chars == 180
        assert metrics.blocked_count == 1
        assert metrics.large_paste_count == 2  # 50 and 100 are >= 40

    def test_large_paste_flag(
        self,
        large_paste_event: PasteEvent,
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should flag large paste events."""
        trial = SlopitTrial(
            trial_id="large-paste",
            trial_index=0,
            start_time=0,
            end_time=10000,
            behavioral=BehavioralData(
                keystrokes=[],
                focus=[],
                paste=[large_paste_event],
            ),
        )
        session = SlopitSession(
            session_id="large-paste-session",
            platform=sample_platform_info,
            environment=sample_environment_info,
            timing=sample_session_timing,
            trials=[trial],
            global_events=sample_global_events,
        )

        config = PasteAnalyzerConfig(large_paste_threshold=50)
        analyzer = PasteAnalyzer(config)
        result = analyzer.analyze_session(session)

        flag_types = {f.type for f in result.flags}
        assert "large_paste" in flag_types

    def test_paste_without_typing_flag(
        self,
        paste_without_typing: PasteEvent,
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should flag paste with no prior typing."""
        trial = SlopitTrial(
            trial_id="no-typing-paste",
            trial_index=0,
            start_time=0,
            end_time=10000,
            behavioral=BehavioralData(
                keystrokes=[],
                focus=[],
                paste=[paste_without_typing],
            ),
        )
        session = SlopitSession(
            session_id="no-typing-paste-session",
            platform=sample_platform_info,
            environment=sample_environment_info,
            timing=sample_session_timing,
            trials=[trial],
            global_events=sample_global_events,
        )

        config = PasteAnalyzerConfig(suspicious_preceding_keystrokes=5)
        analyzer = PasteAnalyzer(config)
        result = analyzer.analyze_session(session)

        flag_types = {f.type for f in result.flags}
        assert "paste_without_typing" in flag_types

    def test_paste_without_typing_high_severity(
        self,
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should assign high severity for large paste without typing."""
        paste = PasteEvent(
            time=500,
            text_length=150,  # >= 100 chars
            preceding_keystrokes=0,
            blocked=False,
        )
        trial = SlopitTrial(
            trial_id="high-sev-paste",
            trial_index=0,
            start_time=0,
            end_time=5000,
            behavioral=BehavioralData(
                keystrokes=[],
                focus=[],
                paste=[paste],
            ),
        )
        session = SlopitSession(
            session_id="high-sev-session",
            platform=sample_platform_info,
            environment=sample_environment_info,
            timing=sample_session_timing,
            trials=[trial],
            global_events=sample_global_events,
        )

        analyzer = PasteAnalyzer()
        result = analyzer.analyze_session(session)

        # Find the paste_without_typing flag
        paste_flags = [f for f in result.flags if f.type == "paste_without_typing"]
        assert len(paste_flags) > 0
        assert paste_flags[0].severity == "high"

    def test_paste_with_typing_no_flag(
        self,
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should not flag paste after sufficient typing."""
        paste = PasteEvent(
            time=5000,
            text_length=30,  # Small paste
            preceding_keystrokes=20,  # Enough prior typing
            blocked=False,
        )
        trial = SlopitTrial(
            trial_id="with-typing-paste",
            trial_index=0,
            start_time=0,
            end_time=10000,
            behavioral=BehavioralData(
                keystrokes=[],
                focus=[],
                paste=[paste],
            ),
        )
        session = SlopitSession(
            session_id="with-typing-session",
            platform=sample_platform_info,
            environment=sample_environment_info,
            timing=sample_session_timing,
            trials=[trial],
            global_events=sample_global_events,
        )

        config = PasteAnalyzerConfig(
            large_paste_threshold=50,
            suspicious_preceding_keystrokes=5,
        )
        analyzer = PasteAnalyzer(config)
        result = analyzer.analyze_session(session)

        assert len(result.flags) == 0

    def test_multiple_paste_events(
        self,
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should analyze multiple paste events in one trial."""
        pastes = [
            PasteEvent(time=1000, text_length=100, preceding_keystrokes=0, blocked=False),
            PasteEvent(time=3000, text_length=50, preceding_keystrokes=10, blocked=False),
            PasteEvent(time=5000, text_length=200, preceding_keystrokes=2, blocked=False),
        ]
        trial = SlopitTrial(
            trial_id="multi-paste",
            trial_index=0,
            start_time=0,
            end_time=10000,
            behavioral=BehavioralData(
                keystrokes=[],
                focus=[],
                paste=pastes,
            ),
        )
        session = SlopitSession(
            session_id="multi-paste-session",
            platform=sample_platform_info,
            environment=sample_environment_info,
            timing=sample_session_timing,
            trials=[trial],
            global_events=sample_global_events,
        )

        config = PasteAnalyzerConfig(
            large_paste_threshold=50,
            suspicious_preceding_keystrokes=5,
        )
        analyzer = PasteAnalyzer(config)
        result = analyzer.analyze_session(session)

        # Count flag types
        large_paste_count = sum(1 for f in result.flags if f.type == "large_paste")
        without_typing_count = sum(1 for f in result.flags if f.type == "paste_without_typing")

        assert large_paste_count == 3  # All 3 are >= 50
        assert without_typing_count == 2  # First (0 keystrokes) and third (2 keystrokes)

    def test_blocked_paste_metrics(
        self,
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should count blocked paste events."""
        pastes = [
            PasteEvent(time=1000, text_length=100, preceding_keystrokes=0, blocked=True),
            PasteEvent(time=2000, text_length=50, preceding_keystrokes=10, blocked=True),
            PasteEvent(time=3000, text_length=30, preceding_keystrokes=20, blocked=False),
        ]
        trial = SlopitTrial(
            trial_id="blocked-paste",
            trial_index=0,
            start_time=0,
            end_time=5000,
            behavioral=BehavioralData(
                keystrokes=[],
                focus=[],
                paste=pastes,
            ),
        )
        session = SlopitSession(
            session_id="blocked-session",
            platform=sample_platform_info,
            environment=sample_environment_info,
            timing=sample_session_timing,
            trials=[trial],
            global_events=sample_global_events,
        )

        analyzer = PasteAnalyzer()
        result = analyzer.analyze_session(session)

        # Check metrics in trial result
        metrics = result.trials[0]["metrics"]
        assert metrics["blocked_count"] == 2

    def test_session_summary(
        self,
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should compute session summary correctly."""
        pastes = [
            PasteEvent(time=1000, text_length=50, preceding_keystrokes=10, blocked=False),
            PasteEvent(time=2000, text_length=100, preceding_keystrokes=20, blocked=False),
        ]
        trial = SlopitTrial(
            trial_id="summary-trial",
            trial_index=0,
            start_time=0,
            end_time=5000,
            behavioral=BehavioralData(
                keystrokes=[],
                focus=[],
                paste=pastes,
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

        analyzer = PasteAnalyzer()
        result = analyzer.analyze_session(session)

        assert result.session_summary["trials_analyzed"] == 1
        assert result.session_summary["total_paste_events"] == 2
        assert result.session_summary["total_pasted_chars"] == 150

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

        analyzer = PasteAnalyzer()
        result = analyzer.analyze_session(session)

        assert result.session_summary == {"trials_analyzed": 0}
        assert len(result.flags) == 0

    def test_analyze_sessions_multiple(
        self,
        sample_paste_event: PasteEvent,
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
            behavioral=BehavioralData(
                keystrokes=[],
                focus=[],
                paste=[sample_paste_event],
            ),
        )
        session = SlopitSession(
            session_id="multi-session",
            platform=sample_platform_info,
            environment=sample_environment_info,
            timing=sample_session_timing,
            trials=[trial],
            global_events=sample_global_events,
        )

        analyzer = PasteAnalyzer()
        results = analyzer.analyze_sessions([session, session])

        assert len(results) == 2
