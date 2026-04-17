"""Tests for loyalty-points-api."""
import pytest
from app import app, _redemptions, _next_id


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health_endpoint_exempt_from_rate_limiting(client):
    """Health endpoint should be exempt from rate limits."""
    for _ in range(150):
        response = client.get("/health")
        assert response.status_code == 200


def test_post_rate_limiting(client):
    """POST endpoint should enforce 10 requests per minute limit."""
    # First 10 requests should succeed
    for i in range(10):
        response = client.post(
            "/api/v1/redemption",
            json={"name": f"Test {i}", "value": 100}
        )
        assert response.status_code == 201

    # 11th request should be rate limited
    response = client.post(
        "/api/v1/redemption",
        json={"name": "Should fail", "value": 100}
    )
    assert response.status_code == 429


def test_get_rate_limiting(client):
    """GET endpoints should enforce 50 requests per minute limit."""
    # First 50 requests should succeed
    for _ in range(50):
        response = client.get("/api/v1/redemption")
        assert response.status_code == 200

    # 51st request should be rate limited
    response = client.get("/api/v1/redemption")
    assert response.status_code == 429


def test_rate_limit_headers_present(client):
    """Response should include X-RateLimit headers."""
    response = client.get("/api/v1/redemption")
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers
