@echo off
REM NMR Spectra Simulator - Standalone Executable Builder
REM This script builds a standalone .exe file

REM Change to the directory where this batch file is located
cd /d %~dp0

echo Building NMR Spectra Simulator Standalone Executable...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or later from https://python.org
    pause
    exit /b 1
)

REM Install PyInstaller if not available
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo Installing PyInstaller...
    python -m pip install PyInstaller
    if errorlevel 1 (
        echo ERROR: Failed to install PyInstaller
        pause
        exit /b 1
    )
)

REM Install other requirements
echo Installing/updating requirements...
python -m pip install -r requirements_full.txt
if errorlevel 1 (
    echo ERROR: Failed to install requirements
    pause
    exit /b 1
)

REM Clean previous builds
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Build the executable using the spec file
echo.
echo ================================================
echo        Building Standalone Executable
echo ================================================
echo.
echo This may take several minutes...
echo.

python -m PyInstaller nmr_simulator.spec

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    echo Check the output above for error details.
    pause
    exit /b 1
)

echo.
echo ================================================
echo           Build Completed Successfully!
echo ================================================
echo.
echo Executable location: dist\NMR-Spectra-Simulator.exe
echo.
echo You can now distribute this single .exe file to users.
echo No additional installation or Python required on target systems.
echo.

pause
