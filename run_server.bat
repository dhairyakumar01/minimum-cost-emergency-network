@echo off
setlocal enabledelayedexpansion
title Minimum-Cost Emergency Communication Network (Bengaluru BBMP)
echo ===============================================================================
echo  BENGALURU MINIMUM-COST EMERGENCY COMMUNICATION NETWORK (MST OPTIMIZATION)
echo ===============================================================================
echo.

:: Check for Python
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python 3 was not found in your system PATH.
    echo Please install Python 3.10 or higher from https://www.python.org/downloads/
    echo Make sure to check the box "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo [1/3] Python environment detected:
python --version

echo.
echo [2/3] Verifying and installing required packages...
python -m pip install -r requirements.txt --quiet
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Pip encountered an issue installing packages. Continuing to launch server...
)

echo.
echo [3/3] Starting Flask web server at http://127.0.0.1:5000 ...
echo -------------------------------------------------------------------------------
echo Application URL:   http://127.0.0.1:5000  or  http://localhost:5000
echo Health Check:      http://127.0.0.1:5000/api/health
echo Press [Ctrl + C] in this window to stop the server at any time.
echo -------------------------------------------------------------------------------
echo.

:: Automatically open browser after 2 seconds
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:5000"

:: Launch the Flask server
python backend/flask_app.py

pause
