"""Generic Log Writer."""

from __future__ import annotations

from typing import Any


def plain_printer(
    message: str,
    *,
    is_header: bool,  # noqa: ARG001
    _this_level: int,
    _is_text: bool,
    # Logger-specific parameters that need to be initialized with partial(...)
    **kwargs: Any,
) -> None:
    """Print log message."""
    values = ' '.join([f'{key}={value}' for key, value in kwargs.items()])
    print(f'{message} {values}'.strip())  # noqa: T201
