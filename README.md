# NMR Spectra Simulator Web Application

A web-based tool for simulating and analyzing NMR (Nuclear Magnetic Resonance) spectra with interactive visualization, peak editing, and multiple export formats.

## Features

- 📊 **Interactive NMR Simulation**: Generate spectra from peak data
- ✏️ **Peak Editing**: Modify chemical shifts, intensities, linewidths, and integrations in real-time
- 🔍 **Multiplet Grouping**: Automatic identification and visualization of multiplet patterns
- 📈 **Interactive Plots**: Zoom, pan, and explore spectra with Plotly
- 💾 **Multiple Export Formats**: 
  - CSV, TXT (peak tables and full spectra)
  - PNG (publication-ready images)
  - JCAMP-DX (for MNova and other software)
  - Bruker format (for TopSpin)
- 🎨 **Customizable Parameters**: Control resolution, noise, linewidths, and grouping tolerance

## Installation

### Local Setup

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/nmr-spectra-simulator.git
cd nmr-spectra-simulator

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python web_app.py
```

Access the app at: `http://localhost:5000`

## Quick Start

1. Run `python web_app.py`
2. Open browser to `http://localhost:5000`
3. Paste NMR peak data in SDBS or standard format
3. Click "Load Demo Data"
4. View the NMR peak data in the text display

## Project Structure

```
spectra-simulation/
├── main.py                 # Main application entry point
├── simple_gui.py           # Working simple GUI
├── test_simulator.py       # Test script for core functionality
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── nmr_simulator/         # Core NMR simulation modules
│   ├── __init__.py
│   ├── simulator.py       # Main simulation engine
│   ├── molecule.py        # Molecule representation
│   └── spectrum.py        # Spectrum data structures
├── sdbs_import/           # SDBS database integration
│   ├── __init__.py
│   ├── scraper.py         # Web scraping for SDBS data (demo mode)
│   └── parser.py          # Parse SDBS data formats
├── gui/                   # User interface (advanced, in progress)
│   ├── __init__.py
│   ├── main_window.py     # Main application window
│   └── spectrum_viewer.py # Spectrum visualization widget
└── data/                  # Data files and cache
    └── sdbs_cache/        # Cached chemical shift data
```

## Technical Details

### Core Components

1. **Molecule Class**: Represents molecular structures with atoms and chemical shifts
2. **Spectrum Class**: Handles NMR spectrum data with peaks and visualization
3. **NMRSimulator**: Main simulation engine for generating spectra
4. **SDBSParser**: Handles demo data and future SDBS integration

### Demo Data

The simulator includes realistic demo data for:
- **Ethanol**: 1H NMR (3 peaks) and 13C NMR (2 peaks)
- **Acetone**: 1H NMR (1 peak) and 13C NMR (2 peaks)  
- **Benzene**: 1H NMR (1 peak) and 13C NMR (1 peak)

### Sample Output

For Ethanol:
```
1H NMR Spectrum:
Peak 1: δ 1.25 ppm (t, 3H)
Peak 2: δ 3.69 ppm (q, 2H)
Peak 3: δ 5.32 ppm (s, 1H)

13C NMR Spectrum:
Peak 1: δ 18.30 ppm (s, 1H)
Peak 2: δ 58.20 ppm (s, 1H)
```

## Dependencies

- **numpy**: Numerical computations
- **matplotlib**: Spectrum plotting and visualization
- **scipy**: Signal processing and peak fitting
- **pandas**: Data manipulation and analysis
- **requests**: HTTP requests for future SDBS scraping
- **beautifulsoup4**: HTML parsing for web scraping
- **lxml**: XML/HTML parsing backend
- **tkinter**: GUI framework (included with Python)

## Future Enhancements

- [ ] Real SDBS database integration
- [ ] Interactive spectrum plotting with matplotlib
- [ ] More compound examples
- [ ] 2D NMR simulation
- [ ] SMILES string parsing
- [ ] Coupling constant calculations
- [ ] Peak integration analysis

## License

This project is for educational and research purposes.

## Contributing

Feel free to contribute by:
- Adding more demo compounds
- Improving the GUI interface
- Implementing real SDBS integration
- Adding more NMR simulation features
