"""
Structured logging for fmus-vox.

This module provides structured logging capabilities for the library,
allowing for consistent logging across all components.
"""

import json
import logging
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from fmus_vox.core.errors import FmusVoxError

class StructuredLogFormatter(logging.Formatter):
    """
    Format logs as structured JSON for easier parsing and analysis.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log string
        """
        # Basic log data
        log_data = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Add exception info if available
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }

        # Add extra attributes if available
        if hasattr(record, "data") and record.data:
            log_data["data"] = record.data

        return json.dumps(log_data)

class JSONLogger(logging.Logger):
    """
    Logger that allows attaching structured data to log messages.
    """

    def _log_with_data(self, level: int, msg: str, data: Dict[str, Any],
                      *args, **kwargs) -> None:
        """
        Log a message with attached structured data.

        Args:
            level: Log level
            msg: Log message
            data: Structured data to attach to the log
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        if self.isEnabledFor(level):
            record = self.makeRecord(
                self.name, level, kwargs.get('filename', ''),
                kwargs.get('lineno', 0), msg, args,
                kwargs.get('exc_info'), kwargs.get('func'),
                kwargs.get('extra')
            )
            record.data = data
            self.handle(record)

    def debug_data(self, msg: str, data: Dict[str, Any], *args, **kwargs) -> None:
        """Log a DEBUG message with structured data."""
        self._log_with_data(logging.DEBUG, msg, data, *args, **kwargs)

    def info_data(self, msg: str, data: Dict[str, Any], *args, **kwargs) -> None:
        """Log an INFO message with structured data."""
        self._log_with_data(logging.INFO, msg, data, *args, **kwargs)

    def warning_data(self, msg: str, data: Dict[str, Any], *args, **kwargs) -> None:
        """Log a WARNING message with structured data."""
        self._log_with_data(logging.WARNING, msg, data, *args, **kwargs)

    def error_data(self, msg: str, data: Dict[str, Any], *args, **kwargs) -> None:
        """Log an ERROR message with structured data."""
        self._log_with_data(logging.ERROR, msg, data, *args, **kwargs)

    def critical_data(self, msg: str, data: Dict[str, Any], *args, **kwargs) -> None:
        """Log a CRITICAL message with structured data."""
        self._log_with_data(logging.CRITICAL, msg, data, *args, **kwargs)

def setup_logging(level: str = "INFO",
                 json_output: bool = False,
                 log_file: Optional[Union[str, Path]] = None) -> None:
    """
    Set up logging configuration for the entire library.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_output: Whether to format logs as JSON
        log_file: Path to log file (if None, logs to stdout only)

    Raises:
        FmusVoxError: If logging setup fails
    """
    try:
        # Register custom logger class
        logging.setLoggerClass(JSONLogger)

        # Get root logger
        root_logger = logging.getLogger()

        # Clear existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Set level
        numeric_level = getattr(logging, level.upper(), None)
        if not isinstance(numeric_level, int):
            raise FmusVoxError(f"Invalid log level: {level}")
        root_logger.setLevel(numeric_level)

        # Create formatter
        if json_output:
            formatter = StructuredLogFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        # Create file handler if specified
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_path)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

    except Exception as e:
        raise FmusVoxError(f"Failed to set up logging: {str(e)}")

def get_logger(name: str) -> JSONLogger:
    """
    Get a JSONLogger with the given name.

    Args:
        name: Logger name

    Returns:
        JSONLogger instance
    """
    return logging.getLogger(name)
