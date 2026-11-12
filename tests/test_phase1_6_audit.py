"""Automated unit and integration tests for Phase 1.6 Source-Code Audit & Mathematical Verification."""
import csv
import math
from collections import defaultdict, deque
import numpy as np
import pandas as pd
import pytest

from src.mst_network import (
    haversine_km,
    kruskal_mst,
    prim_mst,
    build_complete_edges,
    load_facilities,
    EARTH_KM,
)
from src.validation import validate_mst


# -----------------------------------------------------------------------------
# AUDIT A: Dataset and Global Graph Invariants
# -----------------------------------------------------------------------------

def test_audit_a_dataset_invariants():
    """Verify 1,255 facilities, no invalid coordinates, and 786,885 theoretical edges."""
    df = load_facilities("data/processed/emergency_facilities.csv")
    assert len(df) == 1255
    assert df["facility_id"].nunique() == 1255
    assert not df["latitude"].isna().any()
    assert not df["longitude"].isna().any()
    assert df["latitude"].between(-90, 90).all()
    assert df["longitude"].between(-180, 180).all()

    # Complete graph edges = V * (V - 1) / 2
    v = len(df)
    expected_complete_edges = v * (v - 1) // 2
    assert expected_complete_edges == 786885


def test_audit_a_global_mst_weights_and_parity():
    """Verify Kruskal and Prim CSV results: 1,254 edges, exact total weight, identical sets."""
    with open("results/kruskal_mst_edges.csv", encoding="utf-8-sig") as f:
        k_edges = list(csv.DictReader(f))
    with open("results/prim_mst_edges.csv", encoding="utf-8-sig") as f:
        p_edges = list(csv.DictReader(f))

    assert len(k_edges) == 1254
    assert len(p_edges) == 1254

    k_weights = [float(e["weight_km"]) for e in k_edges]
    p_weights = [float(e["weight_km"]) for e in p_edges]

    k_sum = sum(k_weights)
    p_sum = sum(p_weights)

    # 480.1783984126 km
    assert k_sum == pytest.approx(480.1783984126, abs=1e-6)
    assert p_sum == pytest.approx(480.1783984126, abs=1e-6)
    assert abs(k_sum - p_sum) < 1e-12, f"Discrepancy: {abs(k_sum - p_sum)}"

    # Check min and max edges
    assert min(k_weights) == 0.0
    assert min(p_weights) == 0.0
    assert max(k_weights) == pytest.approx(7.825585, abs=1e-4)
    assert max(p_weights) == pytest.approx(7.825585, abs=1e-4)

    # Edge set parity
    def canon(u, v):
        return (u, v) if u < v else (v, u)

    k_set = {canon(e["u"], e["v"]) for e in k_edges}
    p_set = {canon(e["u"], e["v"]) for e in p_edges}
    assert k_set == p_set, "Kruskal and Prim must produce identical edge sets on this graph"


# -----------------------------------------------------------------------------
# AUDIT B: Zero-Weight Edge Investigation
# -----------------------------------------------------------------------------

def test_audit_b_zero_weight_edge():
    """Verify the unique 0.0000 km edge connecting identical coordinate facilities."""
    with open("data/processed/emergency_facilities.csv", encoding="utf-8-sig") as f:
        facs = {r["facility_id"]: r for r in csv.DictReader(f)}

    with open("results/kruskal_mst_edges.csv", encoding="utf-8-sig") as f:
        k_edges = list(csv.DictReader(f))

    zero_edges = [e for e in k_edges if float(e["weight_km"]) == 0.0]
    assert len(zero_edges) == 1

    ze = zero_edges[0]
    u, v = ze["u"], ze["v"]
    assert u == "way/1544830710"
    assert v == "way/1544831540"
    assert ze["u_name"] == "SPS Surgicals"
    assert ze["v_name"] == ""

    u_rec = facs[u]
    v_rec = facs[v]
    assert u_rec["latitude"] == v_rec["latitude"] == "12.9541576"
    assert u_rec["longitude"] == v_rec["longitude"] == "77.6608368"
    assert u != v, "Must not be a self-loop"


# -----------------------------------------------------------------------------
# AUDIT C: LCA Binary-Lifting Cycle Property Verification
# -----------------------------------------------------------------------------

