#!/usr/bin/env python3
"""
Pet Activity Tracker - Main Application Entry Point

A comprehensive pet monitoring system using YOLO object detection
to track pet activities, zone violations, and feeding behaviors.
"""

import sys
import os
import platform
import tkinter as tk
from tkinter import messagebox

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def check_dependencies():
    """Check if all required dependencies are installed."""
    required_packages = {
        'cv2': 'opencv-python',
        'ultralytics': 'ultralytics',
        'numpy': 'numpy',
        'matplotlib': 'matplotlib',
        'PIL': 'pillow',
        'pandas': 'pandas',
        'pygame': 'pygame'
    }
    
    missing_packages = []
    
    for module_name, package_name in required_packages.items():
        try:
            __import__(module_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        print("❌ Missing required packages:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ All dependencies satisfied")
    return True


def check_model_file():
    """Check if YOLO model file exists."""
    model_path = os.path.join(project_root, "models", "yolo12n.pt")
    
    if not os.path.exists(model_path):
        print(f"❌ Model file not found: {model_path}")
        print("   Please ensure yolo12n.pt is in the models/ directory")
        return False
    
    print(f"✅ Model file found: {model_path}")
    return True


def setup_directories():
    """Create necessary directories if they don't exist."""
    directories = [
        "models",
        "config", 
        "exports",
        "backups"
    ]
    
    for directory in directories:
        dir_path = os.path.join(project_root, directory)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"✅ Created directory: {dir_path}")


def apply_platform_fixes():
    """Apply platform-specific fixes."""
    if platform.system() == 'Darwin':  # macOS
        try:
            # High DPI support for macOS
            from Foundation import NSBundle
            bundle = NSBundle.mainBundle()
            if bundle:
                info = bundle.localizedInfoDictionary() or bundle.infoDictionary()
                if info:
                    info['NSHighResolutionCapable'] = True
        except ImportError:
            pass


def main():
    """Main application entry point."""
    print("🐾 Pet Activity Tracker Starting...")
    print("=" * 50)
    
    # Apply platform-specific fixes
    apply_platform_fixes()
    
    # Setup directories
    setup_directories()
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Please install missing dependencies and try again.")
        return 1
    
    # Check model file
    if not check_model_file():
        print("\n❌ Please ensure the YOLO model file is available.")
        return 1
    
    try:
        # Import and run the frontend application
        from frontend.app import PetTrackerApplication
        
        print("✅ Starting Pet Activity Tracker...")
        
        # Create and run the application
        app = PetTrackerApplication()
        app.run()
        
        print("👋 Pet Activity Tracker closed successfully")
        return 0
        
    except KeyboardInterrupt:
        print("\n🛑 Application interrupted by user")
        return 0
        
    except Exception as e:
        print(f"\n❌ Application error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        sys.exit(1)
    
    sys.exit(main())