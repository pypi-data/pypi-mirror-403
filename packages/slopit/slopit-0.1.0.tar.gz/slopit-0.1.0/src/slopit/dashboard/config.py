"""Dashboard configuration.

This module defines the configuration model for the slopit dashboard,
including server settings, data storage paths, and integration credentials.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class DashboardConfig(BaseModel):
    """Dashboard configuration.

    Attributes
    ----------
    host
        Host address to bind the server to.
    port
        Port number to listen on.
    data_dir
        Directory for storing session data files.
    cors_origins
        List of allowed CORS origins for API requests.
    reload
        Enable auto-reload for development.
    jatos_url
        URL of the JATOS server for data synchronization.
    jatos_token
        Authentication token for JATOS API access.
    prolific_token
        Authentication token for Prolific API access.

    Examples
    --------
    >>> config = DashboardConfig(port=8080, data_dir=Path("./sessions"))
    >>> print(config.host)
    127.0.0.1
    """

    host: str = Field(default="127.0.0.1", description="Server host address")
    port: int = Field(default=8000, description="Server port number")
    data_dir: Path = Field(default=Path("./data"), description="Data storage directory")
    cors_origins: list[str] = Field(default=["*"], description="Allowed CORS origins")
    reload: bool = Field(default=False, description="Enable auto-reload")
    jatos_url: str | None = Field(default=None, description="JATOS server URL")
    jatos_token: str | None = Field(default=None, description="JATOS API token")
    prolific_token: str | None = Field(default=None, description="Prolific API token")
