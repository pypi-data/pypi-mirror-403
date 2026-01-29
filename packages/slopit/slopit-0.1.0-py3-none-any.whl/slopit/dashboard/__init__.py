"""Dashboard module for slopit.

This module provides a web-based dashboard for real-time monitoring and
analysis of behavioral data from crowdsourced experiments.

Example
-------
>>> from slopit.dashboard import DashboardConfig, create_app
>>> config = DashboardConfig(port=8080)
>>> app = create_app(config)
"""

from __future__ import annotations

from slopit.dashboard.config import DashboardConfig

__all__ = [
    "DashboardConfig",
]
