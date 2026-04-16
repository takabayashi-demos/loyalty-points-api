"""Shared fixtures for loyalty-points-api tests."""
import os
import tempfile

import pytest

os.environ["DATABASE_PATH"] = ":memory:"

from app import app as flask_app, init_db  # noqa: E402


@pytest.fixture()
def app():
    flask_app.config["TESTING"] = True
    with flask_app.app_context():
        init_db()
    yield flask_app


@pytest.fixture()
def client(app):
    return app.test_client()
