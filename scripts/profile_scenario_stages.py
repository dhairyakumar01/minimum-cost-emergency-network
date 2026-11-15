"""Detailed stage-by-stage microsecond profiler for Emergency Simulation.
Measures:
1. Candidate selection
2. In-memory route lookup
3. SQLite route cache lookup (standalone comparison)
4. OSRM matrix retrieval (if any missing)
5. Graph construction
6. MST computation (Prim & Kruskal)
7. Optimality validation (LCA binary-lifting oracle)
8. Road geometry retrieval & caching
9. Scenario cache lookup
10. Total execution
"""
import sys
import os
import time
import sqlite3
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.audit_service import audit_facilities_dataset, normalize_agency
from backend.services.graph_engine import (
    haversine_km,
    kruskal_mst,
    prim_mst,
    validate_mst_structural,
    LCABinaryLiftingOracle,
    compute_compromise_tradeoff_sweep,
)
from backend.services.routing_service import (
    get_pairwise_measurements,
    fetch_mst_edge_geometries,
    _IN_MEMORY_ROUTE_CACHE,
    ensure_route_cache_loaded,
    CACHE_DB_PATH,
)
from backend.services.scenario_service import (
    compute_scenario_cache_key,
    get_scenario_db,
    extract_tree_paths_and_stretch,
    calculate_kendall_tau_b,
    ASSUMED_FUEL_RATES,
)

