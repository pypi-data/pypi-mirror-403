"""Centralized logging configuration for DataSkipper Boat.

This module provides:
- Environment variable support for log level configuration
- File handler with log rotation for production deployments
- Consistent log formatting across all modules
- Module-specific log level overrides for verbose modules
"""

import logging
import os
import sys
from datetime import datetime, timezone, timedelta
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Dict

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

# Default configuration
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %I:%M:%S %p"
DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
DEFAULT_BACKUP_COUNT = 5

# Verbose modules that should default to WARNING unless DEBUG is set
VERBOSE_MODULES = [
    "pymodbus",
    "asyncio",
    "urllib3",
    "aiohttp",
    "httpx",
]


def get_log_level_from_env() -> int:
    """Get log level from environment variable.

    Supports: DEBUG, INFO, WARNING, ERROR, CRITICAL
    Default: INFO
    """
    level_str = os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL).upper()
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "WARN": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return level_map.get(level_str, logging.INFO)


def get_log_file_path() -> Optional[Path]:
    """Get log file path from environment variable.

    If LOG_FILE is set, logs will be written to that file.
    If LOG_DIR is set, logs will be written to LOG_DIR/dataskipper.log
    Otherwise, no file logging is used (console only).
    """
    log_file = os.getenv("LOG_FILE")
    if log_file:
        return Path(log_file)

    log_dir = os.getenv("LOG_DIR")
    if log_dir:
        return Path(log_dir) / "dataskipper.log"

    return None


class ISTFormatter(logging.Formatter):
    """Custom formatter that outputs timestamps in IST (Indian Standard Time)."""

    def formatTime(self, record, datefmt=None):
        # Convert the timestamp to IST
        ct = datetime.fromtimestamp(record.created, tz=IST)
        if datefmt:
            return ct.strftime(datefmt)
        return ct.strftime(DEFAULT_DATE_FORMAT)


def create_formatter(detailed: bool = False) -> logging.Formatter:
    """Create a log formatter with IST timezone.

    Args:
        detailed: If True, include more details (module, function, line number)
    """
    if detailed:
        fmt = "%(asctime)s - %(name)s - %(levelname)s - [%(module)s:%(funcName)s:%(lineno)d] - %(message)s"
    else:
        fmt = DEFAULT_LOG_FORMAT

    return ISTFormatter(fmt, datefmt=DEFAULT_DATE_FORMAT)


def setup_logging(
    level: Optional[int] = None,
    log_file: Optional[str] = None,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT,
    module_levels: Optional[Dict[str, int]] = None,
) -> logging.Logger:
    """Configure logging for the application.

    Args:
        level: Log level (default: from LOG_LEVEL env var or INFO)
        log_file: Path to log file (default: from LOG_FILE/LOG_DIR env var)
        max_bytes: Max size per log file for rotation (default: 10MB)
        backup_count: Number of backup files to keep (default: 5)
        module_levels: Dict of module name -> log level for specific modules

    Returns:
        The root logger configured for the application

    Environment Variables:
        LOG_LEVEL: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
        LOG_FILE: Full path to log file
        LOG_DIR: Directory for log file (uses dataskipper.log)
        LOG_FORMAT: "simple" or "detailed" (default: simple)
    """
    # Get log level
    if level is None:
        level = get_log_level_from_env()

    # Get log file path
    if log_file is None:
        file_path = get_log_file_path()
    else:
        file_path = Path(log_file)

    # Determine format style
    use_detailed = os.getenv("LOG_FORMAT", "simple").lower() == "detailed"
    formatter = create_formatter(detailed=use_detailed)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Console handler (always enabled)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if path is configured)
    if file_path:
        try:
            # Create directory if it doesn't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = RotatingFileHandler(
                str(file_path),
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            root_logger.info(f"File logging enabled: {file_path}")
        except Exception as e:
            root_logger.warning(f"Failed to setup file logging to {file_path}: {e}")

    # Quiet down verbose third-party modules unless DEBUG is enabled
    if level > logging.DEBUG:
        for module_name in VERBOSE_MODULES:
            logging.getLogger(module_name).setLevel(logging.WARNING)

    # Apply custom module levels
    if module_levels:
        for module_name, module_level in module_levels.items():
            logging.getLogger(module_name).setLevel(module_level)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a module.

    This is a convenience function that returns a properly named logger.
    Use this instead of logging.getLogger(__name__) for consistency.

    Args:
        name: Usually __name__ from the calling module

    Returns:
        A logger configured for the module

    Example:
        from src.utils.logging_config import get_logger
        logger = get_logger(__name__)
        logger.info("Starting service")
    """
    return logging.getLogger(name)


def log_startup_info(logger: logging.Logger, service_name: str, version: str = "1.0.0") -> None:
    """Log standard startup information.

    Args:
        logger: The logger to use
        service_name: Name of the service starting up
        version: Version string
    """
    logger.info("=" * 60)
    logger.info(f"Starting {service_name} v{version}")
    logger.info(f"Log level: {logging.getLevelName(logger.getEffectiveLevel())}")
    logger.info(f"Python version: {sys.version}")
    logger.info("=" * 60)


def log_exception(logger: logging.Logger, msg: str, exc: Exception, include_traceback: bool = True) -> None:
    """Log an exception with consistent formatting.

    Args:
        logger: The logger to use
        msg: Message describing the context
        exc: The exception that occurred
        include_traceback: Whether to include full traceback (default: True)
    """
    if include_traceback:
        logger.error(f"{msg}: {exc}", exc_info=True)
    else:
        logger.error(f"{msg}: {type(exc).__name__}: {exc}")
