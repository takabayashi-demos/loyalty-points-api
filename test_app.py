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


class TestSQLInjectionPrevention:
    """Verify that SQL injection payloads are neutralized."""

    @pytest.mark.parametrize("malicious_id", [
        "' OR 1=1 --",
        "1; DROP TABLE redemptions;--",
        "' UNION SELECT id,name,value,created_at FROM redemptions--",
        "1' AND '1'='1",
    ])
    def test_injection_in_path_param(self, client, malicious_id):
        """Crafted IDs should be rejected by the allowlist pattern."""
        response = client.get(f"/api/v1/redemption/{malicious_id}")
        assert response.status_code in (400, 404)

    def test_injection_in_limit_param(self, client):
        """Non-integer limit should return 400."""
        response = client.get("/api/v1/redemption?limit=1;DROP+TABLE+redemptions")
        assert response.status_code == 400

    @pytest.mark.parametrize("payload", [
        {"name": "'; DROP TABLE redemptions;--", "value": 10},
        {"name": "test", "value": "5 OR 1=1"},
    ])
    def test_injection_in_post_body(self, client, payload):
        """Injection in POST body should either be safely stored or rejected."""
        response = client.post("/api/v1/redemption", json=payload)
        if response.status_code in (200, 201):
            data = response.get_json()
            assert data["name"] == payload["name"].strip()
        else:
            assert response.status_code in (400, 422)


class TestInputSanitization:
    """Verify input length and type constraints."""

    def test_reject_missing_name(self, client):
        response = client.post("/api/v1/redemption", json={"value": 10})
        assert response.status_code == 422

    def test_reject_missing_value(self, client):
        response = client.post("/api/v1/redemption", json={"name": "test"})
        assert response.status_code == 422

    def test_reject_negative_value(self, client):
        response = client.post("/api/v1/redemption", json={"name": "test", "value": -5})
        assert response.status_code == 422

    def test_reject_oversized_name(self, client):
        long_name = "x" * 201
        response = client.post("/api/v1/redemption", json={"name": long_name, "value": 10})
        assert response.status_code == 422

    def test_reject_boolean_value(self, client):
        response = client.post("/api/v1/redemption", json={"name": "test", "value": True})
        assert response.status_code == 422

    def test_reject_empty_body(self, client):
        response = client.post("/api/v1/redemption", data="", content_type="application/json")
        assert response.status_code == 400

    def test_whitespace_name_trimmed(self, client):
        response = client.post("/api/v1/redemption", json={"name": "  padded  ", "value": 5})
        assert response.status_code == 201
        assert response.get_json()["name"] == "padded"

    def test_pagination_limit_capped(self, client):
        response = client.get("/api/v1/redemption?limit=9999")
        assert response.status_code == 200
        data = response.get_json()
        assert data["limit"] <= 100
