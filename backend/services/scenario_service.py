"""
Emergency Scenario Orchestrator and SQLite Persistence Service
Manages end-to-end incident scenario execution, candidate filtering,
road measurement collection, Prim/Kruskal optimization, LCA validation,
dispatch ranking, MST network-position analysis, and algorithm tracing.
"""
import json
import math
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from backend.services.audit_service import audit_facilities_dataset, haversine_meters, normalize_agency
from backend.services.graph_engine import (
    haversine_km,
    kruskal_mst,
    prim_mst,
    validate_mst_structural,
    LCABinaryLiftingOracle,
    compute_compromise_tradeoff_sweep,
    round_half_up,
)
from backend.services.routing_service import (
    check_osrm_health,
    get_pairwise_measurements,
    DEFAULT_MAX_SNAPPING_METERS,
)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DB_PATH = DATA_DIR / "scenarios.db"

# Fuel rates per kilometer (assumed project parameters)
ASSUMED_FUEL_RATES = {
    "hospital_clinic": 12.50,
    "police": 6.25,
    "fire": 18.00,
}


def get_scenario_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS scenarios (
                scenario_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL,
                stage_index INTEGER NOT NULL,
                stage_name TEXT NOT NULL,
                error_message TEXT,
                incident_lat REAL NOT NULL,
                incident_lon REAL NOT NULL,
                incident_label TEXT,
                agency TEXT NOT NULL,
                radius_km REAL NOT NULL,
                optimization_mode TEXT NOT NULL,
                k_param INTEGER NOT NULL,
                result_json TEXT
            )
        """)
    return conn


def calculate_kendall_tau_b(ranks_x: List[int], ranks_y: List[int]) -> float:
    """Calculate Kendall rank correlation coefficient tau-b between two rankings."""
    n = len(ranks_x)
    if n <= 1:
        return 1.0

    concordant = 0
    discordant = 0
    ties_x = 0
    ties_y = 0

    for i in range(n):
        for j in range(i + 1, n):
            dx = ranks_x[i] - ranks_x[j]
            dy = ranks_y[i] - ranks_y[j]

            if dx == 0 and dy == 0:
                ties_x += 1
                ties_y += 1
            elif dx == 0:
                ties_x += 1
            elif dy == 0:
                ties_y += 1
            elif (dx > 0 and dy > 0) or (dx < 0 and dy < 0):
                concordant += 1
            else:
                discordant += 1

    denom = math.sqrt((concordant + discordant + ties_x) * (concordant + discordant + ties_y))
    if denom == 0:
        return 0.0
    return round((concordant - discordant) / denom, 4)


def extract_tree_paths_and_stretch(
    incident_id: str,
    vertices: List[Any],
    tree_edges: List[Dict[str, Any]],
    directed_measurements: Dict[Tuple[str, str], Dict[str, int]]
) -> Dict[str, Any]:
    """
    Extract unique path from incident to every facility in the tree/forest.
    Computes cumulative path weight, hops, parent, and stretch ratio.
    """
    adj = {v: [] for v in vertices}
    for e in tree_edges:
        u, v = e["u"], e["v"]
        adj[u].append((v, e))
        adj[v].append((u, e))

    from collections import deque
    queue = deque([incident_id])
    visited = {incident_id}
    parent_map = {incident_id: None}
    path_map = {incident_id: [incident_id]}
    hops_map = {incident_id: 0}
    weight_map = {incident_id: 0}

    while queue:
        curr = queue.popleft()
        curr_dist = weight_map[curr]

        for nbr, edge_data in adj.get(curr, []):
            if nbr not in visited:
                visited.add(nbr)
                parent_map[nbr] = curr
                path_map[nbr] = path_map[curr] + [nbr]
                hops_map[nbr] = hops_map[curr] + 1
                edge_w = edge_data.get("s_t_ds", edge_data.get("s_d_dm", edge_data.get("weight", 0)))
                weight_map[nbr] = curr_dist + edge_w
                queue.append(nbr)

    telemetry = []
    for v in vertices:
        if v == incident_id:
            continue

        in_tree = v in visited
        path = path_map.get(v, [])
        hops = hops_map.get(v, None)
        cum_w = weight_map.get(v, None)
        parent = parent_map.get(v, None)

        # Direct measurement from facility to incident
        direct_fwd = directed_measurements.get((v, incident_id))
        direct_time_ds = direct_fwd.get("duration_ds") if direct_fwd else None
        direct_dist_dm = direct_fwd.get("distance_dm") if direct_fwd else None

        stretch = None
        if in_tree and direct_time_ds and direct_time_ds > 0 and cum_w is not None:
            stretch = round(cum_w / direct_time_ds, 3)

        telemetry.append({
            "facility_id": v,
            "connected_to_incident": in_tree,
            "hops": hops,
            "parent_id": parent,
            "tree_path": path,
            "cumulative_tree_weight": cum_w,
            "direct_travel_time_ds": direct_time_ds,
            "direct_road_distance_dm": direct_dist_dm,
            "stretch_ratio": stretch,
        })

    return {"incident_id": incident_id, "node_telemetry": telemetry}


def execute_scenario_pipeline(
    scenario_id: str,
    incident_lat: float,
    incident_lon: float,
    incident_label: str,
    agency: str,
    radius_km: float,
    optimization_mode: str = "time",
    k_param: int = 5
) -> None:
    """Synchronous or asynchronous execution of the full 8-stage pipeline."""
    conn = get_scenario_db()

    def update_stage(idx: int, name: str, status: str = "RUNNING"):
        with conn:
            conn.execute(
                "UPDATE scenarios SET stage_index=?, stage_name=?, status=? WHERE scenario_id=?",
                (idx, name, status, scenario_id)
            )

    try:
        # Stage 1: Validate Incident Location
        update_stage(1, "Validating Incident Coordinates & Boundary")
        if math.isnan(incident_lat) or math.isnan(incident_lon) or not (12.0 <= incident_lat <= 14.0) or not (77.0 <= incident_lon <= 78.5):
            raise ValueError(f"Incident coordinates ({incident_lat}, {incident_lon}) outside valid study region.")

        # Stage 2: Select Candidates & Exclusions Reconciliation
        update_stage(2, "Selecting Eligible Candidates in Radius")
        audit_data = audit_facilities_dataset()
        norm_agency = normalize_agency(agency)
        all_facilities = audit_data["facilities"]

        eligible_candidates = []
        exclusions = []

        incident_point = {
            "id": "incident_0",
            "facility_id": "incident_0",
            "facility_name": incident_label or "Incident Origin",
            "latitude": incident_lat,
            "longitude": incident_lon,
            "is_incident": True,
        }

        for fac in all_facilities:
            d_hav = haversine_km(incident_lat, incident_lon, fac["latitude"], fac["longitude"])
            if fac["agency"] != norm_agency:
                exclusions.append({
                    "facility_id": fac["facility_id"],
                    "facility_name": fac["facility_name"],
                    "reason_code": "AGENCY_MISMATCH",
                    "reason": f"Agency '{fac['agency']}' does not match chosen agency '{norm_agency}'.",
                    "haversine_km": round(d_hav, 3),
                })
            elif d_hav > radius_km:
                exclusions.append({
                    "facility_id": fac["facility_id"],
                    "facility_name": fac["facility_name"],
                    "reason_code": "OUTSIDE_RADIUS",
                    "reason": f"Distance {d_hav:.2f} km exceeds candidate radius {radius_km:.1f} km.",
                    "haversine_km": round(d_hav, 3),
                })
            else:
                fac_entry = dict(fac)
                fac_entry["id"] = fac["facility_id"]
                fac_entry["haversine_km"] = round(d_hav, 3)
                eligible_candidates.append(fac_entry)

        if not eligible_candidates:
            raise ValueError(f"No eligible {norm_agency} facilities found within {radius_km:.1f} km radius. Try increasing search radius.")

        # Limit candidate graph if excessive (e.g., > 25 nodes) to fit OSRM Table API URL limits and ensure sub-second response
        MAX_SAFE_CANDIDATES = 25
        if len(eligible_candidates) > MAX_SAFE_CANDIDATES:
            # Sort by straight-line Haversine distance and retain top nearest candidates
            eligible_candidates.sort(key=lambda x: x["haversine_km"])
            excess = eligible_candidates[MAX_SAFE_CANDIDATES:]
            eligible_candidates = eligible_candidates[:MAX_SAFE_CANDIDATES]
            for exc in excess:
                exclusions.append({
                    "facility_id": exc["facility_id"],
                    "facility_name": exc["facility_name"],
                    "reason_code": "COMPUTATIONAL_LIMIT",
                    "reason": f"Candidate beyond 25-nearest threshold for real-time road measurement. Preserved nearest 25 candidates for dispatch.",
                    "haversine_km": exc["haversine_km"],
                })

        # All points in graph: Incident (vertex 0) + Candidates
        graph_points = [incident_point] + eligible_candidates
        vertex_ids = [p["id"] for p in graph_points]

        # Stage 3: Measuring Road Routes via OSRM
        update_stage(3, "Measuring Road Routes via OSRM")
        measurements_result = get_pairwise_measurements(graph_points)

        if measurements_result["status"] != "COMPLETED":
            with conn:
                conn.execute(
                    "UPDATE scenarios SET status='BLOCKED', stage_name='Routing Service Offline', error_message=? WHERE scenario_id=?",
                    (measurements_result.get("reason", "OSRM offline"), scenario_id)
                )
            return

        directed_measurements = measurements_result["directed_measurements"]
        symmetric_edges = measurements_result["symmetric_edges"]

        # Stage 4: Constructing Graph & Components
        update_stage(4, "Constructing Undirected Symmetric Graph")
        time_edges = []
        dist_edges = []
        for e in symmetric_edges:
            time_edges.append({
                "u": e["u"], "v": e["v"],
                "weight": e["s_t_ds"],
                "duration_ds": e["s_t_ds"],
                "distance_dm": e["s_d_dm"],
                "t_avg_min": e["t_avg_min"],
                "d_avg_km": e["d_avg_km"],
            })
            dist_edges.append({
                "u": e["u"], "v": e["v"],
                "weight": e["s_d_dm"],
                "duration_ds": e["s_t_ds"],
                "distance_dm": e["s_d_dm"],
                "t_avg_min": e["t_avg_min"],
                "d_avg_km": e["d_avg_km"],
            })

        # Stage 5: Running Graph Optimization
        update_stage(5, f"Optimizing Network ({optimization_mode.upper()} Mode)")
        
        # Calculate Pure Time MST & Pure Dist MST
        mst_time_res = kruskal_mst(vertex_ids, time_edges, track_trace=True)
        mst_dist_res = kruskal_mst(vertex_ids, dist_edges, track_trace=True)
        prim_time_res = prim_mst(vertex_ids, time_edges, start_vertex="incident_0", track_trace=True)

        selected_mst_res = mst_time_res
        if optimization_mode == "distance":
            selected_mst_res = mst_dist_res
        elif optimization_mode == "compromise":
            tradeoff = compute_compromise_tradeoff_sweep(vertex_ids, time_edges)
            # Find the point matching k_param
            match_point = next((p for p in tradeoff["tradeoff_points"] if p["k"] == k_param), tradeoff["tradeoff_points"][5])
            selected_mst_res = {
                "algorithm": "kruskal_compromise",
                "mst_edges": match_point["edges"],
                "edge_count": match_point["edge_count"],
                "total_integer_weight": match_point["tree_time_ds"],
                "is_connected": mst_time_res["is_connected"],
                "num_components": mst_time_res["num_components"],
                "components": mst_time_res["components"],
                "trace": mst_time_res["trace"],
                "compromise_point": match_point,
                "tradeoff_sweep": tradeoff,
            }

        # Stage 6: Validating Results
        update_stage(6, "Validating Optimality & Cycle Property")
        active_edges = selected_mst_res["mst_edges"]
        struct_val = validate_mst_structural(vertex_ids, active_edges)
        oracle = LCABinaryLiftingOracle(vertex_ids, active_edges, weight_key="weight")
        eval_edges = time_edges if optimization_mode == "time" else dist_edges
        optimality_cert = oracle.verify_cycle_property(eval_edges, active_edges)

        # Stage 7: Direct Dispatch Ranking (Independent of MST)
        update_stage(7, "Ranking Emergency Dispatch Candidates")
        fuel_rate = ASSUMED_FUEL_RATES.get(norm_agency, 12.50)
        dispatch_rows = []

        for fac in eligible_candidates:
            f_id = fac["id"]
            direct_data = directed_measurements.get((f_id, "incident_0"))
            
            if direct_data:
                dur_ds = direct_data["duration_ds"]
                dist_dm = direct_data["distance_dm"]
                dur_min = round(dur_ds / 600.0, 2)
                dist_km = round(dist_dm / 10000.0, 3)
                detour = round(dist_km / fac["haversine_km"], 2) if fac["haversine_km"] > 0 else 1.0
                est_fuel = round(dist_km * fuel_rate, 2)
                
                dispatch_rows.append({
                    "facility_id": f_id,
                    "facility_name": fac["facility_name"],
                    "agency": norm_agency,
                    "travel_time_ds": dur_ds,
                    "travel_time_min": dur_min,
                    "road_distance_dm": dist_dm,
                    "road_distance_km": dist_km,
                    "haversine_km": fac["haversine_km"],
                    "detour_ratio": detour,
                    "fuel_cost_est_inr": est_fuel,
                    "fuel_rate_inr_km": fuel_rate,
                    "fuel_model_label": f"Estimated fuel (assumed rate ₹{fuel_rate:.2f}/km × road distance)",
                    "snapping_status": "VALID",
                })
            else:
                exclusions.append({
                    "facility_id": f_id,
                    "facility_name": fac["facility_name"],
                    "reason_code": "UNROUTABLE_NULL",
                    "reason": "OSRM returned unreachable null route between facility and incident.",
                    "haversine_km": fac["haversine_km"],
                })

        # Sort dispatch rows strictly by (travel_time_ds, road_distance_dm, facility_id)
        dispatch_rows.sort(key=lambda r: (r["travel_time_ds"], r["road_distance_dm"], r["facility_id"]))
        for rank_idx, row in enumerate(dispatch_rows, start=1):
            row["rank"] = rank_idx

        # Stage 8: MST Network Position & Kendall Tau
        update_stage(8, "Analyzing Network Topology & Saving Scenario")
        net_pos = extract_tree_paths_and_stretch(
            "incident_0",
            vertex_ids,
            active_edges,
            directed_measurements
        )

        # Calculate Kendall tau-b between dispatch ranking and tree hops
        common_facs = [r["facility_id"] for r in dispatch_rows]
        dispatch_ranks = [r["rank"] for r in dispatch_rows]
        telemetry_by_id = {t["facility_id"]: t for t in net_pos["node_telemetry"]}
        tree_hops = [telemetry_by_id.get(f_id, {}).get("hops", 999) or 999 for f_id in common_facs]
        kendall_tau = calculate_kendall_tau_b(dispatch_ranks, tree_hops)

        # Check pure compromise sweep
        tradeoff_summary = compute_compromise_tradeoff_sweep(vertex_ids, time_edges)

        # Assemble Full Scenario Payload
        scenario_result = {
            "scenario_id": scenario_id,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "COMPLETED" if struct_val["is_valid_tree"] and optimality_cert["is_optimal"] else "COMPLETED_WITH_WARNINGS",
            "incident": {
                "latitude": incident_lat,
                "longitude": incident_lon,
                "label": incident_label,
            },
            "parameters": {
                "agency": norm_agency,
                "radius_km": radius_km,
                "optimization_mode": optimization_mode,
                "k_param": k_param,
                "fuel_rate_inr_km": fuel_rate,
            },
            "summary": {
                "total_candidates_in_radius": len(eligible_candidates),
                "graph_vertices_count": len(vertex_ids),
                "evaluated_chords_count": optimality_cert["chords_tested"],
                "tree_edge_count": len(active_edges),
                "is_connected": struct_val["is_valid_tree"],
                "num_components": struct_val["num_components"],
                "kendall_tau_b": kendall_tau,
            },
            "dispatch_ranking": dispatch_rows,
            "network_mst": {
                "algorithm": selected_mst_res["algorithm"],
                "edges": active_edges,
                "total_integer_weight": selected_mst_res["total_integer_weight"],
                "num_components": selected_mst_res["num_components"],
                "components": selected_mst_res["components"],
            },
            "validation": {
                "structural": struct_val,
                "optimality": optimality_cert,
                "prim_kruskal_parity": (mst_time_res["total_integer_weight"] == prim_time_res["total_integer_weight"]),
            },
            "tradeoff_analysis": tradeoff_summary,
            "network_position": net_pos,
            "exclusions_reconciliation": {
                "total_excluded": len(exclusions),
                "exclusions": exclusions,
            },
            "traces": {
                "kruskal": mst_time_res["trace"][:50] if mst_time_res["trace"] else [],
                "prim": prim_time_res["trace"][:50] if prim_time_res["trace"] else [],
            },
        }

        with conn:
            conn.execute(
                "UPDATE scenarios SET status=?, stage_index=8, stage_name='Completed', result_json=? WHERE scenario_id=?",
                (scenario_result["status"], json.dumps(scenario_result), scenario_id)
            )

    except Exception as e:
        import traceback
        err_str = f"{str(e)}\n{traceback.format_exc()}"
        with conn:
            conn.execute(
                "UPDATE scenarios SET status='FAILED', stage_name='Failed', error_message=? WHERE scenario_id=?",
                (err_str, scenario_id)
            )
    finally:
        conn.close()


def create_and_run_scenario(
    incident_lat: float,
    incident_lon: float,
    incident_label: str,
    agency: str,
    radius_km: float,
    optimization_mode: str = "time",
    k_param: int = 5,
    async_mode: bool = True
) -> str:
    """Creates a new scenario in SQLite and triggers execution pipeline."""
    scenario_id = str(uuid.uuid4())
    conn = get_scenario_db()
    with conn:
        conn.execute("""
            INSERT INTO scenarios 
            (scenario_id, created_at, status, stage_index, stage_name, incident_lat, incident_lon, incident_label, agency, radius_km, optimization_mode, k_param)
            VALUES (?, datetime('now'), 'PENDING', 0, 'Initializing Scenario', ?, ?, ?, ?, ?, ?, ?)
        """, (scenario_id, incident_lat, incident_lon, incident_label, agency, radius_km, optimization_mode, k_param))
    conn.close()

    if async_mode:
        t = threading.Thread(
            target=execute_scenario_pipeline,
            args=(scenario_id, incident_lat, incident_lon, incident_label, agency, radius_km, optimization_mode, k_param),
            daemon=True
        )
        t.start()
    else:
        execute_scenario_pipeline(
            scenario_id, incident_lat, incident_lon, incident_label, agency, radius_km, optimization_mode, k_param
        )

    return scenario_id


def get_scenario_status(scenario_id: str) -> Optional[Dict[str, Any]]:
    conn = get_scenario_db()
    row = conn.execute("SELECT * FROM scenarios WHERE scenario_id=?", (scenario_id,)).fetchone()
    conn.close()
    if not row:
        return None
    return {
        "scenario_id": row["scenario_id"],
        "created_at": row["created_at"],
        "status": row["status"],
        "stage_index": row["stage_index"],
        "stage_name": row["stage_name"],
        "error_message": row["error_message"],
    }


def get_scenario_result(scenario_id: str) -> Optional[Dict[str, Any]]:
    conn = get_scenario_db()
    row = conn.execute("SELECT * FROM scenarios WHERE scenario_id=?", (scenario_id,)).fetchone()
    conn.close()
    if not row or not row["result_json"]:
        return None
    return json.loads(row["result_json"])


def list_recent_scenarios(limit: int = 20) -> List[Dict[str, Any]]:
    conn = get_scenario_db()
    rows = conn.execute("SELECT scenario_id, created_at, status, incident_label, agency, radius_km, optimization_mode FROM scenarios ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]
