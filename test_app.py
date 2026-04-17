"""Tests for loyalty-points-api."""
import concurrent.futures
import pytest
from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_health_endpoint(client):
    """Verify health check returns correct status."""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.get_json()['status'] == 'UP'


def test_create_redemption(client):
    """Verify basic redemption creation works."""
    response = client.post(
        '/api/v1/redemption',
        json={'name': 'Test Redemption', 'value': 100}
    )
    assert response.status_code == 201
    data = response.get_json()
    assert 'id' in data
    assert data['name'] == 'Test Redemption'
    assert data['value'] == 100


def test_concurrent_redemption_creation(client):
    """Verify concurrent requests generate unique IDs with no race conditions."""
    def create_redemption(index):
        response = client.post(
            '/api/v1/redemption',
            json={'name': f'Redemption {index}', 'value': 50}
        )
        assert response.status_code == 201
        return response.get_json()['id']

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(create_redemption, i) for i in range(50)]
        ids = [f.result() for f in concurrent.futures.as_completed(futures)]

    assert len(ids) == len(set(ids)), "Duplicate IDs detected in concurrent requests"
