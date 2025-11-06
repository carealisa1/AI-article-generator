"""
Quick Setup Script for AI Article Generator
This script installs dependencies step by step to avoid conflicts
"""

import subprocess
import sys
import os

def run_command(command):
    """Run a command and return success status"""
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {command}")
        print(f"Error: {e.stderr}")
        return False

def main():
    print("🚀 AI Article Generator - Quick Setup")
    print("=====================================")
    
    # Core dependencies first
    core_packages = [
        "setuptools",
        "wheel", 
        "pip --upgrade"
    ]
    
    print("\n📦 Installing core dependencies...")
    for package in core_packages:
        if not run_command(f"pip install {package}"):
            print(f"Failed to install {package}")
            return False
    
    # Main dependencies
    main_packages = [
        "streamlit",
        "openai", 
        "requests",
        "beautifulsoup4",
        "python-docx",
        "python-dotenv",
        "pandas",
        "numpy",
        "plotly",
        "Pillow",
        "markdown"
    ]
    
    print("\n📦 Installing main dependencies...")
    for package in main_packages:
        if not run_command(f"pip install {package}"):
            print(f"⚠️ Warning: Failed to install {package}, continuing...")
    
    # Optional dependencies
    optional_packages = [
        "lxml"
    ]
    
    print("\n📦 Installing optional dependencies...")
    for package in optional_packages:
        if not run_command(f"pip install {package}"):
            print(f"⚠️ Optional package {package} failed, skipping...")
    
    print("\n✅ Setup complete!")
    
    # Check for .env file
    if not os.path.exists('.env'):
        print("\n🔧 Setting up environment file...")
        if os.path.exists('.env.template'):
            import shutil
            shutil.copy('.env.template', '.env')
            print("✅ Created .env file from template")
            print("\n⚠️ IMPORTANT: Please edit .env file and add your API keys!")
        else:
            print("⚠️ No .env.template found")
    
    print("\n🚀 Ready to start! Run: streamlit run app.py")

if __name__ == "__main__":
    main()