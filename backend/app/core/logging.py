"""Logging setup.

Provides a single, consistent log format across the API, the Celery worker
and the CLI scripts.  Secrets are never logged.
"""

from __future__ import annotations

import logging
import sys

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured = False


def configure_logging(level: str = "INFO") -> None:
    """Install a stdout handler on the root logger (idempotent)."""
    global _configured
    root = logging.getLogger()
    root.setLevel(level.upper())

    if _configured and root.handlers:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))

    root.handlers = [handler]
    # uvicorn's access log is noisy for an API demo
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("celery.worker").setLevel(logging.INFO)
    # per-request transport traces (ES/AMQP) are debug level only
    logging.getLogger("elastic_transport").setLevel(logging.WARNING)
    logging.getLogger("kombu").setLevel(logging.WARNING)
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger."""
    return logging.getLogger(name)
