#!/usr/bin/env python3
"""
NMR Spectra Simulator - Universal Launcher

This script provides a universal launcher that can start either:
1. Desktop GUI version (tkinter)
2. Web application version (Flask)
3. Build standalone executable

Usage:
    python launcher.py --gui          # Start desktop GUI
    python launcher.py --web          # Start web application
    python launcher.py --build        # Build standalone executable
    python launcher.py --help         # Show help
"""

import sys
import os
import argparse
import subprocess
import webbrowser
import time
import threading

def check_requirements(mode='gui'):
    """Check if required packages are installed."""
    required_packages = {
        'gui': ['tkinter', 'matplotlib', 'numpy', 'scipy'],
        'web': ['flask', 'matplotlib', 'numpy', 'scipy'],
        'build': ['PyInstaller', 'matplotlib', 'numpy', 'scipy']
    }
    
    missing = []
    for package in required_packages.get(mode, []):
        try:
            if package == 'tkinter':
                import tkinter
            elif package == 'flask':
                import flask
            elif package == 'matplotlib':
                import matplotlib
            elif package == 'numpy':
                import numpy
            elif package == 'scipy':
                import scipy
            elif package == 'PyInstaller':
                try:
                    import PyInstaller
                except ImportError:
                    missing.append(package)
        except ImportError:
            missing.append(package)
    
    return missing

def install_requirements(packages):
    """Install missing packages."""
    print(f"📦 Installing missing packages: {', '.join(packages)}")
    
    # Map package names to pip install names
    pip_names = {
        'tkinter': 'tk',  # Usually comes with Python
        'flask': 'Flask',
        'matplotlib': 'matplotlib',
        'numpy': 'numpy',
        'scipy': 'scipy',
        'PyInstaller': 'PyInstaller'
    }
    
    for package in packages:
        if package == 'tkinter':
            print("⚠️  tkinter should come with Python. If missing, reinstall Python with tkinter support.")
            continue
            
        pip_name = pip_names.get(package, package)
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', pip_name], check=True)
            print(f"✅ {package} installed successfully")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {package}")
            return False
    
    return True

def start_gui():
    """Start the desktop GUI version."""
    print("🖥️  Starting Desktop GUI...")
    
    missing = check_requirements('gui')
    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        if input("Install missing packages? (y/n): ").lower() == 'y':
            if not install_requirements(missing):
                return False
        else:
            return False
    
    try:
        # Import and start the GUI
        from enhanced_gui import create_enhanced_gui
        print("✅ Launching NMR Spectra Simulator GUI...")
        create_enhanced_gui()
        return True
    except Exception as e:
        print(f"❌ Failed to start GUI: {e}")
        return False

def start_web():
    """Start the web application version."""
    print("🌐 Starting Web Application...")
    
    missing = check_requirements('web')
    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        if input("Install missing packages? (y/n): ").lower() == 'y':
            if not install_requirements(missing):
                return False
        else:
            return False
    
    try:
        print("🚀 Starting Flask server...")
        print("📱 Web interface will be available at: http://localhost:5000")
        
        # Start browser after a short delay
        def open_browser():
            time.sleep(2)
            webbrowser.open('http://localhost:5000')
        
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # Start the web app
        import web_app
        return True
    except Exception as e:
        print(f"❌ Failed to start web application: {e}")
        return False

def build_executable():
    """Build standalone executable."""
    print("🔨 Building Standalone Executable...")
    
    missing = check_requirements('build')
    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        if input("Install missing packages? (y/n): ").lower() == 'y':
            if not install_requirements(missing):
                return False
        else:
            return False
    
    try:
        import build_exe
        return build_exe.build_executable()
    except Exception as e:
        print(f"❌ Failed to build executable: {e}")
        return False

def main():
    """Main launcher function."""
    parser = argparse.ArgumentParser(
        description="NMR Spectra Simulator - Universal Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python launcher.py --gui          Start desktop GUI version
  python launcher.py --web          Start web application
  python launcher.py --build        Build standalone executable
  python launcher.py                Interactive mode (choose option)
        """
    )
    
    parser.add_argument('--gui', action='store_true', help='Start desktop GUI version')
    parser.add_argument('--web', action='store_true', help='Start web application')
    parser.add_argument('--build', action='store_true', help='Build standalone executable')
    
    args = parser.parse_args()
    
    print("🧪 NMR Spectra Simulator - Universal Launcher")
    print("=" * 50)
    
    # If no arguments provided, show interactive menu
    if not any([args.gui, args.web, args.build]):
        print("\nChoose launch mode:")
        print("1. Desktop GUI (tkinter)")
        print("2. Web Application (Flask)")
        print("3. Build Standalone Executable")
        print("4. Exit")
        
        while True:
            try:
                choice = input("\nEnter choice (1-4): ").strip()
                if choice == '1':
                    args.gui = True
                    break
                elif choice == '2':
                    args.web = True
                    break
                elif choice == '3':
                    args.build = True
                    break
                elif choice == '4':
                    print("👋 Goodbye!")
                    return
                else:
                    print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                return
    
    # Execute chosen mode
    success = False
    if args.gui:
        success = start_gui()
    elif args.web:
        success = start_web()
    elif args.build:
        success = build_executable()
    
    if success:
        print("\n✅ Operation completed successfully!")
    else:
        print("\n❌ Operation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
