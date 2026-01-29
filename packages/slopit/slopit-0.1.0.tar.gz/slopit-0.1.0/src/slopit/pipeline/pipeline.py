"""Analysis pipeline for orchestrating multiple analyzers.

This module provides the main AnalysisPipeline class that runs
analyzers and aggregates their results.
"""

from dataclasses import dataclass
from typing import Literal

from slopit.behavioral.base import Analyzer
from slopit.pipeline.aggregation import AggregationStrategy, aggregate_flags
from slopit.schemas import SlopitSession
from slopit.schemas.analysis import AnalysisResult, PipelineResult, SessionVerdict
from slopit.schemas.flags import AnalysisFlag


@dataclass
class PipelineConfig:
    """Configuration for the analysis pipeline.

    Attributes
    ----------
    aggregation
        Strategy for combining flags from multiple analyzers.
        - "any": Flag if any analyzer flags
        - "majority": Flag if majority of analyzers flag
        - "weighted": Use confidence-weighted voting
    severity_threshold
        Minimum severity level to include in final verdict.
    confidence_threshold
        Minimum confidence to include flag in aggregation.
    """

    aggregation: AggregationStrategy = "weighted"
    severity_threshold: Literal["info", "low", "medium", "high"] = "low"
    confidence_threshold: float = 0.5


class AnalysisPipeline:
    """Orchestrates multiple analyzers and aggregates results.

    The pipeline runs each analyzer on the input sessions, combines
    their flags according to the configured strategy, and produces
    a unified result.

    Parameters
    ----------
    analyzers
        List of analyzers to run.
    config
        Pipeline configuration.

    Examples
    --------
    >>> from slopit import load_sessions
    >>> from slopit.pipeline import AnalysisPipeline
    >>> from slopit.behavioral import KeystrokeAnalyzer
    >>>
    >>> sessions = load_sessions("data/")
    >>> pipeline = AnalysisPipeline([KeystrokeAnalyzer()])
    >>> result = pipeline.analyze(sessions)
    >>>
    >>> for session_id, verdict in result.verdicts.items():
    ...     print(f"{session_id}: {verdict.status}")
    """

    def __init__(
        self,
        analyzers: list[Analyzer],
        config: PipelineConfig | None = None,
    ) -> None:
        self.analyzers = analyzers
        self.config = config or PipelineConfig()

    def analyze(self, sessions: list[SlopitSession]) -> PipelineResult:
        """Run all analyzers and aggregate results.

        Parameters
        ----------
        sessions
            Sessions to analyze.

        Returns
        -------
        PipelineResult
            Combined results from all analyzers.
        """
        # Run each analyzer
        analyzer_results: dict[str, list[AnalysisResult]] = {}

        for analyzer in self.analyzers:
            results = analyzer.analyze_sessions(sessions)
            analyzer_results[analyzer.name] = results

        # Aggregate flags per session
        session_flags: dict[str, list[AnalysisFlag]] = {}

        for session in sessions:
            flags = self._collect_session_flags(session.session_id, analyzer_results)
            filtered = self._filter_flags(flags)
            session_flags[session.session_id] = filtered

        # Compute verdicts
        verdicts = {
            session_id: self._compute_verdict(flags) for session_id, flags in session_flags.items()
        }

        return PipelineResult(
            sessions=[s.session_id for s in sessions],
            analyzer_results=analyzer_results,
            aggregated_flags=session_flags,
            verdicts=verdicts,
        )

    def _collect_session_flags(
        self,
        session_id: str,
        analyzer_results: dict[str, list[AnalysisResult]],
    ) -> list[AnalysisFlag]:
        """Collect all flags for a session from all analyzers."""
        flags: list[AnalysisFlag] = []

        for results in analyzer_results.values():
            for result in results:
                if result.session_id == session_id:
                    flags.extend(result.flags)

        return flags

    def _filter_flags(self, flags: list[AnalysisFlag]) -> list[AnalysisFlag]:
        """Filter flags based on configuration."""
        severity_order = ["info", "low", "medium", "high"]
        threshold_idx = severity_order.index(self.config.severity_threshold)

        filtered: list[AnalysisFlag] = []
        for flag in flags:
            flag_idx = severity_order.index(flag.severity)
            if flag_idx < threshold_idx:
                continue

            if flag.confidence is not None and flag.confidence < self.config.confidence_threshold:
                continue

            filtered.append(flag)

        return filtered

    def _compute_verdict(self, flags: list[AnalysisFlag]) -> SessionVerdict:
        """Compute final verdict for a session."""
        if not flags:
            return SessionVerdict(
                status="clean",
                confidence=1.0,
                flags=[],
                summary="No flags detected",
            )

        status, confidence = aggregate_flags(
            flags,
            self.config.aggregation,
            len(self.analyzers),
        )

        return SessionVerdict(
            status=status,
            confidence=confidence,
            flags=flags,
            summary=self._generate_summary(flags),
        )

    def _generate_summary(self, flags: list[AnalysisFlag]) -> str:
        """Generate human-readable summary of flags."""
        if not flags:
            return "No issues detected"

        flag_types = sorted({f.type for f in flags})
        return f"Detected: {', '.join(flag_types)}"
