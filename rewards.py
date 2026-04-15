"""Tests for transfer in loyalty-points-api."""
import pytest
import time


class TestTransfer:
    """Test suite for transfer operations."""

    def test_health_endpoint(self, client):
        """Health endpoint should return UP."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "UP"

    def test_transfer_create(self, client):
        """Should create a new transfer entry."""
        payload = {"name": "test", "value": 42}
        response = client.post("/api/v1/transfer", json=payload)
        assert response.status_code in (200, 201)

    def test_transfer_validation(self, client):
        """Should reject invalid transfer data."""
        response = client.post("/api/v1/transfer", json={})
        assert response.status_code in (400, 422)

    def test_transfer_not_found(self, client):
        """Should return 404 for missing transfer."""
        response = client.get("/api/v1/transfer/nonexistent")
        assert response.status_code == 404

    @pytest.mark.parametrize("limit", [1, 10, 50, 100])
    def test_transfer_pagination(self, client, limit):
        """Should respect pagination limits."""
        response = client.get(f"/api/v1/transfer?limit={limit}")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data.get("items", data.get("transfers", []))) <= limit

    def test_transfer_performance(self, client):
        """Response time should be under 500ms."""
        start = time.monotonic()
        response = client.get("/api/v1/transfer")
        elapsed = time.monotonic() - start
        assert elapsed < 0.5, f"Took {elapsed:.2f}s, expected <0.5s"
