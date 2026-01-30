#!/usr/bin/env python
"""
Virtual environment setup script for fmus-vox.

This script creates a Python virtual environment with all the necessary
dependencies for developing and using fmus-vox.
"""

import os
import sys
import argparse
import subprocess
import platform
from pathlib import Path
from typing import List, Optional

# Determine the project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Default venv location
DEFAULT_VENV_DIR = PROJECT_ROOT / ".venv"

# Package options with corresponding pip requirements
PACKAGE_OPTIONS = {
    "dev": [
        "black",
        "flake8",
        "isort",
        "mypy",
        "pytest",
        "pytest-cov",
        "sphinx",
        "sphinx-rtd-theme",
        "sphinxcontrib-napoleon",
    ],
    "stt": [
        "openai-whisper",
        "pytorch>=1.7.0",
        "torchaudio>=0.7.0",
    ],
    "tts": [
        "espnet",
        "gdown",
        "praat-parselmouth",
        "coqui-tts",
    ],
    "voice": [
        "resemblyzer",
        "umap-learn",
        "scikit-learn",
    ],
    "wakeword": [
        "pvporcupine",
        "precise-runner",
    ],
    "api": [
        "fastapi",
        "uvicorn[standard]",
        "python-multipart",
        "pydantic>=2.0.0",
    ],
    "cli": [
        "typer",
        "rich",
        "shellingham",
    ],
}

def run_command(cmd: List[str], cwd: Optional[Path] = None) -> bool:
    """
    Run a command and return True if successful.

    Args:
        cmd: Command to run as a list of strings
        cwd: Working directory to run the command in

    Returns:
        True if the command exited with code 0, False otherwise
    """
    try:
        subprocess.run(
            cmd,
            cwd=cwd if cwd else PROJECT_ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command {' '.join(cmd)}")
        print(f"Exit code: {e.returncode}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False

def create_venv(venv_dir: Path, python_exe: Optional[str] = None) -> bool:
    """
    Create a Python virtual environment.

    Args:
        venv_dir: Directory to create the venv in
        python_exe: Path to Python executable to use

    Returns:
        True if successful, False otherwise
    """
    # Determine the Python executable to use
    if python_exe:
        python = python_exe
    else:
        python = sys.executable

    print(f"Creating virtual environment in {venv_dir}")

    # Create the venv
    cmd = [python, "-m", "venv", str(venv_dir)]
    return run_command(cmd)

def install_wheel_support(venv_dir: Path) -> bool:
    """
    Install wheel support in the virtual environment.

    Args:
        venv_dir: Virtual environment directory

    Returns:
        True if successful, False otherwise
    """
    # Determine pip executable
    if platform.system() == "Windows":
        pip = venv_dir / "Scripts" / "pip"
    else:
        pip = venv_dir / "bin" / "pip"

    print("Installing wheel support")

    # Upgrade pip and install wheel
    cmd = [str(pip), "install", "--upgrade", "pip", "setuptools", "wheel"]
    return run_command(cmd)

def install_package(venv_dir: Path, package_extras: Optional[List[str]] = None) -> bool:
    """
    Install the fmus-vox package and its dependencies.

    Args:
        venv_dir: Virtual environment directory
        package_extras: Extra package options to install

    Returns:
        True if successful, False otherwise
    """
    # Determine pip executable
    if platform.system() == "Windows":
        pip = venv_dir / "Scripts" / "pip"
    else:
        pip = venv_dir / "bin" / "pip"

    # Build package spec with extras
    package_spec = "."
    if package_extras:
        extras = ",".join(package_extras)
        package_spec = f".[{extras}]"

    print(f"Installing fmus-vox with extras: {package_extras if package_extras else 'none'}")

    # Install the package in development mode
    cmd = [str(pip), "install", "-e", package_spec]
    return run_command(cmd)

def print_activation_instructions(venv_dir: Path) -> None:
    """
    Print instructions for activating the virtual environment.

    Args:
        venv_dir: Virtual environment directory
    """
    print("\nVirtual environment setup complete!")
    print("\nTo activate the virtual environment:")

    if platform.system() == "Windows":
        print(f"    {venv_dir}\\Scripts\\activate")
    else:
        print(f"    source {venv_dir}/bin/activate")

    print("\nTo deactivate:")
    print("    deactivate")

def main() -> None:
    parser = argparse.ArgumentParser(description="Set up a virtual environment for fmus-vox")

    parser.add_argument(
        "--venv-dir", "-d",
        default=DEFAULT_VENV_DIR,
        type=Path,
        help=f"Directory to create the virtual environment in (default: {DEFAULT_VENV_DIR})"
    )

    parser.add_argument(
        "--python", "-p",
        help="Path to Python executable to use (default: current Python)"
    )

    parser.add_argument(
        "--full", "-f",
        action="store_true",
        help="Install all extras (equivalent to -edscvwa)"
    )

    parser.add_argument(
        "--editable", "-e",
        action="store_true",
        help="Install the package in editable mode"
    )

    parser.add_argument(
        "--dev", "-D",
        action="store_true",
        help="Install development dependencies"
    )

    parser.add_argument(
        "--stt", "-s",
        action="store_true",
        help="Install STT dependencies"
    )

    parser.add_argument(
        "--tts", "-t",
        action="store_true",
        help="Install TTS dependencies"
    )

    parser.add_argument(
        "--voice", "-v",
        action="store_true",
        help="Install voice cloning dependencies"
    )

    parser.add_argument(
        "--wakeword", "-w",
        action="store_true",
        help="Install wake word detection dependencies"
    )

    parser.add_argument(
        "--api", "-a",
        action="store_true",
        help="Install API dependencies"
    )

    parser.add_argument(
        "--cli", "-c",
        action="store_true",
        help="Install CLI dependencies"
    )

    parser.add_argument(
        "--force", "-F",
        action="store_true",
        help="Force creation of virtual environment if it already exists"
    )

    args = parser.parse_args()

    # Check if the venv directory already exists
    if args.venv_dir.exists() and not args.force:
        print(f"Error: Directory {args.venv_dir} already exists. Use --force to overwrite.")
        sys.exit(1)

    # Determine which extras to install
    extras = []

    if args.full:
        extras = list(PACKAGE_OPTIONS.keys())
    else:
        if args.dev:
            extras.append("dev")
        if args.stt:
            extras.append("stt")
        if args.tts:
            extras.append("tts")
        if args.voice:
            extras.append("voice")
        if args.wakeword:
            extras.append("wakeword")
        if args.api:
            extras.append("api")
        if args.cli:
            extras.append("cli")

    # Create the virtual environment
    if not create_venv(args.venv_dir, args.python):
        print("Failed to create virtual environment")
        sys.exit(1)

    # Install wheel support
    if not install_wheel_support(args.venv_dir):
        print("Failed to install wheel support")
        sys.exit(1)

    # Install the package with extras
    if not install_package(args.venv_dir, extras):
        print("Failed to install package")
        sys.exit(1)

    # Print activation instructions
    print_activation_instructions(args.venv_dir)

if __name__ == "__main__":
    main()
