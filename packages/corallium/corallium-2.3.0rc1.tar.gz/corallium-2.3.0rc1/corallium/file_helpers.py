"""File Helpers."""

from __future__ import annotations

import os
import shutil
import string
import time
import webbrowser
from contextlib import suppress
from functools import lru_cache
from pathlib import Path
from typing import Any

from .log import LOGGER
from .tomllib import tomllib
from .vcs import find_repo_root as find_repo_root  # noqa: PLC0414


@lru_cache(maxsize=1)
def get_lock() -> Path:
    """Return path to dependency manager's lock file.

    Supports both uv.lock and poetry.lock files.

    Raises:
        FileNotFoundError: if a lock file can't be located

    """
    for name in ('uv.lock', 'poetry.lock'):
        with suppress(FileNotFoundError):
            return find_in_parents(name=name)
    raise FileNotFoundError('Could not locate a known lock file type (uv.lock or poetry.lock)')


LOCK = Path('poetry.lock')
"""[DEPRECATED] Use get_lock() instead. This constant assumes poetry.lock and doesn't support uv.lock."""

PROJECT_TOML = Path('pyproject.toml')
"""pyproject.toml Path."""

COPIER_ANSWERS = Path('.copier-answers.yml')
"""Copier Answer file name."""

MKDOCS_CONFIG = Path('mkdocs.yml')
"""mkdocs.yml Path."""

# ----------------------------------------------------------------------------------------------------------------------
# Read General Text Files


def read_lines(path_file: Path, encoding: str | None = 'utf-8', errors: str | None = None) -> list[str]:
    """Read a file and split on newlines for later parsing.

    Args:
        path_file: path to the file
        encoding: defaults to 'utf-8'
        errors: defaults to None. Use 'ignore' if needed. Full documentation: https://docs.python.org/3.12/library/functions.html#open

    Returns:
        List[str]: lines of text as list

    """
    return path_file.read_text(encoding=encoding, errors=errors).splitlines() if path_file.is_file() else []


def tail_lines(path_file: Path, *, count: int) -> list[str]:
    """Tail a file for up to the last count (or full file) lines.

    Optimized to read in chunks instead of byte-by-byte for better performance.

    Args:
        path_file: path to the file
        count: maximum number of lines to return

    Returns:
        List[str]: lines of text as list

    """
    max_chunk_size = 8192  # 8KB chunks for efficient disk I/O
    with path_file.open('rb') as f_h:
        file_size = f_h.seek(0, os.SEEK_END)
        if file_size == 0:
            return []

        buffer = b''
        remaining_bytes = file_size

        while remaining_bytes > 0:
            chunk_size = min(max_chunk_size, remaining_bytes)
            f_h.seek(remaining_bytes - chunk_size, os.SEEK_SET)
            chunk = f_h.read(chunk_size)
            buffer = chunk + buffer
            remaining_bytes -= chunk_size

            # Count newlines in buffer to see if we have enough lines
            lines_found = buffer.count(b'\n')
            if lines_found >= count:
                break

        # Decode and split into lines
        decoded = buffer.decode('utf-8', errors='replace')
        all_lines = [line.rstrip('\r') for line in decoded.split('\n')]

        # Return last 'count' lines (matching original behavior)
        # Note: split on '\n' creates an extra empty string if text ends with '\n'
        return all_lines[-count:]


# ----------------------------------------------------------------------------------------------------------------------
# Read Specific File Types


def find_in_parents(*, name: str, cwd: Path | None = None) -> Path:
    """Return path to specific file by recursively searching in cwd and parents.

    Raises:
        FileNotFoundError: if not found

    """
    msg = f'Could not locate {name} in {cwd} or in any parent directory'
    start_path = (cwd or Path()).resolve() / name
    try:
        while not start_path.is_file():
            start_path = start_path.parents[1] / name
    except IndexError:
        raise FileNotFoundError(msg) from None
    return start_path


def _parse_mise_lock(lock_path: Path) -> dict[str, list[str]]:
    content = lock_path.read_bytes()
    data = tomllib.loads(content.decode('utf-8'))

    versions: dict[str, list[str]] = {}
    if 'tools' in data:
        for tool, tool_data in data['tools'].items():
            if isinstance(tool_data, dict) and 'version' in tool_data:
                version = tool_data['version']
                if version:
                    versions.setdefault(tool, []).append(version)
    return versions


