"""
Configuration management for fmus-vox.

This module provides facilities for loading, storing, and accessing
configuration settings throughout the library.
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

from fmus_vox.core.errors import ConfigError

class Config:
    """
    Configuration manager for fmus-vox.

    Handles loading, saving, and accessing configuration settings.
    Supports both global and model-specific configurations.
    """

    # Default configuration values
    _defaults = {
        "models_dir": str(Path.home() / ".fmus-vox" / "models"),
        "cache_dir": str(Path.home() / ".fmus-vox" / "cache"),
        "log_level": "INFO",
        "device": "auto",  # 'cpu', 'cuda', 'auto'
        "default_stt_model": "whisper",
        "default_tts_model": "vits",
        "default_sample_rate": 16000,
        "default_voice": "en_female",
    }

    def __init__(self):
        """Initialize configuration with default values."""
        self._config = self._defaults.copy()
        self._user_config_path = Path.home() / ".fmus-vox" / "config.json"

        # Load user configuration if exists
        self._load_user_config()

        # Create necessary directories
        self._ensure_directories_exist()

    def _load_user_config(self) -> None:
        """Load user configuration from file if it exists."""
        if self._user_config_path.exists():
            try:
                with open(self._user_config_path, 'r') as f:
                    user_config = json.load(f)
                self._config.update(user_config)
            except Exception as e:
                raise ConfigError(f"Failed to load user configuration: {str(e)}")

    def _ensure_directories_exist(self) -> None:
        """Create necessary directories if they don't exist."""
        for dir_key in ["models_dir", "cache_dir"]:
            Path(self._config[dir_key]).mkdir(parents=True, exist_ok=True)

    def save(self) -> None:
        """Save current configuration to user config file."""
        try:
            # Ensure directory exists
            self._user_config_path.parent.mkdir(parents=True, exist_ok=True)

            # Write config to file
            with open(self._user_config_path, 'w') as f:
                json.dump(self._config, f, indent=2)
        except Exception as e:
            raise ConfigError(f"Failed to save configuration: {str(e)}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.

        Args:
            key: Configuration key
            default: Default value if key doesn't exist

        Returns:
            Configuration value
        """
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value.

        Args:
            key: Configuration key
            value: Configuration value
        """
        self._config[key] = value

    def update(self, config_dict: Dict[str, Any]) -> None:
        """
        Update multiple configuration values.

        Args:
            config_dict: Dictionary of configuration key-value pairs
        """
        self._config.update(config_dict)

    def reset(self) -> None:
        """Reset configuration to default values."""
        self._config = self._defaults.copy()

    def get_model_path(self, model_type: str, model_name: str) -> Path:
        """
        Get path to a specific model.

        Args:
            model_type: Type of model (e.g., 'stt', 'tts')
            model_name: Name of model (e.g., 'whisper', 'vits')

        Returns:
            Path to model directory
        """
        models_dir = Path(self._config["models_dir"])
        return models_dir / model_type / model_name

    def get_device(self) -> str:
        """
        Get the computation device to use.

        Returns:
            Device string ('cpu', 'cuda:0', etc.)
        """
        device = self._config["device"]

        # If auto, determine best device
        if device == "auto":
            try:
                import torch
                if torch.cuda.is_available():
                    return "cuda:0"
                else:
                    return "cpu"
            except ImportError:
                return "cpu"

        return device

    @property
    def as_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary."""
        return self._config.copy()


# Global configuration instance
_config_instance = None

def get_config() -> Config:
    """
    Get the global configuration instance.

    Returns:
        Global Config instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
