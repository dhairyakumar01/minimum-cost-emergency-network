"""
Vercel Serverless Function entrypoint for Bengaluru Emergency Network Platform.
Exposes the WSGI Flask application callable named `app`.
"""
import sys
from pathlib import Path

# Add project root to sys.path so backend and src can be imported
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.flask_app import create_app

flask_app = create_app()

class VercelPathMiddleware:
    """WSGI middleware ensuring correct PATH_INFO when deployed behind Vercel serverless rewrites."""
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        # 1. Restore path from query parameter if passed by vercel.json
        query_string = environ.get('QUERY_STRING', '')
        if '__path__=' in query_string:
            import urllib.parse
            qs = urllib.parse.parse_qs(query_string)
            if '__path__' in qs and qs['__path__']:
                environ['PATH_INFO'] = qs['__path__'][0]
        # 2. Otherwise restore from Vercel's x-matched-path header
        elif environ.get('HTTP_X_MATCHED_PATH'):
            environ['PATH_INFO'] = environ['HTTP_X_MATCHED_PATH']
        return self.app(environ, start_response)

# Vercel looks for the WSGI application object named `app`
app = VercelPathMiddleware(flask_app)

if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=5000)
