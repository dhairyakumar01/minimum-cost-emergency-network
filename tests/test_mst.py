import random
from itertools import combinations

import pandas as pd
import pytest

from src.mst_network import (
    build_complete_edges,
    haversine_km,
    kruskal_mst,
    prim_mst,
)
from src.validation import validate_mst


def make_nodes(coords):
    return pd.DataFrame(
        {
            "facility_id": [f"n{i}" for i in range(len(coords))],
            "facility_name": [f"Facility {i}" for i in range(len(coords))],
            "facility_type": ["hospital"] * len(coords),
            "latitude": [c[0] for c in coords],
            "longitude": [c[1] for c in coords],
        }
    )


def brute_force_min_total(nodes, edges):
    """Independent reference: try every (V-1)-edge subset, keep spanning trees."""
    ids = nodes.facility_id.tolist()
    rows = list(edges.itertuples(index=False))
    best = None
    for subset in combinations(rows, len(ids) - 1):
        parent = {x: x for x in ids}

        def find(x):
            while parent[x] != x:
                x = parent[x]
            return x

        ok = True
        for e in subset:
            a, b = find(e.u), find(e.v)
            if a == b:
                ok = False
                break
            parent[b] = a
        if ok:
            total = sum(e.weight_km for e in subset)
            if best is None or total < best:
                best = total
    return best


# ---------- Haversine ----------

def test_haversine_same_point_is_zero():
    assert haversine_km(12.97, 77.59, 12.97, 77.59) == 0.0


def test_haversine_is_symmetric():
    a = haversine_km(12.97, 77.59, 13.05, 77.65)
    b = haversine_km(13.05, 77.65, 12.97, 77.59)
    assert a == pytest.approx(b)


def test_haversine_one_degree_latitude():
    # 1 degree of latitude is about 111.195 km on a sphere of radius 6371.0088 km
    assert haversine_km(0, 0, 1, 0) == pytest.approx(111.195, rel=1e-3)


# ---------- MST algorithms ----------

SMALL = [(12.90, 77.50), (12.95, 77.60), (13.00, 77.55), (13.05, 77.70)]


def test_small_graph_matches_brute_force():
    nodes = make_nodes(SMALL)
    edges = build_complete_edges(nodes)
    _, pt = prim_mst(nodes, edges)
    _, kt = kruskal_mst(nodes, edges)
    ref = brute_force_min_total(nodes, edges)
    assert pt == pytest.approx(ref)
    assert kt == pytest.approx(ref)


@pytest.mark.parametrize("seed", range(5))
def test_random_graphs_prim_kruskal_brute_force_agree(seed):
    rnd = random.Random(seed)
    coords = [
        (12.85 + rnd.random() * 0.3, 77.45 + rnd.random() * 0.3) for _ in range(6)
    ]
    nodes = make_nodes(coords)
    edges = build_complete_edges(nodes)
    _, pt = prim_mst(nodes, edges)
    _, kt = kruskal_mst(nodes, edges)
    ref = brute_force_min_total(nodes, edges)
    assert pt == pytest.approx(ref)
    assert kt == pytest.approx(ref)


def test_duplicate_coordinates_zero_weight_edge():
    nodes = make_nodes([(12.9, 77.5), (12.9, 77.5), (13.0, 77.6)])
    edges = build_complete_edges(nodes)
    assert (edges.weight_km == 0).any()
    p, pt = prim_mst(nodes, edges)
    k, kt = kruskal_mst(nodes, edges)
    assert len(p) == len(k) == 2
    assert pt == pytest.approx(kt)
    assert pt == pytest.approx(brute_force_min_total(nodes, edges))


def test_disconnected_graph_raises():
    nodes = make_nodes(SMALL)
    edges = build_complete_edges(nodes)
    # keep only edges among n0, n1, n2 so n3 is isolated
    partial = edges[(edges.u != "n3") & (edges.v != "n3")]
    with pytest.raises(ValueError):
        prim_mst(nodes, partial)
    with pytest.raises(ValueError):
        kruskal_mst(nodes, partial)


# ---------- Validation module ----------

def test_validation_passes_on_correct_msts():
    nodes = make_nodes(SMALL)
    edges = build_complete_edges(nodes)
    p, _ = prim_mst(nodes, edges)
    k, _ = kruskal_mst(nodes, edges)
    assert all(validate_mst(nodes, p).values())
    assert all(validate_mst(nodes, k).values())


def test_validation_detects_cycle_and_bad_edge_count():
    nodes = make_nodes(SMALL)
    edges = build_complete_edges(nodes)
    p, _ = prim_mst(nodes, edges)
    # replace the last edge with a duplicate of the first: not a valid tree
    bad = pd.concat([p.iloc[:-1], p.iloc[[0]]], ignore_index=True)
    result = validate_mst(nodes, bad)
    assert not all(result.values())


