"""External service integrations for the slopit dashboard.

This subpackage provides API clients for integrating with external
services such as JATOS and Prolific.
"""

from __future__ import annotations

from slopit.dashboard.integrations.jatos import JATOSClient
from slopit.dashboard.integrations.prolific import (
    ParticipantAction,
    ProlificClient,
    SubmissionStatus,
)

__all__ = [
    "JATOSClient",
    "ParticipantAction",
    "ProlificClient",
    "SubmissionStatus",
]
