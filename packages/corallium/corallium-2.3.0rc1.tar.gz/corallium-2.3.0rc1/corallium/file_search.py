"""Find files using git, with filesystem walk fallback.

Migrated from calcipy.file_search for git-based file discovery.
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from corallium.log import LOGGER
from corallium.vcs._git_commands import git_ls_files
from corallium.vcs._jj_commands import jj_file_list


def _walk_files(*, cwd: Path) -> list[str]:
    """Get all files using recursive filesystem walk.

    Args:
        cwd: directory to search recursively

    Returns:
        list of all file paths relative to cwd

    """
    files = []
    for path in cwd.rglob('*'):
        if path.is_file():
            try:
                rel_path = path.relative_to(cwd)
                files.append(rel_path.as_posix())
            except ValueError:
                LOGGER.debug('Skipping path outside cwd', path=path, cwd=cwd)
    return sorted(files)


def _get_default_ignore_patterns() -> list[str]:
    """Default ignore patterns for filesystem walk (when git unavailable)."""
    return [
        '**/.git/**',
        '**/.jj/**',
        '**/__pycache__/**',
        '**/*.pyc',
        '**/*.egg-info/**',
        '**/dist/**',
        '**/build/**',
        '**/.pytest_cache/**',
        '**/.mypy_cache/**',
        '**/.ruff_cache/**',
        '**/.nox/**',
        '**/.tox/**',
        '**/htmlcov/**',
        '**/.coverage*',
        '**/.venv/**',
        '**/venv/**',
        '**/node_modules/**',
    ]


def _get_all_files(*, cwd: Path) -> tuple[list[str], bool]:
    """Get all files using git, falling back to filesystem walk.

    Args:
        cwd: Current working directory to pass to git command

    Returns:
        Tuple of (file paths, used_git)

    """
    if (files := git_ls_files(cwd=cwd)) is not None:
        return files, True

    if (files := jj_file_list(cwd=cwd)) is not None:
        return files, True

    LOGGER.debug('VCS not available, using filesystem walk', cwd=cwd)
    return _walk_files(cwd=cwd), False


def _filter_files(rel_filepaths: list[str], ignore_patterns: list[str]) -> list[str]:
    """Filter a list of string file paths with specified ignore patterns in glob syntax.

    Args:
        rel_filepaths: List of string file paths
        ignore_patterns: Glob ignore patterns (e.g., ['*.pyc', '__pycache__/*'])

    Returns:
        List of all non-ignored file path names

    """
    if ignore_patterns:
        matches = []
        for fp in rel_filepaths:
            pth = Path(fp).resolve()
            if not any(pth.match(pat) for pat in ignore_patterns):
                matches.append(fp)
        return matches
    return rel_filepaths


def find_project_files(path_project: Path, ignore_patterns: list[str]) -> list[Path]:
    """Find project files in git version control or via filesystem walk.

    Note: Uses git ls-files and verifies that each file exists.
    Falls back to recursive filesystem walk when git is unavailable.

    Args:
        path_project: Path to the project directory
        ignore_patterns: Glob ignore patterns

    Returns:
        List of Path objects for all tracked, non-ignored files

    Example:
        >>> from pathlib import Path
        >>> files = find_project_files(
        ...     Path('.'),
        ...     ignore_patterns=['*.pyc', '__pycache__/*', '.git/*']
        ... )

    """
    file_paths = []
    rel_filepaths, used_git = _get_all_files(cwd=path_project)

    effective_patterns = ignore_patterns
    if not used_git and not ignore_patterns:
        effective_patterns = _get_default_ignore_patterns()
        LOGGER.info(
            'Using default ignore patterns for filesystem walk. Specify --ignore-patterns to customize.',
            pattern_count=len(effective_patterns),
        )

    filtered_rel_files = _filter_files(
        rel_filepaths=rel_filepaths,
        ignore_patterns=effective_patterns,
    )
    for rel_file in filtered_rel_files:
        path_file = path_project / rel_file
        if path_file.is_file():
            file_paths.append(path_file)
        else:  # pragma: no cover
            LOGGER.warning('Could not find the specified file', path_file=path_file)
    return file_paths


def find_project_files_by_suffix(
    path_project: Path,
    *,
    ignore_patterns: list[str] | None = None,
) -> dict[str, list[Path]]:
    """Find project files in git version control grouped by file extension.

    Note: Uses git ls-files and verifies that each file exists.
    Falls back to recursive filesystem walk when git is unavailable.

    Args:
        path_project: Path to the project directory
        ignore_patterns: Glob ignore patterns (optional)

    Returns:
        Dictionary where keys are file extensions (without leading dot) and
        values are lists of Path objects with that extension

    Example:
        >>> from pathlib import Path
        >>> files_by_ext = find_project_files_by_suffix(
        ...     Path('.'),
        ...     ignore_patterns=['*.pyc', '__pycache__/*']
        ... )
        >>> py_files = files_by_ext.get('py', [])
        >>> md_files = files_by_ext.get('md', [])

    """
    file_lookup: dict[str, list[Path]] = defaultdict(list)
    for path_file in find_project_files(path_project, ignore_patterns or []):
        file_lookup[path_file.suffix.lstrip('.')].append(path_file)
    return dict(file_lookup)
