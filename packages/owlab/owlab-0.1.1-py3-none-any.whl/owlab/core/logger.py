"""Logging utilities for OwLab."""

from pathlib import Path
import sys
from typing import Any, Optional

from loguru import logger

# Plain format (no color) - for non-TTY or when color is disabled
LOG_FORMAT_PLAIN = (
    "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}"
)
# Colored format for console only
LOG_FORMAT_COLOR = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

_logger_configured = False
_logger_level = "INFO"  # Level used for console (so file handler can match)


def get_logger(
    name: Optional[str] = None,
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None,
) -> Any:
    """Get a configured logger instance.

    Configures the global loguru logger only on first call, so that
    handlers added later (e.g. per-experiment owlab.log) are not removed.
    Console uses colored format; log files use plain format (no ANSI codes).

    Args:
        name: Logger name (optional)
        level: Logging level (default: INFO)
        log_file: Path to log file (optional)
        format_string: Custom format string (optional)

    Returns:
        Configured logger instance
    """
    global _logger_configured, _logger_level
    if _logger_configured:
        return logger

    logger.remove()
    _logger_level = level
    console_fmt = format_string if format_string is not None else LOG_FORMAT_COLOR
    logger.add(
        sys.stderr,
        format=console_fmt,
        level=level,
        colorize=True,
    )
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_fmt = LOG_FORMAT_PLAIN if format_string is None else format_string
        logger.add(
            log_file,
            format=file_fmt,
            level=level,
            colorize=False,
            rotation="10 MB",
            retention="7 days",
            compression="zip",
            encoding="utf-8",
        )
    _logger_configured = True
    return logger


def get_logger_level() -> str:
    """Return the level used for the console handler (so file handler can match)."""
    return _logger_level


def reset_logger_config() -> None:
    """Reset logger configuration (for testing). Clears all handlers and allows get_logger to reconfigure."""
    global _logger_configured
    logger.remove()
    _logger_configured = False


# Default logger instance
default_logger = get_logger("owlab")
