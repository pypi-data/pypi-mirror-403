"""Tests for analysis API endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


class TestAnalysisSummary:
    """Tests for GET /api/v1/analysis/summary endpoint."""

    def test_get_summary_returns_statistics(self, client: TestClient) -> None:
        """Endpoint returns analysis summary statistics."""
        response = client.get("/api/v1/analysis/summary")

        assert response.status_code == 200
        data = response.json()

        assert "total_sessions" in data
        assert "analyzed_sessions" in data
        assert "flagged_sessions" in data
        assert "verdict_distribution" in data
        assert "common_flags" in data

        assert isinstance(data["total_sessions"], int)
        assert isinstance(data["analyzed_sessions"], int)
        assert isinstance(data["verdict_distribution"], dict)


class TestFlagDistribution:
    """Tests for GET /api/v1/analysis/flags endpoint."""

    def test_get_flag_types_returns_list(self, client: TestClient) -> None:
        """Endpoint returns list of flag types."""
        response = client.get("/api/v1/analysis/flags")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)


class TestVerdictList:
    """Tests for GET /api/v1/analysis/verdicts endpoint."""

    def test_list_verdicts_returns_paginated_response(self, client: TestClient) -> None:
        """Endpoint returns paginated verdict list."""
        response = client.get("/api/v1/analysis/verdicts")

        assert response.status_code == 200
        data = response.json()

        assert "verdicts" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert isinstance(data["verdicts"], list)

    def test_list_verdicts_custom_pagination(self, client: TestClient) -> None:
        """Endpoint respects pagination parameters."""
        response = client.get("/api/v1/analysis/verdicts?page=2&page_size=10")

        assert response.status_code == 200
        data = response.json()

        assert data["page"] == 2
        assert data["page_size"] == 10


class TestBatchAnalysis:
    """Tests for POST /api/v1/analysis/batch endpoint."""

    def test_batch_analysis_specific_sessions(self, client: TestClient) -> None:
        """Endpoint accepts specific session IDs for batch analysis."""
        response = client.post(
            "/api/v1/analysis/batch",
            json={"session_ids": ["session-1", "session-2"]},
        )

        assert response.status_code == 200
        data = response.json()

        assert "task_id" in data
        assert "queued_count" in data
        assert "skipped_count" in data

    def test_batch_analysis_with_force(self, client: TestClient) -> None:
        """Endpoint accepts force_reanalyze parameter."""
        response = client.post(
            "/api/v1/analysis/batch",
            json={"session_ids": ["session-1"], "force_reanalyze": True},
        )

        assert response.status_code == 200
