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

# Vercel looks for the WSGI application object named `app`
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
