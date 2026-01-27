@echo off
echo Testing NMR Spectra Simulator Web Application...
echo.

REM Test imports
python -c "import sys; print('Python version:', sys.version)"
python -c "import flask; print('Flask version:', flask.__version__)"
python -c "import matplotlib; print('Matplotlib version:', matplotlib.__version__)"
python -c "import numpy; print('NumPy version:', numpy.__version__)"

echo.
echo All required packages are available!
echo.
echo To start the web application:
echo   python web_app.py
echo.
echo To use the universal launcher:
echo   python launcher.py
echo.
echo To build standalone executable:
echo   python build_exe.py
echo.

pause
