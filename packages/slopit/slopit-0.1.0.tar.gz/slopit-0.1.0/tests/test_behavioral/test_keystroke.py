"""Tests for KeystrokeAnalyzer."""

from __future__ import annotations

import pytest

from slopit.behavioral import KeystrokeAnalyzer, KeystrokeAnalyzerConfig
from slopit.schemas import (
    BehavioralData,
    EnvironmentInfo,
    GlobalEvents,
    KeystrokeEvent,
    PlatformInfo,
    ResponseInfo,
    SessionTiming,
    SlopitSession,
    SlopitTrial,
)


class TestKeystrokeAnalyzerConfig:
    """Tests for KeystrokeAnalyzerConfig."""

    def test_default_config(self) -> None:
        """Should have sensible defaults."""
        config = KeystrokeAnalyzerConfig()
        assert config.pause_threshold_ms == 2000.0
        assert config.burst_threshold_ms == 500.0
        assert config.min_keystrokes == 20
        assert config.min_iki_std_threshold == 100.0
        assert config.max_ppr_threshold == 0.95

    def test_custom_config(self) -> None:
        """Should accept custom values."""
        config = KeystrokeAnalyzerConfig(
            pause_threshold_ms=1500.0,
            min_keystrokes=10,
            min_iki_std_threshold=50.0,
        )
        assert config.pause_threshold_ms == 1500.0
        assert config.min_keystrokes == 10


