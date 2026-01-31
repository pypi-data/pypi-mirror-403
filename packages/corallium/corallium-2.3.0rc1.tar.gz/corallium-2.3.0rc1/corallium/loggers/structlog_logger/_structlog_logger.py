"""Structlog Logger."""

from __future__ import annotations

import logging
from typing import Any

import structlog


def structlog_logger(
    message: str,
    *,
    is_header: bool,
    _this_level: int,
    _is_text: bool,
    # Logger-specific parameters that need to be initialized with partial(...)
    **kwargs: Any,
) -> None:
    logger = structlog.get_logger()
    log = {
        logging.CRITICAL: logger.exception,
        logging.ERROR: logger.error,
        logging.WARNING: logger.warning,
        logging.INFO: logger.info,
        logging.DEBUG: logger.debug,
        logging.NOTSET: logger.debug,
    }.get(_this_level, logger.msg)
    log(message, is_header=is_header, _this_level=_this_level, _is_text=_is_text, **kwargs)
