import pytest
from app import app
from jwt_module import generate_jwt

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_get_country_destination_success(client):
    """Test /api/order/<UPC_ID>/country_destination endpoint for a valid UPC_ID."""
    token = generate_jwt("UPC_1")
    response = client.get(
        '/api/order/UPC_1/country_destination',
        headers={"Authorization": token}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['UPC_ID'] == 'UPC_1'
    assert 'country' in data
    assert 'province' in data
    assert 'city' in data
    assert 'time' in data

def test_get_country_destination_missing_token(client):
    """Test /api/order/<UPC_ID>/country_destination endpoint with no token."""
    response = client.get('/api/order/UPC_1/country_destination')
    assert response.status_code == 401
    data = response.get_json()
    assert data['error'] == 'Missing authorization token'

def test_get_postalcode_destination_success(client):
    """Test /api/order/<UPC_ID>/postalcode_destination endpoint for a valid UPC_ID."""
    token = generate_jwt("UPC_2")
    response = client.get(
        '/api/order/UPC_2/postalcode_destination',
        headers={"Authorization": token}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['UPC_ID'] == 'UPC_2'
    assert 'postal_code' in data
    assert 'time' in data

def test_get_postalcode_destination_not_found(client):
    """Test /api/order/<UPC_ID>/postalcode_destination endpoint for an invalid UPC_ID."""
    token = generate_jwt("UPC_999")
    response = client.get(
        '/api/order/UPC_999/postalcode_destination',
        headers={"Authorization": token}
    )
    assert response.status_code == 404
    data = response.get_json()
    assert data['error'] == 'UPC_ID not found'

def test_get_door_destination_success(client):
    """Test /api/order/<UPC_ID>/door_destination endpoint for a valid UPC_ID."""
    token = generate_jwt("UPC_3")
    response = client.get(
        '/api/order/UPC_3/door_destination',
        headers={"Authorization": token}
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data['UPC_ID'] == 'UPC_3'
    assert 'client_name' in data
    assert 'door_number' in data
    assert 'phone_number' in data
    assert 'time' in data

def test_get_door_destination_not_found(client):
    """Test /api/order/<UPC_ID>/door_destination endpoint for an invalid UPC_ID."""
    token = generate_jwt("UPC_999")
    response = client.get(
        '/api/order/UPC_999/door_destination',
        headers={"Authorization": token}
    )
    assert response.status_code == 404
    data = response.get_json()
    assert data['error'] == 'UPC_ID not found'


def test_get_door_destination_missing_token(client):
    """Test /api/order/<UPC_ID>/door_destination endpoint with no token."""
    response = client.get('/api/order/UPC_3/door_destination')
    assert response.status_code == 401
    data = response.get_json()
    assert data['error'] == 'Missing authorization token'


def test_get_door_destination_invalid_token(client):
    """Test /api/order/<UPC_ID>/door_destination endpoint with an invalid token."""
    response = client.get(
        '/api/order/UPC_3/door_destination',
        headers={"Authorization": "invalid_token"}
    )
    assert response.status_code == 403
    data = response.get_json()
    assert data['error'] == 'Invalid or expired token'