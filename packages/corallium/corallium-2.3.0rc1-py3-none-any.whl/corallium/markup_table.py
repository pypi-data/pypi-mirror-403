"""Markup table formatting."""

from __future__ import annotations

from collections.abc import Iterable
from itertools import starmap
from typing import Any


def format_table(
    headers: list[str],
    records: list[dict[str, Any]],
    delimiters: list[str] | None = None,
) -> str:
    """Returns a formatted table.

    Args:
        headers: ordered keys to use as column title
        records: list of key:row-value dictionaries
        delimiters: optional list to allow for alignment (e.g., [':-', '-:', ':-:'])
            Valid delimiters: '-' (default), ':-' (left), '-:' (right), ':-:' (center)

    Returns:
        Formatted table with headers, separators, and data rows

    Raises:
        ValueError: if delimiters count doesn't match headers or uses invalid values

    Example:
        >>> headers = ['Name', 'Age', 'Score']
        >>> records = [
        ...     {'Name': 'Alice', 'Age': 30, 'Score': 95},
        ...     {'Name': 'Bob', 'Age': 25, 'Score': 88}
        ... ]
        >>> print(format_table(headers, records))
        | Name  | Age | Score |
        |-------|-----|-------|
        | Alice | 30  | 95    |
        | Bob   | 25  | 88    |

    """
    table = [[str(r_[col]) for col in headers] for r_ in records]
    widths = [max(len(row[col_idx].strip()) for row in [headers, *table]) for col_idx in range(len(headers))]

    def pad(values: list[str]) -> list[str]:
        return [val.strip().ljust(widths[col_idx]) for col_idx, val in enumerate(values)]

    def join(row: Iterable[str], spacer: str = ' ') -> str:
        return f'|{spacer}' + f'{spacer}|{spacer}'.join(row) + f'{spacer}|'

    def expand_delimiters(delim: str, width: int) -> str:
        expanded = '-' * (width + 2)
        if delim.startswith(':'):
            expanded = ':' + expanded[1:]
        if delim.endswith(':'):
            expanded = expanded[:-1] + ':'
        return expanded

    if delimiters:
        errors = []
        if len(delimiters) != len(headers):
            errors.append(f'Incorrect number of delimiters provided ({len(delimiters)}). Expected: ({len(headers)})')
        allowed_delimiters = {'-', ':-', '-:', ':-:'}
        if not all(delim in allowed_delimiters for delim in delimiters):
            errors.append(f'Delimiters must be one of {allowed_delimiters}. Received: {delimiters}')
        if errors:
            raise ValueError(' and '.join(errors))

    delimiter_values = delimiters or ['-'] * len(headers)
    expanded_delimiters = list(starmap(expand_delimiters, zip(delimiter_values, widths, strict=True)))
    lines = [
        join(pad(headers)),
        join(expanded_delimiters, ''),
        *[join(pad(row)) for row in table],
    ]
    return '\n'.join(lines)
