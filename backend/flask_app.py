"""Flask application factory and main server entry point."""
import os
import sys
import time
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from flask import Flask, jsonify, request, send_from_directory

from backend.config import Config
from backend.routes import health_bp, facilities_bp, network_bp, scenarios_bp


def create_app(config: Config = None) -> Flask:
    """Create and configure the Flask web application."""
    config = config or Config()
    frontend_dir = config.FRONTEND_DIR

    app = Flask(
        __name__,
        static_folder=str(frontend_dir),
        static_url_path="",
    )
    app.config.from_object(config)

    # Register API blueprints
    app.register_blueprint(health_bp)
    app.register_blueprint(facilities_bp)
    app.register_blueprint(network_bp)
    app.register_blueprint(scenarios_bp)

    # Pre-warm in-memory dataset cache for maximum initial request speed
    try:
        from backend.services.data_service import data_service
        data_service.load_facilities()
    except Exception:
        pass

    # Server timing header middleware
    @app.before_request
    def start_timer():
        request._start_time = time.perf_counter()

    @app.after_request
    def add_headers(response):
        # Add server processing duration header
        if hasattr(request, "_start_time"):
            duration_ms = (time.perf_counter() - request._start_time) * 1000.0
            response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"

        # Lightweight CORS headers for local APIs
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return response

    # Frontend serving routes
    @app.route("/", methods=["GET"])
    def serve_index():
        """Serve the primary Single-Page Application HTML."""
        return send_from_directory(str(frontend_dir), "index.html")

    @app.route("/assets/<path:subpath>", methods=["GET"])
    def serve_assets(subpath):
        """Serve static CSS, JS, and image assets."""
        assets_dir = frontend_dir / "assets"
        return send_from_directory(str(assets_dir), subpath)

    @app.route("/frontend/assets/<path:subpath>", methods=["GET"])
    def serve_frontend_assets(subpath):
        """Serve static assets if requested with /frontend/ prefix."""
        assets_dir = frontend_dir / "assets"
        return send_from_directory(str(assets_dir), subpath)

    @app.route("/frontend/index.html", methods=["GET"])
    def serve_frontend_index():
        """Serve index.html if requested with /frontend/ prefix."""
        return send_from_directory(str(frontend_dir), "index.html")

    @app.route("/favicon.ico", methods=["GET"])
    def serve_favicon():
        """Return favicon or 204 No Content."""
        favicon_file = frontend_dir / "favicon.ico"
        if favicon_file.exists():
            return send_from_directory(str(frontend_dir), "favicon.ico")
        return ("", 204)

    # Flutter Web Application serving routes
    flutter_dir = frontend_dir / "app"

    @app.route("/app", methods=["GET"])
    @app.route("/app/", methods=["GET"])
    def serve_flutter_index():
        """Serve the Flutter Web Application index HTML."""
        if flutter_dir.exists() and (flutter_dir / "index.html").exists():
            return send_from_directory(str(flutter_dir), "index.html")
        return "Flutter app build not found. Please compile with `flutter build web --base-href /app/`.", 404

    @app.route("/app/<path:subpath>", methods=["GET"])
    def serve_flutter_assets(subpath):
        """Serve compiled Flutter Web assets."""
        if flutter_dir.exists():
            return send_from_directory(str(flutter_dir), subpath)
        return "404 Not Found", 404

    # Centralized JSON error handlers for API requests
    @app.errorhandler(404)
    def handle_not_found(e):
        if request.path.startswith("/api/"):
            return jsonify({
                "success": False,
                "error": {
                    "code": "ENDPOINT_NOT_FOUND",
                    "message": f"Endpoint '{request.path}' was not found on this server.",
                },
            }), 404
        # If requested path exists as a static file in frontend, serve it
        possible_file = frontend_dir / request.path.lstrip("/")
        if possible_file.is_file():
            return send_from_directory(str(frontend_dir), request.path.lstrip("/"))
        # Fallback to SPA index for non-API frontend navigation
        if frontend_dir.exists() and (frontend_dir / "index.html").exists():
            return send_from_directory(str(frontend_dir), "index.html")
        return "404 Not Found", 404

    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        if request.path.startswith("/api/"):
            return jsonify({
                "success": False,
                "error": {
                    "code": "METHOD_NOT_ALLOWED",
                    "message": f"Method '{request.method}' is not permitted for '{request.path}'.",
                },
            }), 405
        return "405 Method Not Allowed", 405

    @app.errorhandler(500)
    def handle_internal_error(e):
        return jsonify({
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred. Please try again.",
            },
        }), 500

    return app


if __name__ == "__main__":
    flask_app = create_app()
    port = int(os.getenv("PORT", "5000"))
    host = os.getenv("HOST", "127.0.0.1")
    print(f"\n=======================================================")
    print(f"  Emergency Communication Network — Flask Web Server")
    print(f"  URL: http://{host}:{port}")
    print(f"  Health Check: http://{host}:{port}/api/health")
    print(f"  Facilities API: http://{host}:{port}/api/facilities")
    print(f"  Global MST API: http://{host}:{port}/api/mst/full")
    print(f"=======================================================\n")
    flask_app.run(host=host, port=port, debug=False)
