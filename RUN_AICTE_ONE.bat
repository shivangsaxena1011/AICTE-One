@echo off
setlocal enabledelayedexpansion
title AICTE ONE - Unified Institutional Governance Platform

echo ==============================================================================
echo                      AICTE ONE - PRODUCTION PLATFORM
echo     Unified Institution Intelligence, Approval, Compliance ^& Document Verification
echo ==============================================================================
echo.

:: 1. Check Python installation
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

echo [OK] Python detected:
python --version
echo.

:: 2. Check / Install requirements if needed
echo [INFO] Checking Python dependencies...
python -c "import fastapi, uvicorn, sqlalchemy, pydantic, requests" >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [INFO] Installing required dependencies from requirements.txt...
    pip install -r requirements.txt
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
) else (
    echo [OK] All core dependencies verified.
)
echo.

:: 3. Launch Platform Backend and Open Browser
echo [INFO] Starting AICTE ONE FastAPI Server on http://localhost:8000 ...
echo [INFO] Press Ctrl+C at any time to stop the server.
echo.

start "" "http://localhost:8000/"
python backend/main.py

pause
