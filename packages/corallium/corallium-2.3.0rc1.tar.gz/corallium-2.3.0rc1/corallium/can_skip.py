"""Support can-skip logic from Make.

Migrated from calcipy.can_skip for general-purpose build optimization.
"""

from __future__ import annotations

from pathlib import Path

from corallium.log import LOGGER


def can_skip(*, prerequisites: list[Path], targets: list[Path]) -> bool:
    """Return true if the prerequisite files have newer `mtime` than targets.

    Implements Make-style dependency checking: if all targets are newer than
    all prerequisites, the build can be skipped.

    Args:
        prerequisites: List of source files (must all exist)
        targets: List of generated files (may or may not exist)

    Returns:
        True if targets exist and are newer than prerequisites, False otherwise

    Raises:
        ValueError: if any prerequisite file does not exist

    Example:
        >>> from pathlib import Path
        >>> # Skip test run if coverage file is newer than source
        >>> if can_skip(
        ...     prerequisites=[*Path('src').rglob('*.py')],
        ...     targets=[Path('.coverage.xml')]
        ... ):
        ...     print("Skipping - targets are up to date")
        ...     return

    """
    if not (ts_prerequisites := [pth.stat().st_mtime for pth in prerequisites]):
        raise ValueError('Required files do not exist', prerequisites)

    # Collect target mtimes, skipping missing files
    ts_targets = [pth.stat().st_mtime for pth in targets if pth.is_file()]
    if ts_targets and len(ts_targets) == len(targets) and min(ts_targets) > max(ts_prerequisites):
        LOGGER.warning('Skipping because targets are newer', targets=targets)
        return True
    return False


def dont_skip(*, prerequisites: list[Path], targets: list[Path]) -> bool:
    """Returns False. To use for testing with mock.

    This is a drop-in replacement for can_skip() that always returns False,
    useful for testing scenarios where you want to force execution.

    Args:
        prerequisites: List of source files (logged but not checked)
        targets: List of generated files (logged but not checked)

    Returns:
        Always returns False

    """
    LOGGER.debug('Mocking can_skip', prerequisites=prerequisites, targets=targets)
    return False
