from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint_is_available():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert response.headers["X-Request-ID"]


def test_location_catalogue_search_and_detail():
    response = client.get("/api/v1/locations", params={"query": "Delhi"})
    assert response.status_code == 200
    assert response.json()["items"][0]["id"] == "new-delhi"

    detail = client.get("/api/v1/locations/new-delhi")
    assert detail.status_code == 200
    assert detail.json()["timezone"] == "Asia/Kolkata"


def test_unknown_location_has_standard_error():
    response = client.get("/api/v1/locations/not-a-real-location")
    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "location_not_found"
    assert error["request_id"]


def test_weather_requires_location():
    response = client.get("/api/v1/weather")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "location_required"


def test_startup_and_readiness_do_not_contact_external_providers():
    with TestClient(app) as running_client:
        response = running_client.get("/api/v1/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
