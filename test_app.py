"""Tests for loyalty-points-api input validation and security controls."""
import pytest
from app import app, _redemptions, NAME_MAX_LENGTH, VALUE_MAX


@pytest.fixture(autouse=True)
def reset_state():
    import app as app_module
    app_module._redemptions.clear()
    app_module._next_id = 1
    yield


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


class TestHealth:
    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "UP"


class TestCreateRedemption:
    def test_valid_creation(self, client):
        resp = client.post("/api/v1/redemption",
                           json={"name": "Free Coffee", "value": 500})
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["name"] == "Free Coffee"
        assert data["value"] == 500

    def test_rejects_non_json_content_type(self, client):
        resp = client.post("/api/v1/redemption",
                           data="not json",
                           content_type="text/plain")
        assert resp.status_code == 415

    def test_rejects_missing_name(self, client):
        resp = client.post("/api/v1/redemption",
                           json={"value": 100})
        assert resp.status_code == 400
        assert any("name" in e for e in resp.get_json()["errors"])

    def test_rejects_non_string_name(self, client):
        resp = client.post("/api/v1/redemption",
                           json={"name": 12345, "value": 100})
        assert resp.status_code == 400

    def test_rejects_blank_name(self, client):
        resp = client.post("/api/v1/redemption",
                           json={"name": "   ", "value": 100})
        assert resp.status_code == 400

    def test_rejects_long_name(self, client):
        resp = client.post("/api/v1/redemption",
                           json={"name": "A" * (NAME_MAX_LENGTH + 1), "value": 100})
        assert resp.status_code == 400

    def test_strips_whitespace_from_name(self, client):
        resp = client.post("/api/v1/redemption",
                           json={"name": "  Latte  ", "value": 200})
        assert resp.status_code == 201
        assert resp.get_json()["name"] == "Latte"

    def test_rejects_missing_value(self, client):
        resp = client.post("/api/v1/redemption",
                           json={"name": "Test"})
        assert resp.status_code == 400

    def test_rejects_zero_value(self, client):
        resp = client.post("/api/v1/redemption",
                           json={"name": "Test", "value": 0})
        assert resp.status_code == 400

    def test_rejects_negative_value(self, client):
        resp = client.post("/api/v1/redemption",
                           json={"name": "Test", "value": -10})
        assert resp.status_code == 400

    def test_rejects_value_exceeding_max(self, client):
        resp = client.post("/api/v1/redemption",
                           json={"name": "Test", "value": VALUE_MAX + 1})
        assert resp.status_code == 400

    def test_rejects_boolean_value(self, client):
        resp = client.post("/api/v1/redemption",
                           json={"name": "Test", "value": True})
        assert resp.status_code == 400


class TestListRedemptions:
    def test_pagination_defaults(self, client):
        resp = client.get("/api/v1/redemption")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["limit"] == 20
        assert data["offset"] == 0

    def test_limit_capped_at_100(self, client):
        resp = client.get("/api/v1/redemption?limit=999")
        data = resp.get_json()
        assert data["limit"] == 100

    def test_negative_offset_clamped(self, client):
        resp = client.get("/api/v1/redemption?offset=-5")
        data = resp.get_json()
        assert data["offset"] == 0


class TestGetRedemption:
    def test_not_found(self, client):
        resp = client.get("/api/v1/redemption/999")
        assert resp.status_code == 404

    def test_found(self, client):
        client.post("/api/v1/redemption",
                     json={"name": "Gift Card", "value": 1000})
        resp = client.get("/api/v1/redemption/1")
        assert resp.status_code == 200
        assert resp.get_json()["name"] == "Gift Card"
