"""Styles."""

from __future__ import annotations

import logging
from dataclasses import dataclass


@dataclass
class Colors:
    """Based on Tokyo Night: https://github.com/folke/tokyonight.nvim#-extras."""

    level_error: str = '#e77d8f'
    level_warn: str = '#d8b172'
    level_info: str = '#a8cd76'
    level_debug: str = '#82a1f1'
    level_fallback: str = '#b69bf1'


@dataclass
class Styles:
    """Inspired by `loguru` and `structlog` and used in `tail-jsonl`.

    https://rich.readthedocs.io/en/latest/style.html

    Inspired by: https://github.com/Delgan/loguru/blob/07f94f3c8373733119f85aa8b9ca05ace3325a4b/loguru/_defaults.py#L31-L73

    And: https://github.com/hynek/structlog/blob/bcfc7f9e60640c150bffbdaeed6328e582f93d1e/src/structlog/dev.py#L126-L141

    """

    timestamp: str = '#8DAAA1'
    message: str = 'bold'

    colors: Colors | None = None

    # triadic from: https://coolors.co/a28eab
    key: str = '#8DAAA1'
    value: str = '#A28EAB'
    value_own_line: str = '#AAA18D'

    @classmethod
    def from_dict(cls, data: dict) -> Styles:  # type: ignore[type-arg]
        """Return Self instance."""
        if colors := (data.pop('colors', None) or None):
            colors = Colors(**colors)
        return cls(**data, colors=colors)

    def get_style(self, *, level: int) -> str:
        """Return the right style for the specified level."""
        if not self.colors:
            self.colors = Colors()
        return {
            logging.CRITICAL: self.colors.level_error,
            logging.ERROR: self.colors.level_error,
            logging.WARNING: self.colors.level_warn,
            logging.INFO: self.colors.level_info,
            logging.DEBUG: self.colors.level_debug,
        }.get(level, self.colors.level_fallback)


def get_level(*, name: str) -> int:
    """Return the logging level based on the provided name."""
    return {
        'ERROR': logging.ERROR,
        'WARNING': logging.WARNING,
        'WARN': logging.WARNING,
        'INFO': logging.INFO,
        'DEBUG': logging.DEBUG,
    }.get(name.upper(), logging.NOTSET)


def get_name(*, level: int) -> str:
    """Return the logging name based on the provided level.

    https://docs.python.org/3.11/library/logging.html#logging-levels

    """
    return {
        logging.CRITICAL: 'EXCEPTION',
        logging.ERROR: 'ERROR',
        logging.WARNING: 'WARNING',
        logging.INFO: 'INFO',
        logging.DEBUG: 'DEBUG',
        logging.NOTSET: 'NOTSET',
    }.get(level, '')


STYLES = Styles()
