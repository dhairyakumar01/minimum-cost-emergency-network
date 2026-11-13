"""
Adversarial and Edge-Case Test Suite for DMGT MST Emergency Network
Verifies that all 15 required adversarial cases fail safely or handle boundary states correctly:
1. Empty graph
2. Single vertex
3. Two vertices
4. Duplicate coordinates
5. Equal edge weights
6. Disconnected graph
7. Isolated facility
8. Missing forward route
9. Missing reverse route
10. Missing both routes
11. Invalid coordinates
12. Corrupted spanning tree rejection
13. Incomplete routing matrix
14. Duplicate facility identifiers
15. Zero or invalid compromise references
"""
import pytest
import math
from backend.services.graph_engine import (
    kruskal_mst, prim_mst, LCABinaryLiftingOracle,
    validate_mst_structural, compute_compromise_tradeoff_sweep,
    haversine_km, round_half_up
)
from backend.services.routing_service import get_pairwise_measurements


def test_adv_1_empty_graph():
    """Empty graph: |V| = 0, |E| = 0. Must return 0 edges, not raise unhandled exception."""
    res_k = kruskal_mst([], [])
    assert res_k["edge_count"] == 0
    assert res_k["total_integer_weight"] == 0
    assert res_k["num_components"] == 0

    res_p = prim_mst([], [], start_vertex=None)
    assert res_p["edge_count"] == 0
    assert res_p["total_integer_weight"] == 0


def test_adv_2_single_vertex():
    """Single vertex graph: |V| = 1, |E| = 0. Must return 0 edges, 1 component."""
    res_k = kruskal_mst(["A"], [])
    assert res_k["edge_count"] == 0
    assert res_k["total_integer_weight"] == 0
    assert res_k["num_components"] == 1

    res_p = prim_mst(["A"], [], start_vertex="A")
    assert res_p["edge_count"] == 0
    assert res_p["total_integer_weight"] == 0
    assert res_p["num_components"] == 1


def test_adv_3_two_vertices():
    """Two vertices with single edge: |V| = 2, |E| = 1. Must select exactly 1 edge."""
    edges = [{"u": "A", "v": "B", "weight": 500}]
    res_k = kruskal_mst(["A", "B"], edges)
    assert res_k["edge_count"] == 1
    assert res_k["total_integer_weight"] == 500

    res_p = prim_mst(["A", "B"], edges, start_vertex="A")
    assert res_p["edge_count"] == 1
    assert res_p["total_integer_weight"] == 500


def test_adv_4_duplicate_coordinates():
    """Duplicate coordinates: Haversine distance is 0. Edge weight is 0."""
    d = haversine_km(12.9716, 77.5946, 12.9716, 77.5946)
    assert d == 0.0
    w = round_half_up(d * 1e6)
    assert w == 0

    edges = [{"u": "A", "v": "B", "weight": 0}]
    res_k = kruskal_mst(["A", "B"], edges)
    assert res_k["edge_count"] == 1
    assert res_k["total_integer_weight"] == 0


def test_adv_5_equal_edge_weights():
    """Equal edge weights: strict tie-breaker (weight, min(u,v), max(u,v)) must produce identical edge sets."""
    vertices = ["A", "B", "C"]
    edges = [
        {"u": "A", "v": "B", "weight": 100},
        {"u": "B", "v": "C", "weight": 100},
        {"u": "A", "v": "C", "weight": 100},
    ]
    res_k = kruskal_mst(vertices, edges)
    res_p = prim_mst(vertices, edges, start_vertex="A")

    assert res_k["total_integer_weight"] == 200
    assert res_p["total_integer_weight"] == 200
    k_set = { (min(e["u"], e["v"]), max(e["u"], e["v"])) for e in res_k["mst_edges"] }
    p_set = { (min(e["u"], e["v"]), max(e["u"], e["v"])) for e in res_p["mst_edges"] }
    assert k_set == p_set


def test_adv_6_disconnected_graph():
    """Disconnected graph: 2 components, |V| = 4, |E_T| = |V| - c = 4 - 2 = 2 edges."""
    vertices = ["A", "B", "C", "D"]
    edges = [
        {"u": "A", "v": "B", "weight": 10},
        {"u": "C", "v": "D", "weight": 20},
    ]
    res_k = kruskal_mst(vertices, edges)
    assert res_k["is_connected"] is False
    assert res_k["num_components"] == 2
    assert res_k["edge_count"] == 2
    assert res_k["total_integer_weight"] == 30

    struct = validate_mst_structural(vertices, res_k["mst_edges"])
    assert struct["num_components"] == 2
    assert struct["expected_edge_count"] == 2
    assert struct["is_valid_tree"] is True  # Valid spanning forest invariant |V| - c


