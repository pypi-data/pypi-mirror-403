"""Paste event analyzer.

This module provides analysis of paste events and clipboard usage.
"""

from dataclasses import dataclass

from slopit.behavioral.base import Analyzer, AnalyzerConfig
from slopit.schemas import PasteEvent, SlopitSession, SlopitTrial
from slopit.schemas.analysis import AnalysisResult
from slopit.schemas.flags import AnalysisFlag
from slopit.schemas.types import JsonValue


@dataclass
class PasteAnalyzerConfig(AnalyzerConfig):
    """Configuration for paste analysis.

    Attributes
    ----------
    large_paste_threshold
        Minimum characters to flag as large paste.
    suspicious_preceding_keystrokes
        Maximum preceding keystrokes for suspicious paste.
    """

    large_paste_threshold: int = 50
    suspicious_preceding_keystrokes: int = 5


@dataclass
class PasteMetrics:
    """Computed paste metrics for a trial.

    Attributes
    ----------
    paste_count
        Number of paste events.
    total_pasted_chars
        Total number of pasted characters.
    blocked_count
        Number of blocked paste events.
    large_paste_count
        Number of large paste events.
    """

    paste_count: int
    total_pasted_chars: int
    blocked_count: int
    large_paste_count: int

    def to_dict(self) -> dict[str, JsonValue]:
        """Convert to dictionary for JSON serialization."""
        return {
            "paste_count": self.paste_count,
            "total_pasted_chars": self.total_pasted_chars,
            "blocked_count": self.blocked_count,
            "large_paste_count": self.large_paste_count,
        }


class PasteAnalyzer(Analyzer):
    """Analyzer for paste events and clipboard usage.

    Detects suspicious paste patterns such as large pastes
    without prior typing.

    Parameters
    ----------
    config
        Analyzer configuration.

    Examples
    --------
    >>> from slopit import load_session
    >>> from slopit.behavioral import PasteAnalyzer
    >>>
    >>> session = load_session("data/session.json")
    >>> analyzer = PasteAnalyzer()
    >>> result = analyzer.analyze_session(session)
    """

    def __init__(self, config: PasteAnalyzerConfig | None = None) -> None:
        self.config = config or PasteAnalyzerConfig()

    @property
    def name(self) -> str:
        return "paste"

    def analyze_session(self, session: SlopitSession) -> AnalysisResult:
        """Analyze paste patterns for a session."""
        trial_results: list[dict[str, JsonValue]] = []
        trial_metrics: list[PasteMetrics] = []
        all_flags: list[AnalysisFlag] = []

        for trial in session.trials:
            if not self._has_paste_data(trial):
                continue

            # Safe to assert: _has_paste_data validates these are not None
            assert trial.behavioral is not None
            assert trial.behavioral.paste is not None
            paste_events = trial.behavioral.paste
            metrics = self._compute_metrics(paste_events)
            flags = self._compute_flags(trial.trial_id, paste_events)

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

    def _has_paste_data(self, trial: SlopitTrial) -> bool:
        """Check if trial has paste data."""
        return (
            trial.behavioral is not None
            and trial.behavioral.paste is not None
            and len(trial.behavioral.paste) > 0
        )

    def _compute_metrics(self, paste_events: list[PasteEvent]) -> PasteMetrics:
        """Compute metrics from paste events."""
        total_pasted = sum(e.text_length for e in paste_events)
        blocked_count = sum(1 for e in paste_events if e.blocked)
        large_pastes = sum(
            1 for e in paste_events if e.text_length >= self.config.large_paste_threshold
        )

        return PasteMetrics(
            paste_count=len(paste_events),
            total_pasted_chars=total_pasted,
            blocked_count=blocked_count,
            large_paste_count=large_pastes,
        )

    def _compute_flags(self, trial_id: str, paste_events: list[PasteEvent]) -> list[AnalysisFlag]:
        """Generate flags based on paste events."""
        flags: list[AnalysisFlag] = []

        for event in paste_events:
            # Large paste
            if event.text_length >= self.config.large_paste_threshold:
                flags.append(
                    AnalysisFlag(
                        type="large_paste",
                        analyzer=self.name,
                        severity="medium",
                        message=f"Large paste detected ({event.text_length} characters)",
                        confidence=0.7,
                        evidence={
                            "text_length": event.text_length,
                            "time": event.time,
                        },
                        trial_ids=[trial_id],
                    )
                )

            # Paste without prior typing
            if event.preceding_keystrokes <= self.config.suspicious_preceding_keystrokes:
                severity = "high" if event.text_length >= 100 else "medium"
                flags.append(
                    AnalysisFlag(
                        type="paste_without_typing",
                        analyzer=self.name,
                        severity=severity,
                        message=f"Paste with minimal prior typing ({event.preceding_keystrokes} keystrokes before)",
                        confidence=0.8,
                        evidence={
                            "preceding_keystrokes": event.preceding_keystrokes,
                            "text_length": event.text_length,
                        },
                        trial_ids=[trial_id],
                    )
                )

        return flags

    def _compute_session_summary(
        self, trial_metrics: list[PasteMetrics], trial_results: list[dict[str, JsonValue]]
    ) -> dict[str, JsonValue]:
        """Compute session-level summary."""
        if not trial_metrics:
            return {"trials_analyzed": 0}

        total_pastes = sum(m.paste_count for m in trial_metrics)
        total_chars = sum(m.total_pasted_chars for m in trial_metrics)
        total_flags = sum(
            len(r["flags"]) if isinstance(r["flags"], list) else 0 for r in trial_results
        )

        return {
            "trials_analyzed": len(trial_metrics),
            "total_paste_events": total_pastes,
            "total_pasted_chars": total_chars,
            "total_flags": total_flags,
        }
