"""Shared logging configuration for flux_config packages.

This module provides a centralized logging configuration function.
Each application (daemon, TUI, CLI) should call configure_logging() at startup.

Best practice: Libraries should NOT configure handlers, only applications should.
See: https://docs.python-guide.org/writing/logging/
"""

from __future__ import annotations

import logging
import os
import sys
from logging.config import dictConfig
from pathlib import Path

# Track if logging has been configured to avoid duplicate setup
_configured = False


def configure_logging(
    app_name: str,
    *,
    use_textual: bool = False,
    log_level: int = logging.INFO,
) -> None:
    """Configure logging for an application.

    This should be called once at application startup. Each app gets its own
    log directory and file: /var/log/{app_name}/{app_name}.log

    Args:
        app_name: Application name for log file (e.g., "flux-configd", "flux-config-tui")
        use_textual: Use TextualHandler for console output (for TUI apps)
        log_level: Logging level (default: INFO)
    """
    global _configured  # noqa: PLW0603

    if _configured:
        logging.getLogger(__name__).warning(
            f"Logging already configured, ignoring configure_logging({app_name})"
        )
        return

    # Determine if we can write to log directory
    log_file = None
    try:
        log_dir = Path(f"/var/log/{app_name}")
        if not log_dir.exists():
            log_dir.mkdir(parents=True, exist_ok=True)
        if os.access(log_dir, os.W_OK):
            log_file = log_dir / f"{app_name}.log"
    except (PermissionError, OSError):
        pass

    # Build handlers
    handlers: dict = {}

    # Console handler - TextualHandler for TUI, StreamHandler for others
    if use_textual:
        handlers["console"] = {
            "level": "INFO",
            "formatter": "standard",
            "class": "textual.logging.TextualHandler",
        }
    elif sys.stdout.isatty():
        # Only add console handler if running interactively
        handlers["console"] = {
            "level": "INFO",
            "formatter": "standard",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        }

    # File handler (if we can write)
    if log_file:
        handlers["file"] = {
            "level": "DEBUG",  # File gets all logs
            "formatter": "detailed",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(log_file),
            "mode": "a",
            "maxBytes": 50 * 1024 * 1024,  # 50MB
            "backupCount": 5,
            "encoding": "utf-8",
        }

    # Determine which handlers to use for loggers
    logger_handlers = list(handlers.keys())

    # Build the config
    config = {
        "version": 1,
        "disable_existing_loggers": False,  # Important: don't break existing loggers
        "formatters": {
            "standard": {
                "format": "{asctime} [{levelname}] {name}: {message}",
                "datefmt": "%H:%M:%S",
                "style": "{",
            },
            "detailed": {
                "format": "{asctime} [{levelname}] {name}:{lineno} - {message}",
                "datefmt": "%Y-%m-%d %H:%M:%S",
                "style": "{",
            },
        },
        "handlers": handlers,
        "root": {
            "handlers": logger_handlers,
            "level": log_level,
        },
    }

    # Apply configuration
    dictConfig(config)

    # Suppress noisy library logs
    logging.getLogger("websockets").setLevel(logging.WARNING)
    logging.getLogger("websockets.server").setLevel(logging.WARNING)
    logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)

    _configured = True
