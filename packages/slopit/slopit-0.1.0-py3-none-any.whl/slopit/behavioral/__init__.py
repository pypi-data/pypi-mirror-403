"""Behavioral analyzers for slopit.

This module provides analyzers for keystroke dynamics, focus patterns,
timing, and paste events.
"""

from slopit.behavioral.base import Analyzer, AnalyzerConfig
from slopit.behavioral.focus import FocusAnalyzer, FocusAnalyzerConfig
from slopit.behavioral.keystroke import KeystrokeAnalyzer, KeystrokeAnalyzerConfig
from slopit.behavioral.paste import PasteAnalyzer, PasteAnalyzerConfig
from slopit.behavioral.timing import TimingAnalyzer, TimingAnalyzerConfig

__all__ = [
    "Analyzer",
    "AnalyzerConfig",
    "FocusAnalyzer",
    "FocusAnalyzerConfig",
    "KeystrokeAnalyzer",
    "KeystrokeAnalyzerConfig",
    "PasteAnalyzer",
    "PasteAnalyzerConfig",
    "TimingAnalyzer",
    "TimingAnalyzerConfig",
]
