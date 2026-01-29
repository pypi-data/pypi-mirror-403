"""Real-time analysis service with background worker.

This module provides asynchronous analysis processing for sessions,
running behavioral analyzers in a background task queue.
"""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import Callable
from typing import TYPE_CHECKING

from slopit.behavioral import (
    FocusAnalyzer,
    KeystrokeAnalyzer,
    PasteAnalyzer,
    TimingAnalyzer,
)
from slopit.pipeline import AnalysisPipeline

if TYPE_CHECKING:
    from slopit.schemas import SlopitSession
    from slopit.schemas.analysis import PipelineResult


# Type alias for verdict callback
type VerdictCallback = Callable[[str, dict[str, str | int | float | bool | list[str] | None]], None]


class AnalysisService:
    """Background analysis service.

    Provides real-time analysis of sessions using the standard
    slopit analysis pipeline. Sessions can be queued for background
    processing or analyzed synchronously.

    Examples
    --------
    >>> service = AnalysisService()
    >>> await service.start()
    >>> await service.enqueue_session(session)
    >>> # ... later ...
    >>> await service.stop()
    """

    def __init__(self) -> None:
        self._queue: asyncio.Queue[SlopitSession] = asyncio.Queue()
        self._running = False
        self._task: asyncio.Task[None] | None = None
        self._on_complete: list[VerdictCallback] = []

        # Standard pipeline with all behavioral analyzers
        self._pipeline = AnalysisPipeline(
            [
                KeystrokeAnalyzer(),
                FocusAnalyzer(),
                PasteAnalyzer(),
                TimingAnalyzer(),
            ]
        )

    async def start(self) -> None:
        """Start the background analysis worker.

        Spawns an asyncio task that continuously processes sessions
        from the queue.
        """
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._worker())

    async def stop(self) -> None:
        """Stop the background worker.

        Cancels the worker task and waits for it to finish.
        """
        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def enqueue_session(self, session: SlopitSession) -> None:
        """Add a session to the analysis queue.

        Parameters
        ----------
        session
            Session to analyze. Will be processed asynchronously.
        """
        await self._queue.put(session)

    def on_complete(self, callback: VerdictCallback) -> None:
        """Register callback for when analysis completes.

        Parameters
        ----------
        callback
            Function to call with (session_id, verdict) when analysis finishes.
        """
        self._on_complete.append(callback)

    async def analyze_session(
        self,
        session: SlopitSession,
    ) -> dict[str, str | int | float | bool | list[str] | None]:
        """Analyze a single session synchronously.

        Parameters
        ----------
        session
            Session to analyze.

        Returns
        -------
        dict[str, str | int | float | bool | list[str] | None]
            Analysis verdict containing status, confidence, flags, and summary.
        """
        # Run the pipeline on a single session
        result: PipelineResult = self._pipeline.analyze([session])

        # Extract verdict for this session
        if session.session_id in result.verdicts:
            verdict = result.verdicts[session.session_id]
            return {
                "status": verdict.status,
                "confidence": verdict.confidence,
                "flags": [f.type for f in verdict.flags],
                "summary": verdict.summary,
            }

        return {
            "status": "clean",
            "confidence": 1.0,
            "flags": [],
            "summary": "No analysis performed",
        }

    async def _worker(self) -> None:
        """Background worker that processes queued sessions."""
        while self._running:
            try:
                session = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                verdict = await self.analyze_session(session)
                for callback in self._on_complete:
                    callback(session.session_id, verdict)
            except TimeoutError:
                continue
            except asyncio.CancelledError:
                raise
            except Exception:
                # Log error but continue processing
                # In production, this should use proper logging
                continue
