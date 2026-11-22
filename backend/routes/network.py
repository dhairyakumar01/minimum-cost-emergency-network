"""Network and MST API routes."""
from flask import Blueprint, jsonify, request

from backend.services.data_service import data_service
from backend.services.simulator_service import simulator_service

network_bp = Blueprint("network", __name__, url_prefix="/api")


@network_bp.route("/mst/full", methods=["GET"])
def get_full_mst():
    """Return the precomputed, verified global Minimum Spanning Tree.
    
    Guarantees zero recomputation of the 786,885-edge candidate graph.
    """
    algo = request.args.get("algo", "kruskal")

    try:
        mst_data = data_service.get_global_mst(algo=algo)
        return jsonify({
            "success": True,
            "data": mst_data,
        }), 200

    except ValueError as ve:
        return jsonify({
            "success": False,
            "error": {
                "code": "INVALID_ALGORITHM",
                "message": str(ve),
            },
        }), 400

    except FileNotFoundError as fnf:
        return jsonify({
            "success": False,
            "error": {
                "code": "MST_RESULT_NOT_FOUND",
                "message": str(fnf),
            },
        }), 500

    except Exception:
        return jsonify({
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An error occurred while loading global MST data.",
            },
        }), 500


@network_bp.route("/mst/trace", methods=["GET"])
def get_mst_execution_trace():
    """
    Return step-by-step event trace for Algorithm Construction Simulator.
    Supports graph='global'|'incident' and algo='kruskal'|'prim'.
    Optional lat, lon, radius_km for incident-specific 5km radius graph.
    """
    graph_context = request.args.get("graph", "global")
    algo = request.args.get("algo", "kruskal")
    scenario_id = request.args.get("scenario_id")
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    radius_km = request.args.get("radius_km", default=5.0, type=float)

    try:
        trace_data = simulator_service.get_algorithm_trace(
            graph_context=graph_context,
            algorithm=algo,
            scenario_id=scenario_id,
            incident_lat=lat,
            incident_lon=lon,
            radius_km=radius_km
        )
        return jsonify({
            "success": True,
            "data": trace_data,
        }), 200

    except ValueError as ve:
        return jsonify({
            "success": False,
            "error": {
                "code": "INVALID_PARAMETERS",
                "message": str(ve),
            },
        }), 400

    except FileNotFoundError as fnf:
        return jsonify({
            "success": False,
            "error": {
                "code": "TRACE_NOT_FOUND",
                "message": str(fnf),
            },
        }), 404

    except Exception as e:
        return jsonify({
            "success": False,
            "error": {
                "code": "SIMULATOR_TRACE_ERROR",
                "message": str(e),
            },
        }), 500


@network_bp.route("/mst/compare", methods=["GET"])
def get_mst_comparison():
    """
    Return synchronized comparison telemetry for Prim vs Kruskal on the exact same graph.
    Supports graph='global'|'incident'. Optional lat, lon, radius_km for incident graph.
    """
    graph_context = request.args.get("graph", "global")
    scenario_id = request.args.get("scenario_id")
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    radius_km = request.args.get("radius_km", default=5.0, type=float)

    try:
        compare_data = simulator_service.get_comparison_trace(
            graph_context=graph_context,
            scenario_id=scenario_id,
            incident_lat=lat,
            incident_lon=lon,
            radius_km=radius_km
        )
        return jsonify({
            "success": True,
            "data": compare_data,
        }), 200

    except ValueError as ve:
        return jsonify({
            "success": False,
            "error": {
                "code": "INVALID_PARAMETERS",
                "message": str(ve),
            },
        }), 400

    except Exception as e:
        return jsonify({
            "success": False,
            "error": {
                "code": "COMPARISON_ERROR",
                "message": str(e),
            },
        }), 500


