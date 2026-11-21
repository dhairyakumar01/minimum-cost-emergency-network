#!/usr/bin/env bash
set -e

echo "==============================================================================="
echo " BENGALURU MINIMUM-COST EMERGENCY COMMUNICATION NETWORK (MST OPTIMIZATION)"
echo "==============================================================================="
echo ""

# Find Python 3
if command -v python3 &>/dev/null; then
    PY_BIN=python3
elif command -v python &>/dev/null; then
    PY_BIN=python
else
    echo "[ERROR] Python 3 was not found in your PATH."
    echo "Please install Python 3.10+ and ensure it is accessible in terminal."
    exit 1
fi

echo "[1/3] Using Python:"
$PY_BIN --version

echo ""
echo "[2/3] Verifying and installing required packages..."
$PY_BIN -m pip install -r requirements.txt --quiet || true

echo ""
echo "[3/3] Starting Flask web server at http://127.0.0.1:5000 ..."
echo "-------------------------------------------------------------------------------"
echo "Application URL:   http://127.0.0.1:5000  or  http://localhost:5000"
echo "Health Check:      http://127.0.0.1:5000/api/health"
echo "Press [Ctrl + C] in this terminal to stop the server."
echo "-------------------------------------------------------------------------------"
echo ""

# Automatically open default browser after 2 seconds
(sleep 2 && (xdg-open http://127.0.0.1:5000 2>/dev/null || open http://127.0.0.1:5000 2>/dev/null || true)) &

$PY_BIN backend/flask_app.py