def test_validation_detects_unknown_facility_id():
    nodes = make_nodes(SMALL)
    edges = build_complete_edges(nodes)
    p, _ = prim_mst(nodes, edges)
    bad = p.copy()
    bad.loc[0, "u"] = "does_not_exist"
    assert not validate_mst(nodes, bad)["endpoints_are_valid_facility_ids"]


def test_validation_detects_wrong_weight():
    nodes = make_nodes(SMALL)
    edges = build_complete_edges(nodes)
    p, _ = prim_mst(nodes, edges)
    bad = p.copy()
    bad.loc[0, "weight_km"] = bad.loc[0, "weight_km"] + 5.0
    assert not validate_mst(nodes, bad)["stored_weights_match_haversine"]


# ============================================================================
# COMPREHENSIVE MATHEMATICAL AUDIT TEST CASES (Cases 1 through 12)
# ============================================================================

def test_case_1_simple_graph_with_unique_mst():
    """Case 1: Simple graph with strictly distinct weights has a unique MST."""
    nodes = make_nodes([(12.90, 77.50), (12.95, 77.62), (13.02, 77.53)])
    edges = build_complete_edges(nodes)
    p, pt = prim_mst(nodes, edges)
    k, kt = kruskal_mst(nodes, edges)
    ref = brute_force_min_total(nodes, edges)
    assert len(p) == len(nodes) - 1 == 2
    assert pt == pytest.approx(ref)
    assert kt == pytest.approx(ref)
    p_edges = {frozenset((r.u, r.v)) for r in p.itertuples()}
    k_edges = {frozenset((r.u, r.v)) for r in k.itertuples()}
    assert p_edges == k_edges, "Unique MST must produce identical edge sets in Prim and Kruskal"


def test_case_2_and_10_multiple_valid_msts_and_differing_edge_sets():
    """Cases 2 & 10: Graph with multiple valid MSTs and identical total weight."""
    # 4 vertices with symmetric equal weights on cycle C4
    nodes = pd.DataFrame({
        "facility_id": ["A", "B", "C", "D"],
        "facility_name": ["Node A", "Node B", "Node C", "Node D"],
        "facility_type": ["hospital"] * 4,
        "latitude": [12.90, 12.90, 13.00, 13.00],
        "longitude": [77.50, 77.60, 77.60, 77.50],
    })
    # Synthetic edges: C4 perimeter has weight 1.0, diagonals have weight 2.0
    custom_edges = pd.DataFrame([
        {"u": "A", "v": "B", "u_name": "A", "v_name": "B", "u_type": "hospital", "v_type": "hospital", "weight_km": 1.0},
        {"u": "B", "v": "C", "u_name": "B", "v_name": "C", "u_type": "hospital", "v_type": "hospital", "weight_km": 1.0},
        {"u": "C", "v": "D", "u_name": "C", "v_name": "D", "u_type": "hospital", "v_type": "hospital", "weight_km": 1.0},
        {"u": "D", "v": "A", "u_name": "D", "v_name": "A", "u_type": "hospital", "v_type": "hospital", "weight_km": 1.0},
        {"u": "A", "v": "C", "u_name": "A", "v_name": "C", "u_type": "hospital", "v_type": "hospital", "weight_km": 2.0},
        {"u": "B", "v": "D", "u_name": "B", "v_name": "D", "u_type": "hospital", "v_type": "hospital", "weight_km": 2.0},
    ])
    p, pt = prim_mst(nodes, custom_edges)
    k, kt = kruskal_mst(nodes, custom_edges)
    ref = brute_force_min_total(nodes, custom_edges)
    assert pt == pytest.approx(3.0)
    assert kt == pytest.approx(3.0)
    assert pt == pytest.approx(ref)
    assert len(p) == 3 and len(k) == 3


def test_case_3_equal_edge_weights():
    """Case 3: Complete graph where multiple edges have identical weight."""
    nodes = pd.DataFrame({
        "facility_id": ["A", "B", "C"],
        "facility_name": ["Node A", "Node B", "Node C"],
        "facility_type": ["hospital"] * 3,
        "latitude": [12.90, 12.90, 13.00],
        "longitude": [77.50, 77.60, 77.55],
    })
    custom_edges = pd.DataFrame([
        {"u": "A", "v": "B", "u_name": "A", "v_name": "B", "u_type": "hospital", "v_type": "hospital", "weight_km": 2.5},
        {"u": "B", "v": "C", "u_name": "B", "v_name": "C", "u_type": "hospital", "v_type": "hospital", "weight_km": 2.5},
        {"u": "A", "v": "C", "u_name": "A", "v_name": "C", "u_type": "hospital", "v_type": "hospital", "weight_km": 2.5},
    ])
    p, pt = prim_mst(nodes, custom_edges)
    k, kt = kruskal_mst(nodes, custom_edges)
    assert len(p) == 2 and len(k) == 2
    assert pt == pytest.approx(5.0)
    assert kt == pytest.approx(5.0)