def _parse_mise_toml(mise_path: Path) -> dict[str, list[str]]:
    content = mise_path.read_bytes()
    data = tomllib.loads(content.decode('utf-8'))

    versions: dict[str, list[str]] = {}
    if 'tools' in data:
        for tool, version in data['tools'].items():
            if isinstance(version, str):
                versions.setdefault(tool, []).append(version)
            elif isinstance(version, list):
                versions.setdefault(tool, []).extend(version)
    return versions


def _parse_tool_versions(tv_path: Path) -> dict[str, list[str]]:
    """Parse .tool-versions file handling multiple spaces/tabs and comments.

    Returns:
        dict mapping tool names to lists of version strings

    """
    result = {}
    for line in tv_path.read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue  # Skip empty lines and comments
        parts = line.split()
        if parts:
            result[parts[0]] = parts[1:]
    return result


def get_tool_versions(cwd: Path | None = None) -> dict[str, list[str]]:
    """Return versions from mise.lock, mise.toml, or .tool-versions file.

    Priority order: mise.lock, mise.toml, .tool-versions (legacy asdf format).

    """
    with suppress(FileNotFoundError):
        lock_path = find_in_parents(name='mise.lock', cwd=cwd)
        return _parse_mise_lock(lock_path)

    with suppress(FileNotFoundError):
        mise_path = find_in_parents(name='mise.toml', cwd=cwd)
        return _parse_mise_toml(mise_path)

    tv_path = find_in_parents(name='.tool-versions', cwd=cwd)
    return _parse_tool_versions(tv_path)


@lru_cache(maxsize=25)
def read_pyproject(cwd: Path | None = None) -> Any:
    """Return the 'pyproject.toml' file contents.

    Cached with maxsize=128 to support multi-project workflows.

    Raises:
        FileNotFoundError: if not found or cannot be read

    """
    toml_path = find_in_parents(name='pyproject.toml', cwd=cwd)
    try:
        pyproject_txt = toml_path.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError) as exc:
        msg = f'Could not read pyproject.toml at: {toml_path}'
        raise FileNotFoundError(msg) from exc

    try:
        return tomllib.loads(pyproject_txt)
    except tomllib.TOMLDecodeError as exc:
        msg = f'Invalid TOML in pyproject.toml at: {toml_path}'
        raise ValueError(msg) from exc


@lru_cache(maxsize=25)
def read_package_name(cwd: Path | None = None) -> str:
    """Return the package name."""
    pyproject = read_pyproject(cwd=cwd)
    with suppress(KeyError):
        return str(pyproject['project']['name'])  # For uv
    return str(pyproject['tool']['poetry']['name'])


def read_yaml_file(path_yaml: Path) -> Any:
    """Attempt to read the specified yaml file. Returns an empty dictionary if not found or a parser error occurs.

    > Note: suppresses all tags in the YAML file

    Args:
        path_yaml: path to the yaml file

    Returns:
        dictionary representation of the source file

    Raises:
        RuntimeError: when yaml dependency is missing

    """
    try:
        import yaml  # noqa: PLC0415 # lazy-load the optional dependency
    except ImportError as exc:
        raise RuntimeError("The 'calcipy[docs]' extras are missing") from exc

    # Based on: https://github.com/yaml/pyyaml/issues/86#issuecomment-380252434
    # Use safe_load with custom constructors to suppress tags
    yaml.add_multi_constructor('', lambda _loader, _suffix, _node: None, Loader=yaml.SafeLoader)
    yaml.add_multi_constructor('!', lambda _loader, _suffix, _node: None, Loader=yaml.SafeLoader)
    yaml.add_multi_constructor('!!', lambda _loader, _suffix, _node: None, Loader=yaml.SafeLoader)
    try:
        return yaml.safe_load(path_yaml.read_text(encoding='utf-8'))
    except (FileNotFoundError, KeyError) as exc:  # pragma: no cover
        LOGGER.warning('Unexpected read error', path_yaml=path_yaml, error=str(exc))
        return {}
    except yaml.constructor.ConstructorError:
        LOGGER.exception('Warning: burying poorly handled yaml error')
        return {}


# ----------------------------------------------------------------------------------------------------------------------
# General

