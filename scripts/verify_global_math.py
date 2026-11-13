import sys
sys.path.insert(0, '.')
import time
from backend.services.audit_service import audit_facilities_dataset
from backend.services.graph_engine import (
    haversine_km, round_half_up, kruskal_mst, prim_mst,
    LCABinaryLiftingOracle, validate_mst_structural
)

def run():
    print("Starting global graph recomputation...")
    audit = audit_facilities_dataset()
    facs = audit["facilities"]
    n = len(facs)
    print(f"Vertices: {n}")

    t0 = time.time()
    vertex_ids = [f["facility_id"] for f in facs]
    all_edges = []
    for i in range(n):
        f1 = facs[i]
        lat1, lon1 = f1["latitude"], f1["longitude"]
        u = f1["facility_id"]
        for j in range(i + 1, n):
            f2 = facs[j]
            v = f2["facility_id"]
            d_km = haversine_km(lat1, lon1, f2["latitude"], f2["longitude"])
            w_mm = round_half_up(d_km * 1000000.0)
            all_edges.append({"u": u, "v": v, "weight": w_mm, "d_km": d_km})

    t_edges = time.time() - t0
    print(f"Total complete graph edges: {len(all_edges)} (built in {t_edges:.2f}s)")
    assert len(all_edges) == (n * (n - 1)) // 2 == 786885

    t1 = time.time()
    kruskal_res = kruskal_mst(vertex_ids, all_edges)
    t_kruskal = time.time() - t1
    print(f"Kruskal completed in {t_kruskal:.3f}s: edges={len(kruskal_res['edges'])} total_weight={kruskal_res['total_integer_weight']} mm ({kruskal_res['total_integer_weight']/1e6:.6f} km)")

    t2 = time.time()
    prim_res = prim_mst(vertex_ids, all_edges, start_vertex=vertex_ids[0])
    t_prim = time.time() - t2
    print(f"Prim completed in {t_prim:.3f}s: edges={len(prim_res['edges'])} total_weight={prim_res['total_integer_weight']} mm ({prim_res['total_integer_weight']/1e6:.6f} km)")

    assert kruskal_res["total_integer_weight"] == prim_res["total_integer_weight"], "Weight parity failed!"
    print("EXACT INTEGER WEIGHT PARITY: PASSED")

    # Check edge sets
    k_set = { (min(e["u"], e["v"]), max(e["u"], e["v"]), e["weight"]) for e in kruskal_res["edges"] }
    p_set = { (min(e["u"], e["v"]), max(e["u"], e["v"]), e["weight"]) for e in prim_res["edges"] }
    diff = k_set ^ p_set
    print(f"Edge set difference: {len(diff)}")
    assert len(diff) == 0, "Edge set identity failed!"
    print("EDGE SET IDENTITY: PASSED")

    # LCA Cycle Property Verification over 785,631 chords
    t3 = time.time()
    oracle = LCABinaryLiftingOracle(vertex_ids, kruskal_res["edges"])
    cert = oracle.verify_cycle_property(all_edges, kruskal_res["edges"])
    t_lca = time.time() - t3
    print(f"LCA Oracle verification completed in {t_lca:.3f}s:")
    print(f"  Chords evaluated: {cert['chords_tested']}")
    print(f"  Violations count: {cert['violations_count']}")
    print(f"  Is Optimal: {cert['is_optimal']}")
    print(f"  Max violation: {cert['max_violation']}")
    assert cert["violations_count"] == 0
    assert cert["is_optimal"] is True
    print("GLOBAL LCA CYCLE PROPERTY VERIFICATION: 100% PASSED (0 VIOLATIONS)")

if __name__ == "__main__":
    run()
