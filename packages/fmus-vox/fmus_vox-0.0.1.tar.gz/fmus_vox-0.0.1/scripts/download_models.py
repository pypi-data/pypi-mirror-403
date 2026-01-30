#!/usr/bin/env python
"""
Model downloader for fmus-vox.

This script downloads pre-trained models for different components of
the fmus-vox library and places them in the appropriate directories.
"""

import os
import sys
import argparse
import subprocess
import tempfile
import hashlib
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import requests
from tqdm import tqdm

# Determine the project root directory
if getattr(sys, 'frozen', False):
    # we are running in a bundle
    PROJECT_ROOT = Path(sys._MEIPASS).parent
else:
    # we are running in a normal Python environment
    PROJECT_ROOT = Path(__file__).parent.parent

# Directory to store models
MODELS_DIR = PROJECT_ROOT / 'models'

# Model information
MODELS = {
    'stt': {
        'whisper-tiny': {
            'url': 'https://openaipublic.azureedge.net/main/whisper/models/d3dd57d32accea0b295c96e26691aa14d8822fac7d9d27d5dc00b4ca2826dd03/tiny.en.pt',
            'size': 152000000,
            'md5': 'd3dd57d32accea0b295c96e26691aa14',
            'filename': 'whisper-tiny.en.pt',
            'description': 'Whisper tiny.en model (English only, 152MB)'
        },
        'whisper-base': {
            'url': 'https://openaipublic.azureedge.net/main/whisper/models/25a8566e1d0c1e2231d1c762132cd20e0f96a85d16145c3a00adf5d1ac670ead/base.en.pt',
            'size': 291000000,
            'md5': '25a8566e1d0c1e2231d1c762132cd20e',
            'filename': 'whisper-base.en.pt',
            'description': 'Whisper base.en model (English only, 291MB)'
        },
        'whisper-small': {
            'url': 'https://openaipublic.azureedge.net/main/whisper/models/f953ad0fd29cacd07d5a9eda5624af0f6bcf2258be67c92b79389873d91e0872/small.en.pt',
            'size': 499000000,
            'md5': 'f953ad0fd29cacd07d5a9eda5624af0f',
            'filename': 'whisper-small.en.pt',
            'description': 'Whisper small.en model (English only, 499MB)'
        }
    },
    'tts': {
        'vits-ljspeech': {
            'url': 'https://huggingface.co/espnet/kan-bayashi_ljspeech_vits/resolve/main/train.loss.ave_10best.pth',
            'size': 76000000,
            'md5': '5f1ebcf5cc4b8cd20c3b047d05252fe0',
            'filename': 'vits-ljspeech.pth',
            'description': 'VITS model trained on LJSpeech dataset (76MB)'
        }
    },
    'voice': {
        'yourtts-pretrained': {
            'url': 'https://huggingface.co/coqui/XTTS-v1/resolve/main/model.pth',
            'size': 1360000000,
            'md5': 'e5d2850b5e7bef525c0ebe78681ddb37',
            'filename': 'yourtts-pretrained.pth',
            'description': 'YourTTS pre-trained model (1.36GB)'
        },
        'sv2tts-encoder': {
            'url': 'https://github.com/CorentinJ/Real-Time-Voice-Cloning/releases/download/v1.0/encoder.pt',
            'size': 16700000,
            'md5': '3f31a6f2c33ad0d3679e31b6b27c6d67',
            'filename': 'sv2tts-encoder.pt',
            'description': 'SV2TTS speaker encoder (16.7MB)'
        }
    },
    'wakeword': {
        'porcupine-en': {
            'url': 'https://github.com/Picovoice/porcupine/raw/master/lib/common/porcupine_params.pv',
            'size': 1000000,
            'md5': 'ee23eaa2ee3b39e7ae9df0a174dcc8e1',
            'filename': 'porcupine-en.pv',
            'description': 'Porcupine English parameters (1MB)'
        }
    }
}

def calculate_md5(file_path: Path) -> str:
    """Calculate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def download_file(url: str, target_path: Path, desc: str) -> bool:
    """
    Download a file with progress bar.

    Args:
        url: URL to download
        target_path: Path to save the file
        desc: Description for the progress bar

    Returns:
        True if successful, False otherwise
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        # Get file size from headers
        file_size = int(response.headers.get('content-length', 0))

        # Ensure parent directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)

        # Download with progress bar
        with open(target_path, 'wb') as f, tqdm(
            desc=desc,
            total=file_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))

        return True

    except Exception as e:
        print(f"Error downloading {url}: {str(e)}")
        if target_path.exists():
            target_path.unlink()
        return False

