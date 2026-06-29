"""
Structured logging configuration for the FastAPI backend.

Supports two output formats:
  - "json": Machine-readable JSON lines (production)
  - "text": Human-readable colored output (development)
"""
import logging
import logging.config
import sys
from typing import Literal


def setup_logging(
    level: str = "INFO",
    fmt: Literal["json", "text"] = "json",
) -> None:
    """
    Configures the root logger and all 'backend.*' loggers.

    Called once during app startup (lifespan).
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    if fmt == "json":
        formatter_class = "logging.Formatter"
        format_str = (
            '{"time":"%(asctime)s","level":"%(levelname)s",'
            '"logger":"%(name)s","message":"%(message)s"}'
        )
    else:
        formatter_class = "logging.Formatter"
        format_str = "[%(asctime)s] %(levelname)-8s %(name)-25s │ %(message)s"

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "class": formatter_class,
                "format": format_str,
                "datefmt": "%Y-%m-%dT%H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "backend": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False,
            },
        },
        "root": {
            "level": log_level,
            "handlers": ["console"],
        },
    }

    logging.config.dictConfig(config)
