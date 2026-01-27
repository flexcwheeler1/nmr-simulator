@echo off
REM NMR Spectra Simulator - Web Application Launcher
REM This script starts the Flask web application

REM Change to the directory where this batch file is located
cd /d %~dp0

echo Starting NMR Spectra Simulator Web Application...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or later from https://python.org
    pause
    exit /b 1
)

REM Check if Flask is installed
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    python -m pip install -r requirements_full.txt
    if errorlevel 1 (
        echo ERROR: Failed to install required packages
        pause
        exit /b 1
    )
)

REM Start the web application
echo.
echo ================================================
echo    NMR Spectra Simulator Web Application
echo ================================================
echo.
echo Starting server...
echo Open your browser and go to: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.

python web_app.py

pause
