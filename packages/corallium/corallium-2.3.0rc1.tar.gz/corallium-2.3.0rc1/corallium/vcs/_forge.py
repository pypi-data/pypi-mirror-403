"""Forge detection and URL generation."""

from __future__ import annotations

import re

from ._types import ForgeKind

_REMOTE_URL_RE = re.compile(r'^(?:https?://[^/]+/|[^@]+@[^:]+:)(?P<owner>[^/]+)/(?P<repo>[^/.]+)(?:\.git)?/?$')

_FORGE_HOSTNAME_MAP = {
    'bitbucket.org': ForgeKind.BITBUCKET,
    'github.com': ForgeKind.GITHUB,
    'gitlab.com': ForgeKind.GITLAB,
}


def parse_remote_url(remote_url: str) -> tuple[str, str]:
    """Extract (owner, repo_name) from an SSH or HTTPS remote URL.

    Returns:
        Tuple of (owner, repo_name), or ('', '') if not parseable.

    """
    if m := _REMOTE_URL_RE.match(remote_url):
        return m['owner'], m['repo']
    return '', ''


def detect_forge(remote_url: str) -> ForgeKind:
    """Detect forge kind from a remote URL hostname."""
    for hostname, kind in _FORGE_HOSTNAME_MAP.items():
        if hostname in remote_url:
            return kind
    return ForgeKind.UNKNOWN


def forge_repo_url(*, forge: ForgeKind, owner: str, repo: str) -> str:
    """Base repository URL for the given forge."""
    match forge:
        case ForgeKind.GITHUB:
            return f'https://github.com/{owner}/{repo}'
        case ForgeKind.GITLAB:
            return f'https://gitlab.com/{owner}/{repo}'
        case ForgeKind.BITBUCKET:
            return f'https://bitbucket.org/{owner}/{repo}'
        case _:
            return ''


def forge_blame_url(
    *,
    forge: ForgeKind,
    owner: str,
    repo: str,
    rev: str,
    path: str,
    line: int,
) -> str:
    """Forge-specific blame URL."""
    base = forge_repo_url(forge=forge, owner=owner, repo=repo)
    if not base:
        return ''
    match forge:
        case ForgeKind.GITHUB:
            return f'{base}/blame/{rev}/{path}#L{line}'
        case ForgeKind.GITLAB:
            return f'{base}/-/blame/{rev}/{path}#L{line}'
        case ForgeKind.BITBUCKET:
            return f'{base}/annotate/{rev}/{path}#{path}-{line}'
        case _:
            return ''


def forge_file_url(
    *,
    forge: ForgeKind,
    owner: str,
    repo: str,
    rev: str,
    path: str,
    line: int,
) -> str:
    """Forge-specific file view URL."""
    base = forge_repo_url(forge=forge, owner=owner, repo=repo)
    if not base:
        return ''
    match forge:
        case ForgeKind.GITHUB:
            return f'{base}/blob/{rev}/{path}#L{line}'
        case ForgeKind.GITLAB:
            return f'{base}/-/blob/{rev}/{path}#L{line}'
        case ForgeKind.BITBUCKET:
            return f'{base}/src/{rev}/{path}#{path}-{line}'
        case _:
            return ''
