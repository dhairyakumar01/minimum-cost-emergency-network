"""Health check API route."""
from flask import Blueprint, jsonify

from backend.services.data_service import data_service

health_bp = Blueprint("health", __name__, url_prefix="/api")


@health_bp.route("/health", methods=["GET"])
def health_check():
    """Return application health, version, and dataset availability."""
    try:
        health_info = data_service.get_health_status()
        status_code = 200 if health_info["status"] == "healthy" else 503
        return jsonify({
            "success": True,
            "data": health_info,
        }), status_code
    except Exception as e:
        return jsonify({
            "success": False,
            "error": {
                "code": "HEALTH_CHECK_FAILED",
                "message": "Health check encountered an unexpected error.",
            },
        }), 500

