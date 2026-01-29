"""Tests for session API endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


class TestListSessions:
    """Tests for GET /api/v1/sessions endpoint."""

    def test_list_sessions_returns_paginated_response(self, client: TestClient) -> None:
        """Endpoint returns properly structured paginated response."""
        response = client.get("/api/v1/sessions/")

        assert response.status_code == 200
        data = response.json()

        assert "sessions" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data

        assert isinstance(data["sessions"], list)
        assert isinstance(data["total"], int)
        assert data["page"] == 1
        assert data["page_size"] == 20

    def test_list_sessions_custom_pagination(self, client: TestClient) -> None:
        """Endpoint respects custom pagination parameters."""
        response = client.get("/api/v1/sessions/?page=2&page_size=50")

        assert response.status_code == 200
        data = response.json()

        assert data["page"] == 2
        assert data["page_size"] == 50

    def test_list_sessions_invalid_page(self, client: TestClient) -> None:
        """Endpoint rejects invalid page number."""
        response = client.get("/api/v1/sessions/?page=0")
        assert response.status_code == 422

    def test_list_sessions_invalid_page_size(self, client: TestClient) -> None:
        """Endpoint rejects page size over limit."""
        response = client.get("/api/v1/sessions/?page_size=200")
        assert response.status_code == 422

    def test_list_sessions_filter_by_verdict(self, client: TestClient) -> None:
        """Endpoint accepts has_verdict filter."""
        response = client.get("/api/v1/sessions/?has_verdict=true")
        assert response.status_code == 200

        response = client.get("/api/v1/sessions/?has_verdict=false")
        assert response.status_code == 200


class TestGetSession:
    """Tests for GET /api/v1/sessions/{session_id} endpoint."""

    def test_get_session_not_found(self, client: TestClient) -> None:
        """Endpoint returns 404 for non-existent session."""
        response = client.get("/api/v1/sessions/nonexistent-id")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "nonexistent-id" in data["detail"]


class TestGetSessionTrials:
    """Tests for GET /api/v1/sessions/{session_id}/trials endpoint."""

    def test_get_session_trials_returns_list(self, client: TestClient) -> None:
        """Endpoint returns list of trial summaries."""
        response = client.get("/api/v1/sessions/test-session/trials")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)


class TestGetSessionVerdict:
    """Tests for GET /api/v1/sessions/{session_id}/verdict endpoint."""

    def test_get_session_verdict_not_found(self, client: TestClient) -> None:
        """Endpoint returns 404 when verdict not found."""
        response = client.get("/api/v1/sessions/test-session/verdict")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
