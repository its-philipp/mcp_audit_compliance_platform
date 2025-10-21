#!/usr/bin/env python3
"""
Startup script for the A2A Audit & Compliance Agent Network.
"""

import os
import sys
import subprocess
from pathlib import Path


def check_environment():
    """Check if required environment variables are set."""
    required_vars = ["OPENAI_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in your .env file or environment.")
        return False
    
    return True


def install_dependencies():
    """Install project dependencies."""
    print("📦 Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], check=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def start_server():
    """Start the A2A agent server."""
    print("🚀 Starting A2A Audit & Compliance Agent Network...")
    try:
        subprocess.run([sys.executable, "main.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Server failed to start: {e}")
        return False
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
        return True


def main():
    """Main startup function."""
    print("🎯 A2A Audit & Compliance Agent Network")
    print("=" * 50)
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  No .env file found. Creating from template...")
        try:
            subprocess.run(["cp", "env.example", ".env"], check=True)
            print("✅ Created .env file from template")
            print("📝 Please edit .env file with your API keys before running again")
            return
        except subprocess.CalledProcessError:
            print("❌ Failed to create .env file")
            return
    
    # Check environment
    if not check_environment():
        return
    
    # Install dependencies
    if not install_dependencies():
        return
    
    # Start server
    start_server()


if __name__ == "__main__":
    main()
