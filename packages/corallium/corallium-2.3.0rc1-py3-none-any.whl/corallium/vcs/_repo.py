"""Repo root discovery, VCS detection, and metadata resolution."""

from __future__ import annotations

from contextlib import suppress
from functools import lru_cache
from pathlib import Path
from subprocess import CalledProcessError

from corallium.shell import capture_shell

from ._forge import detect_forge, parse_remote_url
from ._git_commands import git_show_toplevel
from ._jj_commands import jj_git_remote_list, jj_root
from ._types import RepoMetadata, VcsKind

_VCS_MARKERS = {
    '.git': VcsKind.GIT,
    '.jj': VcsKind.JUJUTSU,
}


def find_repo_root(start_path: Path | None = None) -> Path | None:
    """Find the repository root by searching for .git or .jj directory.

    Args:
        start_path: Path to start searching from. Defaults to current working directory.

    Returns:
        Path to the repository root, or None if not found

    """
    current = (start_path or Path.cwd()).resolve()
    while current != current.parent:
        if any((current / marker).is_dir() for marker in _VCS_MARKERS):
            return current
        current = current.parent
    return None


def detect_vcs_kind(repo_root: Path) -> VcsKind | None:
    """Detect which VCS is in use at the given repo root."""
    for marker, kind in _VCS_MARKERS.items():
        if (repo_root / marker).is_dir():
            return kind
    return None


def _get_git_remote_url(*, cwd: Path) -> str:
    with suppress(CalledProcessError):
        return capture_shell('git remote get-url origin', cwd=cwd).strip()
    return ''


def _get_git_branch(*, cwd: Path) -> str:
    with suppress(CalledProcessError):
        return capture_shell('git branch --show-current', cwd=cwd).strip()
    return ''


def _get_jj_remote_url(*, cwd: Path) -> str:
    if raw := jj_git_remote_list(cwd=cwd):
        for line in raw.splitlines():
            parts = line.split(maxsplit=1)
            if len(parts) == 2 and parts[0] == 'origin':  # noqa: PLR2004
                return parts[1].strip()
    return ''


def _get_jj_bookmark(*, cwd: Path) -> str:
    with suppress(CalledProcessError):
        raw = capture_shell('jj bookmark list --pointing-at @-', cwd=cwd)
        for line in raw.splitlines():
            if name := line.split(':')[0].strip():
                return name
    return ''


@lru_cache(maxsize=128)
def get_repo_metadata(cwd: Path) -> RepoMetadata | None:
    """Resolve full repository metadata from a working directory.

    Cached to avoid repeated subprocess calls for the same directory.

    Args:
        cwd: Path to the current working directory

    Returns:
        RepoMetadata, or None if no VCS repository is found

    """
    if git_root := git_show_toplevel(cwd=cwd):
        root = git_root
        vcs = VcsKind.GIT
    elif jj_repo_root := jj_root(cwd=cwd):
        root = jj_repo_root
        vcs = VcsKind.JUJUTSU
    elif repo_root := find_repo_root(cwd):
        root = repo_root
        vcs = detect_vcs_kind(root) or VcsKind.GIT
    else:
        return None

    match vcs:
        case VcsKind.JUJUTSU:
            remote_url = _get_jj_remote_url(cwd=root)
            branch = _get_jj_bookmark(cwd=root)
        case _:
            remote_url = _get_git_remote_url(cwd=root)
            branch = _get_git_branch(cwd=root)

    owner, repo_name = parse_remote_url(remote_url)
    forge = detect_forge(remote_url)

    return RepoMetadata(
        root=root,
        vcs=vcs,
        remote_url=remote_url,
        owner=owner,
        repo_name=repo_name,
        branch=branch,
        forge=forge,
    )
