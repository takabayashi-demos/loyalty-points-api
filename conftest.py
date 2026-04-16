"""Shared test fixtures for loyalty-points-api."""
import pytest
from app import app, _redemptions


@pytest.fixture()
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        _redemptions.clear()
        yield c
    _redemptions.clear()
