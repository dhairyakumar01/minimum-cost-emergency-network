@echo off
setlocal
title Run Verification Tests - Emergency Network MST
echo ===============================================================================
echo  Running Automated Test Suite (107 Tests across 10 Test Modules)
echo ===============================================================================
echo.
python -m pytest tests/ -v
echo.
echo ===============================================================================
echo Test execution complete.
echo ===============================================================================
pause
