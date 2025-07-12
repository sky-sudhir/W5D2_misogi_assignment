#!/usr/bin/env python3
"""
Simple run script for the AI Stock Market Chat Agent
"""

import os
import sys
import subprocess
from config import config

def check_requirements():
    """Check if all requirements are met"""
    print("🔍 Checking requirements...")
    
    try:
        # Check if required packages are installed
        import streamlit
        import langchain
        import chromadb
        import groq
        print("✅ All required packages are installed")
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("💡 Please run: pip install -r requirements.txt")
        return False
    
    # Check API keys
    try:
        config.validate_required_keys()
        print("✅ API keys are configured")
    except ValueError as e:
        print(f"❌ {e}")
        print("💡 Please set up your API keys in the .env file")
        return False
    
    return True

def start_application():
    """Start the Streamlit application"""
    print("🚀 Starting AI Stock Market Chat Agent...")
    print("📱 The application will open in your default browser")
    print("🛑 Press Ctrl+C to stop the application")
    print("-" * 50)
    
    try:
        # Run Streamlit app
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Error starting application: {e}")

def main():
    """Main function"""
    print("=" * 50)
    print("📈 AI Stock Market Chat Agent")
    print("=" * 50)
    
    if not check_requirements():
        print("\n❌ Requirements not met. Please fix the issues above.")
        sys.exit(1)
    
    print("\n🎉 All checks passed!")
    print("🔄 Initializing application...")
    
    start_application()

if __name__ == "__main__":
    main() 