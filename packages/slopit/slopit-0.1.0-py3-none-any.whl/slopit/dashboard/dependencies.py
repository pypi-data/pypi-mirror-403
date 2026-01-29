"""Dependency injection for the dashboard.

This module provides FastAPI dependency injection functions for accessing
services, configuration, and other shared resources.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from slopit.dashboard.config import DashboardConfig

# Global configuration instance (set during app startup)
_config: DashboardConfig | None = None


def get_config() -> DashboardConfig:
    """Get the current dashboard configuration.

    Returns
    -------
    DashboardConfig
        The active configuration instance.

    Raises
    ------
    RuntimeError
        If configuration has not been initialized.

    Examples
    --------
    >>> # In a FastAPI route:
    >>> # config: DashboardConfig = Depends(get_config)
    """
    if _config is None:
        raise RuntimeError(
            "Dashboard configuration not initialized. Call set_config() during application startup."
        )
    return _config


def set_config(config: DashboardConfig) -> None:
    """Set the dashboard configuration.

    Parameters
    ----------
    config
        Configuration instance to use for the application.

    Examples
    --------
    >>> config = DashboardConfig(port=8080)
    >>> set_config(config)
    """
    global _config
    _config = config