ALLOWED_CHARS = string.ascii_lowercase + string.ascii_uppercase + string.digits + '-_.'
"""Default string of acceptable characters in a filename."""

# Windows reserved filenames that cannot be used
RESERVED_NAMES = frozenset(
    {
        'CON',
        'PRN',
        'AUX',
        'NUL',
        'COM1',
        'COM2',
        'COM3',
        'COM4',
        'COM5',
        'COM6',
        'COM7',
        'COM8',
        'COM9',
        'LPT1',
        'LPT2',
        'LPT3',
        'LPT4',
        'LPT5',
        'LPT6',
        'LPT7',
        'LPT8',
        'LPT9',
    }
)
"""Windows reserved filenames."""


def sanitize_filename(filename: str, repl_char: str = '_', allowed_chars: str = ALLOWED_CHARS) -> str:
    """Replace all characters not in the `allow_chars` with `repl_char`.

    Handles empty strings, path separators, and Windows reserved names.

    Args:
        filename: string filename (stem and suffix only, not a full path)
        repl_char: replacement character. Default is `_`
        allowed_chars: all allowed characters. Default is `ALLOWED_CHARS`

    Returns:
        str: sanitized filename

    Raises:
        ValueError: if filename is empty or becomes empty after sanitization

    """
    if not filename:
        raise ValueError('Filename cannot be empty')

    # Remove path separators first (prevents directory traversal)
    filename = filename.replace('/', repl_char).replace('\\', repl_char)

    # Replace disallowed characters
    sanitized = ''.join((char if char in allowed_chars else repl_char) for char in filename)

    if not sanitized:
        msg = f'Filename becomes empty after sanitization: {filename!r}'
        raise ValueError(msg)

    return sanitized


def trim_trailing_whitespace(pth: Path) -> None:
    """Trim trailing whitespace from the specified file.

    Preserves the original line ending style (LF or CRLF).
    """
    text = pth.read_text(encoding='utf-8')
    # Detect line ending style
    has_crlf = '\r\n' in text
    line_break = '\r\n' if has_crlf else '\n'

    # Strip trailing spaces from each line
    stripped = [line.rstrip(' ') for line in text.split(line_break)]
    pth.write_text(line_break.join(stripped), encoding='utf-8')


# ----------------------------------------------------------------------------------------------------------------------
# Manage Files and Directories


def if_found_unlink(path_file: Path) -> None:
    """Remove file if it exists. Function is intended to a doit action.

    Args:
        path_file: Path to file to remove

    """
    if path_file.is_file():
        LOGGER.text('Deleting', path_file=path_file)
        path_file.unlink()


def delete_old_files(dir_path: Path, *, ttl_seconds: int) -> None:
    """Delete old files within the specified directory.

    Skips symlinks to avoid deleting files outside the target directory.

    Args:
        dir_path: Path to directory to delete
        ttl_seconds: if last modified within this number of seconds, will not be deleted

    """
    for pth in dir_path.rglob('*'):
        # Skip symlinks to avoid deleting files outside directory
        if pth.is_symlink():
            continue
        if pth.is_file() and (time.time() - pth.stat().st_mtime) > ttl_seconds:
            pth.unlink()


def delete_dir(dir_path: Path) -> None:
    """Delete the specified directory from a doit task.

    Args:
        dir_path: Path to directory to delete

    """
    if dir_path.is_dir():
        LOGGER.text('Deleting', dir_path=dir_path)
        shutil.rmtree(dir_path)


def ensure_dir(dir_path: Path) -> None:
    """Make sure that the specified dir_path exists and create any missing folders from a doit task.

    Args:
        dir_path: Path to directory that needs to exists

    """
    LOGGER.text('Creating', dir_path=dir_path)
    dir_path.mkdir(parents=True, exist_ok=True)


def get_relative(full_path: Path, other_path: Path) -> Path | None:
    """Try to return the relative path between the two paths. None if no match.

    Args:
        full_path: the full path to use
        other_path: the path that the full_path may be relative to

    Returns:
        relative path

    """
    with suppress(ValueError):
        return full_path.relative_to(other_path)
    return None


# ----------------------------------------------------------------------------------------------------------------------
# Open Files


def open_in_browser(path_file: Path) -> None:  # pragma: no cover
    """Open the path in the default web browser.

    Args:
        path_file: Path to file

    """
    webbrowser.open(path_file.resolve().as_uri())
