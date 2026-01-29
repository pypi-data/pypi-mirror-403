"""slopit: AI response detection toolkit for crowdsourced behavioral research.

This package provides tools for detecting AI-assisted responses in
crowdsourced behavioral research through keystroke dynamics, focus patterns,
stylometric analysis, and response homogeneity detection.

Example
-------
>>> from slopit import load_session, load_sessions
>>> from slopit.pipeline import AnalysisPipeline
>>> from slopit.behavioral import KeystrokeAnalyzer
>>>
>>> sessions = load_sessions("data/")
>>> pipeline = AnalysisPipeline([KeystrokeAnalyzer()])
>>> result = pipeline.analyze(sessions)
"""

from slopit.io import load_session, load_sessions
from slopit.schemas import SlopitSession, SlopitTrial

__version__ = "0.1.0"

__all__ = [
    "SlopitSession",
    "SlopitTrial",
    "__version__",
    "load_session",
    "load_sessions",
]
