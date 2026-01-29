"""Tests for trials API endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


class TestGetTrial:
    """Tests for GET /api/v1/trials/{session_id}/{trial_index} endpoint."""

    def test_get_trial_not_found(self, client: TestClient) -> None:
        """Endpoint returns 404 for non-existent trial."""
        response = client.get("/api/v1/trials/nonexistent-session/0")

        assert response.status_code == 404


class TestGetTrialBehavioral:
    """Tests for GET /api/v1/trials/{session_id}/{trial_index}/behavioral endpoint."""

    def test_get_trial_behavioral_not_found(self, client: TestClient) -> None:
        """Endpoint returns 404 for non-existent trial."""
        response = client.get("/api/v1/trials/nonexistent-session/0/behavioral")

        assert response.status_code == 404


class TestGetTrialMetrics:
    """Tests for GET /api/v1/trials/{session_id}/{trial_index}/metrics endpoint."""

    def test_get_trial_metrics_not_found(self, client: TestClient) -> None:
        """Endpoint returns 404 for non-existent trial."""
        response = client.get("/api/v1/trials/nonexistent-session/0/metrics")

        assert response.status_code == 404