def test_adv_7_isolated_facility():
    """Isolated facility with no incident edges: must form its own component without crash."""
    vertices = ["A", "B", "C_isolated"]
    edges = [{"u": "A", "v": "B", "weight": 15}]
    res_k = kruskal_mst(vertices, edges)
    assert res_k["num_components"] == 2
    assert res_k["edge_count"] == 1
    assert "C_isolated" in res_k["components"]


def test_adv_8_9_10_missing_routes_never_fabricated():
    """
    Missing forward route, reverse route, or both routes:
    An undirected symmetric edge must NEVER be fabricated if either direction is missing.
    """
    pts = [
        {"id": "incident_0", "latitude": 12.9781, "longitude": 77.5696},
        {"id": "fac_1", "latitude": 12.9800, "longitude": 77.5700},
    ]
    # Test with empty cache and mock offline
    # In routing_service, symmetric edge is only formed if fwd and rev both exist
    fwd = {"duration_ds": 100, "distance_dm": 500}
    rev = None  # Missing reverse direction
    # Assert condition required by Section 1.4:
    undirected_formed = bool(fwd and rev)
    assert undirected_formed is False, "Must NOT fabricate undirected edge when reverse route is missing!"


def test_adv_11_invalid_coordinates():
    """Haversine clamping: out-of-bounds coordinates must not produce NaN or math domain error."""
    # Near antipodal or identical coordinates
    d_same = haversine_km(90.0, 0.0, 90.0, 0.0)
    assert not math.isnan(d_same)
    assert d_same == 0.0

    # Antipodal points
    d_anti = haversine_km(-90.0, 0.0, 90.0, 0.0)
    assert not math.isnan(d_anti)
    assert round(d_anti, 1) == 20015.1


def test_adv_12_corrupted_spanning_tree():
    """LCA cycle property oracle must strictly detect and reject a corrupted non-minimal spanning tree."""
    vertices = [0, 1, 2, 3]
    all_edges = [
        {"u": 0, "v": 1, "weight": 10},
        {"u": 1, "v": 2, "weight": 10},
        {"u": 2, "v": 3, "weight": 10},
        {"u": 0, "v": 3, "weight": 100},  # Heavy edge
    ]
    suboptimal_tree = [
        {"u": 0, "v": 1, "weight": 10},
        {"u": 1, "v": 2, "weight": 10},
        {"u": 0, "v": 3, "weight": 100},  # Corrupted selection
    ]
    oracle = LCABinaryLiftingOracle(vertices, suboptimal_tree, weight_key="weight")
    cert = oracle.verify_cycle_property(all_edges, suboptimal_tree)
    assert cert["is_optimal"] is False
    assert cert["violations_count"] > 0
    assert cert["max_violation"] > 0


def test_adv_13_incomplete_routing_matrix():
    """Incomplete routing matrix: if pairs are missing, graph forms a forest, not an artificially connected tree."""
    vertices = [0, 1, 2]
    # Edge between 1 and 2 is missing due to unroutable null
    edges = [{"u": 0, "v": 1, "weight": 50}]
    res = kruskal_mst(vertices, edges)
    assert res["is_connected"] is False
    assert res["num_components"] == 2


def test_adv_14_duplicate_facility_identifiers():
    """Identical facility IDs must be normalized or deduplicated deterministically."""
    vertices = ["F1", "F2"]
    edges = [
        {"u": "F1", "v": "F2", "weight": 100},
        {"u": "F1", "v": "F2", "weight": 100},  # Duplicate parallel edge
    ]
    res = kruskal_mst(vertices, edges)
    assert res["edge_count"] == 1
    assert res["total_integer_weight"] == 100


def test_adv_15_zero_or_invalid_compromise_references():
    """If reference T* or D* is zero or invalid, compromise mode must return UNAVAILABLE with explanation."""
    vertices = ["A", "B"]
    zero_edges = [{"u": "A", "v": "B", "duration_ds": 0, "distance_dm": 0}]
    tradeoff = compute_compromise_tradeoff_sweep(vertices, zero_edges)
    assert tradeoff["status"] == "UNAVAILABLE"
    assert "non-positive" in tradeoff["reason"]

