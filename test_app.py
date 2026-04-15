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

    def test_redemption_performance(self, client):
        """Response time should be under 500ms."""
        start = time.monotonic()
        response = client.get("/api/v1/redemption")
        elapsed = time.monotonic() - start
        assert elapsed < 0.5, f"Took {elapsed:.2f}s, expected <0.5s"

    def test_cached_response_faster(self, client):
        """Second request should be served from cache and be faster."""
        # Prime the cache
        resp1 = client.get("/api/v1/redemption?limit=10")
        assert resp1.status_code == 200

        start = time.monotonic()
        resp2 = client.get("/api/v1/redemption?limit=10")
        cached_elapsed = time.monotonic() - start

        assert resp2.status_code == 200
        assert resp1.get_json() == resp2.get_json()
        assert cached_elapsed < 0.1, f"Cached request took {cached_elapsed:.2f}s"

    def test_cache_invalidation_on_create(self, client):
        """Creating a redemption should invalidate list cache."""
        # Prime list cache
        client.get("/api/v1/redemption")

        # Create a new entry — should bust the cache
        payload = {"name": "cache-test", "value": 99}
        resp = client.post("/api/v1/redemption", json=payload)
        assert resp.status_code == 201

        # Subsequent list should reflect new entry
        resp2 = client.get("/api/v1/redemption")
        assert resp2.status_code == 200
        items = resp2.get_json().get("items", [])
        assert any(item["name"] == "cache-test" for item in items)

    def test_batch_create(self, client):
        """Batch endpoint should create multiple redemptions."""
        payload = {
            "items": [
                {"name": "batch-1", "value": 10},
                {"name": "batch-2", "value": 20},
                {"name": "batch-3", "value": 30},
            ]
        }
        response = client.post("/api/v1/redemption/batch", json=payload)
        assert response.status_code == 201
        data = response.get_json()
        assert data["created"] == 3
        assert len(data["items"]) == 3

    def test_batch_validation(self, client):
        """Batch endpoint should reject items missing required fields."""
        payload = {
            "items": [
                {"name": "valid", "value": 10},
                {"value": 20},  # missing name
            ]
        }
        response = client.post("/api/v1/redemption/batch", json=payload)
        assert response.status_code == 400
        data = response.get_json()
        assert "details" in data

    def test_batch_empty(self, client):
        """Batch endpoint should reject empty items array."""
        response = client.post("/api/v1/redemption/batch", json={"items": []})
        assert response.status_code == 400

    def test_batch_exceeds_limit(self, client):
        """Batch endpoint should reject payloads exceeding max size."""
        payload = {"items": [{"name": f"item-{i}", "value": i} for i in range(101)]}
        response = client.post("/api/v1/redemption/batch", json=payload)
        assert response.status_code == 400
