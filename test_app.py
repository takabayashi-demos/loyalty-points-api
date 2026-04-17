"""Tests for loyalty-points-api."""
import json
import pytest
from app import app


@pytest.fixture
def client():
    """Create a test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_create_redemption_with_array_payload(client):
    """Test that array payloads return 400 instead of 500."""
    response = client.post(
        "/api/v1/redemption",
        data=json.dumps([{"name": "Test", "value": 100}]),
        content_type="application/json"
    )
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert "JSON object" in data["error"]


def test_create_redemption_with_null_payload(client):
    """Test that null payloads return 400."""
    response = client.post(
        "/api/v1/redemption",
        data=json.dumps(None),
        content_type="application/json"
    )
    assert response.status_code == 400


def test_create_redemption_success(client):
    """Test successful redemption creation."""
    response = client.post(
        "/api/v1/redemption",
        data=json.dumps({"name": "Test Reward", "value": 100}),
        content_type="application/json"
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["name"] == "Test Reward"
    assert data["value"] == 100
