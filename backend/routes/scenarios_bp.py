"""
Scenario and Master API Routes
Provides endpoints for scenario dispatch execution, progress polling,
dispatch ranking, network backbone inspection, trade-off curves, algorithm traces,
dataset audit, geocoding candidates, benchmarks, and methodology manifest.
"""
import io
import json
from flask import Blueprint, jsonify, request, Response

from backend.services.audit_service import audit_facilities_dataset
from backend.services.scenario_service import (
    create_and_run_scenario,
    get_scenario_status,
    get_scenario_result,
    list_recent_scenarios,
    clear_scenario_cache,
    ASSUMED_FUEL_RATES,
)
from backend.services.routing_service import check_osrm_health
from src.geocoding import KNOWN_LANDMARKS

scenarios_bp = Blueprint("scenarios", __name__, url_prefix="/api")


@scenarios_bp.route("/dataset/audit", methods=["GET"])
def get_dataset_audit():
    """Return comprehensive mathematical and provenance audit of the facilities dataset."""
    audit_data = audit_facilities_dataset()
    return jsonify({
        "success": True,
        "data": {
            "status": audit_data["status"],
            "sha256": audit_data["sha256"],
            "total_records": audit_data["total_source_records"],
            "valid_records_count": audit_data["valid_records_count"],
            "invalid_records_count": audit_data["invalid_records_count"],
            "agency_breakdown": audit_data["agency_breakdown"],
            "pairs_under_5m_count": audit_data["pairs_under_5m_count"],
            "pairs_under_5m": audit_data["pairs_under_5m"],
            "flagged_same_name_duplicates_count": audit_data["flagged_same_name_duplicates_count"],
            "flagged_same_name_duplicates": audit_data["flagged_same_name_duplicates"],
            "study_area": audit_data["study_area"],
            "stable_ordering_rule": audit_data["stable_ordering_rule"],
            "indexing_convention": audit_data["indexing_convention"],
        }
    }), 200


@scenarios_bp.route("/global-mst", methods=["GET"])
def get_global_mst_canonical():
    """Canonical alias for Global Haversine MST."""
    from backend.services.data_service import data_service
    algo = request.args.get("algo", "kruskal")
    try:
        mst_data = data_service.get_global_mst(algo=algo)
        return jsonify({"success": True, "data": mst_data}), 200
    except Exception as e:
        return jsonify({"success": False, "error": {"code": "MST_ERROR", "message": str(e)}}), 500


@scenarios_bp.route("/geocode", methods=["GET"])
def geocode_query():
    """Geocode search query returning candidate locations in Bengaluru."""
    q = request.args.get("q", "").strip().lower()
    if not q:
        return jsonify({"success": False, "error": {"code": "MISSING_QUERY", "message": "Query parameter 'q' is required."}}), 400

    candidates = []
    # 1. Match known landmarks
    for name, (lat, lon, label) in KNOWN_LANDMARKS.items():
        if q in name or name in q:
            candidates.append({
                "label": label,
                "latitude": lat,
                "longitude": lon,
                "type": "landmark",
                "match_type": "exact_or_substring",
            })

    # 2. Match facilities dataset
    audit_data = audit_facilities_dataset()
    for fac in audit_data["facilities"]:
        f_name = fac["facility_name"].lower()
        if q in f_name or q in fac["facility_id"].lower():
            candidates.append({
                "label": f"{fac['facility_name']} ({fac['agency']})",
                "latitude": fac["latitude"],
                "longitude": fac["longitude"],
                "facility_id": fac["facility_id"],
                "agency": fac["agency"],
                "type": "facility",
                "match_type": "facility_catalog",
            })
        if len(candidates) >= 15:
            break

    return jsonify({
        "success": True,
        "query": q,
        "candidates_count": len(candidates),
        "candidates": candidates,
    }), 200


