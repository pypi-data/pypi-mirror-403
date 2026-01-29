"""Base classes for behavioral analyzers.

This module defines the interface that all analyzers must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from slopit.schemas import SlopitSession
from slopit.schemas.analysis import AnalysisResult


@dataclass
class AnalyzerConfig:
    """Base configuration for analyzers."""

    pass


class Analyzer(ABC):
    """Base class for all analyzers.

    Analyzers process session data and produce analysis results
    containing metrics and flags.

    Attributes
    ----------
    name
        Unique identifier for this analyzer.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this analyzer."""
        ...

    @abstractmethod
    def analyze_session(self, session: SlopitSession) -> AnalysisResult:
        """Analyze a single session.

        Parameters
        ----------
        session
            Session data to analyze.

        Returns
        -------
        AnalysisResult
            Analysis results including metrics and flags.
        """
        ...

    def analyze_sessions(self, sessions: list[SlopitSession]) -> list[AnalysisResult]:
        """Analyze multiple sessions.

        Override this method for cross-session analysis
        (e.g., homogeneity detection).

        Parameters
        ----------
        sessions
            List of sessions to analyze.

        Returns
        -------
        list[AnalysisResult]
            Analysis results for each session.
        """
        return [self.analyze_session(s) for s in sessions]
