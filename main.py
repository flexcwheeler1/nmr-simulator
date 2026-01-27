#!/usr/bin/env python3
"""
NMR Spectra Simulator with SDBS Import

Main entry point for the NMR spectra simulation application.
"""

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main entry point for the application."""
    try:
        # Import and run the enhanced GUI
        from enhanced_gui import create_enhanced_gui
        
        print("Starting NMR Spectra Simulator...")
        create_enhanced_gui()
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Please ensure all required packages are installed:")
        print("pip install -r requirements.txt")
        sys.exit(1)
        
    except Exception as e:
        print(f"Error starting application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