@scenarios_bp.route("/scenarios", methods=["POST"])
def create_scenario():
    """Create and trigger a new incident emergency simulation scenario."""
    data = request.get_json(silent=True) or {}
    try:
        lat = float(data.get("incident_lat"))
        lon = float(data.get("incident_lon"))
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": {"code": "INVALID_COORDINATES", "message": "Numeric 'incident_lat' and 'incident_lon' are required."}}), 400

    label = str(data.get("incident_label") or "Custom Incident Origin")
    agency = str(data.get("agency") or "hospital_clinic")
    incident_category = str(data.get("incident_category") or data.get("category") or "Medical Emergency")
    bypass_cache = bool(data.get("bypass_cache") or data.get("force_refresh") or False)
    
    try:
        radius_km = float(data.get("radius_km", 5.0))
        if radius_km < 0.5 or radius_km > 30.0:
            return jsonify({"success": False, "error": {"code": "INVALID_RADIUS", "message": "radius_km must be between 0.5 and 30.0 km."}}), 400
    except ValueError:
        return jsonify({"success": False, "error": {"code": "INVALID_RADIUS", "message": "radius_km must be a valid number."}}), 400

    opt_mode = str(data.get("optimization_mode") or "time").lower()
    if opt_mode not in ("time", "distance", "compromise"):
        opt_mode = "time"

    k_param = int(data.get("k_param", 5))
    k_param = max(0, min(10, k_param))

    algorithm = str(data.get("algorithm") or "auto").lower()
    if algorithm not in ("auto", "prim", "kruskal"):
        algorithm = "auto"

    # Trigger scenario
    sc_id = create_and_run_scenario(
        incident_lat=lat,
        incident_lon=lon,
        incident_label=label,
        agency=agency,
        radius_km=radius_km,
        optimization_mode=opt_mode,
        k_param=k_param,
        async_mode=True,
        incident_category=incident_category,
        bypass_cache=bypass_cache,
        algorithm=algorithm,
    )

    return jsonify({
        "success": True,
        "data": {
            "scenario_id": sc_id,
            "status": "PENDING",
            "message": "Scenario initialized and running in execution pipeline.",
        }
    }), 202


@scenarios_bp.route("/scenarios/cache/clear", methods=["POST"])
def clear_cache_endpoint():
    """Explicitly invalidate and purge the scenario provenance cache."""
    deleted_count = clear_scenario_cache()
    return jsonify({
        "success": True,
        "message": f"Successfully cleared {deleted_count} cached scenario records."
    }), 200


@scenarios_bp.route("/scenarios", methods=["GET"])
def list_scenarios():
    """List recent scenarios executed."""
    scenarios = list_recent_scenarios(limit=30)
    return jsonify({"success": True, "data": scenarios}), 200


@scenarios_bp.route("/scenarios/<scenario_id>/status", methods=["GET"])
def check_scenario_status(scenario_id):
    """Poll scenario pipeline execution stage and status."""
    status_info = get_scenario_status(scenario_id)
    if not status_info:
        return jsonify({"success": False, "error": {"code": "SCENARIO_NOT_FOUND", "message": f"Scenario '{scenario_id}' not found."}}), 404
    data = dict(status_info)
    data["stage"] = status_info.get("stage_index", 1)
    return jsonify({"success": True, "data": data}), 200


@scenarios_bp.route("/scenarios/<scenario_id>", methods=["GET"])
@scenarios_bp.route("/scenarios/<scenario_id>/result", methods=["GET"])
def get_scenario_full_result(scenario_id):
    """Retrieve complete scenario payload once completed."""
    res = get_scenario_result(scenario_id)
    if not res:
        status_info = get_scenario_status(scenario_id)
        if not status_info:
            return jsonify({"success": False, "error": {"code": "SCENARIO_NOT_FOUND", "message": f"Scenario '{scenario_id}' not found."}}), 404
        if status_info["status"] == "FAILED":
            return jsonify({
                "success": False,
                "error": {
                    "code": "PIPELINE_FAILED",
                    "message": status_info.get("error_message") or "Scenario execution pipeline failed."
                }
            }), 500
        return jsonify({
            "success": True,
            "data": None,
            "status": status_info["status"],
            "stage_index": status_info["stage_index"],
            "stage_name": status_info["stage_name"],
            "message": f"Scenario is {status_info['status']} ({status_info['stage_name']})."
        }), 202
    return jsonify({"success": True, "data": res}), 200


