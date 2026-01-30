"""
Utility functions for fmus-vox.

This module contains various utility functions used throughout the library.
"""

import logging
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union, TypeVar, Generic

from fmus_vox.core.errors import FmusVoxError

# Type variable for generic functions
T = TypeVar('T')

def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Get a logger with the given name and level.

    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    # Get level from config if not provided
    if level is None:
        from fmus_vox.core.config import get_config
        level = get_config().get("log_level", "INFO")

    # Create logger
    logger = logging.getLogger(name)

    # Set level
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise FmusVoxError(f"Invalid log level: {level}")
    logger.setLevel(numeric_level)

    # Create handler if not already configured
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger

def timed(func: Callable) -> Callable:
    """
    Decorator to time function execution.

    Args:
        func: Function to time

    Returns:
        Wrapped function that logs execution time
    """
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logger.debug(f"{func.__name__} executed in {end_time - start_time:.2f}s")
        return result
    return wrapper

def ensure_path_exists(path: Union[str, Path]) -> Path:
    """
    Ensure that a directory path exists, creating it if necessary.

    Args:
        path: Directory path

    Returns:
        Path object for the directory
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj

def download_file(url: str, dest_path: Union[str, Path],
                 progress: bool = True) -> Path:
    """
    Download a file from a URL to a destination path.

    Args:
        url: URL to download from
        dest_path: Path to save the file to
        progress: Whether to show progress bar

    Returns:
        Path to the downloaded file

    Raises:
        FmusVoxError: If download fails
    """
    try:
        import requests
        from tqdm import tqdm

        # Create directory if it doesn't exist
        dest_path = Path(dest_path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Download file
        response = requests.get(url, stream=True)
        response.raise_for_status()

        # Get file size for progress bar
        total_size = int(response.headers.get('content-length', 0))

        # Write to file
        with open(dest_path, 'wb') as f:
            if progress and total_size > 0:
                with tqdm(total=total_size, unit='B', unit_scale=True,
                          desc=f"Downloading {dest_path.name}") as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
            else:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

        return dest_path

    except Exception as e:
        raise FmusVoxError(f"Failed to download file: {str(e)}")

class LazyLoader(Generic[T]):
    """
    Lazy loader for objects that are expensive to initialize.

    Initializes the object only when it's first accessed.
    """

    def __init__(self, init_func: Callable[[], T]):
        """
        Initialize the lazy loader.

        Args:
            init_func: Function that initializes the object
        """
        self._init_func = init_func
        self._instance = None

    def get(self) -> T:
        """
        Get the object, initializing it if necessary.

        Returns:
            The initialized object
        """
        if self._instance is None:
            self._instance = self._init_func()
        return self._instance

    def reset(self) -> None:
        """Reset the object, forcing re-initialization on next get()."""
        self._instance = None

def format_timestamp(seconds: float) -> str:
    """
    Format seconds as a timestamp (MM:SS.mmm).

    Args:
        seconds: Time in seconds

    Returns:
        Formatted timestamp
    """
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    return f"{minutes:02d}:{remaining_seconds:06.3f}"