def download_model(model_type: str, model_name: str, force: bool = False) -> bool:
    """
    Download a specific model.

    Args:
        model_type: Type of model (stt, tts, voice, wakeword)
        model_name: Name of the model
        force: Force download even if model exists

    Returns:
        True if successful, False otherwise
    """
    if model_type not in MODELS:
        print(f"Error: Unknown model type '{model_type}'")
        return False

    if model_name not in MODELS[model_type]:
        print(f"Error: Unknown model '{model_name}' for type '{model_type}'")
        return False

    model_info = MODELS[model_type][model_name]
    target_dir = MODELS_DIR / model_type
    target_path = target_dir / model_info['filename']

    # Check if model already exists and has correct MD5
    if target_path.exists() and not force:
        if calculate_md5(target_path) == model_info['md5']:
            print(f"Model {model_name} already exists and is valid. Use --force to re-download.")
            return True
        else:
            print(f"Model {model_name} exists but is invalid. Re-downloading...")

    # Ensure target directory exists
    target_dir.mkdir(parents=True, exist_ok=True)

    # Download model
    success = download_file(
        model_info['url'],
        target_path,
        f"Downloading {model_name} ({model_info['description']})"
    )

    if success:
        # Verify MD5
        downloaded_md5 = calculate_md5(target_path)
        if downloaded_md5 != model_info['md5']:
            print(f"Warning: MD5 mismatch for {model_name}")
            print(f"  Expected: {model_info['md5']}")
            print(f"  Got: {downloaded_md5}")
            if not force:
                print("Download may be corrupted. Use --force to keep anyway.")
                target_path.unlink()
                return False

        print(f"Successfully downloaded {model_name} to {target_path}")
        return True

    return False

def list_available_models() -> None:
    """Print a list of available models."""
    print("Available models:")
    for model_type, models in MODELS.items():
        print(f"\n{model_type.upper()} Models:")
        for name, info in models.items():
            print(f"  {name}: {info['description']}")

def list_installed_models() -> None:
    """Print a list of installed models."""
    print("Installed models:")
    installed_count = 0

    for model_type, models in MODELS.items():
        installed_type = []
        for name, info in models.items():
            target_path = MODELS_DIR / model_type / info['filename']
            if target_path.exists():
                if calculate_md5(target_path) == info['md5']:
                    installed_type.append(f"  {name}: {info['description']} [VALID]")
                    installed_count += 1
                else:
                    installed_type.append(f"  {name}: {info['description']} [INVALID]")

        if installed_type:
            print(f"\n{model_type.upper()} Models:")
            for line in installed_type:
                print(line)

    if installed_count == 0:
        print("  No models installed")

def main() -> None:
    parser = argparse.ArgumentParser(description="Download pre-trained models for fmus-vox")

    # Command arguments
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Download command
    download_parser = subparsers.add_parser("download", help="Download models")
    download_parser.add_argument("--model-type", "-t", choices=MODELS.keys(), help="Type of model to download")
    download_parser.add_argument("--model-name", "-n", help="Name of model to download")
    download_parser.add_argument("--all", "-a", action="store_true", help="Download all models")
    download_parser.add_argument("--force", "-f", action="store_true", help="Force download even if model exists")

    # List command
    list_parser = subparsers.add_parser("list", help="List models")
    list_parser.add_argument("--available", "-a", action="store_true", help="List available models")
    list_parser.add_argument("--installed", "-i", action="store_true", help="List installed models")

    # Parse arguments
    args = parser.parse_args()

    # Create models directory if it doesn't exist
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    if args.command == "download":
        if args.all:
            # Download all models
            for model_type, models in MODELS.items():
                for model_name in models:
                    download_model(model_type, model_name, args.force)
        elif args.model_type and args.model_name:
            # Download specific model
            download_model(args.model_type, args.model_name, args.force)
        else:
            print("Error: Must specify --all or both --model-type and --model-name")
            parser.print_help()

    elif args.command == "list":
        if args.available or not (args.available or args.installed):
            list_available_models()

        if args.installed or not (args.available or args.installed):
            if args.available:
                print()  # Add newline between lists
            list_installed_models()

    else:
        # No command specified, show help
        parser.print_help()

if __name__ == "__main__":
    main()
