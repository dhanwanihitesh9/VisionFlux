#!/usr/bin/env python3
"""
VisionFlux Setup Script
Helps set up the VisionFlux environment and dependencies
"""

import subprocess
import sys
import os
import shutil
from pathlib import Path


def run_command(command, check=True):
    """Run a shell command"""
    print(f"Running: {command}")
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major != 3 or version.minor < 8:
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    return True


def check_system_dependencies():
    """Check for system dependencies"""
    print("\n🔍 Checking system dependencies...")
    
    # Check for essential tools
    dependencies = {
        'git': 'git --version',
        'pip': f'{sys.executable} -m pip --version'
    }
    
    missing = []
    for name, command in dependencies.items():
        if not run_command(command, check=False):
            missing.append(name)
        else:
            print(f"✅ {name} is available")
    
    if missing:
        print(f"❌ Missing dependencies: {', '.join(missing)}")
        return False
    
    return True


def install_python_packages():
    """Install Python packages from requirements.txt"""
    print("\n📦 Installing Python packages...")
    
    # Upgrade pip first
    if not run_command(f'{sys.executable} -m pip install --upgrade pip'):
        print("❌ Failed to upgrade pip")
        return False
    
    # Install requirements
    if not run_command(f'{sys.executable} -m pip install -r requirements.txt'):
        print("❌ Failed to install requirements")
        return False
    
    print("✅ Python packages installed successfully")
    return True


def setup_environment():
    """Set up environment configuration"""
    print("\n⚙️ Setting up environment configuration...")
    
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ Created .env file from .env.example")
        print("📝 Please edit .env file to configure your settings")
    elif env_file.exists():
        print("✅ .env file already exists")
    else:
        print("⚠️ No .env.example found, creating basic .env file")
        with open(env_file, 'w') as f:
            f.write("# VisionFlux Configuration\n")
            f.write("HOST=0.0.0.0\n")
            f.write("PORT=8000\n")
            f.write("DEBUG=false\n")
        print("✅ Created basic .env file")
    
    return True


def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = [
        'detected_frames',
        'logs',
        'static/images'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    return True


def test_installation():
    """Test if the installation works"""
    print("\n🧪 Testing installation...")
    
    try:
        # Test imports
        print("Testing imports...")
        import cv2
        print("✅ OpenCV imported successfully")
        
        import numpy
        print("✅ NumPy imported successfully")
        
        try:
            import torch
            print("✅ PyTorch imported successfully")
        except ImportError:
            print("⚠️ PyTorch not available - some AI features may not work")
        
        try:
            import transformers
            print("✅ Transformers imported successfully")
        except ImportError:
            print("⚠️ Transformers not available - custom prompts may not work")
        
        try:
            import fastapi
            print("✅ FastAPI imported successfully")
        except ImportError:
            print("⚠️ FastAPI not available - web interface may not work")
        
        print("✅ Basic installation test passed")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def main():
    """Main setup function"""
    print("🚀 VisionFlux Setup Script")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check system dependencies
    if not check_system_dependencies():
        print("\n❌ Please install missing system dependencies and try again")
        sys.exit(1)
    
    # Install Python packages
    if not install_python_packages():
        print("\n❌ Failed to install Python packages")
        sys.exit(1)
    
    # Setup environment
    if not setup_environment():
        print("\n❌ Failed to setup environment")
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        print("\n❌ Failed to create directories")
        sys.exit(1)
    
    # Test installation
    if not test_installation():
        print("\n❌ Installation test failed")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("🎉 VisionFlux setup completed successfully!")
    print("\nNext steps:")
    print("1. Edit .env file to configure your RTSP cameras")
    print("2. Run the application: python main.py")
    print("3. Open http://localhost:8000 in your browser")
    print("\nFor help, check the README.md file")


if __name__ == "__main__":
    main()
