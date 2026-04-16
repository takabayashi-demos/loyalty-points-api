"""Tests for redemption in loyalty-points-api."""
import pytest
import time


class TestRedemption:
    """Test suite for redemption operations."""

    def test_health_endpoint(self, client):
        """Health endpoint should return UP."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "UP"

    def test_redemption_create(self, client):
        """Should create a new redemption entry."""
        payload = {"name": "test", "value": 42}
        response = client.post("/api/v1/redemption", json=payload)
        assert response.status_code in (200, 201)

    def test_redemption_validation(self, client):
        """Should reject invalid redemption data."""
        response = client.post("/api/v1/redemption", json={})
        assert response.status_code in (400, 422)

    def test_redemption_not_found(self, client):
        """Should return 404 for missing redemption."""
        response = client.get("/api/v1/redemption/nonexistent")
        assert response.status_code == 404

    @pytest.mark.parametrize("limit", [1, 10, 50, 100])
    def test_redemption_pagination(self, client, limit):
        """Should respect pagination limits."""
        response = client.get(f"/api/v1/redemption?limit={limit}")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data.get("items", data.get("redemptions", []))) <= limit

    def test_redemption_pagination_exact_count(self, client):
        """Requesting limit=10 with 15 records should return exactly 10."""
        for i in range(15):
            client.post("/api/v1/redemption", json={"name": f"item-{i}", "value": i + 1})

        response = client.get("/api/v1/redemption?limit=10")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["items"]) == 10, (
            f"Expected exactly 10 items, got {len(data['items'])}"
        )

    def test_redemption_rejects_zero_value(self, client):
        """Should reject redemption with value=0."""
        response = client.post("/api/v1/redemption", json={"name": "bad", "value": 0})
        assert response.status_code == 400

    def test_redemption_rejects_negative_value(self, client):
        """Should reject redemption with negative value."""
        response = client.post("/api/v1/redemption", json={"name": "bad", "value": -5})
        assert response.status_code == 400

    def test_redemption_performance(self, client):
        """Response time should be under 500ms."""
        start = time.monotonic()
        response = client.get("/api/v1/redemption")
        elapsed = time.monotonic() - start
        assert elapsed < 0.5, f"Took {elapsed:.2f}s, expected <0.5s"
