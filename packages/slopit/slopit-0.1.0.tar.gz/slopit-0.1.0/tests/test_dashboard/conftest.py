"""Fixtures for dashboard tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from fastapi.testclient import TestClient

from slopit.dashboard.app import create_app
from slopit.dashboard.config import DashboardConfig

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture
def dashboard_config() -> DashboardConfig:
    """Create test dashboard configuration."""
    return DashboardConfig(
        host="127.0.0.1",
        port=8000,
        cors_origins=["*"],
    )


@pytest.fixture
def app(dashboard_config: DashboardConfig) -> TestClient:
    """Create test FastAPI application."""
    application = create_app(dashboard_config)
    return TestClient(application)


@pytest.fixture
def client(app: TestClient) -> Generator[TestClient, None, None]:
    """Create test client for dashboard API."""
    yield app
