from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_locations_type_filtering():
    # Filter by state
    states_resp = client.get("/api/v1/locations", params={"type": "state", "limit": 50})
    assert states_resp.status_code == 200
    states_data = states_resp.json()
    assert len(states_data["items"]) >= 28
    for item in states_data["items"]:
        assert item["type"] == "state"
        assert "grid cell" in item["representation"] or "average" in item["representation"]

    # Filter by district
    dist_resp = client.get("/api/v1/locations", params={"type": "district", "limit": 50})
    assert dist_resp.status_code == 200
    dist_data = dist_resp.json()
    assert len(dist_data["items"]) >= 5
    for item in dist_data["items"]:
        assert item["type"] == "district"
        assert "rather than district-wide average" in item["representation"]

    # Filter by city
    city_resp = client.get("/api/v1/locations", params={"type": "city", "limit": 50})
    assert city_resp.status_code == 200
    city_data = city_resp.json()
    assert len(city_data["items"]) >= 10
    for item in city_data["items"]:
        assert item["type"] == "city"


def test_list_states_endpoint():
    response = client.get("/api/v1/locations/states")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 28
    state_names = [s["state"] for s in data["items"]]
    assert "Maharashtra" in state_names
    assert "Tamil Nadu" in state_names
    assert "Delhi" in state_names
    assert "Karnataka" in state_names


def test_location_detail_representation_field():
    resp = client.get("/api/v1/locations/leh-district")
    assert resp.status_code == 200
    data = resp.json()
    assert data["type"] == "district"
    assert "district-wide average" in data["representation"]
