#!/usr/bin/env bash
set -e

if command -v python3 &>/dev/null; then
    PY_BIN=python3
else
    PY_BIN=python
fi

echo "==============================================================================="
echo " Running Automated Test Suite (107 Tests across 10 Test Modules)"
echo "==============================================================================="
$PY_BIN -m pytest tests/ -v
