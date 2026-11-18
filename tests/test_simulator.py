import pytest
import json
from backend.services.simulator_service import SimulatorService
from backend.flask_app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_simulator_service_global_kruskal():
    result = SimulatorService.get_algorithm_trace("global", "kruskal")
    assert result is not None
    assert result["algorithm"] == "kruskal"
    assert result["graph_context"] == "global"
    assert result["vertex_count"] == 1255
    assert result["total_required_edges"] == 1254
    assert result["final_tree_weight"] == 480178419
    assert result["final_tree_weight_formatted"] == "480.1784 km"
    assert result["is_connected"] is True
    
    events = result["events"]
    assert len(events) > 1254
    assert events[0]["event_type"] == "START"
    assert events[-1]["event_type"] == "COMPLETED"
    
    accepted_count = 0
    for ev in events:
        assert "sequence_number" in ev
        assert "event_type" in ev
        assert "accepted" in ev
        assert "reason" in ev
        assert "current_tree_weight" in ev
        if ev["event_type"] == "EDGE_ACCEPTED":
            accepted_count += 1
            assert ev["accepted_edge_count"] == accepted_count
            assert ev["u_lat"] is not None
            assert ev["v_lat"] is not None
    assert accepted_count == 1254

def test_simulator_service_global_prim():
    result = SimulatorService.get_algorithm_trace("global", "prim")
    assert result is not None
    assert result["algorithm"] == "prim"
    assert result["graph_context"] == "global"
    assert result["vertex_count"] == 1255
    assert result["total_required_edges"] == 1254
    assert result["final_tree_weight"] == 480178419
    assert result["final_tree_weight_formatted"] == "480.1784 km"
    assert result["is_connected"] is True
    
    events = result["events"]
    assert len(events) >= 1254
    assert events[0]["event_type"] == "START"
    assert events[-1]["event_type"] == "COMPLETED"

def test_simulator_service_incident_traces():
    res_kruskal = SimulatorService.get_algorithm_trace("incident", "kruskal")
    assert res_kruskal is not None
    assert res_kruskal["algorithm"] == "kruskal"
    assert res_kruskal["graph_context"] == "incident"
    assert res_kruskal["vertex_count"] >= 5
    assert res_kruskal["total_required_edges"] == res_kruskal["vertex_count"] - 1
    assert len(res_kruskal["events"]) > 0

    res_prim = SimulatorService.get_algorithm_trace("incident", "prim")
    assert res_prim is not None
    assert res_prim["algorithm"] == "prim"
    assert res_prim["vertex_count"] == res_kruskal["vertex_count"]
    assert res_prim["final_tree_weight"] == res_kruskal["final_tree_weight"]

def test_simulator_service_comparison():
    comp_global = SimulatorService.get_comparison_trace("global")
    assert comp_global is not None
    parity_g = comp_global["parity"]
    assert parity_g["convergence_verified"] is True
    assert parity_g["weights_agree"] is True
    assert parity_g["weights_delta"] == 0
    assert parity_g["both_trees_connected"] is True
    assert parity_g["kruskal_weight_formatted"] == "480.1784 km"
    assert parity_g["prim_weight_formatted"] == "480.1784 km"

    comp_inc = SimulatorService.get_comparison_trace("incident")
    assert comp_inc is not None
    parity_i = comp_inc["parity"]
    assert parity_i["convergence_verified"] is True
    assert parity_i["weights_agree"] is True
    assert parity_i["weights_delta"] == 0

def test_simulator_api_endpoints(client):
    # 1. Trace endpoint global kruskal
    res = client.get("/api/mst/trace?graph=global&algo=kruskal")
    assert res.status_code == 200
    d = json.loads(res.data)
    assert d["success"] is True
    assert d["data"]["algorithm"] == "kruskal"
    assert len(d["data"]["events"]) > 1000

    # 2. Trace endpoint global prim
    res = client.get("/api/mst/trace?graph=global&algo=prim")
    assert res.status_code == 200
    d = json.loads(res.data)
    assert d["success"] is True
    assert d["data"]["algorithm"] == "prim"

    # 3. Trace endpoint incident
    res = client.get("/api/mst/trace?graph=incident&algo=kruskal")
    assert res.status_code == 200
    d = json.loads(res.data)
    assert d["success"] is True
    assert d["data"]["graph_context"] == "incident"

    # 4. Compare endpoint global
    res = client.get("/api/mst/compare?graph=global")
    assert res.status_code == 200
    d = json.loads(res.data)
    assert d["success"] is True
    assert d["data"]["parity"]["weights_agree"] is True

    # 5. Compare endpoint incident
    res = client.get("/api/mst/compare?graph=incident")
    assert res.status_code == 200
    d = json.loads(res.data)
    assert d["success"] is True
    assert d["data"]["parity"]["convergence_verified"] is True

    # 6. Invalid parameters
    res = client.get("/api/mst/trace?graph=invalid&algo=kruskal")
    assert res.status_code == 400
