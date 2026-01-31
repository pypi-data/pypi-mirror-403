"""VCS (Version Control System) subpackage for repo discovery and forge integration."""

from ._forge import detect_forge, forge_blame_url, forge_file_url, forge_repo_url, parse_remote_url
from ._git_commands import git_blame_porcelain, git_ls_files, git_show_toplevel, zsplit
from ._jj_commands import jj_file_annotate, jj_file_list, jj_git_remote_list, jj_root
from ._repo import detect_vcs_kind, find_repo_root, get_repo_metadata
from ._types import ForgeKind, RepoMetadata, VcsKind

__all__ = [
    'ForgeKind',
    'RepoMetadata',
    'VcsKind',
    'detect_forge',
    'detect_vcs_kind',
    'find_repo_root',
    'forge_blame_url',
    'forge_file_url',
    'forge_repo_url',
    'get_repo_metadata',
    'git_blame_porcelain',
    'git_ls_files',
    'git_show_toplevel',
    'jj_file_annotate',
    'jj_file_list',
    'jj_git_remote_list',
    'jj_root',
    'parse_remote_url',
    'zsplit',
]
