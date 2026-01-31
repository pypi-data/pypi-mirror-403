"""Unified logging setup for Cindergrace applications.

Provides consistent logging configuration with:
- Colorized console output (optional)
- File logging support
- Configurable log levels per module
- Clean, readable format
"""

import logging
import sys
from pathlib import Path
from typing import TextIO

# ANSI color codes for terminal output
_COLORS = {
    "DEBUG": "\033[36m",     # Cyan
    "INFO": "\033[32m",      # Green
    "WARNING": "\033[33m",   # Yellow
    "ERROR": "\033[31m",     # Red
    "CRITICAL": "\033[35m",  # Magenta
    "RESET": "\033[0m",
}


class ColoredFormatter(logging.Formatter):
    """Formatter that adds color codes to log level names."""

    def __init__(self, fmt: str | None = None, datefmt: str | None = None):
        super().__init__(fmt, datefmt)
        self._use_color = sys.stderr.isatty()

    def format(self, record: logging.LogRecord) -> str:
        if self._use_color:
            color = _COLORS.get(record.levelname, "")
            reset = _COLORS["RESET"]
            record.levelname = f"{color}{record.levelname}{reset}"
        return super().format(record)


def setup_logging(
    app_name: str,
    level: int | str = logging.INFO,
    log_file: Path | str | None = None,
    colored: bool = True,
    format_string: str | None = None,
    date_format: str = "%Y-%m-%d %H:%M:%S",
    stream: TextIO | None = None,
    module_levels: dict[str, int | str] | None = None,
) -> logging.Logger:
    """Configure logging for a Cindergrace application.

    Args:
        app_name: Name of the application (used as logger name)
        level: Default log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        colored: Enable colored console output (default: True)
        format_string: Custom format string (default: includes timestamp, level, name)
        date_format: Date format for timestamps
        stream: Output stream for console handler (default: stderr)
        module_levels: Dict of module names to their specific log levels
            Example: {"urllib3": logging.WARNING, "gradio": logging.ERROR}

    Returns:
        Configured logger instance

    Usage:
        logger = setup_logging("cindergrace_sysmon", level=logging.DEBUG)
        logger.info("Application started")

        # With file logging and module-specific levels
        logger = setup_logging(
            "cindergrace_netman",
            log_file="~/.local/share/cindergrace_netman/app.log",
            module_levels={"urllib3": logging.WARNING}
        )
    """
    # Resolve log level if string
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)

    # Default format
    if format_string is None:
        format_string = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    # Get or create logger
    logger = logging.getLogger(app_name)
    logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(stream or sys.stderr)
    console_handler.setLevel(level)

    if colored:
        console_formatter = ColoredFormatter(format_string, date_format)
    else:
        console_formatter = logging.Formatter(format_string, date_format)

    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_path = Path(log_file).expanduser()
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(format_string, date_format)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    # Set module-specific log levels
    if module_levels:
        for module_name, module_level in module_levels.items():
            if isinstance(module_level, str):
                module_level = getattr(logging, module_level.upper(), logging.INFO)
            logging.getLogger(module_name).setLevel(module_level)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a child logger for a specific module.

    Use this in sub-modules to get a logger that inherits
    the configuration from the app's main logger.

    Args:
        name: Module name (typically __name__)

    Returns:
        Logger instance

    Usage:
        # In providers.py
        from cgc_common import get_logger
        logger = get_logger(__name__)
    """
    return logging.getLogger(name)


def set_level(logger_name: str, level: int | str) -> None:
    """Change log level for a specific logger at runtime.

    Args:
        logger_name: Name of the logger to modify
        level: New log level

    Usage:
        set_level("cindergrace_sysmon", logging.DEBUG)
        set_level("urllib3", "WARNING")
    """
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    logging.getLogger(logger_name).setLevel(level)
