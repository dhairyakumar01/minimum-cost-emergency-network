"""Facilities API routes."""
from flask import Blueprint, jsonify, request

from backend.services.data_service import data_service

facilities_bp = Blueprint("facilities", __name__, url_prefix="/api")


@facilities_bp.route("/facilities", methods=["GET"])
def get_facilities():
    """Return verified emergency facilities with optional agency filtering and search."""
    agency = request.args.get("agency")
    search = request.args.get("search")
    
    # Optional pagination parameters
    page_str = request.args.get("page")
    per_page_str = request.args.get("per_page")
    page = None
    per_page = None

    if page_str is not None:
        try:
            page = int(page_str)
            if page < 1:
                return jsonify({
                    "success": False,
                    "error": {
                        "code": "INVALID_PAGINATION",
                        "message": "Query parameter 'page' must be an integer >= 1.",
                    },
                }), 400
        except ValueError:
            return jsonify({
                "success": False,
                "error": {
                    "code": "INVALID_PAGINATION",
                    "message": "Query parameter 'page' must be a valid integer.",
                },
            }), 400

    if per_page_str is not None:
        try:
            per_page = int(per_page_str)
            if per_page < 1 or per_page > 5000:
                return jsonify({
                    "success": False,
                    "error": {
                        "code": "INVALID_PAGINATION",
                        "message": "Query parameter 'per_page' must be between 1 and 5000.",
                    },
                }), 400
        except ValueError:
            return jsonify({
                "success": False,
                "error": {
                    "code": "INVALID_PAGINATION",
                    "message": "Query parameter 'per_page' must be a valid integer.",
                },
            }), 400

    try:
        result = data_service.get_facilities(
            agency=agency,
            search=search,
            page=page,
            per_page=per_page,
        )
        return jsonify({
            "success": True,
            "data": result,
        }), 200

    except ValueError as ve:
        return jsonify({
            "success": False,
            "error": {
                "code": "INVALID_AGENCY",
                "message": str(ve),
            },
        }), 400

    except FileNotFoundError as fnf:
        return jsonify({
            "success": False,
            "error": {
                "code": "DATASET_NOT_FOUND",
                "message": str(fnf),
            },
        }), 500

    except Exception:
        return jsonify({
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An error occurred while retrieving emergency facilities.",
            },
        }), 500


@facilities_bp.route("/facilities/<path:facility_id>", methods=["GET"])
def get_facility(facility_id: str):
    """Return details for a single emergency facility by ID."""
    try:
        facility = data_service.get_facility_by_id(facility_id)
        if facility is None:
            return jsonify({
                "success": False,
                "error": {
                    "code": "FACILITY_NOT_FOUND",
                    "message": f"Facility with ID '{facility_id}' was not found.",
                },
            }), 404

        return jsonify({
            "success": True,
            "data": facility,
        }), 200

    except Exception:
        return jsonify({
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": f"An error occurred while retrieving facility '{facility_id}'.",
            },
        }), 500