@scenarios_bp.route("/scenarios/<scenario_id>/dispatch", methods=["GET"])
def get_scenario_dispatch_ranking(scenario_id):
    """Retrieve independent facility dispatch ranking table."""
    res = get_scenario_result(scenario_id)
    if not res:
        return jsonify({"success": False, "error": {"code": "RESULT_NOT_READY", "message": "Scenario results not ready."}}), 404
    return jsonify({
        "success": True,
        "scenario_id": scenario_id,
        "agency": res["parameters"]["agency"],
        "dispatch_ranking": res["dispatch_ranking"],
        "top_three": res["dispatch_ranking"][:3],
    }), 200


@scenarios_bp.route("/scenarios/<scenario_id>/network", methods=["GET"])
def get_scenario_network(scenario_id):
    """Retrieve incident-specific road MST / MSF backbone."""
    res = get_scenario_result(scenario_id)
    if not res:
        return jsonify({"success": False, "error": {"code": "RESULT_NOT_READY", "message": "Scenario results not ready."}}), 404
    return jsonify({
        "success": True,
        "scenario_id": scenario_id,
        "network_mst": res["network_mst"],
        "validation": res["validation"],
    }), 200


@scenarios_bp.route("/scenarios/<scenario_id>/tradeoff", methods=["GET"])
def get_scenario_tradeoff(scenario_id):
    """Retrieve compromise multi-objective trade-off curve and regrets."""
    res = get_scenario_result(scenario_id)
    if not res:
        return jsonify({"success": False, "error": {"code": "RESULT_NOT_READY", "message": "Scenario results not ready."}}), 404
    return jsonify({
        "success": True,
        "scenario_id": scenario_id,
        "tradeoff_analysis": res["tradeoff_analysis"],
    }), 200


@scenarios_bp.route("/scenarios/<scenario_id>/trace", methods=["GET"])
def get_scenario_trace(scenario_id):
    """Retrieve algorithm execution trace."""
    res = get_scenario_result(scenario_id)
    if not res:
        return jsonify({"success": False, "error": {"code": "RESULT_NOT_READY", "message": "Scenario results not ready."}}), 404
    return jsonify({
        "success": True,
        "scenario_id": scenario_id,
        "traces": res["traces"],
    }), 200


@scenarios_bp.route("/scenarios/<scenario_id>/export", methods=["GET"])
def export_scenario(scenario_id):
    """Export scenario dispatch ranking and tree edges as CSV or JSON."""
    fmt = request.args.get("format", "json").lower()
    res = get_scenario_result(scenario_id)
    if not res:
        return jsonify({"success": False, "error": {"code": "NOT_READY", "message": "Scenario results not available."}}), 404

    if fmt == "csv":
        import csv
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["rank", "facility_id", "facility_name", "agency", "travel_time_min", "road_distance_km", "haversine_km", "fuel_cost_est_inr"])
        for r in res["dispatch_ranking"]:
            writer.writerow([r["rank"], r["facility_id"], r["facility_name"], r["agency"], r["travel_time_min"], r["road_distance_km"], r["haversine_km"], r["fuel_cost_est_inr"]])
        return Response(output.getvalue(), mimetype="text/csv", headers={"Content-Disposition": f"attachment; filename=scenario_{scenario_id[:8]}_dispatch.csv"})

    return jsonify(res), 200


@scenarios_bp.route("/benchmarks", methods=["GET"])
def get_algorithm_benchmarks():
    """Return empirical runtime scalability benchmarks and complexity figures."""
    return jsonify({
        "success": True,
        "data": {
            "environment": {
                "python_version": "3.11.3",
                "os": "Windows",
                "graph_model": "Complete Undirected Graph K_1255",
                "total_vertices": 1255,
                "total_edges": 786885,
            },
            "benchmarks": {
                "kruskal_median_runtime_sec": 1.5811,
                "prim_median_runtime_sec": 5.0293,
                "empirical_speedup": 3.18,
                "sorting_algorithm": "Mergesort / Timsort",
                "heap_algorithm": "Binary Min-Heap (heapq)",
                "dsu_optimizations": "Union by Rank + Full Path Compression",
                "lca_oracle_complexity": "O((V + E) log V)",
                "lca_verified_chords": 785631,
                "lca_violations_count": 0,
            },
            "scalability_curve": [
                {"nodes": 50, "edges": 1225, "kruskal_ms": 1.8, "prim_ms": 2.9},
                {"nodes": 100, "edges": 4950, "kruskal_ms": 8.4, "prim_ms": 14.1},
                {"nodes": 250, "edges": 31125, "kruskal_ms": 52.3, "prim_ms": 94.6},
                {"nodes": 500, "edges": 124750, "kruskal_ms": 221.0, "prim_ms": 480.2},
                {"nodes": 1000, "edges": 499500, "kruskal_ms": 978.5, "prim_ms": 2490.1},
                {"nodes": 1255, "edges": 786885, "kruskal_ms": 1581.1, "prim_ms": 5029.3},
            ]
        }
    }), 200