class TestKeystrokeAnalyzer:
    """Tests for KeystrokeAnalyzer."""

    def test_analyzer_name(self) -> None:
        """Should have correct name."""
        analyzer = KeystrokeAnalyzer()
        assert analyzer.name == "keystroke"

    def test_default_config(self) -> None:
        """Should use default config when none provided."""
        analyzer = KeystrokeAnalyzer()
        assert analyzer.config.min_keystrokes == 20

    def test_custom_config(self) -> None:
        """Should accept custom config."""
        config = KeystrokeAnalyzerConfig(min_keystrokes=5)
        analyzer = KeystrokeAnalyzer(config)
        assert analyzer.config.min_keystrokes == 5

    def test_analyze_session_insufficient_data(
        self, sample_session: SlopitSession
    ) -> None:
        """Should skip trials with insufficient keystroke data."""
        # sample_session has only 10 keystrokes (5 keys * 2 events)
        analyzer = KeystrokeAnalyzer()
        result = analyzer.analyze_session(sample_session)

        assert result.analyzer == "keystroke"
        assert result.session_id == sample_session.session_id
        # Should have no analyzed trials due to insufficient keystrokes
        assert len(result.trials) == 0

    def test_analyze_session_with_sufficient_data(
        self, session_with_sufficient_keystrokes: SlopitSession
    ) -> None:
        """Should analyze trials with sufficient keystroke data."""
        # Configure with lower threshold to ensure our fixture passes
        config = KeystrokeAnalyzerConfig(min_keystrokes=10)
        analyzer = KeystrokeAnalyzer(config)
        result = analyzer.analyze_session(session_with_sufficient_keystrokes)

        assert len(result.trials) == 1
        assert "metrics" in result.trials[0]

    def test_compute_metrics_basic(
        self,
        modifier_state_default,
    ) -> None:
        """Should compute basic keystroke metrics."""
        # Create keystrokes with known timing
        events: list[KeystrokeEvent] = []
        time = 0.0
        for i, key in enumerate("hello world"):
            events.append(
                KeystrokeEvent(
                    time=time,
                    key=key if key != " " else " ",
                    code="Space" if key == " " else f"Key{key.upper()}",
                    event="keydown",
                    text_length=i + 1,
                    modifiers=modifier_state_default,
                )
            )
            time += 100.0  # 100ms between keys

        analyzer = KeystrokeAnalyzer()
        metrics = analyzer._compute_metrics(events)

        assert metrics.total_keystrokes == 11
        assert metrics.printable_keystrokes == 11  # All are printable
        assert metrics.deletions == 0
        assert metrics.mean_iki == pytest.approx(100.0, rel=0.01)

    def test_compute_metrics_with_deletions(
        self,
        keystroke_events_with_deletions: list[KeystrokeEvent],
    ) -> None:
        """Should count deletions correctly."""
        analyzer = KeystrokeAnalyzer()
        metrics = analyzer._compute_metrics(keystroke_events_with_deletions)

        assert metrics.deletions == 2  # Two backspace events

    def test_compute_ikis(self, modifier_state_default) -> None:
        """Should compute inter-keystroke intervals correctly."""
        events = [
            KeystrokeEvent(
                time=0, key="a", code="KeyA", event="keydown", modifiers=modifier_state_default
            ),
            KeystrokeEvent(
                time=100, key="b", code="KeyB", event="keydown", modifiers=modifier_state_default
            ),
            KeystrokeEvent(
                time=250, key="c", code="KeyC", event="keydown", modifiers=modifier_state_default
            ),
        ]

        analyzer = KeystrokeAnalyzer()
        ikis = analyzer._compute_ikis(events)

        assert len(ikis) == 2
        assert ikis[0] == pytest.approx(100.0)
        assert ikis[1] == pytest.approx(150.0)

    def test_compute_ikis_single_keystroke(self, modifier_state_default) -> None:
        """Should return empty array for single keystroke."""
        events = [
            KeystrokeEvent(
                time=0, key="a", code="KeyA", event="keydown", modifiers=modifier_state_default
            )
        ]

        analyzer = KeystrokeAnalyzer()
        ikis = analyzer._compute_ikis(events)

        assert len(ikis) == 0

    def test_compute_ikis_empty(self) -> None:
        """Should return empty array for no keystrokes."""
        analyzer = KeystrokeAnalyzer()
        ikis = analyzer._compute_ikis([])

        assert len(ikis) == 0

    def test_low_iki_variance_flag(
        self,
        keystroke_events_uniform_timing: list[KeystrokeEvent],
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should flag low IKI variance (uniform timing)."""
        behavioral = BehavioralData(
            keystrokes=keystroke_events_uniform_timing,
            focus=[],
            paste=[],
        )
        trial = SlopitTrial(
            trial_id="uniform-trial",
            trial_index=0,
            start_time=0,
            end_time=10000,
            behavioral=behavioral,
        )
        session = SlopitSession(
            session_id="uniform-session",
            platform=sample_platform_info,
            environment=sample_environment_info,
            timing=sample_session_timing,
            trials=[trial],
            global_events=sample_global_events,
        )

        config = KeystrokeAnalyzerConfig(min_keystrokes=20, min_iki_std_threshold=50.0)
        analyzer = KeystrokeAnalyzer(config)
        result = analyzer.analyze_session(session)

        # Should have low_iki_variance flag
        flag_types = {f.type for f in result.flags}
        assert "low_iki_variance" in flag_types

    def test_natural_typing_no_iki_flag(
        self,
        keystroke_events_natural_timing: list[KeystrokeEvent],
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should not flag natural typing variance."""
        behavioral = BehavioralData(
            keystrokes=keystroke_events_natural_timing,
            focus=[],
            paste=[],
        )
        trial = SlopitTrial(
            trial_id="natural-trial",
            trial_index=0,
            start_time=0,
            end_time=10000,
            behavioral=behavioral,
        )
        session = SlopitSession(
            session_id="natural-session",
            platform=sample_platform_info,
            environment=sample_environment_info,
            timing=sample_session_timing,
            trials=[trial],
            global_events=sample_global_events,
        )

        config = KeystrokeAnalyzerConfig(min_keystrokes=10)
        analyzer = KeystrokeAnalyzer(config)
        result = analyzer.analyze_session(session)

        # Should not have low_iki_variance flag with natural timing
        flag_types = {f.type for f in result.flags}
        assert "low_iki_variance" not in flag_types

    def test_minimal_revision_flag(
        self,
        modifier_state_default,
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should flag high product-process ratio (minimal revision)."""
        # Create keystrokes with no deletions and high PPR
        events: list[KeystrokeEvent] = []
        time = 0.0
        text = "This is a perfect response without any mistakes"
        for i, char in enumerate(text):
            events.append(
                KeystrokeEvent(
                    time=time,
                    key=char if char != " " else " ",
                    code="Space" if char == " " else f"Key{char.upper()}",
                    event="keydown",
                    text_length=i + 1,
                    modifiers=modifier_state_default,
                )
            )
            time += 100.0

        behavioral = BehavioralData(keystrokes=events, focus=[], paste=[])
        trial = SlopitTrial(
            trial_id="high-ppr-trial",
            trial_index=0,
            start_time=0,
            end_time=10000,
            behavioral=behavioral,
        )
        session = SlopitSession(
            session_id="high-ppr-session",
            platform=sample_platform_info,
            environment=sample_environment_info,
            timing=sample_session_timing,
            trials=[trial],
            global_events=sample_global_events,
        )

        config = KeystrokeAnalyzerConfig(min_keystrokes=20, max_ppr_threshold=0.9)
        analyzer = KeystrokeAnalyzer(config)
        result = analyzer.analyze_session(session)

        # Should have minimal_revision flag
        flag_types = {f.type for f in result.flags}
        assert "minimal_revision" in flag_types

    def test_no_deletions_flag(
        self,
        modifier_state_default,
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should flag no deletions in extended response."""
        # Create 60 keystrokes with no deletions
        events: list[KeystrokeEvent] = []
        time = 0.0
        for i in range(60):
            events.append(
                KeystrokeEvent(
                    time=time,
                    key="a",
                    code="KeyA",
                    event="keydown",
                    text_length=i + 1,
                    modifiers=modifier_state_default,
                )
            )
            time += 100.0

        behavioral = BehavioralData(keystrokes=events, focus=[], paste=[])
        trial = SlopitTrial(
            trial_id="no-delete-trial",
            trial_index=0,
            start_time=0,
            end_time=10000,
            behavioral=behavioral,
        )
        session = SlopitSession(
            session_id="no-delete-session",
            platform=sample_platform_info,
            environment=sample_environment_info,
            timing=sample_session_timing,
            trials=[trial],
            global_events=sample_global_events,
        )

        config = KeystrokeAnalyzerConfig(min_keystrokes=20)
        analyzer = KeystrokeAnalyzer(config)
        result = analyzer.analyze_session(session)

        # Should have no_deletions flag
        flag_types = {f.type for f in result.flags}
        assert "no_deletions" in flag_types

    def test_iki_confidence_calculation(self) -> None:
        """Should compute IKI confidence correctly."""
        config = KeystrokeAnalyzerConfig(min_iki_std_threshold=100.0)
        analyzer = KeystrokeAnalyzer(config)

        # At threshold, confidence should be 0
        assert analyzer._iki_confidence(100.0) == 0.0

        # Well below threshold, confidence should be high
        assert analyzer._iki_confidence(0.0) == 1.0

        # Halfway below threshold
        assert analyzer._iki_confidence(50.0) == pytest.approx(0.5)

    def test_session_summary_computation(
        self,
        keystroke_events_natural_timing: list[KeystrokeEvent],
        sample_platform_info: PlatformInfo,
        sample_environment_info: EnvironmentInfo,
        sample_session_timing: SessionTiming,
        sample_global_events: GlobalEvents,
    ) -> None:
        """Should compute session summary correctly."""
        behavioral = BehavioralData(
            keystrokes=keystroke_events_natural_timing,
            focus=[],
            paste=[],
        )
        trial = SlopitTrial(
            trial_id="summary-trial",
            trial_index=0,
            start_time=0,
            end_time=10000,
            behavioral=behavioral,
        )
        session = SlopitSession(
            session_id="summary-session",
            platform=sample_platform_info,
            environment=sample_environment_info,
            timing=sample_session_timing,
            trials=[trial],
            global_events=sample_global_events,
        )

        config = KeystrokeAnalyzerConfig(min_keystrokes=10)
        analyzer = KeystrokeAnalyzer(config)
        result = analyzer.analyze_session(session)

        assert "trials_analyzed" in result.session_summary
        assert result.session_summary["trials_analyzed"] == 1

    def test_analyze_sessions_multiple(
        self,
        session_with_sufficient_keystrokes: SlopitSession,
    ) -> None:
        """Should analyze multiple sessions."""
        config = KeystrokeAnalyzerConfig(min_keystrokes=10)
        analyzer = KeystrokeAnalyzer(config)

        results = analyzer.analyze_sessions([
            session_with_sufficient_keystrokes,
            session_with_sufficient_keystrokes,
        ])

        assert len(results) == 2

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

        analyzer = KeystrokeAnalyzer()
        result = analyzer.analyze_session(session)

        assert result.session_summary == {"trials_analyzed": 0}
        assert len(result.flags) == 0
