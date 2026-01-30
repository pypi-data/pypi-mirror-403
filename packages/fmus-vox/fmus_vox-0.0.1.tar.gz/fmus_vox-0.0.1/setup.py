"""
Setup script for fmus-vox package.
"""

import os
import re
from setuptools import setup, find_packages

# Get package version from __init__.py without executing it
with open(os.path.join("fmus_vox", "__init__.py")) as f:
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              f.read(), re.M)
    version = version_match.group(1) if version_match else "0.0.1"

# Read the long description from README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Define package dependencies
install_requires = [
    "numpy>=1.20.0",
    "scipy>=1.7.0",
    "librosa>=0.9.0",
    "soundfile>=0.10.0",
    "pyrubberband>=0.3.0",
    "sounddevice>=0.4.0",
    "requests>=2.27.0",
    "tqdm>=4.62.0",
    "pydantic>=1.9.0",
]

extras_require = {
    # STT (Speech-to-Text) dependencies
    "stt": [
        "torch>=1.10.0",
        "openai-whisper>=20230314",
        "transformers>=4.18.0",
        "pyctcdecode>=0.3.0",
    ],

    # TTS (Text-to-Speech) dependencies
    "tts": [
        "torch>=1.10.0",
        "torchaudio>=0.10.0",
        "phonemizer>=3.0.0",
        "unidecode>=1.3.0",
    ],

    # Voice cloning dependencies - basic
    "voice": [
        "torch>=1.10.0",
        "resemblyzer>=0.1.0",
        "praat-parselmouth>=0.4.0",
        "phonemizer>=3.0.0",
        "gruut>=2.0.0; platform_system!='Windows'",  # Not available on Windows
        "unidecode>=1.3.0",
    ],

    # Voice cloning with YourTTS
    "voice-yourtts": [
        "TTS>=0.10.0",
    ],

    # Voice cloning with SV2TTS
    "voice-sv2tts": [
        "tensorflow==1.15.0; python_version<'3.10'",  # SV2TTS requires TF 1.x which is not available for Python 3.10+
        "numpy==1.19.3; python_version<'3.10'",  # Required for TF 1.x
        "librosa==0.8.0; python_version<'3.10'",  # Required for SV2TTS
        "webrtcvad==2.0.10",
        "inflect>=5.3.0",
    ],

    # Wake word detection dependencies
    "wakeword": [
        "pvporcupine>=2.1.0",  # Picovoice Porcupine (commercial)
        "webrtcvad>=2.0.10",   # WebRTC VAD
    ],

    # API server dependencies
    "api": [
        "fastapi>=0.75.0",
        "uvicorn>=0.17.0",
        "python-multipart>=0.0.5",
    ],

    # CLI dependencies
    "cli": [
        "typer>=0.4.0",
        "rich>=12.0.0",
    ],

    # Chatbot dependencies
    "chatbot": [
        "langchain>=0.0.139",
    ],

    # Development dependencies
    "dev": [
        "pytest>=7.0.0",
        "pytest-cov>=3.0.0",
        "black>=22.1.0",
        "isort>=5.10.0",
        "mypy>=0.931",
        "flake8>=4.0.0",
        "sphinx>=4.4.0",
        "sphinx-rtd-theme>=1.0.0",
    ],
}

# Add voice-all group combining all voice cloning methods
extras_require["voice-all"] = sorted(set(
    extras_require["voice"] +
    extras_require["voice-yourtts"] +
    extras_require.get("voice-sv2tts", [])
))

# Full dependencies
extras_require["full"] = sorted(set(sum(extras_require.values(), [])))

setup(
    name="fmus-vox",
    version=version,
    author="Yusef Ulum",
    author_email="yusef314159@gmail.com",
    description="A speech processing library",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mexyusef/fmus-vox",
    project_urls={
        "Bug Tracker": "https://github.com/mexyusef/fmus-vox/issues",
        "Documentation": "https://fmus-vox.readthedocs.io/",
        "Source Code": "https://github.com/mexyusef/fmus-vox",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=install_requires,
    extras_require=extras_require,
    entry_points={
        "console_scripts": [
            "fmus-vox=fmus_vox.cli:main",
        ],
    },
)
