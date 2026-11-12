"""Unit and integration tests for the Flask backend foundation (Phase 1)."""
import time
import pytest
from backend.flask_app import create_app
from backend.config import Config
from backend.services.data_service import DataService


@pytest.fixture
def client():
    """Create test client for Flask application."""
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


# ----------------------------------------------------------------------------
# 1. Health Endpoint Tests
# ----------------------------------------------------------------------------

def test_health_endpoint_success(client):
    """GET /api/health returns 200 with healthy status and facility counts."""
    # Warm request
    client.get("/api/health")

    t0 = time.perf_counter()
    resp = client.get("/api/health")
    latency_ms = (time.perf_counter() - t0) * 1000.0

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["data"]["status"] == "healthy"
    assert data["data"]["facilities_count"] == 1255
    assert data["data"]["ready"] is True
    assert "hospital" in data["data"]["agency_breakdown"]
    assert data["data"]["agency_breakdown"]["hospital"] == 1097
    assert data["data"]["agency_breakdown"]["police_station"] == 138
    assert data["data"]["agency_breakdown"]["fire_station"] == 20
    assert latency_ms < 50.0, f"Warm health check should be instantaneous, took {latency_ms:.2f}ms"


# ----------------------------------------------------------------------------
# 2. Facilities Endpoint Tests
# ----------------------------------------------------------------------------

def test_facilities_endpoint_all(client):
    """GET /api/facilities returns all 1,255 facilities with required fields."""
    resp = client.get("/api/facilities")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["data"]["total"] == 1255
    assert data["data"]["count"] == 1255
    assert len(data["data"]["facilities"]) == 1255

    first = data["data"]["facilities"][0]
    for required_key in ["facility_id", "facility_name", "agency", "agency_label", "latitude", "longitude"]:
        assert required_key in first, f"Missing required field '{required_key}'"
        assert first[required_key] is not None


def test_facilities_endpoint_agency_filter_hospital(client):
    """GET /api/facilities?agency=hospital filters to hospitals only."""
    resp = client.get("/api/facilities?agency=hospital")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["data"]["total"] == 1097
    assert data["data"]["agency_filter"] == "hospital"
    assert all(f["agency"] == "hospital" for f in data["data"]["facilities"])


def test_facilities_endpoint_agency_alias_ambulance(client):
    """GET /api/facilities?agency=ambulance resolves to canonical hospital."""
    resp = client.get("/api/facilities?agency=ambulance")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["data"]["total"] == 1097
    assert data["data"]["agency_filter"] == "hospital"


def test_facilities_endpoint_agency_filter_police(client):
    """GET /api/facilities?agency=police_station filters to police stations."""
    resp = client.get("/api/facilities?agency=police_station")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["data"]["total"] == 138
    assert data["data"]["agency_filter"] == "police_station"


def test_facilities_endpoint_agency_filter_fire(client):
    """GET /api/facilities?agency=fire_station filters to fire stations."""
    resp = client.get("/api/facilities?agency=fire_station")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["data"]["total"] == 20
    assert data["data"]["agency_filter"] == "fire_station"


def test_facilities_endpoint_invalid_agency_returns_400(client):
    """GET /api/facilities?agency=invalid returns 400 with structured error."""
    resp = client.get("/api/facilities?agency=invalid_agency_xyz")
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_AGENCY"
    assert "Unsupported agency" in data["error"]["message"]


def test_facilities_endpoint_search_query(client):
    """GET /api/facilities?search=Victoria returns matching facilities."""
    resp = client.get("/api/facilities?search=Victoria")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["data"]["total"] > 0
    assert any("victoria" in f["facility_name"].lower() for f in data["data"]["facilities"])


def test_facilities_endpoint_pagination(client):
    """GET /api/facilities with pagination returns expected slice."""
    resp = client.get("/api/facilities?page=1&per_page=10")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["data"]["total"] == 1255
    assert data["data"]["count"] == 10
    assert data["data"]["page"] == 1
    assert data["data"]["per_page"] == 10
    assert len(data["data"]["facilities"]) == 10


def test_facility_by_id_endpoint(client):
    """GET /api/facilities/<id> returns specific facility."""
    resp_all = client.get("/api/facilities?per_page=1")
    sample_id = resp_all.get_json()["data"]["facilities"][0]["facility_id"]

    resp = client.get(f"/api/facilities/{sample_id}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["data"]["facility_id"] == sample_id


def test_facility_by_id_not_found_returns_404(client):
    """GET /api/facilities/<nonexistent_id> returns 404."""
    resp = client.get("/api/facilities/nonexistent_facility_id_99999")
    assert resp.status_code == 404
    data = resp.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "FACILITY_NOT_FOUND"


# ----------------------------------------------------------------------------
# 3. Global MST Endpoint Tests
# ----------------------------------------------------------------------------

def test_global_mst_kruskal(client):
    """GET /api/mst/full?algo=kruskal returns precomputed 1,254 edges."""
    t0 = time.perf_counter()
    resp = client.get("/api/mst/full?algo=kruskal")
    latency_ms = (time.perf_counter() - t0) * 1000.0

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    mst = data["data"]
    assert mst["algorithm"] == "Kruskal"
    assert mst["edge_count"] == 1254
    assert mst["vertex_count"] == 1255
    assert mst["total_weight_km"] == pytest.approx(480.1784, abs=1e-3)
    assert len(mst["edges"]) == 1254
    assert latency_ms < 100.0, f"Must not recompute complete graph, took {latency_ms:.2f}ms"


def test_global_mst_prim(client):
    """GET /api/mst/full?algo=prim returns precomputed 1,254 edges."""
    resp = client.get("/api/mst/full?algo=prim")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    mst = data["data"]
    assert mst["algorithm"] == "Prim"
    assert mst["edge_count"] == 1254
    assert mst["total_weight_km"] == pytest.approx(480.1784, abs=1e-3)


def test_global_mst_invalid_algo_returns_400(client):
    """GET /api/mst/full?algo=invalid returns 400."""
    resp = client.get("/api/mst/full?algo=dijkstra")
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_ALGORITHM"


# ----------------------------------------------------------------------------
# 4. Frontend & Static Assets Serving Tests
# ----------------------------------------------------------------------------

def test_frontend_index_serving(client):
    """GET / serves the SPA index.html with 200 OK."""
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "<!DOCTYPE html>" in html
    assert "Minimum-Cost Emergency Communication Network" in html
    assert "id=\"section-dashboard\"" in html
    assert "id=\"section-facilities-map\"" in html
    assert "id=\"section-mst-network\"" in html
    assert "id=\"section-simulation\"" in html
    assert "id=\"section-project-analysis\"" in html
    assert "id=\"section-help\"" in html


def test_static_assets_serving(client):
    """GET /assets/css/style.css serves valid CSS."""
    resp = client.get("/assets/css/style.css")
    assert resp.status_code == 200
    css = resp.get_data(as_text=True)
    assert ":root" in css
    assert "--primary" in css


def test_api_404_json_error(client):
    """Non-existent API endpoint returns structured JSON 404."""
    resp = client.get("/api/nonexistent_endpoint")
    assert resp.status_code == 404
    data = resp.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "ENDPOINT_NOT_FOUND"
