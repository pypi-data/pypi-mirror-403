"""Keystroke dynamics analyzer.

This module provides analysis of keystroke patterns to detect
transcription versus authentic composition.
"""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from slopit.behavioral.base import Analyzer, AnalyzerConfig
from slopit.schemas import KeystrokeEvent, KeystrokeMetrics, SlopitSession, SlopitTrial
from slopit.schemas.analysis import AnalysisResult
from slopit.schemas.flags import AnalysisFlag
from slopit.schemas.types import JsonValue


@dataclass
class KeystrokeAnalyzerConfig(AnalyzerConfig):
    """Configuration for keystroke analysis.

    Attributes
    ----------
    pause_threshold_ms
        Minimum IKI to count as a pause (milliseconds).
    burst_threshold_ms
        Maximum IKI within a typing burst (milliseconds).
    min_keystrokes
        Minimum keystrokes required for analysis.
    min_iki_std_threshold
        Minimum IKI standard deviation for authentic typing.
        Lower values suggest transcription.
    max_ppr_threshold
        Maximum product-process ratio for authentic typing.
        Higher values suggest minimal revision.
    """

    pause_threshold_ms: float = 2000.0
    burst_threshold_ms: float = 500.0
    min_keystrokes: int = 20
    min_iki_std_threshold: float = 100.0
    max_ppr_threshold: float = 0.95


class KeystrokeAnalyzer(Analyzer):
    """Analyzer for keystroke dynamics.

    Detects transcription patterns by analyzing inter-keystroke intervals,
    revision behavior, and typing burst characteristics.

    Parameters
    ----------
    config
        Analyzer configuration.

    Examples
    --------
    >>> from slopit import load_session
    >>> from slopit.behavioral import KeystrokeAnalyzer
    >>>
    >>> session = load_session("data/session.json")
    >>> analyzer = KeystrokeAnalyzer()
    >>> result = analyzer.analyze_session(session)
    >>>
    >>> for flag in result.flags:
    ...     print(f"{flag.type}: {flag.message}")
    """

    def __init__(self, config: KeystrokeAnalyzerConfig | None = None) -> None:
        self.config = config or KeystrokeAnalyzerConfig()

    @property
    def name(self) -> str:
        return "keystroke"

    def analyze_session(self, session: SlopitSession) -> AnalysisResult:
        """Analyze keystroke patterns for a session."""
        trial_results: list[dict[str, JsonValue]] = []
        trial_metrics: list[KeystrokeMetrics] = []
        all_flags: list[AnalysisFlag] = []

        for trial in session.trials:
            if not self._has_sufficient_data(trial):
                continue

            # Safe to assert: _has_sufficient_data validates these are not None
            assert trial.behavioral is not None
            assert trial.behavioral.keystrokes is not None
            keystrokes = trial.behavioral.keystrokes
            metrics = self._compute_metrics(keystrokes)
            flags = self._compute_flags(trial.trial_id, metrics)

            trial_results.append(
                {
                    "trial_id": trial.trial_id,
                    "metrics": metrics.model_dump(),
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

    def _has_sufficient_data(self, trial: SlopitTrial) -> bool:
        """Check if trial has sufficient keystroke data."""
        if trial.behavioral is None:
            return False

        keystrokes = trial.behavioral.keystrokes
        if keystrokes is None:
            return False
        return len(keystrokes) >= self.config.min_keystrokes

    def _compute_metrics(self, keystrokes: list[KeystrokeEvent]) -> KeystrokeMetrics:
        """Compute metrics from keystroke events."""
        keydowns = [k for k in keystrokes if k.event == "keydown"]
        ikis = self._compute_ikis(keydowns)

        printable = sum(1 for k in keydowns if len(k.key) == 1)
        deletions = sum(1 for k in keydowns if k.key in {"Backspace", "Delete"})

        pause_count = sum(1 for iki in ikis if iki > self.config.pause_threshold_ms)

        final_length = keydowns[-1].text_length if keydowns and keydowns[-1].text_length else 0
        total = len(keydowns)
        ppr = final_length / total if total > 0 else 0.0

        return KeystrokeMetrics(
            total_keystrokes=len(keydowns),
            printable_keystrokes=printable,
            deletions=deletions,
            mean_iki=float(np.mean(ikis)) if len(ikis) > 0 else 0.0,
            std_iki=float(np.std(ikis)) if len(ikis) > 0 else 0.0,
            median_iki=float(np.median(ikis)) if len(ikis) > 0 else 0.0,
            pause_count=pause_count,
            product_process_ratio=ppr,
        )

    def _compute_ikis(self, keydowns: list[KeystrokeEvent]) -> NDArray[np.float64]:
        """Compute inter-keystroke intervals."""
        if len(keydowns) < 2:
            return np.array([], dtype=np.float64)

        times = np.array([k.time for k in keydowns], dtype=np.float64)
        return np.diff(times)

    def _compute_flags(self, trial_id: str, metrics: KeystrokeMetrics) -> list[AnalysisFlag]:
        """Generate flags based on metrics."""
        flags: list[AnalysisFlag] = []

        if metrics.std_iki < self.config.min_iki_std_threshold:
            flags.append(
                AnalysisFlag(
                    type="low_iki_variance",
                    analyzer=self.name,
                    severity="medium",
                    message=f"Keystroke timing unusually consistent (std={metrics.std_iki:.1f}ms)",
                    confidence=self._iki_confidence(metrics.std_iki),
                    evidence={"std_iki": metrics.std_iki},
                    trial_ids=[trial_id],
                )
            )

        if metrics.product_process_ratio > self.config.max_ppr_threshold:
            flags.append(
                AnalysisFlag(
                    type="minimal_revision",
                    analyzer=self.name,
                    severity="low",
                    message=f"Very few revisions during composition (PPR={metrics.product_process_ratio:.2f})",
                    confidence=0.6,
                    evidence={"product_process_ratio": metrics.product_process_ratio},
                    trial_ids=[trial_id],
                )
            )

        if metrics.deletions == 0 and metrics.total_keystrokes > 50:
            flags.append(
                AnalysisFlag(
                    type="no_deletions",
                    analyzer=self.name,
                    severity="low",
                    message="No deletion keystrokes in extended response",
                    confidence=0.5,
                    evidence={
                        "deletions": 0,
                        "total_keystrokes": metrics.total_keystrokes,
                    },
                    trial_ids=[trial_id],
                )
            )

        return flags

    def _iki_confidence(self, std_iki: float) -> float:
        """Compute confidence for IKI variance flag."""
        threshold = self.config.min_iki_std_threshold
        if std_iki >= threshold:
            return 0.0

        return min(1.0, (threshold - std_iki) / threshold)

    def _compute_session_summary(
        self, trial_metrics: list[KeystrokeMetrics], trial_results: list[dict[str, JsonValue]]
    ) -> dict[str, JsonValue]:
        """Compute session-level summary."""
        if not trial_metrics:
            return {"trials_analyzed": 0}

        all_mean_ikis = [m.mean_iki for m in trial_metrics]
        all_std_ikis = [m.std_iki for m in trial_metrics]
        total_flags = sum(
            len(r["flags"]) if isinstance(r["flags"], list) else 0 for r in trial_results
        )

        return {
            "trials_analyzed": len(trial_metrics),
            "mean_iki_across_trials": float(np.mean(all_mean_ikis)),
            "std_iki_across_trials": float(np.mean(all_std_ikis)),
            "total_flags": total_flags,
        }
