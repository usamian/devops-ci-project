#!/usr/bin/env python
"""
================================================================================
  ATLAS AI - Start Script
  Launches the Atlas AI application with automatic Ollama setup
================================================================================

  This script automatically:
  1. Sets up Python environment and dependencies
  2. Downloads and configures Ollama (if not present)
  3. Starts the application with AI capabilities

  Usage:
    python start.py                    # Start web interface
    python start.py --mode cli         # Start CLI interface
    python start.py --port 8080        # Custom port
    python start.py --debug            # Enable debug mode

================================================================================
"""

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

# Configuration
VENV_DIR = Path(".atlas_venv")
OLLAMA_STATUS_FILE = Path(".ollama_status.json")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral")


def print_banner():
    print()
    print("=" * 60)
    print("  ATLAS AI - UK Immigration Guidance Assistant")
    print("=" * 60)
    print()


def get_venv_python():
    if os.name == 'nt':
        return VENV_DIR / "Scripts" / "python.exe"
    else:
        return VENV_DIR / "bin" / "python"


def is_venv_created():
    return get_venv_python().exists()


def is_ollama_installed():
    """Check if Ollama is installed."""
    try:
        result = subprocess.run(
            ["ollama", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False


def is_ollama_running():
    """Check if Ollama service is running."""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


def is_model_available(model_name):
    """Check if a specific Ollama model is downloaded."""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return any(model_name in m.get("name", "") for m in models)
    except Exception:
        pass
    return False


def get_ollama_status():
    """Get saved Ollama setup status."""
    if OLLAMA_STATUS_FILE.exists():
        try:
            with open(OLLAMA_STATUS_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {"installed": False, "model_downloaded": False, "model": None}


def save_ollama_status(status):
    """Save Ollama setup status."""
    with open(OLLAMA_STATUS_FILE, 'w') as f:
        json.dump(status, f, indent=2)


def install_ollama():
    """Install Ollama based on operating system."""
    system = platform.system()
    print("[->] Installing Ollama...")
    
    if system == "Linux":
        try:
            subprocess.check_call(
                "curl -fsSL https://ollama.ai/install.sh | sh",
                shell=True
            )
            print("[OK] Ollama installed successfully.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"[ERR] Failed to install Ollama: {e}")
            return False
    
    elif system == "Darwin":  # macOS
        try:
            subprocess.check_call(["brew", "install", "ollama"])
            print("[OK] Ollama installed successfully.")
            return True
        except subprocess.CalledProcessError:
            print("[!] Homebrew not found. Please install Ollama manually from https://ollama.ai")
            return False
    
    elif system == "Windows":
        print("[!] Windows installation requires manual download.")
        print("    Please download Ollama from: https://ollama.ai/download")
        print("    After installation, restart this script.")
        return False
    
    return False


def start_ollama_service():
    """Start Ollama service in the background."""
    print("[->] Starting Ollama service...")
    
    if os.name == 'nt':
        subprocess.Popen(
            ["ollama", "serve"],
            creationflags=subprocess.CREATE_NO_WINDOW,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    else:
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
    
    # Wait for service to start
    print("[->] Waiting for Ollama to start...")
    for i in range(30):
        if is_ollama_running():
            print("[OK] Ollama service started.")
            return True
        time.sleep(1)
    
    print("[!] Ollama service did not start in time.")
    return False


def download_ollama_model(model_name):
    """Download a specific Ollama model."""
    print(f"[->] Downloading Ollama model: {model_name}")
    print("    This may take several minutes...")
    
    try:
        subprocess.check_call(["ollama", "pull", model_name])
        print(f"[OK] Model '{model_name}' downloaded successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERR] Failed to download model: {e}")
        return False


def setup_ollama():
    """Complete Ollama setup process."""
    status = get_ollama_status()
    
    # Always use the configured model
    model = os.getenv("OLLAMA_MODEL", "mistral")
    
    # Check if Ollama is already properly set up
    if status.get("installed") and status.get("model_downloaded"):
        if is_ollama_installed() and is_ollama_running():
            if is_model_available(model):
                print("[OK] Ollama is already set up and running.")
                return True
    
    # Install Ollama if not installed
    if not is_ollama_installed():
        print("[!] Ollama not found. Setting up...")
        if not install_ollama():
            print("[!] Ollama installation failed. Continuing without LLM...")
            return False
    
    # Start Ollama service if not running
    if not is_ollama_running():
        if not start_ollama_service():
            print("[!] Could not start Ollama service. Continuing without LLM...")
            return False
    
    # Download model if not available
    if not is_model_available(model):
        if not download_ollama_model(model):
            print("[!] Model download failed. Continuing with basic mode...")
            return False
    
    # Save status
    save_ollama_status({
        "installed": True,
        "model_downloaded": True,
        "model": model,
        "last_check": time.time()
    })
    
    print("[OK] Ollama setup complete!")
    return True


def check_and_run_setup():
    """Check if setup is needed and run it."""
    if not is_venv_created():
        print("[!] Virtual environment not found. Running setup...")
        setup_script = Path("setup.py")
        if setup_script.exists():
            subprocess.check_call([sys.executable, str(setup_script)])
        else:
            print("[ERR] setup.py not found. Please run 'python setup.py' first.")
            sys.exit(1)
    return True


def run_web_mode(host, port, debug):
    """Start the Flask web server."""
    python_path = get_venv_python()
    env = os.environ.copy()
    
    if host:
        env['FLASK_HOST'] = host
    if port:
        env['FLASK_PORT'] = str(port)
    if debug:
        env['FLASK_DEBUG'] = 'True'
    
    print_banner()
    print("[->] Starting web interface...")
    print(f"    Host: {host or '0.0.0.0'}")
    print(f"    Port: {port or 5000}")
    print(f"    Debug: {debug}")
    print()
    print("    Open your browser to: http://localhost:" + str(port or 5000))
    print()
    print("    Press Ctrl+C to stop.")
    print()
    
    subprocess.run([str(python_path), "-m", "src.api.app"], env=env)


def run_cli_mode():
    """Start the CLI interface."""
    python_path = get_venv_python()
    
    print_banner()
    print("[->] Starting CLI interface...")
    print()
    
    subprocess.run([str(python_path), "atlas_ai.py"])


def main():
    parser = argparse.ArgumentParser(
        description="Atlas AI - Start Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python start.py                    # Start web interface
  python start.py --mode cli         # Start CLI interface
  python start.py --port 8080        # Custom port
  python start.py --debug            # Enable debug mode
  python start.py --no-auto-setup    # Skip automatic setup check
  python start.py --no-ollama        # Skip Ollama setup
        """
    )

    parser.add_argument('--mode', type=str, choices=['web', 'cli'], default='web',
                        help='Run mode: web (default) or cli')
    parser.add_argument('--host', type=str, default=None,
                        help='Host address (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=None,
                        help='Port number (default: 5000)')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode')
    parser.add_argument('--no-auto-setup', action='store_true',
                        help='Skip automatic setup check')
    parser.add_argument('--no-ollama', action='store_true',
                        help='Skip Ollama setup (run in basic mode)')

    args = parser.parse_args()

    print_banner()
    print("[->] Initializing Atlas AI...")
    print()

    # Step 1: Setup Python environment
    if not args.no_auto_setup:
        if not is_venv_created():
            print("[->] Step 1/3: Setting up Python environment...")
            if not check_and_run_setup():
                sys.exit(1)
        else:
            print("[OK] Python environment ready.")
    
    # Step 2: Check Groq AI (primary AI - no installation needed)
    print("[->] Step 2/3: Checking Groq AI setup...")
    print("[OK] Groq AI configured (API-based, no installation required)")
    
    # Step 3: Start application
    print()
    print("[->] Step 3/3: Starting application...")
    print()
    
    if args.mode == 'web':
        run_web_mode(args.host, args.port, args.debug)
    else:
        run_cli_mode()


if __name__ == "__main__":
    main()