def test_case_4_duplicate_coordinates():
    """Case 4: Two facilities located at identical coordinates (distance 0.0 km)."""
    nodes = make_nodes([(12.954158, 77.660837), (12.954158, 77.660837), (12.960000, 77.670000)])
    edges = build_complete_edges(nodes)
    assert (edges.weight_km == 0.0).any()
    p, pt = prim_mst(nodes, edges)
    k, kt = kruskal_mst(nodes, edges)
    assert len(p) == 2 and len(k) == 2
    assert (p.weight_km == 0.0).any(), "Prim must include 0.0 km edge"
    assert (k.weight_km == 0.0).any(), "Kruskal must include 0.0 km edge"
    assert pt == pytest.approx(kt)


def test_case_5_zero_weight_edges():
    """Case 5: Explicit zero-weight edge must be accepted without failure."""
    nodes = make_nodes([(12.90, 77.50), (12.90, 77.50)])
    edges = build_complete_edges(nodes)
    p, pt = prim_mst(nodes, edges)
    k, kt = kruskal_mst(nodes, edges)
    assert len(p) == 1 and len(k) == 1
    assert pt == 0.0 and kt == 0.0


def test_case_6_graph_containing_cycles():
    """Case 6: Dense graph with cycles must produce an acyclic tree with V-1 edges."""
    nodes = make_nodes(SMALL + [(13.10, 77.75)])  # 5 nodes -> K5 complete graph (10 edges, 10 cycles)
    edges = build_complete_edges(nodes)
    p, pt = prim_mst(nodes, edges)
    k, kt = kruskal_mst(nodes, edges)
    v_p = validate_mst(nodes, p)
    v_k = validate_mst(nodes, k)
    assert v_p["acyclic"] and v_p["edge_count_is_V_minus_1"]
    assert v_k["acyclic"] and v_k["edge_count_is_V_minus_1"]
    assert len(p) == 4 and len(k) == 4


def test_case_7_disconnected_graph():
    """Case 7: Disconnected graph must raise ValueError in both algorithms."""
    nodes = make_nodes([(12.90, 77.50), (12.95, 77.55), (13.00, 77.60)])
    edges = build_complete_edges(nodes)
    # Remove all edges to n2
    disconnected_edges = edges[(edges.u != "n2") & (edges.v != "n2")]
    with pytest.raises(ValueError, match="Graph is disconnected"):
        prim_mst(nodes, disconnected_edges)
    with pytest.raises(ValueError, match="Could not construct spanning tree"):
        kruskal_mst(nodes, disconnected_edges)


def test_case_8_single_vertex_graph():
    """Case 8: Single-vertex graph (V=1) produces 0 edges and 0.0 total weight."""
    nodes = make_nodes([(12.9716, 77.5946)])
    edges = build_complete_edges(nodes)
    p, pt = prim_mst(nodes, edges)
    k, kt = kruskal_mst(nodes, edges)
    assert len(p) == 0 and len(k) == 0
    assert pt == 0.0 and kt == 0.0


def test_case_9_two_vertices_graph():
    """Case 9: Two-vertex graph (V=2) produces exactly 1 edge."""
    nodes = make_nodes([(12.90, 77.50), (12.95, 77.55)])
    edges = build_complete_edges(nodes)
    p, pt = prim_mst(nodes, edges)
    k, kt = kruskal_mst(nodes, edges)
    assert len(p) == 1 and len(k) == 1
    w_expected = float(edges.iloc[0]["weight_km"])
    assert pt == pytest.approx(w_expected)
    assert kt == pytest.approx(w_expected)


