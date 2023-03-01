from fastapi import status
from fastapi.testclient import TestClient

from .main import app

# Initialize test client
client = TestClient(app)

# Test routes
def test_root():
    response = client.get("/")
    assert response.status_code == 200
    test_example_request = "http://127.0.0.1:8000/search/?left=-168.65&bottom=-15.17&right=-168.12&top=-14.45"
    test_context = {
        "message": "Welcome to the Flood Data API!",
        "example request": test_example_request,
    }
    assert response.json() == test_context

def test_search():
    response = client.get("/search/?left=-168.65&bottom=-15.17&right=-168.12&top=-14.45")
    assert response.status_code == status.HTTP_200_OK
    assert "tilejson" in response.json()