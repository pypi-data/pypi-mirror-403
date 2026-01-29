"""Timing analyzer.

This module provides analysis of response timing patterns.
"""

from dataclasses import dataclass

import numpy as np

from slopit.behavioral.base import Analyzer, AnalyzerConfig
from slopit.schemas import SlopitSession, SlopitTrial
from slopit.schemas.analysis import AnalysisResult
from slopit.schemas.flags import AnalysisFlag
from slopit.schemas.types import JsonValue


@dataclass
class TimingAnalyzerConfig(AnalyzerConfig):
    """Configuration for timing analysis.

    Attributes
    ----------
    min_rt_per_char_ms
        Minimum expected milliseconds per character.
    max_rt_cv_threshold
        Maximum coefficient of variation for RT.
    instant_response_threshold_ms
        Threshold for instant response detection.
    instant_response_min_chars
        Minimum characters for instant response flag.
    """

    min_rt_per_char_ms: float = 20.0
    max_rt_cv_threshold: float = 0.1
    instant_response_threshold_ms: float = 2000.0
    instant_response_min_chars: int = 100


@dataclass
class TimingMetrics:
    """Computed timing metrics for a trial.

    Attributes
    ----------
    rt
        Response time in milliseconds.
    character_count
        Number of characters in response.
    ms_per_char
        Milliseconds per character, or None if not applicable.
    chars_per_minute
        Characters per minute, or None if not applicable.
    """

    rt: int
    character_count: int | None
    ms_per_char: float | None
    chars_per_minute: float | None

    def to_dict(self) -> dict[str, JsonValue]:
        """Convert to dictionary for JSON serialization."""
        return {
            "rt": self.rt,
            "character_count": self.character_count,
            "ms_per_char": self.ms_per_char,
            "chars_per_minute": self.chars_per_minute,
        }


class TimingAnalyzer(Analyzer):
    """Analyzer for response timing patterns.

    Detects suspiciously fast responses or unusually consistent
    timing across trials.

    Parameters
    ----------
    config
        Analyzer configuration.

    Examples
    --------
    >>> from slopit import load_session
    >>> from slopit.behavioral import TimingAnalyzer
    >>>
    >>> session = load_session("data/session.json")
    >>> analyzer = TimingAnalyzer()
    >>> result = analyzer.analyze_session(session)
    """

    def __init__(self, config: TimingAnalyzerConfig | None = None) -> None:
        self.config = config or TimingAnalyzerConfig()

    @property
    def name(self) -> str:
        return "timing"

    def analyze_session(self, session: SlopitSession) -> AnalysisResult:
        """Analyze timing patterns for a session."""
        trial_results: list[dict[str, JsonValue]] = []
        all_flags: list[AnalysisFlag] = []
        rts: list[float] = []

        for trial in session.trials:
            if trial.rt is None:
                continue

            metrics = self._compute_trial_metrics(trial)
            flags = self._compute_trial_flags(trial.trial_id, trial, metrics)

            trial_results.append(
                {
                    "trial_id": trial.trial_id,
                    "metrics": metrics.to_dict(),
                    "flags": [f.model_dump() for f in flags],
                }
            )
            all_flags.extend(flags)
            rts.append(trial.rt)

        # Check for consistent timing across trials
        session_flags = self._check_session_consistency(rts, session)
        all_flags.extend(session_flags)

        return AnalysisResult(
            analyzer=self.name,
            session_id=session.session_id,
            trials=trial_results,
            flags=all_flags,
            session_summary=self._compute_session_summary(rts, trial_results),
        )

    def _compute_trial_metrics(self, trial: SlopitTrial) -> TimingMetrics:
        """Compute timing metrics for a trial."""
        rt = trial.rt or 0
        char_count = trial.response.character_count if trial.response else None

        ms_per_char = rt / char_count if char_count and char_count > 0 else None
        chars_per_minute = (char_count / (rt / 60000)) if rt > 0 and char_count else None

        return TimingMetrics(
            rt=rt,
            character_count=char_count,
            ms_per_char=ms_per_char,
            chars_per_minute=chars_per_minute,
        )

    def _compute_trial_flags(
        self, trial_id: str, trial: SlopitTrial, metrics: TimingMetrics
    ) -> list[AnalysisFlag]:
        """Generate flags for a single trial."""
        flags: list[AnalysisFlag] = []

        rt = trial.rt or 0
        char_count = metrics.character_count or 0

        # Instant response detection
        if (
            rt < self.config.instant_response_threshold_ms
            and char_count > self.config.instant_response_min_chars
        ):
            flags.append(
                AnalysisFlag(
                    type="instant_response",
                    analyzer=self.name,
                    severity="high",
                    message=f"Suspiciously fast response ({rt}ms for {char_count} chars)",
                    confidence=0.9,
                    evidence={
                        "rt": rt,
                        "character_count": char_count,
                    },
                    trial_ids=[trial_id],
                )
            )

        # Too fast per character
        ms_per_char = metrics.ms_per_char
        if ms_per_char is not None and ms_per_char < self.config.min_rt_per_char_ms:
            flags.append(
                AnalysisFlag(
                    type="fast_typing",
                    analyzer=self.name,
                    severity="medium",
                    message=f"Typing speed exceeds human capability ({ms_per_char:.1f}ms/char)",
                    confidence=0.7,
                    evidence={"ms_per_char": ms_per_char},
                    trial_ids=[trial_id],
                )
            )

        return flags

    def _check_session_consistency(
        self,
        rts: list[float],
        session: SlopitSession,  # noqa: ARG002
    ) -> list[AnalysisFlag]:
        """Check for suspiciously consistent timing across trials."""
        flags: list[AnalysisFlag] = []

        if len(rts) < 3:
            return flags

        rt_array = np.array(rts)
        mean_rt = float(np.mean(rt_array))
        std_rt = float(np.std(rt_array))

        # Coefficient of variation
        cv = std_rt / mean_rt if mean_rt > 0 else float("inf")

        if cv < self.config.max_rt_cv_threshold:
            flags.append(
                AnalysisFlag(
                    type="consistent_timing",
                    analyzer=self.name,
                    severity="medium",
                    message=f"Unusually consistent response times across trials (CV={cv:.3f})",
                    confidence=0.6,
                    evidence={
                        "coefficient_of_variation": cv,
                        "mean_rt": mean_rt,
                        "std_rt": std_rt,
                    },
                    trial_ids=None,
                )
            )

        return flags

    def _compute_session_summary(
        self, rts: list[float], trial_results: list[dict[str, JsonValue]]
    ) -> dict[str, JsonValue]:
        """Compute session-level summary."""
        if not rts:
            return {"trials_analyzed": 0}

        rt_array = np.array(rts)
        total_flags = sum(
            len(r["flags"]) if isinstance(r["flags"], list) else 0 for r in trial_results
        )

        return {
            "trials_analyzed": len(trial_results),
            "mean_rt": float(np.mean(rt_array)),
            "std_rt": float(np.std(rt_array)),
            "min_rt": float(np.min(rt_array)),
            "max_rt": float(np.max(rt_array)),
            "total_flags": total_flags,
        }
