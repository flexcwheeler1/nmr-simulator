#!/usr/bin/env python3
"""
Start the web app and test it
"""

import os
import sys
import subprocess
import time
import webbrowser
from threading import Thread

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def start_web_app():
    """Start the web application"""
    try:
        from web_app import app
        print("Starting Flask web application...")
        app.run(debug=False, host='127.0.0.1', port=5000, use_reloader=False)
    except Exception as e:
        print(f"Error starting web app: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=== NMR Web App Launcher ===")
    
    # Start the web app in a separate thread
    web_thread = Thread(target=start_web_app, daemon=True)
    web_thread.start()
    
    # Wait a moment for the server to start
    time.sleep(2)
    
    print("Web application should be running at: http://127.0.0.1:5000")
    print("Press Ctrl+C to stop the server")
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
