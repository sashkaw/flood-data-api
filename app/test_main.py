from fastapi import status
from fastapi.testclient import TestClient

from .main import app

# Initialize test client
client = TestClient(app)

# Test main path operation function
def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Flood Data API!"}

def test_search():
    response = client.get("/search/?country=france")
    assert response.status_code == status.HTTP_200_OK
    assert "tilejson" in response.json()