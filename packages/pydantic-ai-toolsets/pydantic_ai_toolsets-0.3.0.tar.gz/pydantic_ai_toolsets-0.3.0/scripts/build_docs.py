#!/usr/bin/env python3
"""
Build script for Sphinx documentation.
This mimics the ReadTheDocs build process.
"""
import subprocess
import sys
import os
from pathlib import Path

# Colors for terminal output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def print_colored(message, color=Colors.NC):
    """Print colored message."""
    print(f"{color}{message}{Colors.NC}")

def run_command(cmd, cwd=None, check=True):
    """Run a shell command."""
    print_colored(f"Running: {' '.join(cmd)}", Colors.BLUE)
    result = subprocess.run(cmd, cwd=cwd, check=check)
    return result.returncode == 0

def main():
    """Main build function."""
    # Get project root (parent of scripts directory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    docs_dir = project_root / "docs"
    
    print_colored("Building Sphinx documentation...", Colors.GREEN)
    print(f"Project root: {project_root}")
    print(f"Docs directory: {docs_dir}\n")
    
    # Check if we're in the right directory
    if not (project_root / "pyproject.toml").exists():
        print_colored("Error: pyproject.toml not found!", Colors.RED)
        sys.exit(1)
    
    # Check Python version
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    print(f"Python version: {python_version}\n")
    
    # Install dependencies
    print_colored("Installing dependencies...", Colors.YELLOW)
    install_cmd = [
        sys.executable, "-m", "pip", "install", "-e", ".[docs]"
    ]
    if not run_command(install_cmd, cwd=project_root):
        print_colored("Failed to install dependencies!", Colors.RED)
        sys.exit(1)
    
    # Change to docs directory
    os.chdir(docs_dir)
    
    # Build documentation
    print_colored("\nBuilding HTML documentation...", Colors.YELLOW)
    
    # Try using sphinx-build directly (matches RTD)
    build_cmd = [
        sys.executable, "-m", "sphinx",
        "-b", "html",
        "source",
        "build/html"
    ]
    
    if not run_command(build_cmd, cwd=docs_dir):
        print_colored("Build failed! Check the errors above.", Colors.RED)
        sys.exit(1)
    
    # Check if build was successful
    index_file = docs_dir / "build" / "html" / "index.html"
    if index_file.exists():
        print_colored("\n✓ Documentation built successfully!", Colors.GREEN)
        print("\nTo view the documentation:")
        print(f"  cd {docs_dir}/build/html")
        print("  python3 -m http.server 8000")
        print("\nThen open http://localhost:8000 in your browser")
        print(f"\nOr open directly:")
        print(f"  file://{index_file.absolute()}")
    else:
        print_colored("✗ Build completed but index.html not found!", Colors.RED)
        sys.exit(1)

if __name__ == "__main__":
    main()