def profile_run(lat=12.9781, lon=77.5696, agency="hospital_clinic", radius_km=5.0, mode="time", k_param=5):
    ensure_route_cache_loaded()
    norm_agency = normalize_agency(agency)
    fuel_rate = ASSUMED_FUEL_RATES.get(norm_agency, 12.50)

    # 0. Scenario Cache Lookup
    t_start = time.perf_counter()
    cache_key = compute_scenario_cache_key(lat, lon, agency, radius_km, mode, k_param)
    conn = get_scenario_db()
    t_sc_lookup_start = time.perf_counter()
    cached_row = conn.execute(
        "SELECT result_json FROM scenarios WHERE cache_key=? AND status IN ('COMPLETED', 'DISCONNECTED_FOREST') LIMIT 1",
        (cache_key,)
    ).fetchone()
    t_sc_lookup_end = time.perf_counter()
    time_scenario_cache_lookup = t_sc_lookup_end - t_sc_lookup_start
    conn.close()

    # 1. Candidate Selection
    t_cand_start = time.perf_counter()
    audit_data = audit_facilities_dataset()
    all_facilities = audit_data["facilities"]
    eligible_candidates = []
    exclusions = []
    incident_point = {
        "id": "incident_0",
        "facility_id": "incident_0",
        "facility_name": "Incident Origin",
        "latitude": lat,
        "longitude": lon,
        "is_incident": True,
    }
    for fac in all_facilities:
        d_hav = haversine_km(lat, lon, fac["latitude"], fac["longitude"])
        if fac["agency"] != norm_agency:
            exclusions.append(fac)
        elif d_hav > radius_km:
            exclusions.append(fac)
        else:
            fac_entry = dict(fac)
            fac_entry["id"] = fac["facility_id"]
            fac_entry["haversine_km"] = round(d_hav, 3)
            eligible_candidates.append(fac_entry)

    graph_points = [incident_point] + eligible_candidates
    vertex_ids = [p["id"] for p in graph_points]
    points_by_id = {p["id"]: p for p in graph_points}
    t_cand_end = time.perf_counter()
    time_candidate_selection = t_cand_end - t_cand_start

    # 2. In-Memory Route Lookup
    t_inmem_start = time.perf_counter()
    n = len(graph_points)
    inmem_hits = 0
    missing = []
    directed = {}
    for i in range(n):
        for j in range(n):
            if i == j: continue
            p1, p2 = graph_points[i], graph_points[j]
            u_str = f"{p1['longitude']:.5f},{p1['latitude']:.5f}"
            v_str = f"{p2['longitude']:.5f},{p2['latitude']:.5f}"
            val = _IN_MEMORY_ROUTE_CACHE.get((u_str, v_str))
            if val is not None:
                inmem_hits += 1
                directed[(p1["id"], p2["id"])] = {"duration_ds": val[0], "distance_dm": val[1]}
            else:
                missing.append((u_str, v_str))
    t_inmem_end = time.perf_counter()
    time_in_memory_lookup = t_inmem_end - t_inmem_start

    # 3. SQLite disk comparison (sample 500 lookups extrapolated to full n*(n-1))
    db_conn = sqlite3.connect(CACHE_DB_PATH)
    cur = db_conn.cursor()
    sample_queries = min(500, n*(n-1))
    t_sql_start = time.perf_counter()
    for i in range(min(25, n)):
        for j in range(min(20, n)):
            if i == j: continue
            p1, p2 = graph_points[i], graph_points[j]
            cur.execute("SELECT duration_ds, distance_dm FROM route_measurements WHERE origin=? AND dest=?",
                        (f"{p1['longitude']:.5f},{p1['latitude']:.5f}", f"{p2['longitude']:.5f},{p2['latitude']:.5f}")).fetchone()
    t_sql_end = time.perf_counter()
    db_conn.close()
    extrapolated_sqlite_time = ((t_sql_end - t_sql_start) / sample_queries) * (n * (n - 1))

    # 4. OSRM Matrix Retrieval
    t_osrm_start = time.perf_counter()
    meas_res = get_pairwise_measurements(graph_points)
    t_osrm_end = time.perf_counter()
    time_osrm_matrix = t_osrm_end - t_osrm_start
    symmetric_edges = meas_res["symmetric_edges"]

    # 5. Graph Construction
    t_graph_start = time.perf_counter()
    time_edges = []
    dist_edges = []
    for e in symmetric_edges:
        time_edges.append({
            "u": e["u"], "v": e["v"],
            "weight": e["s_t_ds"],
            "duration_ds": e["s_t_ds"],
            "distance_dm": e["s_d_dm"],
        })
        dist_edges.append({
            "u": e["u"], "v": e["v"],
            "weight": e["s_d_dm"],
            "duration_ds": e["s_t_ds"],
            "distance_dm": e["s_d_dm"],
        })
    t_graph_end = time.perf_counter()
    time_graph_construction = t_graph_end - t_graph_start

    # 6. MST Computation
    t_mst_start = time.perf_counter()
    kruskal_res = kruskal_mst(vertex_ids, time_edges, track_trace=True)
    prim_res = prim_mst(vertex_ids, time_edges, start_vertex="incident_0", track_trace=True)
    t_mst_end = time.perf_counter()
    time_mst_computation = t_mst_end - t_mst_start
    active_edges = kruskal_res["mst_edges"]

    # 7. Optimality Validation (LCA Cycle Property)
    t_val_start = time.perf_counter()
    struct_val = validate_mst_structural(vertex_ids, active_edges)
    oracle = LCABinaryLiftingOracle(vertex_ids, active_edges, weight_key="weight")
    optimality_cert = oracle.verify_cycle_property(time_edges, active_edges)
    t_val_end = time.perf_counter()
    time_optimality_validation = t_val_end - t_val_start

    # 8. Road Geometry Retrieval
    t_geom_start = time.perf_counter()
    active_edges_with_geom = fetch_mst_edge_geometries(active_edges, points_by_id)
    t_geom_end = time.perf_counter()
    time_road_geometry = t_geom_end - t_geom_start

    t_total = time.perf_counter() - t_start

    print("\n" + "="*70)
    print(f"STAGE-BY-STAGE PERFORMANCE TELEMETRY: N={len(eligible_candidates)} facilities (|V|={n})")
    print("="*70)
    print(f"1. Candidate Selection:          {time_candidate_selection*1000:8.3f} ms ({time_candidate_selection:.5f} s)")
    print(f"2. In-Memory Route Lookup:        {time_in_memory_lookup*1000:8.3f} ms ({time_in_memory_lookup:.5f} s) [Pairs: {n*(n-1):,}]")
    print(f"   (vs SQLite single-query loop: {extrapolated_sqlite_time*1000:8.3f} ms ({extrapolated_sqlite_time:.3f} s) -> {extrapolated_sqlite_time/max(time_in_memory_lookup, 0.0001):.1f}x slower)")
    print(f"3. OSRM Matrix Retrieval/Cache:   {time_osrm_matrix*1000:8.3f} ms ({time_osrm_matrix:.5f} s)")
    print(f"4. Graph Construction:            {time_graph_construction*1000:8.3f} ms ({time_graph_construction:.5f} s) [Edges: {len(symmetric_edges):,}]")
    print(f"5. MST Computation (Prim+Krusk): {time_mst_computation*1000:8.3f} ms ({time_mst_computation:.5f} s)")
    print(f"6. Optimality Validation (LCA):  {time_optimality_validation*1000:8.3f} ms ({time_optimality_validation:.5f} s) [Chords: {optimality_cert['chords_tested']:,}]")
    print(f"7. Road Geometry Retrieval:       {time_road_geometry*1000:8.3f} ms ({time_road_geometry:.5f} s) [Links: {len(active_edges_with_geom):,}]")
    print(f"8. Scenario Cache Lookup:        {time_scenario_cache_lookup*1000:8.3f} ms ({time_scenario_cache_lookup:.5f} s)")
    print(f"----------------------------------------------------------------------")
    print(f"TOTAL PIPELINE EXECUTION:         {t_total*1000:8.3f} ms ({t_total:.5f} s)")
    print("="*70)

if __name__ == "__main__":
    profile_run()
