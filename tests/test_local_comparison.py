"""Unit tests for Interactive Local Comparison Graph and Side-by-Side Prim vs Kruskal Evaluation."""
import math
import pytest
import pandas as pd
from pathlib import Path

from src.local_mst_comparison import build_local_comparison_graph, run_local_mst_comparison
from src.mst_network import haversine_km

FACILITIES_CSV = Path(__file__).resolve().parent.parent / "data" / "processed" / "emergency_facilities.csv"


@pytest.fixture
def facilities_df():
    return pd.read_csv(FACILITIES_CSV)


def test_build_local_comparison_graph_incident_at_index_zero(facilities_df):
    lat, lon = 12.89060, 77.57500
    local_nodes, candidate_edges, meta = build_local_comparison_graph(lat, lon, facilities_df, radius_km=5.0)
    
    assert len(local_nodes) >= 4
    assert local_nodes.iloc[0]["facility_id"] == "INCIDENT_LOCATION"
    assert local_nodes.iloc[0]["facility_type"] == "incident"
    assert math.isclose(local_nodes.iloc[0]["latitude"], lat, rel_tol=1e-6)
    assert math.isclose(local_nodes.iloc[0]["longitude"], lon, rel_tol=1e-6)
    assert local_nodes.iloc[0]["dist_to_incident_km"] == 0.0


def test_build_local_comparison_graph_guaranteed_multi_agency(facilities_df):
    lat, lon = 12.94653, 77.58004  # Lalbagh
    local_nodes, candidate_edges, meta = build_local_comparison_graph(lat, lon, facilities_df, radius_km=3.0)
    
    types = set(local_nodes["facility_type"].unique())
    assert "hospital" in types
    assert "police_station" in types
    assert "fire_station" in types
    assert "incident" in types
    
    v = len(local_nodes)
    expected_e = v * (v - 1) // 2
    assert len(candidate_edges) == expected_e
    assert meta["total_vertices"] == v
    assert meta["candidate_edges_count"] == expected_e


def test_run_local_mst_comparison_weights_and_edge_counts(facilities_df):
    lat, lon = 12.89060, 77.57500  # Forum Mall
    local_nodes, candidate_edges, meta = build_local_comparison_graph(lat, lon, facilities_df, radius_km=5.0)
    
    res = run_local_mst_comparison(local_nodes, candidate_edges)
    v = res["v_count"]
    target_e = res["target_edges"]
    assert target_e == v - 1
    
    # Both algorithms must produce exact V - 1 edges
    assert len(res["prim"]["tree"]) == target_e
    assert len(res["kruskal"]["tree"]) == target_e
    assert res["prim"]["is_valid"] is True
    assert res["kruskal"]["is_valid"] is True
    
    # Total weights must match within strict float tolerance
    prim_wt = res["prim"]["total_weight_km"]
    kruskal_wt = res["kruskal"]["total_weight_km"]
    assert prim_wt > 0.0
    assert kruskal_wt > 0.0
    assert math.isclose(prim_wt, kruskal_wt, rel_tol=1e-7, abs_tol=1e-5)
    assert res["comparison"]["weights_agree"] is True
    assert res["comparison"]["weight_difference_km"] < 1e-4


def test_kruskal_cycle_rejected_edges_tracking(facilities_df):
    lat, lon = 12.97818, 77.57218  # Majestic / Kempegowda Bus Station
    local_nodes, candidate_edges, meta = build_local_comparison_graph(lat, lon, facilities_df, radius_km=4.0)
    
    res = run_local_mst_comparison(local_nodes, candidate_edges)
    v = res["v_count"]
    total_candidates = res["candidate_edges_count"]
    target_e = res["target_edges"]
    
    rejected_count = res["kruskal"]["rejected_count"]
    # Candidate edges = Selected MST edges + Rejected cycle edges
    assert rejected_count == total_candidates - target_e
    assert len(res["kruskal"]["rejected_edges_df"]) == rejected_count


def test_multiple_bengaluru_locations_consistency(facilities_df):
    test_locs = [
        ("Forum Mall, Konankunte", 12.89060, 77.57500),
        ("Lalbagh Botanical Garden", 12.94653, 77.58004),
        ("Majestic Bus Station", 12.97818, 77.57218),
    ]
    
    for name, lat, lon in test_locs:
        local_nodes, candidate_edges, meta = build_local_comparison_graph(lat, lon, facilities_df, radius_km=5.0)
        res = run_local_mst_comparison(local_nodes, candidate_edges)
        
        assert res["prim"]["is_valid"]
        assert res["kruskal"]["is_valid"]
        assert math.isclose(res["prim"]["total_weight_km"], res["kruskal"]["total_weight_km"], rel_tol=1e-6)
        assert res["prim"]["execution_time_sec"] > 0.0
        assert res["kruskal"]["execution_time_sec"] > 0.0


def test_facilities_dataframe_immutability(facilities_df):
    orig_shape = facilities_df.shape
    orig_cols = list(facilities_df.columns)
    
    lat, lon = 12.89060, 77.57500
    _ = build_local_comparison_graph(lat, lon, facilities_df, radius_km=5.0)
    
    assert facilities_df.shape == orig_shape
    assert list(facilities_df.columns) == orig_cols

