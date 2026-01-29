"""Tests for dashboard application factory."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from slopit.dashboard.app import create_app
from slopit.dashboard.config import DashboardConfig

if TYPE_CHECKING:
    pass


class TestCreateApp:
    """Tests for create_app factory function."""

    def test_create_app_returns_fastapi(self) -> None:
        """Factory returns FastAPI application instance."""
        app = create_app()

        assert isinstance(app, FastAPI)
        assert app.title == "Slopit Dashboard"

    def test_create_app_with_config(self) -> None:
        """Factory accepts custom configuration."""
        config = DashboardConfig(port=9000)
        app = create_app(config)

        assert isinstance(app, FastAPI)
        assert app.state.config.port == 9000

    def test_create_app_includes_routers(self) -> None:
        """Factory includes all API routers."""
        app = create_app()
        client = TestClient(app)

        # Sessions router
        response = client.get("/api/v1/sessions/")
        assert response.status_code == 200

        # Analysis router
        response = client.get("/api/v1/analysis/summary")
        assert response.status_code == 200

        # Export router
        response = client.get("/api/v1/export/sessions/csv")
        assert response.status_code == 200

    def test_create_app_cors_enabled(self) -> None:
        """Factory enables CORS middleware."""
        config = DashboardConfig(cors_origins=["http://localhost:3000"])
        app = create_app(config)
        client = TestClient(app)

        response = client.options(
            "/api/v1/sessions",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )

        # CORS preflight should return 200
        assert response.status_code == 200

    def test_create_app_websocket_endpoint(self) -> None:
        """Factory includes WebSocket endpoint."""
        app = create_app()
        client = TestClient(app)

        # WebSocket endpoint exists
        with client.websocket_connect("/ws") as websocket:
            # Connection should be established
            assert websocket is not None


class TestDashboardConfig:
    """Tests for DashboardConfig."""

    def test_default_config(self) -> None:
        """Default configuration has expected values."""
        config = DashboardConfig()

        assert config.host == "127.0.0.1"
        assert config.port == 8000
        assert isinstance(config.cors_origins, list)

    def test_custom_config(self) -> None:
        """Custom configuration overrides defaults."""
        config = DashboardConfig(
            host="0.0.0.0",
            port=9000,
            cors_origins=["http://example.com"],
        )

        assert config.host == "0.0.0.0"
        assert config.port == 9000
        assert config.cors_origins == ["http://example.com"]
