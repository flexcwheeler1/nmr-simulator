#!/usr/bin/env python3
"""
Debug script to test spectrum plot generation
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test all required imports"""
    try:
        print("Testing imports...")
        
        # Test core modules
        from nmr_simulator import NMRSimulator
        print("✓ NMRSimulator imported")
        
        from nmr_simulator.spectrum import Spectrum
        print("✓ Spectrum imported")
        
        from nmr_simulator.spectrum import Peak
        print("✓ Peak imported")
        
        # Test plotly
        import plotly.graph_objects as go
        print("✓ Plotly imported")
        
        # Test other modules
        from visual_multiplet_grouper import VisualMultipletGrouper
        print("✓ VisualMultipletGrouper imported")
        
        from nmr_data_input import NMRDataParser
        print("✓ NMRDataParser imported")
        
        return True
        
    except Exception as e:
        print(f"✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_spectrum_creation():
    """Test basic spectrum creation"""
    try:
        print("\nTesting spectrum creation...")
        
        from nmr_simulator.spectrum import Spectrum, Peak
        
        # Create a simple spectrum
        spectrum = Spectrum(nucleus="1H", field_strength=400)
        print("✓ Spectrum created")
        
        # Add a simple peak
        peak = Peak(
            chemical_shift=7.26,
            intensity=1.0,
            width=2.0/400,  # 2 Hz converted to ppm
            multiplicity="s",
            coupling_constants=[],
            integration=1.0
        )
        spectrum.add_peak(peak)
        print("✓ Peak added")
        
        # Generate spectrum data
        spectrum.generate_spectrum_data(resolution=1024, noise_level=0.0)
        print("✓ Spectrum data generated")
        
        print(f"✓ Spectrum has {len(spectrum.ppm_axis)} data points")
        print(f"✓ X-axis range: {spectrum.ppm_axis[0]:.2f} to {spectrum.ppm_axis[-1]:.2f} ppm")
        
        return spectrum
        
    except Exception as e:
        print(f"✗ Spectrum creation failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_plotly_plot(spectrum):
    """Test Plotly plot creation"""
    try:
        print("\nTesting Plotly plot creation...")
        
        import plotly.graph_objects as go
        import json
        
        # Get spectrum data
        x_data = spectrum.ppm_axis
        y_data = spectrum.data_points
        
        print(f"✓ Data extracted: {len(x_data)} points")
        
        # Create Plotly figure
        fig = go.Figure()
        
        # Add trace
        fig.add_trace(go.Scatter(
            x=x_data,
            y=y_data,
            mode='lines',
            line=dict(color='blue', width=1),
            name='1H NMR'
        ))
        
        print("✓ Trace added")
        
        # Configure layout
        fig.update_layout(
            title='Test NMR Spectrum',
            xaxis=dict(title='Chemical Shift (ppm)', autorange='reversed'),
            yaxis=dict(title='Intensity'),
            plot_bgcolor='white'
        )
        
        print("✓ Layout configured")
        
        # Convert to JSON
        plotly_json = fig.to_json()
        plot_data = json.loads(plotly_json)
        
        print("✓ Plot converted to JSON")
        print(f"✓ Plot data keys: {list(plot_data.keys())}")
        
        return plot_data
        
    except Exception as e:
        print(f"✗ Plotly plot creation failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_web_app_method():
    """Test the web app's generate_spectrum_plot method"""
    try:
        print("\nTesting web app method...")
        
        from web_app import NMRWebApp
        
        app = NMRWebApp()
        print("✓ Web app created")
        
        # Test data
        test_peaks = [
            {
                'shift': 7.26,
                'multiplicity': 's',
                'coupling': 0.0,
                'integration': 1.0
            }
        ]
        
        print("✓ Test data prepared")
        
        # Call the method
        result, multiplet_count = app.generate_spectrum_plot(
            peaks=test_peaks,
            nucleus="1H",
            field_strength=400,
            spectral_width=12.0,
            resolution=1024,
            noise_level=0.0,
            default_linewidth=2.0,
            enable_multiplet_grouping=False,
            grouping_tolerance=0.3
        )
        
        if result is not None:
            print("✓ Method executed successfully")
            print(f"✓ Result type: {type(result)}")
            print(f"✓ Result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
            print(f"✓ Multiplet count: {multiplet_count}")
            return True
        else:
            print("✗ Method returned None")
            return False
            
    except Exception as e:
        print(f"✗ Web app method failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== NMR Spectrum Plot Debug Test ===\n")
    
    # Run tests
    if test_imports():
        spectrum = test_spectrum_creation()
        if spectrum:
            plot_data = test_plotly_plot(spectrum)
            if plot_data:
                if test_web_app_method():
                    print("\n🎉 All tests passed! The spectrum plot generation should work.")
                else:
                    print("\n❌ Web app method test failed.")
            else:
                print("\n❌ Plotly plot test failed.")
        else:
            print("\n❌ Spectrum creation test failed.")
    else:
        print("\n❌ Import test failed.")
