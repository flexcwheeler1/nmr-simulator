<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# NMR Spectra Simulator Project Instructions

This is an NMR (Nuclear Magnetic Resonance) spectra simulation project with SDBS database integration.

## Project Context
- **Primary Goal**: Create a realistic NMR spectrum simulator that can import chemical shift data from SDBS
- **Key Technologies**: Python, NumPy, Matplotlib, SciPy, tkinter for GUI
- **Data Source**: SDBS (Spectral Database for Organic Compounds) web scraping

## Code Style Guidelines
- Use clear, descriptive variable names (e.g., `chemical_shift`, `peak_intensity`)
- Follow PEP 8 Python style guidelines
- Add comprehensive docstrings for all functions and classes
- Use type hints where appropriate
- Include error handling for web scraping and data parsing

## NMR-Specific Conventions
- Chemical shifts in ppm (parts per million)
- Field strength in MHz (e.g., 400 MHz, 600 MHz)
- Use standard NMR terminology (multipicity: s, d, t, q, m, etc.)
- Coupling constants in Hz

## Architecture Notes
- Separate concerns: simulation logic, data import, and GUI
- Make the simulator extensible for different nuclei (1H, 13C, etc.)
- Cache SDBS data to minimize web requests
- Provide both programmatic API and GUI interface
