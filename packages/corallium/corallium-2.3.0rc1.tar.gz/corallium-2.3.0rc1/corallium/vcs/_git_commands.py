"""Thin git shell command wrappers."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from subprocess import CalledProcessError

from beartype.typing import List

from corallium.shell import capture_shell


def zsplit(stdout: str) -> list[str]:
    """Split output from git when used with `-z`.

    Args:
        stdout: Output from git command with null-byte separators

    Returns:
        List of non-empty strings split on null bytes

    """
    return [item for item in stdout.split('\0') if item]


def git_ls_files(*, cwd: Path) -> List[str] | None:
    """Run `git ls-files -z` and return the file list, or None on failure."""
    with suppress(CalledProcessError):
        return zsplit(capture_shell('git ls-files -z', cwd=cwd))
    return None


def git_blame_porcelain(*, file_path: Path, line: int, cwd: Path) -> str | None:
    """Run `git blame --porcelain` for a single line, or None on failure."""
    with suppress(CalledProcessError):
        return capture_shell(f'git blame {file_path} -L {line},{line} --porcelain', cwd=cwd)
    return None


def git_show_toplevel(*, cwd: Path) -> Path | None:
    """Run `git rev-parse --show-toplevel`, or None on failure."""
    with suppress(CalledProcessError):
        return Path(capture_shell('git rev-parse --show-toplevel', cwd=cwd).strip())
    return None