def test_case_11_short_edge_correctly_excluded_due_to_cycle():
    """Case 11: A shorter edge is excluded if including it forms a cycle."""
    # Nodes A, B, C form a triangle: (A,B)=1.0, (B,C)=1.2, (A,C)=1.5.
    # Node D connects to C with (C,D)=8.0.
    # Edge (A,C) with weight 1.5 is SHORTER than (C,D) with weight 8.0 (1.5 < 8.0).
    # Yet (A,C) is excluded because A and C are already connected via B, and 1.5 > max(1.0, 1.2).
    nodes = pd.DataFrame({
        "facility_id": ["A", "B", "C", "D"],
        "facility_name": ["A", "B", "C", "D"],
        "facility_type": ["hospital"] * 4,
        "latitude": [12.90, 12.91, 12.92, 13.00],
        "longitude": [77.50, 77.51, 77.52, 77.60],
    })
    custom_edges = pd.DataFrame([
        {"u": "A", "v": "B", "u_name": "A", "v_name": "B", "u_type": "hospital", "v_type": "hospital", "weight_km": 1.0},
        {"u": "B", "v": "C", "u_name": "B", "v_name": "C", "u_type": "hospital", "v_type": "hospital", "weight_km": 1.2},
        {"u": "A", "v": "C", "u_name": "A", "v_name": "C", "u_type": "hospital", "v_type": "hospital", "weight_km": 1.5},
        {"u": "C", "v": "D", "u_name": "C", "v_name": "D", "u_type": "hospital", "v_type": "hospital", "weight_km": 8.0},
    ])
    p, pt = prim_mst(nodes, custom_edges)
    k, kt = kruskal_mst(nodes, custom_edges)

    p_pairs = {frozenset((r.u, r.v)) for r in p.itertuples()}
    k_pairs = {frozenset((r.u, r.v)) for r in k.itertuples()}

    # Both must select (A,B), (B,C), (C,D) -> total 10.2
    assert pt == pytest.approx(10.2)
    assert kt == pytest.approx(10.2)
    # The shorter edge (A,C)=1.5 must NOT be in the MST
    assert frozenset(("A", "C")) not in p_pairs, "Edge (A,C) must be excluded despite being shorter than (C,D)"
    assert frozenset(("A", "C")) not in k_pairs, "Edge (A,C) must be excluded despite being shorter than (C,D)"


def test_case_12_kruskal_rejects_edge_forming_cycle():
    """Case 12: Kruskal rejects an edge when endpoints already belong to the same component."""
    nodes = pd.DataFrame({
        "facility_id": ["A", "B", "C"],
        "facility_name": ["A", "B", "C"],
        "facility_type": ["hospital"] * 3,
        "latitude": [12.90, 12.91, 12.92],
        "longitude": [77.50, 77.51, 77.52],
    })
    custom_edges = pd.DataFrame([
        {"u": "A", "v": "B", "u_name": "A", "v_name": "B", "u_type": "hospital", "v_type": "hospital", "weight_km": 1.0},
        {"u": "B", "v": "C", "u_name": "B", "v_name": "C", "u_type": "hospital", "v_type": "hospital", "weight_km": 2.0},
        {"u": "A", "v": "C", "u_name": "A", "v_name": "C", "u_type": "hospital", "v_type": "hospital", "weight_km": 3.0},
    ])
    k_tree, k_tot, k_dec = kruskal_mst(nodes, custom_edges, track_decisions=True)
    assert len(k_tree) == 2
    assert len(k_dec["accepted"]) == 2
    assert len(k_dec["rejected"]) == 1
    rej = k_dec["rejected"][0]
    assert rej["u"] == "A" and rej["v"] == "C"
    assert rej["weight_km"] == 3.0
    assert "cycle" in rej["reason"].lower()


def test_independent_boruvka_oracle_cross_validation():
    """Independent Test Oracle: Borůvka's algorithm cross-validates Prim and Kruskal."""
    def boruvka(nodes_df, edges_df):
        parent = {x: x for x in nodes_df.facility_id}
        def find(x):
            while parent[x] != parent[parent[x]]:
                parent[x] = parent[parent[x]]
            return parent[x]
        def union(a, b):
            ra, rb = find(a), find(b)
            if ra == rb: return False
            parent[rb] = ra
            return True
        chosen = []
        ids = list(nodes_df.facility_id)
        num_comp = len(ids)
        edge_list = list(edges_df.itertuples(index=False))
        while num_comp > 1:
            cheapest = {}
            for e in edge_list:
                ru, rv = find(e.u), find(e.v)
                if ru != rv:
                    if ru not in cheapest or e.weight_km < cheapest[ru][0]:
                        cheapest[ru] = (e.weight_km, e)
                    if rv not in cheapest or e.weight_km < cheapest[rv][0]:
                        cheapest[rv] = (e.weight_km, e)
            if not cheapest:
                break
            added = 0
            for comp, (w, e) in cheapest.items():
                if union(e.u, e.v):
                    chosen.append(e)
                    num_comp -= 1
                    added += 1
            if added == 0:
                break
        return chosen, sum(e.weight_km for e in chosen)

    nodes = make_nodes(SMALL)
    edges = build_complete_edges(nodes)
    _, p_weight = prim_mst(nodes, edges)
    _, k_weight = kruskal_mst(nodes, edges)
    _, b_weight = boruvka(nodes, edges)

    assert p_weight == pytest.approx(k_weight)
    assert p_weight == pytest.approx(b_weight)

