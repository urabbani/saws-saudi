"""
SAWS Logging Configuration

Structured logging with context support.
"""

import logging
import sys
from pathlib import Path
from typing import Literal

import structlog
from structlog.types import EventDict, Processor


def setup_logging(file: Path | None = None) -> None:
    """
    Setup standard logging for third-party libraries.

    Args:
        file: Optional log file path
    """
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]

    if file:
        file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(file))

    logging.basicConfig(
        format="%(message)s",
        handlers=handlers,
        level=logging.INFO,
    )


def add_app_context(logger: logging.Logger, method_name: str, event_dict: EventDict) -> EventDict:
    """
    Add application context to log entries.

    Args:
        logger: Logger instance
        method_name: Method being called
        event_dict: Event dictionary

    Returns:
        Enhanced event dictionary
    """
    # Add timestamp if not present
    if "timestamp" not in event_dict:
        import datetime

        event_dict["timestamp"] = datetime.datetime.utcnow().isoformat()

    # Add app name
    from app.config import get_settings

    settings = get_settings()
    event_dict["app"] = settings.app_name
    event_dict["environment"] = settings.environment

    return event_dict


def configure_logging(
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO",
    format: Literal["json", "text"] = "json",
    log_file: Path | None = None,
) -> None:
    """
    Configure structured logging for the application.

    Args:
        level: Logging level
        format: Log format (json or text)
        log_file: Optional log file path
    """
    # Setup standard logging
    setup_logging(log_file)

    # Configure processors
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        add_app_context,
    ]

    # Add format-specific processor
    if format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured bound logger
    """
    return structlog.get_logger(name)
