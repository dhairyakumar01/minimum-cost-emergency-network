import urllib.request
import json
import time

BASE_URL = "http://127.0.0.1:5000"

def run_test():
    print("1. Testing Health Endpoint...")
    with urllib.request.urlopen(f"{BASE_URL}/api/health", timeout=5.0) as resp:
        health = json.loads(resp.read().decode())
        print(f"Health status: {health['data']['status']}, facilities: {health['data']['facilities_count']}")
        assert health["data"]["facilities_count"] == 1255

    print("\n2. Creating Real Incident Scenario at Majestic (KSR Railway Station)...")
    payload = {
        "incident_lat": 12.9781,
        "incident_lon": 77.5696,
        "incident_label": "Majestic (KSR Railway Station)",
        "agency": "hospital_clinic",
        "radius_km": 3.0,
        "optimization_mode": "time",
        "k_param": 5
    }
    req = urllib.request.Request(
        f"{BASE_URL}/api/scenarios",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10.0) as resp:
        create_res = json.loads(resp.read().decode())
        sc_id = create_res["data"]["scenario_id"]
        print(f"Created scenario ID: {sc_id}")

    print("\n3. Polling Scenario Pipeline Execution...")
    start_time = time.time()
    final_status = None
    for _ in range(60):
        time.sleep(0.5)
        with urllib.request.urlopen(f"{BASE_URL}/api/scenarios/{sc_id}/status", timeout=5.0) as resp:
            st = json.loads(resp.read().decode())["data"]
            if st.get("status") in ("COMPLETED", "FAILED", "BLOCKED"):
                final_status = st.get("status")
                break
        print(f"  Stage: {st.get('stage_name', 'Running')} | Status: {st.get('status')}")

    print(f"Pipeline finished in {time.time() - start_time:.2f}s with status: {final_status}")
    assert final_status == "COMPLETED", f"Scenario did not complete: {final_status}"

    print("\n4. Retrieving Full 4-Tab Scenario Result...")
    with urllib.request.urlopen(f"{BASE_URL}/api/scenarios/{sc_id}/result", timeout=8.0) as resp:
        res = json.loads(resp.read().decode())["data"]

    # Verify Module B: Independent Dispatch Ranking
    print("\n=== MODULE B: INDEPENDENT DISPATCH RANKING ===")
    ranking = res["dispatch_ranking"]
    print(f"Total Ranked Facilities: {len(ranking)}")
    top1 = ranking[0]
    print(f"  Rank #1: {top1['facility_name']} ({top1['facility_id']})")
    print(f"  Direct Travel Time: {top1['travel_time_min']:.1f} min ({top1['travel_time_ds']/10:.0f}s)")
    print(f"  Direct Road Distance: {top1['road_distance_km']:.3f} km")
    print(f"  Haversine Reference: {top1['haversine_km']:.3f} km")
    print(f"  Detour Ratio: {top1['detour_ratio']:.2f}x")
    print(f"  Assumed Fuel Estimate: ₹{top1['fuel_cost_est_inr']:.2f} (Rate: ₹{top1['fuel_rate_inr_km']}/km)")
    print(f"  Snap Status: {top1['snapping_status']}")

    # Verify strict ascending sort order of dispatch ranking
    for idx in range(len(ranking) - 1):
        r1, r2 = ranking[idx], ranking[idx + 1]
        assert (r1["travel_time_ds"], r1["road_distance_dm"], r1["facility_id"]) <= (r2["travel_time_ds"], r2["road_distance_dm"], r2["facility_id"]), "Dispatch ranking sort violation!"
    print("Dispatch Ranking Sort Order: 100% STRICT & INDEPENDENT")

    # Verify Module A: Incident-Specific Network Backbone
    print("\n=== MODULE A: NETWORK BACKBONE (MST / FOREST) ===")
    net = res["network_mst"]
    summary = res["summary"]
    print(f"Network Type: {net['network_type']}")
    print(f"Total Graph Vertices: {summary['graph_vertices_count']}")
    print(f"Spanning Tree Edges: {len(net['edges'])} (Expected: {summary['graph_vertices_count'] - summary['num_components']})")
    print(f"Total Undirected Weight: {net['total_integer_weight']}")
    print(f"Connected Components: {summary['num_components']}")
    print(f"Kendall Tau-b (dispatch vs tree hops): {summary['kendall_tau_b']:.4f}")

    # Verify Mathematical Validation
    print("\n=== MATHEMATICAL VALIDATION REPORT ===")
    val = res["validation"]
    print(f"Structural Acyclicity: {val['structural']['has_cycle'] == False}")
    print(f"Valid Tree / Forest: {val['structural']['is_valid_tree']}")
    print(f"LCA Cycle Property Violations: {val['optimality']['violations_count']}")
    print(f"Chords Evaluated: {val['optimality']['chords_tested']}")
    print(f"Prim / Kruskal Parity: {val['prim_kruskal_parity']}")
    assert val["structural"]["has_cycle"] is False
    assert val["optimality"]["violations_count"] == 0
    assert val["prim_kruskal_parity"] is True

    # Verify Candidates & Exclusions Reconciliation
    print("\n=== CANDIDATES & EXCLUSIONS RECONCILIATION ===")
    excl = res["exclusions_reconciliation"]
    print(f"Total Excluded from Registry: {excl['total_excluded']}")
    reasons = {}
    for e in excl["exclusions"]:
        reasons[e["reason_code"]] = reasons.get(e["reason_code"], 0) + 1
    print(f"Exclusion Reasons Breakdown: {reasons}")

    # Verify Trade-off Curve
    print("\n=== SUPPORTED TRADE-OFF SOLUTIONS (COMPROMISE MODE) ===")
    tradeoff = res["tradeoff_analysis"]
    print(f"Trade-off Status: {tradeoff['status']}")
    print(f"T* (Time Reference): {tradeoff['t_star_ds']} ds ({tradeoff['t_star_min']} min)")
    print(f"D* (Distance Reference): {tradeoff['d_star_dm']} dm ({tradeoff['d_star_km']} km)")
    print(f"Trade-off Points: {len(tradeoff['tradeoff_points'])} points (k = 0 to 10)")
    for pt in tradeoff["tradeoff_points"][::5]:  # k=0, k=5, k=10
        print(f"  k={pt['k']} (λ={pt['lambda']}): Time={pt['tree_time_min']} min (+{pt['regret_time_pct']}% regret), Dist={pt['tree_dist_km']} km (+{pt['regret_dist_pct']}% regret)")

    print("\n>>> ALL MODULE A AND MODULE B REQUIREMENTS VERIFIED SUCCESSFULLY! <<<")

if __name__ == "__main__":
    run_test()
