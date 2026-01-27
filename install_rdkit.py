#!/usr/bin/env python3
"""
Install RDKit for molecular structure processing.
"""

import subprocess
import sys

def install_rdkit():
    """Install RDKit using conda or pip."""
    try:
        # Try conda first (recommended for RDKit)
        print("Attempting to install RDKit via conda...")
        result = subprocess.run([
            "conda", "install", "-c", "conda-forge", "rdkit", "-y"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ RDKit installed successfully via conda!")
            return True
        else:
            print("Conda install failed, trying pip...")
            
    except FileNotFoundError:
        print("Conda not found, trying pip...")
    
    try:
        # Try pip installation
        print("Installing RDKit via pip...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "rdkit"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ RDKit installed successfully via pip!")
            return True
        else:
            print(f"❌ Pip install failed: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Error installing RDKit: {e}")
    
    print("⚠️  RDKit installation failed. InChI processing will be limited.")
    print("Please install RDKit manually:")
    print("  conda install -c conda-forge rdkit")
    print("  or")
    print("  pip install rdkit")
    return False

if __name__ == "__main__":
    install_rdkit()