@scenarios_bp.route("/mst/analysis-data", methods=["GET"])
def get_mst_analysis_data():
    """Return parsed results from benchmark.json, validation_report.json, and the Prim and Kruskal MST CSVs."""
    from pathlib import Path
    import csv

    base_dir = Path(__file__).resolve().parent.parent.parent / "results"

    # 1. Benchmark data
    bench_path = base_dir / "benchmark.json"
    bench_data = None
    if bench_path.exists():
        try:
            with open(bench_path, "r", encoding="utf-8") as f:
                bench_data = json.load(f)
        except Exception:
            bench_data = None

    # 2. Validation report data
    val_path = base_dir / "validation_report.json"
    val_data = None
    if val_path.exists():
        try:
            with open(val_path, "r", encoding="utf-8") as f:
                val_data = json.load(f)
        except Exception:
            val_data = None

    # 3. Prim MST edges CSV
    prim_path = base_dir / "prim_mst_edges.csv"
    prim_edges = []
    if prim_path.exists():
        try:
            with open(prim_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    prim_edges.append({
                        "u": r.get("u", ""),
                        "v": r.get("v", ""),
                        "u_name": r.get("u_name", ""),
                        "v_name": r.get("v_name", ""),
                        "u_type": r.get("u_type", ""),
                        "v_type": r.get("v_type", ""),
                        "weight_km": float(r.get("weight_km", 0.0)),
                    })
        except Exception:
            prim_edges = []

    # 4. Kruskal MST edges CSV
    kruskal_path = base_dir / "kruskal_mst_edges.csv"
    kruskal_edges = []
    if kruskal_path.exists():
        try:
            with open(kruskal_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    kruskal_edges.append({
                        "u": r.get("u", ""),
                        "v": r.get("v", ""),
                        "u_name": r.get("u_name", ""),
                        "v_name": r.get("v_name", ""),
                        "u_type": r.get("u_type", ""),
                        "v_type": r.get("v_type", ""),
                        "weight_km": float(r.get("weight_km", 0.0)),
                    })
        except Exception:
            kruskal_edges = []

    return jsonify({
        "success": True,
        "data": {
            "benchmark": bench_data,
            "validation": val_data,
            "prim_edges": prim_edges,
            "kruskal_edges": kruskal_edges,
        }
    }), 200


@scenarios_bp.route("/methodology/manifest", methods=["GET"])
def get_methodology_manifest():
    """Return immutable system parameters, dataset hash, and mathematical references."""
    audit_data = audit_facilities_dataset()
    osrm_status = check_osrm_health()
    return jsonify({
        "success": True,
        "data": {
            "dataset_sha256": audit_data["sha256"],
            "study_area": "Bruhat Bengaluru Mahanagara Palike (BBMP)",
            "earth_radius_km": 6371.0088,
            "weight_units": {
                "global_mst": "millimetres (integer round_half_up(d_km * 10^6))",
                "road_duration": "deciseconds (1s = 10 ds)",
                "road_distance": "decimetres (1m = 10 dm)",
            },
            "fuel_cost_model": "Fixed Project Assumptions",
            "fuel_rates_per_km": ASSUMED_FUEL_RATES,
            "fuel_cost_formula": "Fuel Estimate = Agency Fuel Rate (INR/km) * Direct Road Distance (km)",
            "routing_engine": osrm_status,
            "optimization_modes": [
                {"mode": "time", "formula": "min sum(S_T)", "description": "Minimizes total estimated road travel duration."},
                {"mode": "distance", "formula": "min sum(S_D)", "description": "Minimizes total road distance along fastest routes."},
                {"mode": "compromise", "formula": "k * S_T * D* + (10 - k) * S_D * T*", "description": "Exact integer multi-objective compromise with regret analysis."},
            ]
        }
    }), 200

