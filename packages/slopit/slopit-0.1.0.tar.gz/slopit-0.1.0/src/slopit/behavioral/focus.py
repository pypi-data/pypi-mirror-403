"""Focus and visibility analyzer.

This module provides analysis of focus and visibility events to detect
external assistance patterns.
"""

from dataclasses import dataclass

from slopit.behavioral.base import Analyzer, AnalyzerConfig
from slopit.schemas import FocusEvent, SlopitSession, SlopitTrial
from slopit.schemas.analysis import AnalysisResult
from slopit.schemas.flags import AnalysisFlag
from slopit.schemas.types import JsonValue


@dataclass
class FocusAnalyzerConfig(AnalyzerConfig):
    """Configuration for focus analysis.

    Attributes
    ----------
    max_blur_count
        Maximum blur events before flagging.
    max_hidden_duration_ms
        Maximum hidden duration in milliseconds.
    blur_paste_window_ms
        Window for detecting blur-paste patterns.
    """

    max_blur_count: int = 5
    max_hidden_duration_ms: float = 30000.0
    blur_paste_window_ms: float = 5000.0


@dataclass
class FocusMetrics:
    """Computed focus metrics for a trial.

    Attributes
    ----------
    blur_count
        Number of blur events.
    total_blur_duration
        Total duration of blur events in milliseconds.
    hidden_count
        Number of visibility hidden events.
    total_hidden_duration
        Total duration of hidden state in milliseconds.
    """

    blur_count: int
    total_blur_duration: float
    hidden_count: int
    total_hidden_duration: float

    def to_dict(self) -> dict[str, JsonValue]:
        """Convert to dictionary for JSON serialization."""
        return {
            "blur_count": self.blur_count,
            "total_blur_duration": self.total_blur_duration,
            "hidden_count": self.hidden_count,
            "total_hidden_duration": self.total_hidden_duration,
        }


