"""Tests for export API endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


class TestExportSessionsCSV:
    """Tests for GET /api/v1/export/sessions/csv endpoint."""

    def test_export_sessions_csv_returns_csv(self, client: TestClient) -> None:
        """Endpoint returns CSV content."""
        response = client.get("/api/v1/export/sessions/csv")

        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")

    def test_export_sessions_csv_with_session_ids(self, client: TestClient) -> None:
        """Endpoint accepts session_ids parameter."""
        response = client.get("/api/v1/export/sessions/csv?session_ids=s1,s2")
        assert response.status_code == 200

    def test_export_sessions_csv_includes_verdicts(self, client: TestClient) -> None:
        """Endpoint accepts include_verdicts parameter."""
        response = client.get("/api/v1/export/sessions/csv?include_verdicts=false")
        assert response.status_code == 200


class TestExportTrialsCSV:
    """Tests for GET /api/v1/export/trials/csv endpoint."""

    def test_export_trials_csv_returns_csv(self, client: TestClient) -> None:
        """Endpoint returns CSV content."""
        response = client.get("/api/v1/export/trials/csv")

        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")


class TestExportKeystrokesCSV:
    """Tests for GET /api/v1/export/keystrokes/csv endpoint."""

    def test_export_keystrokes_csv_returns_csv(self, client: TestClient) -> None:
        """Endpoint returns CSV content."""
        response = client.get("/api/v1/export/keystrokes/csv?session_id=test")

        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")

    def test_export_keystrokes_csv_requires_session_id(self, client: TestClient) -> None:
        """Endpoint requires session_id parameter."""
        response = client.get("/api/v1/export/keystrokes/csv")
        assert response.status_code == 422


class TestExportVerdictsCSV:
    """Tests for GET /api/v1/export/verdicts/csv endpoint."""

    def test_export_verdicts_csv_returns_csv(self, client: TestClient) -> None:
        """Endpoint returns CSV content."""
        response = client.get("/api/v1/export/verdicts/csv")

        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")

    def test_export_verdicts_csv_with_filter(self, client: TestClient) -> None:
        """Endpoint accepts verdict filter."""
        response = client.get("/api/v1/export/verdicts/csv?verdict_filter=human")
        assert response.status_code == 200


class TestExportJSON:
    """Tests for POST /api/v1/export/json endpoint."""

    def test_export_json_returns_task_info(self, client: TestClient) -> None:
        """Endpoint returns task information."""
        response = client.post(
            "/api/v1/export/json",
            json={"session_ids": [], "include_metrics": True},
        )

        assert response.status_code == 200
        data = response.json()

        assert "task_id" in data
        assert "status" in data


class TestExportStatus:
    """Tests for GET /api/v1/export/status/{task_id} endpoint."""

    def test_get_export_status(self, client: TestClient) -> None:
        """Endpoint returns export status."""
        response = client.get("/api/v1/export/status/test-task")

        assert response.status_code == 200
        data = response.json()

        assert "task_id" in data
        assert "status" in data
        assert "progress" in data
