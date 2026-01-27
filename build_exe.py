#!/usr/bin/env python3
"""
NMR Spectra Simulator - Standalone Application Builder

This script builds a standalone executable using PyInstaller.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def build_executable():
    """Build standalone executable using PyInstaller."""
    
    print("🔨 Building NMR Spectra Simulator Standalone Executable...")
    
    # Get current directory
    current_dir = Path(__file__).parent
    
    # Create build directory
    build_dir = current_dir / "build"
    dist_dir = current_dir / "dist"
    
    # Clean previous builds
    if build_dir.exists():
        shutil.rmtree(build_dir)
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    
    # PyInstaller command
    pyinstaller_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "NMR-Spectra-Simulator",
        "--onefile",  # Single executable file
        "--windowed",  # No console window (for GUI)
        "--icon", "icon.ico" if os.path.exists("icon.ico") else None,
        "--add-data", f"{current_dir}/nmr_simulator;nmr_simulator/",
        "--add-data", f"{current_dir}/visual_multiplet_grouper.py;.",
        "--add-data", f"{current_dir}/non_destructive_grouper.py;.",
        "--add-data", f"{current_dir}/nmr_data_input.py;.",
        "--add-data", f"{current_dir}/help_dialog.py;.",
        "--hidden-import", "tkinter",
        "--hidden-import", "matplotlib",
        "--hidden-import", "numpy",
        "--hidden-import", "scipy",
        "--hidden-import", "pandas",
        "--hidden-import", "requests",
        "--hidden-import", "beautifulsoup4",
        "--hidden-import", "lxml",
        "--collect-all", "matplotlib",
        "--collect-all", "tkinter",
        "main.py"
    ]
    
    # Remove None values
    pyinstaller_cmd = [arg for arg in pyinstaller_cmd if arg is not None]
    
    try:
        print("📦 Running PyInstaller...")
        subprocess.run(pyinstaller_cmd, check=True, cwd=current_dir)
        
        print("✅ Build completed successfully!")
        print(f"📁 Executable location: {dist_dir / 'NMR-Spectra-Simulator.exe'}")
        
        # Create a simple README for the executable
        readme_content = """# NMR Spectra Simulator - Standalone Version

## Usage
Double-click the NMR-Spectra-Simulator.exe file to launch the application.

## Features
- Interactive NMR spectrum simulation
- Support for 1H and 13C NMR
- Real data input from literature/SDBS
- Visual multiplet grouping
- Noise simulation and high resolution support
- Export to Bruker TopSpin and JCAMP-DX formats

## System Requirements
- Windows 10 or later
- No additional software required (all dependencies included)

## Support
This standalone version includes all necessary libraries and dependencies.
If you encounter any issues, please check that your antivirus software
is not blocking the executable.
"""
        
        with open(dist_dir / "README.txt", "w") as f:
            f.write(readme_content)
            
        print("📄 README.txt created in distribution folder")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True

def install_pyinstaller():
    """Install PyInstaller if not available."""
    try:
        import PyInstaller
        print("✅ PyInstaller is already installed")
        return True
    except ImportError:
        print("📦 Installing PyInstaller...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
            print("✅ PyInstaller installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("❌ Failed to install PyInstaller")
            return False

if __name__ == "__main__":
    print("🚀 NMR Spectra Simulator - Executable Builder")
    print("=" * 50)
    
    # Check and install PyInstaller
    if not install_pyinstaller():
        sys.exit(1)
    
    # Build executable
    if build_executable():
        print("\n🎉 Build process completed successfully!")
        print("\nNext steps:")
        print("1. Test the executable in the 'dist' folder")
        print("2. Distribute the .exe file to users")
        print("3. Include the README.txt for user instructions")
    else:
        print("\n💥 Build process failed!")
        sys.exit(1)
