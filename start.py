#!/usr/bin/env python3
"""
Simple startup script for the Long-Running Query Manager
"""

import subprocess
import sys
import os

def main():
    print("🚀 Starting Long-Running Query Manager")
    print("=" * 50)
    
    # Change to backend directory
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    os.chdir(backend_dir)
    
    # Install requirements
    print("📦 Installing requirements...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
    
    # Start the server
    print("🌟 Starting server...")
    print("🌐 Access the app at: http://localhost:8000")
    subprocess.run([sys.executable, 'main.py'])

if __name__ == "__main__":
    main()