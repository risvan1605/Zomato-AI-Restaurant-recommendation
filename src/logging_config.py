"""
Structured logging configuration.

Provides a single ``setup_logging()`` entry-point that configures Python's
logging module with a consistent format, respects the ``LOG_LEVEL`` env var,
and masks sensitive values (e.g. API keys) in startup output.

Call ``setup_logging()`` once at application startup (e.g. in ``streamlit_app.py``
or ``main.py``) before any logger is used.
"""

from __future__ import annotations

import logging
import sys

from src.config import settings


_LOG_FORMAT = "[%(asctime)s] %(name)s %(levelname)s — %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_CONFIGURED = False


def setup_logging() -> None:
    """Configure the root logger and emit a masked startup banner.

    Safe to call multiple times — subsequent calls are no-ops.
    """
    global _CONFIGURED  # noqa: PLW0603
    if _CONFIGURED:
        return

    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=level,
        format=_LOG_FORMAT,
        datefmt=_DATE_FORMAT,
        stream=sys.stderr,
        force=True,
    )

    # Quieten noisy third-party loggers
    logging.getLogger("datasets").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("groq").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info(
        "Logging initialised at %s level. Groq model=%s, key=%s",
        settings.log_level.upper(),
        settings.groq_model,
        _mask_key(settings.groq_api_key),
    )

    _CONFIGURED = True


def _mask_key(key: str) -> str:
    """Mask an API key for safe logging: ``gsk_ab…****``."""
    if not key:
        return "<not set>"
    if len(key) <= 8:
        return key[:2] + "…" + "****"
    return key[:6] + "…" + "****"
