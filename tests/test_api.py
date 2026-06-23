"""
FastAPI endpoint tests.
"""

import pytest
from fastapi.testclient import TestClient

from src.api.main import create_app
from src.data.repository import RestaurantRepository

# Create a test app instance
app = create_app()

# Mock repository for testing
class MockRepository:
    def unique_locations(self):
        return ["Banashankari", "Indiranagar"]

    def unique_cuisines(self):
        return ["North Indian", "Italian", "Chinese"]

    def unique_rest_types(self):
        return ["Casual Dining", "Cafe"]
    
    def all_restaurants(self):
        return [] # Return empty list for basic tests

from src.api.dependencies import get_repository

@pytest.fixture
def client():
    # Use FastAPI dependency overrides so lifespan doesn't overwrite it
    app.dependency_overrides[get_repository] = lambda: MockRepository()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "dataset_loaded" in data

def test_locations_endpoint(client):
    response = client.get("/api/v1/locations")
    assert response.status_code == 200
    data = response.json()
    assert "locations" in data
    assert "Banashankari" in data["locations"]

def test_cuisines_endpoint(client):
    response = client.get("/api/v1/cuisines")
    assert response.status_code == 200
    data = response.json()
    assert "cuisines" in data
    assert "Italian" in data["cuisines"]

def test_recommend_validation_error(client):
    # Missing required location and budget
    response = client.post("/api/v1/recommend", json={})
    assert response.status_code == 422

def test_recommend_invalid_budget(client):
    # Invalid budget
    response = client.post("/api/v1/recommend", json={"location": "Indiranagar", "budget": "super-high"})
    assert response.status_code == 422

def test_recommend_valid_request_empty_results(client):
    # Using mock repo, so no restaurants
    response = client.post(
        "/api/v1/recommend", 
        json={
            "location": "Indiranagar", 
            "budget": "medium",
            "cuisine": "Italian"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["summary"] == "No restaurants matched your criteria."
    assert data["recommendations"] == []
    assert "filters" in data
