"""
Vercel Serverless Function entrypoint for Bengaluru Emergency Network Platform.
Exposes the WSGI Flask application callable named `app`.
"""
import sys
import urllib.parse
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
        query_string = environ.get('QUERY_STRING', '')
        if '__path__=' in query_string:
            qs = urllib.parse.parse_qs(query_string, keep_blank_values=True)
            if '__path__' in qs and qs['__path__']:
                target = qs['__path__'][0]
                # If target contains query parameters (e.g. /api/facilities?limit=2), separate them
                if '?' in target:
                    target_path, extra_qs = target.split('?', 1)
                    extra_params = urllib.parse.parse_qs(extra_qs, keep_blank_values=True)
                    for k, v in extra_params.items():
                        qs.setdefault(k, []).extend(v)
                else:
                    target_path = target

                if not target_path.startswith('/'):
                    target_path = '/' + target_path
                environ['PATH_INFO'] = target_path
                del qs['__path__']
                environ['QUERY_STRING'] = urllib.parse.urlencode(qs, doseq=True)
        elif environ.get('HTTP_X_MATCHED_PATH'):
            environ['PATH_INFO'] = environ['HTTP_X_MATCHED_PATH']
        return self.app(environ, start_response)

# Vercel looks for the WSGI application object named `app`
app = VercelPathMiddleware(flask_app)

if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=5000)
