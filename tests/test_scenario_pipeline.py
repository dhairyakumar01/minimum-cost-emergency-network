"""
Test suite for scenario execution pipeline, OSRM road measurements,
dispatch ranking, MST validation, and compromise optimization.
"""
import pytest
from backend.services import scenario_service as ss
from backend.services import routing_service as rs
from backend.services import graph_engine as ge


def test_scenario_pipeline_execution():
    """Test full 8-stage synchronous scenario execution for fire stations in Majestic."""
    sc_id = ss.create_and_run_scenario(
        incident_lat=12.9781,
        incident_lon=77.5696,
        incident_label="Majestic Railway Station",
        agency="fire",
        radius_km=6.0,
        optimization_mode="time",
        k_param=5,
        async_mode=False
    )
    assert sc_id is not None
    status = ss.get_scenario_status(sc_id)
    assert status["status"] in ("COMPLETED", "COMPLETED_WITH_WARNINGS")

    res = ss.get_scenario_result(sc_id)
    assert res is not None
    assert res["summary"]["total_candidates_in_radius"] > 0
    assert len(res["dispatch_ranking"]) > 0

    # Verify dispatch ranking ordering: travel_time_ds ascending
    dispatch = res["dispatch_ranking"]
    for i in range(len(dispatch) - 1):
        assert dispatch[i]["travel_time_ds"] <= dispatch[i + 1]["travel_time_ds"]
        assert dispatch[i]["rank"] == i + 1

    # Verify fuel model parameters
    assert dispatch[0]["fuel_rate_inr_km"] == 18.00
    assert "estimated fuel" in dispatch[0]["fuel_model_label"].lower()

    # Verify structural validity
    assert res["validation"]["structural"]["is_valid_tree"] is True

    # Verify LCA optimality
    assert res["validation"]["optimality"]["is_optimal"] is True


def test_corrupted_spanning_tree_rejection():
    """
    Corrupted tree test: A valid spanning tree with non-minimal edge weights
    must be accepted by structural validator but rejected by LCA cycle-property validator.
    """
    vertices = ["A", "B", "C", "D"]
    all_edges = [
        {"u": "A", "v": "B", "weight": 10},
        {"u": "B", "v": "C", "weight": 15},
        {"u": "C", "v": "D", "weight": 12},
        {"u": "D", "v": "A", "weight": 40}, # heavy chord
        {"u": "A", "v": "C", "weight": 14}, # lighter crossing
    ]

    # Deliberately choose non-minimal spanning tree using (D, A) w=40 instead of (A, C) w=14
    suboptimal_tree = [
        {"u": "A", "v": "B", "weight": 10},
        {"u": "B", "v": "C", "weight": 15},
        {"u": "D", "v": "A", "weight": 40},
    ]

    # 1. Structural validator must accept the tree
    struct = ge.validate_mst_structural(vertices, suboptimal_tree)
    assert struct["is_valid_tree"] is True
    assert struct["has_cycle"] is False
    assert struct["edge_count"] == 3

    # 2. LCA cycle-property validator must REJECT optimality
    oracle = ge.LCABinaryLiftingOracle(vertices, suboptimal_tree)
    cert = oracle.verify_cycle_property(all_edges, suboptimal_tree)
    assert cert["is_optimal"] is False
    assert cert["violations_count"] > 0

