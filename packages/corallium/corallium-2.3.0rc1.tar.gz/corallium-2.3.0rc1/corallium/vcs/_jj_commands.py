"""Thin jj (Jujutsu) shell command wrappers."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from subprocess import CalledProcessError

from beartype.typing import List

from corallium.shell import capture_shell


def jj_file_list(*, cwd: Path) -> List[str] | None:
    """Run `jj file list` and return the file list, or None on failure."""
    with suppress(CalledProcessError):
        stdout = capture_shell('jj file list', cwd=cwd)
        return [item for item in stdout.splitlines() if item]
    return None


def jj_file_annotate(*, file_path: Path, line: int, cwd: Path) -> str | None:  # noqa: ARG001
    """Run `jj file annotate` for a file, or None on failure.

    Note: jj file annotate has no line-range option. The full file output
    is returned; the `line` parameter is reserved for future use.

    """
    with suppress(CalledProcessError):
        return capture_shell(f'jj file annotate {file_path}', cwd=cwd)
    return None


def jj_root(*, cwd: Path) -> Path | None:
    """Run `jj root`, or None on failure."""
    with suppress(CalledProcessError):
        return Path(capture_shell('jj root', cwd=cwd).strip())
    return None


def jj_git_remote_list(*, cwd: Path) -> str | None:
    """Run `jj git remote list`, or None on failure."""
    with suppress(CalledProcessError):
        return capture_shell('jj git remote list', cwd=cwd)
    return None
