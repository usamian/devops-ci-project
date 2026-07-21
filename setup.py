#!/usr/bin/env python
"""
================================================================================
  ATLAS AI - Setup Script
  Handles virtual environment creation and dependency installation
================================================================================

  This script sets up the environment for Atlas AI.
  Run this once before using start.py, or let start.py handle it automatically.

  Usage:
    python setup.py              # Full setup with venv and dependencies
    python setup.py --no-venv    # Install to system Python (not recommended)

================================================================================
"""

import argparse
import os
import subprocess
import sys
import io
from pathlib import Path

# Fix Windows console encoding issues
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Configuration
VENV_DIR = Path(".atlas_venv")
# Use lite requirements by default for faster setup (no heavy ML models)
# Use --full flag to install full requirements with ML models
REQUIREMENTS_FILE = Path("requirements-lite.txt")


def print_header(text):
    print()
    print("=" * 60)
    print(f"  {text}")
    print("=" * 60)
    print()


def get_venv_python():
    if os.name == 'nt':
        return VENV_DIR / "Scripts" / "python.exe"
    else:
        return VENV_DIR / "bin" / "python"


def get_venv_pip():
    if os.name == 'nt':
        return VENV_DIR / "Scripts" / "pip.exe"
    else:
        return VENV_DIR / "bin" / "pip"


def is_venv_created():
    return get_venv_python().exists()


def check_python_version():
    if sys.version_info < (3, 8):
        print("[X] Python 3.8+ required. Found: {}".format(sys.version))
        return False
    print("[OK] Python {}.{} detected.".format(sys.version_info.major, sys.version_info.minor))
    return True


def create_venv():
    if is_venv_created():
        print("[OK] Virtual environment already exists.")
        return True
    print("[>] Creating virtual environment...")
    try:
        subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)])
        print("[OK] Virtual environment created.")
        return True
    except subprocess.CalledProcessError as e:
        print("[X] Failed to create venv: {}".format(e))
        return False


def is_flask_installed():
    pip_path = get_venv_pip()
    if not pip_path.exists():
        return False
    try:
        result = subprocess.run([str(pip_path), "show", "flask"], capture_output=True, text=True)
        return result.returncode == 0
    except Exception:
        return False


def install_dependencies():
    pip_path = get_venv_pip()
    if not pip_path.exists():
        print("[X] pip not found in venv.")
        return False
    if not REQUIREMENTS_FILE.exists():
        print("[X] Requirements file not found.")
        return False
    if is_flask_installed():
        print("[OK] Dependencies already installed.")
        return True
    
    print("[>] Installing dependencies...")
    install_cmd = [str(pip_path), "install", "-r", str(REQUIREMENTS_FILE), "--break-system-packages"]
    try:
        subprocess.check_call(install_cmd)
        print("[OK] Dependencies installed.")
        return True
    except subprocess.CalledProcessError:
        install_cmd = [str(pip_path), "install", "-r", str(REQUIREMENTS_FILE)]
        try:
            subprocess.check_call(install_cmd)
            print("[OK] Dependencies installed.")
            return True
        except subprocess.CalledProcessError as e:
            print("[X] Failed to install: {}".format(e))
            return False


def main():
    parser = argparse.ArgumentParser(description="Atlas AI - Setup Script")
    parser.add_argument('--no-venv', action='store_true', help='Install to system Python')
    parser.add_argument('--force', action='store_true', help='Force reinstallation')
    parser.add_argument('--full', action='store_true', help='Install full requirements (includes heavy ML models like PyTorch, transformers, spaCy)')
    args = parser.parse_args()

    # Use full requirements if --full flag is provided
    if args.full:
        REQUIREMENTS_FILE = Path("requirements.txt")

    print_header("ATLAS AI - Setup")

    if not check_python_version():
        sys.exit(1)

    if args.no_venv:
        print("[!] Installing to system Python...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE), "--break-system-packages"])
            print("[OK] Dependencies installed.")
        except subprocess.CalledProcessError as e:
            print("[X] Failed: {}".format(e))
            sys.exit(1)
        print("\n[OK] Setup complete! Run 'python start.py' to start.")
        return

    print("[>] Step 1/2: Creating virtual environment...")
    if not create_venv():
        sys.exit(1)

    print("\n[>] Step 2/2: Installing dependencies...")
    if args.force and is_flask_installed():
        pip_path = get_venv_pip()
        subprocess.run([str(pip_path), "uninstall", "-y", "flask"], capture_output=True)
    
    if not install_dependencies():
        sys.exit(1)

    print_header("Setup Complete!")
    print("[OK] Virtual environment: .atlas_venv/")
    print("[OK] Dependencies: Installed")
    print("\nNext steps:")
    print("  python start.py          # Start web interface")
    print("  python start.py --mode cli  # Start CLI mode")
    print()


if __name__ == "__main__":
    main()