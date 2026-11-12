"""Network and MST API routes."""
from flask import Blueprint, jsonify, request

from backend.services.data_service import data_service

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