class FocusAnalyzer(Analyzer):
    """Analyzer for focus and visibility patterns.

    Detects patterns that suggest external assistance such as
    excessive tab switching or extended hidden periods.

    Parameters
    ----------
    config
        Analyzer configuration.

    Examples
    --------
    >>> from slopit import load_session
    >>> from slopit.behavioral import FocusAnalyzer
    >>>
    >>> session = load_session("data/session.json")
    >>> analyzer = FocusAnalyzer()
    >>> result = analyzer.analyze_session(session)
    """

    def __init__(self, config: FocusAnalyzerConfig | None = None) -> None:
        self.config = config or FocusAnalyzerConfig()

    @property
    def name(self) -> str:
        return "focus"

    def analyze_session(self, session: SlopitSession) -> AnalysisResult:
        """Analyze focus patterns for a session."""
        trial_results: list[dict[str, JsonValue]] = []
        trial_metrics: list[FocusMetrics] = []
        all_flags: list[AnalysisFlag] = []

        for trial in session.trials:
            if not self._has_focus_data(trial):
                continue

            # Safe to assert: _has_focus_data validates these are not None
            assert trial.behavioral is not None
            assert trial.behavioral.focus is not None
            focus_events = trial.behavioral.focus
            metrics = self._compute_metrics(focus_events)
            flags = self._compute_flags(trial.trial_id, metrics, trial)

            trial_results.append(
                {
                    "trial_id": trial.trial_id,
                    "metrics": metrics.to_dict(),
                    "flags": [f.model_dump() for f in flags],
                }
            )
            trial_metrics.append(metrics)
            all_flags.extend(flags)

        return AnalysisResult(
            analyzer=self.name,
            session_id=session.session_id,
            trials=trial_results,
            flags=all_flags,
            session_summary=self._compute_session_summary(trial_metrics, trial_results),
        )

    def _has_focus_data(self, trial: SlopitTrial) -> bool:
        """Check if trial has focus data."""
        return (
            trial.behavioral is not None
            and trial.behavioral.focus is not None
            and len(trial.behavioral.focus) > 0
        )

    def _compute_metrics(self, focus_events: list[FocusEvent]) -> FocusMetrics:
        """Compute metrics from focus events."""
        blur_count = sum(1 for e in focus_events if e.event == "blur")
        total_blur_duration = sum(e.blur_duration or 0 for e in focus_events if e.event == "blur")

        hidden_count = sum(
            1 for e in focus_events if e.event == "visibilitychange" and e.visibility == "hidden"
        )

        # Calculate hidden duration
        total_hidden_duration = 0.0
        last_hidden_time: float | None = None
        for event in focus_events:
            if event.event == "visibilitychange":
                if event.visibility == "hidden":
                    last_hidden_time = event.time
                elif event.visibility == "visible" and last_hidden_time is not None:
                    total_hidden_duration += event.time - last_hidden_time
                    last_hidden_time = None

        return FocusMetrics(
            blur_count=blur_count,
            total_blur_duration=total_blur_duration,
            hidden_count=hidden_count,
            total_hidden_duration=total_hidden_duration,
        )

    def _compute_flags(
        self, trial_id: str, metrics: FocusMetrics, trial: SlopitTrial
    ) -> list[AnalysisFlag]:
        """Generate flags based on focus metrics."""
        flags: list[AnalysisFlag] = []

        # Excessive blur events
        if metrics.blur_count > self.config.max_blur_count:
            flags.append(
                AnalysisFlag(
                    type="excessive_blur",
                    analyzer=self.name,
                    severity="medium",
                    message=f"Excessive window switches detected ({metrics.blur_count} blur events)",
                    confidence=min(1.0, metrics.blur_count / 10),
                    evidence={"blur_count": metrics.blur_count},
                    trial_ids=[trial_id],
                )
            )

        # Long hidden duration
        if metrics.total_hidden_duration > self.config.max_hidden_duration_ms:
            flags.append(
                AnalysisFlag(
                    type="extended_hidden",
                    analyzer=self.name,
                    severity="medium",
                    message=f"Extended tab switch detected ({metrics.total_hidden_duration / 1000:.1f}s hidden)",
                    confidence=min(1.0, metrics.total_hidden_duration / 60000),
                    evidence={"total_hidden_duration_ms": metrics.total_hidden_duration},
                    trial_ids=[trial_id],
                )
            )

        # Check for blur-paste pattern
        if self._detect_blur_paste_pattern(trial):
            flags.append(
                AnalysisFlag(
                    type="blur_paste_pattern",
                    analyzer=self.name,
                    severity="high",
                    message="Paste event detected shortly after tab switch",
                    confidence=0.8,
                    evidence={},
                    trial_ids=[trial_id],
                )
            )

        return flags

    def _detect_blur_paste_pattern(self, trial: SlopitTrial) -> bool:
        """Detect if there's a blur followed by paste within window."""
        if trial.behavioral is None:
            return False

        focus_events = trial.behavioral.focus or []
        paste_events = trial.behavioral.paste or []

        if not focus_events or not paste_events:
            return False

        for focus_event in focus_events:
            if focus_event.event == "focus":
                # Check for paste shortly after refocus
                for paste_event in paste_events:
                    time_diff = paste_event.time - focus_event.time
                    if 0 <= time_diff <= self.config.blur_paste_window_ms:
                        return True

        return False

    def _compute_session_summary(
        self, trial_metrics: list[FocusMetrics], trial_results: list[dict[str, JsonValue]]
    ) -> dict[str, JsonValue]:
        """Compute session-level summary."""
        if not trial_metrics:
            return {"trials_analyzed": 0}

        total_blur = sum(m.blur_count for m in trial_metrics)
        total_flags = sum(
            len(r["flags"]) if isinstance(r["flags"], list) else 0 for r in trial_results
        )

        return {
            "trials_analyzed": len(trial_metrics),
            "total_blur_events": total_blur,
            "total_flags": total_flags,
        }
