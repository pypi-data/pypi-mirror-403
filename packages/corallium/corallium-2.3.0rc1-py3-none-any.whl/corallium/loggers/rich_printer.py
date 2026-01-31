"""Rich Printer."""

from __future__ import annotations

import logging
import shutil
from datetime import datetime
from typing import Any

from rich.console import Console
from rich.text import Text

from .styles import Styles, get_name


def rich_printer(
    message: str,
    *,
    is_header: bool,
    _this_level: int,
    _is_text: bool,
    # Logger-specific parameters that need to be initialized with partial(...)
    _console: Console,
    _styles: Styles,
    _keys_on_own_line: list[str] | None = None,
    **kwargs: Any,
) -> None:
    """Print log message with rich formatting."""
    text = Text()
    if _is_text:
        if is_header:
            print()  # noqa: T201
        text.append(f'{message}', style=_styles.message)
    else:
        timestamp = kwargs.pop('timestamp', datetime.now())  # noqa: DTZ005
        text.append(f'{timestamp: <28} ', style=_styles.timestamp)
        text.append('[', style=_styles.timestamp)
        level_style = _styles.get_style(level=_this_level)
        text.append(f'{get_name(level=_this_level): <7}', style=level_style)
        text.append(']', style=_styles.timestamp)
        text.append(f' {message}', style=_styles.message)

    full_lines = []
    for key in _keys_on_own_line or []:
        if line := kwargs.pop(key, None):
            full_lines.append((key, line))  # noqa: PERF401
    for key, value in kwargs.items():
        text.append(f' {key}=', style=_styles.key)
        text.append(f'{value!s}', style=_styles.value)
    _console.print(text)
    for key, line in full_lines:
        new_text = Text()
        new_text.append(f' ∟ {key}', style=_styles.key)
        new_text.append(f': {line}', style=_styles.value_own_line)
        _console.print(new_text)

    if _this_level == logging.CRITICAL:
        term_width, _height = shutil.get_terminal_size((100, 50))
        _console.print_exception(
            extra_lines=1,
            max_frames=6,
            show_locals=False,
            width=term_width,
        )
        # > or 'from rich.traceback import install; install(show_locals=True)'