def test_audit_c_lca_binary_lifting_oracle():
    """Verify binary-lifting LCA maximum path query against independent BFS path oracle."""
    mst_df = pd.read_csv("results/kruskal_mst_edges.csv")
    nodes_df = pd.read_csv("data/processed/emergency_facilities.csv")
    all_ids = list(nodes_df["facility_id"])
    id2idx = {id_: i for i, id_ in enumerate(all_ids)}
    n = len(all_ids)

    adj = defaultdict(list)
    for r in mst_df.itertuples():
        u, v, w = id2idx[r.u], id2idx[r.v], float(r.weight_km)
        adj[u].append((v, w))
        adj[v].append((u, w))

    LOGN = 12
    up = np.zeros((LOGN, n), dtype=int)
    max_edge = np.zeros((LOGN, n), dtype=float)
    depth = np.zeros(n, dtype=int)

    visited = [False] * n
    queue = deque([0])
    visited[0] = True
    while queue:
        curr = queue.popleft()
        for neighbor, w in adj[curr]:
            if not visited[neighbor]:
                visited[neighbor] = True
                depth[neighbor] = depth[curr] + 1
                up[0, neighbor] = curr
                max_edge[0, neighbor] = w
                queue.append(neighbor)

    assert sum(visited) == n, "Tree traversal must visit every vertex"
    assert depth.max() < (1 << LOGN), "Tree depth must be within binary-lifting table bounds"

    for k in range(1, LOGN):
        for i in range(n):
            parent_k = up[k - 1, i]
            up[k, i] = up[k - 1, parent_k]
            max_edge[k, i] = max(max_edge[k - 1, i], max_edge[k - 1, parent_k])

    def query_path_max(u, v):
        res = 0.0
        if depth[u] < depth[v]:
            u, v = v, u
        diff = depth[u] - depth[v]
        for k in range(LOGN):
            if (diff >> k) & 1:
                res = max(res, max_edge[k, u])
                u = up[k, u]
        if u == v:
            return res
        for k in range(LOGN - 1, -1, -1):
            if up[k, u] != up[k, v]:
                res = max(res, max_edge[k, u], max_edge[k, v])
                u = up[k, u]
                v = up[k, v]
        return max(res, max_edge[0, u], max_edge[0, v])

    def bfs_path_max(start, target):
        if start == target:
            return 0.0
        q = deque([start])
        vis = {start}
        parent_edge = {}
        while q:
            curr = q.popleft()
            if curr == target:
                break
            for nbr, w in adj[curr]:
                if nbr not in vis:
                    vis.add(nbr)
                    parent_edge[nbr] = (curr, w)
                    q.append(nbr)
        curr = target
        mw = 0.0
        while curr != start:
            prev, w = parent_edge[curr]
            mw = max(mw, w)
            curr = prev
        return mw

    # Compare on 50 deterministic random vertex pairs
    rng = np.random.RandomState(42)
    test_u = rng.randint(0, n, 50)
    test_v = rng.randint(0, n, 50)

    for u, v in zip(test_u, test_v):
        lca_res = query_path_max(u, v)
        bfs_res = bfs_path_max(u, v)
        assert abs(lca_res - bfs_res) < 1e-9, f"Discrepancy at ({u}, {v}): LCA={lca_res}, BFS={bfs_res}"

    # Also test the zero-weight edge endpoints
    zero_idx_u = id2idx["way/1544830710"]
    zero_idx_v = id2idx["way/1544831540"]
    assert query_path_max(zero_idx_u, zero_idx_v) == 0.0
    assert bfs_path_max(zero_idx_u, zero_idx_v) == 0.0


# -----------------------------------------------------------------------------
# AUDIT H: Cost Model and Balanced Objective Equivalence
# -----------------------------------------------------------------------------

def test_audit_h_cost_model_and_balanced_equivalence():
    """Verify that for constant Ra, C_norm == D_norm, proving W_balanced == 0.5 T_norm + 0.5 D_norm."""
    # Synthetic candidate distances and times for a single agency run (e.g. Ambulance Ra = 12.50)
    distances_km = np.array([2.5, 3.8, 5.1, 7.4, 9.0])
    times_min = np.array([5.0, 9.2, 11.0, 16.5, 20.0])
    ra = 12.50

    costs = distances_km * ra

    # Min-max normalization
    d_norm = (distances_km - distances_km.min()) / (distances_km.max() - distances_km.min())
    c_norm = (costs - costs.min()) / (costs.max() - costs.min())

    # C_norm must be numerically identical to D_norm
    np.testing.assert_allclose(d_norm, c_norm, atol=1e-12)

    t_norm = (times_min - times_min.min()) / (times_min.max() - times_min.min())

    w_three_part = 0.50 * t_norm + 0.25 * d_norm + 0.25 * c_norm
    w_two_part = 0.50 * t_norm + 0.50 * d_norm

    np.testing.assert_allclose(w_three_part, w_two_part, atol=1e-12)


def test_earth_radius_consistency():
    """Verify EARTH_KM constant is consistently 6371.0088 across modules."""
    assert EARTH_KM == 6371.0088
    # 1 degree of latitude
    one_deg = haversine_km(0.0, 0.0, 1.0, 0.0)
    expected = (math.pi / 180.0) * 6371.0088
    assert one_deg == pytest.approx(expected, rel=1e-7)

