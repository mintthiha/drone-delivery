import pytest
from app import app, messages
from jwt_module import generate_jwt

@pytest.fixture
def client():

    messages.clear()
    with app.test_client() as client:
        yield client


def test_home(client):
    response = client.get('/')
    assert response.status_code == 200
    assert response.json == {"carrier": "connected"}

def test_post_message(client):
    UPC_ID = "123ABC"
    token = generate_jwt(UPC_ID)  # Generate a valid token
    
    # Test posting a valid message with a valid token
    response = client.post(
        f'/api/shipment/{UPC_ID}', 
        json={"message": "Shipment received", "token": token}
    )
    assert response.status_code == 201
    assert response.json == {"message": "Message added successfully!"}

    # Test retrieving the posted message using the token in the Authorization header
    response = client.get(
        f'/api/shipment/{UPC_ID}', 
        headers={"Authorization": token}
    )
    assert response.status_code == 200
    assert response.json == {UPC_ID: "Shipment received"}

def test_post_message_empty(client):
    UPC_ID = "123ABC"
    token = generate_jwt(UPC_ID)  # Generate a valid token
    
    # Test posting an empty message
    response = client.post(f'/api/shipment/{UPC_ID}', json={"token": token})
    assert response.status_code == 400
    assert response.json == {"error": "No message provided!"}

def test_post_invalid_token(client):
    UPC_ID = "123ABC"
    invalid_token = "invalid.token.here"

    # Test posting a message with an invalid token
    response = client.post(
        f'/api/shipment/{UPC_ID}', 
        json={"message": "Shipment received", "token": invalid_token}
    )
    assert response.status_code == 500  # or 403, depending on how you handle invalid tokens in your code
    assert response.json == {"error": "The JWT Token is either expired or invalid!"}

def test_get_empty_messages(client):
    UPC_ID = "456DEF"
    token = generate_jwt("nonexistentUPC")  # Generate a valid token for a different UPC_ID

    # Test retrieving messages for a UPC_ID that does not exist
    response = client.get(
        f'/api/shipment/{UPC_ID}', 
        headers={"Authorization": token}
    )
    assert response.status_code == 404
    assert response.json == {"error": "UPC_ID not found!"}

def test_get_invalid_token(client):
    UPC_ID = "123ABC"
    invalid_token = "invalid.token.here"

    # Test retrieving the message with an invalid token in the Authorization header
    response = client.get(
        f'/api/shipment/{UPC_ID}', 
        headers={"Authorization": invalid_token}
    )
    assert response.status_code == 403
    assert response.json == {"error": "Invalid or expired token"}

