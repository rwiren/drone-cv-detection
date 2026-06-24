"""Structured logging helpers for drone-cv pipelines.

Usage::

    from logging_utils import get_logger
    log = get_logger(__name__)
    log.info("Loaded model: %s", path)
    log.warning("Skipping frame %d — read failed", frame_idx)

Runtime controls (environment variables):

``LOG_LEVEL``
    Verbosity: ``DEBUG``, ``INFO`` (default), ``WARNING``, ``ERROR``.

``LOG_FORMAT``
    Output format:

    * ``text`` (default) — human-readable ``LEVEL  logger  message``
    * ``json`` — one JSON object per line, useful for log aggregators
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime, timezone


class _JsonFormatter(logging.Formatter):
    """Emit each log record as a single JSON line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def get_logger(name: str, level: int | None = None) -> logging.Logger:
    """Return a configured logger for the drone-cv package.

    Calling this multiple times with the same *name* returns the same cached
    logger without adding duplicate handlers.

    Args:
        name: Logger name — use ``__name__`` in production code.
        level: Override log level (``logging.DEBUG`` etc.).  When *None* the
               ``LOG_LEVEL`` environment variable is consulted, falling back to
               ``INFO``.

    Returns:
        A :class:`logging.Logger` with one :class:`~logging.StreamHandler`
        writing to *stderr*.
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        # Already configured — return cached logger to avoid duplicate output.
        return logger

    if level is None:
        env_level = os.environ.get("LOG_LEVEL", "INFO").upper()
        level = getattr(logging, env_level, logging.INFO)

    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)

    if os.environ.get("LOG_FORMAT", "").lower() == "json":
        handler.setFormatter(_JsonFormatter())
    else:
        fmt = "%(levelname)-8s %(name)s  %(message)s"
        handler.setFormatter(logging.Formatter(fmt))

    logger.addHandler(handler)
    logger.propagate = False
    return logger
