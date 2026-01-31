"""VCS type definitions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class VcsKind(str, Enum):
    """Version control system kind."""

    GIT = 'git'
    JUJUTSU = 'jj'


class ForgeKind(str, Enum):
    """Source forge kind."""

    BITBUCKET = 'bitbucket'
    GITHUB = 'github'
    GITLAB = 'gitlab'
    UNKNOWN = 'unknown'


@dataclass(frozen=True)
class RepoMetadata:
    """Structured metadata about a VCS repository."""

    root: Path
    vcs: VcsKind
    remote_url: str
    owner: str
    repo_name: str
    branch: str
    forge: ForgeKind
