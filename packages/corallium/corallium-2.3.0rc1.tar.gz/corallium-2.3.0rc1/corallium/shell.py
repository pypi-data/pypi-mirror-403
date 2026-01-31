"""Run shell commands."""

from __future__ import annotations

import asyncio
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from time import time

from .log import LOGGER

# Potentially dangerous shell patterns that could indicate command injection
_DANGEROUS_PATTERNS = frozenset(
    {
        ';',  # Command chaining
        '&&',  # Conditional execution
        '||',  # Conditional execution
        '|',  # Pipe (legitimate use but can be dangerous)
        '$(',  # Command substitution
        '`',  # Command substitution
        '>',  # Redirection (legitimate but can overwrite files)
        '<',  # Redirection
        '>>',  # Append redirection
        '\n',  # Newline can execute multiple commands
        '\r',  # Carriage return
    }
)


def _validate_shell_command(cmd: str) -> None:
    """Validate shell command for potentially dangerous patterns.

    This is a best-effort check to detect obvious command injection attempts.
    It is not foolproof and should not be relied upon as the sole security measure.

    Args:
        cmd: The command to validate

    Raises:
        ValueError: If dangerous patterns are detected

    """
    for pattern in _DANGEROUS_PATTERNS:
        if pattern in cmd:
            msg = (
                f'Potentially dangerous pattern {pattern!r} detected in command. '
                f'Use validate_cmd=False to bypass this check if the command is trusted.'
            )
            raise ValueError(msg)


def capture_shell(
    cmd: str,
    *,
    timeout: int | None = 120,
    cwd: Path | None = None,
    printer: Callable[[str], None] | None = None,
    validate_cmd: bool = False,
) -> str:
    """Run shell command, return the output, and optionally print in real time.

    WARNING: This function uses shell=True which can be a security risk.
    Only use with trusted input or enable validate_cmd for basic protection.

    Inspired by: https://stackoverflow.com/a/38745040/3219667

    Args:
        cmd: shell command
        timeout: process timeout in seconds. Defaults to 2 minutes. Use None for no timeout.
        cwd: optional path for shell execution
        printer: optional callable to output the lines in real time
        validate_cmd: if True, validates command for dangerous patterns. Default False
            to preserve backward compatibility and allow legitimate shell features.

    Returns:
        str: stripped output

    Raises:
        CalledProcessError: if return code is non-zero
        TimeoutExpired: if timeout is reached
        ValueError: if validate_cmd=True and dangerous patterns are detected

    """
    if validate_cmd:
        _validate_shell_command(cmd)

    LOGGER.debug('Running', cmd=cmd, timeout=timeout, cwd=cwd, printer=printer, validate_cmd=validate_cmd)
    if timeout and timeout < 0:
        raise ValueError('Negative timeouts are not allowed')

    start = time()
    lines = []
    with subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        shell=True,
    ) as proc:
        if not (stdout := proc.stdout):
            raise NotImplementedError('Failed to read stdout from process.')
        return_code = None
        while return_code is None:
            if timeout is not None and time() - start >= timeout:
                proc.kill()
                break
            if line := stdout.readline():
                lines.append(line)
                if printer:
                    printer(line.rstrip())
            else:
                return_code = proc.poll()

    output = ''.join(lines)
    if return_code is None:
        # Process was killed due to timeout
        raise subprocess.TimeoutExpired(cmd=cmd, timeout=float(timeout or 0), output=output)
    if return_code != 0:
        raise subprocess.CalledProcessError(returncode=return_code, cmd=cmd, output=output)

    duration = time() - start
    LOGGER.debug('Shell command completed', cmd=cmd, returncode=0, duration_seconds=round(duration, 2), cwd=cwd)

    return output


async def _capture_shell_async(cmd: str, *, cwd: Path | None = None, start_time: float = 0) -> str:
    proc = await asyncio.create_subprocess_shell(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True,
    )

    stdout, _stderr = await proc.communicate()
    output = stdout.decode().strip()
    if proc.returncode is None:
        # Process returncode should not be None after communicate(), but handle defensively
        msg = f'Process returncode is None after communicate() for command: {cmd}'
        raise RuntimeError(msg)
    if proc.returncode != 0:
        raise subprocess.CalledProcessError(returncode=proc.returncode, cmd=cmd, output=output)

    duration = time() - start_time if start_time else 0
    LOGGER.debug('Shell command completed', cmd=cmd, returncode=0, duration_seconds=round(duration, 2), cwd=cwd)

    return output


async def capture_shell_async(
    cmd: str,
    *,
    timeout: int | None = 120,
    cwd: Path | None = None,
    validate_cmd: bool = False,
) -> str:
    """Run a shell command asynchronously and return the output.

    WARNING: This function uses shell=True which can be a security risk.
    Only use with trusted input or enable validate_cmd for basic protection.

    ```py
    print(asyncio.run(capture_shell_async('ls ~/.config')))
    ```

    Args:
        cmd: shell command
        timeout: process timeout in seconds. Defaults to 2 minutes. Use None for no timeout.
        cwd: optional path for shell execution
        validate_cmd: if True, validates command for dangerous patterns. Default False
            to preserve backward compatibility and allow legitimate shell features.

    Returns:
        str: stripped output

    """
    if validate_cmd:
        _validate_shell_command(cmd)

    LOGGER.debug('Running', cmd=cmd, timeout=timeout, cwd=cwd, validate_cmd=validate_cmd)
    start = time()
    return await asyncio.wait_for(
        _capture_shell_async(cmd=cmd, cwd=cwd, start_time=start),
        timeout=timeout or None,
    )


def run_shell(cmd: str, *, timeout: int | None = 120, cwd: Path | None = None, validate_cmd: bool = False) -> None:
    """Run a shell command without capturing the output.

    WARNING: This function uses shell=True which can be a security risk.
    Only use with trusted input or enable validate_cmd for basic protection.

    Args:
        cmd: shell command
        timeout: process timeout in seconds. Defaults to 2 minutes. Use None for no timeout.
        cwd: optional path for shell execution
        validate_cmd: if True, validates command for dangerous patterns. Default False
            to preserve backward compatibility and allow legitimate shell features.

    """
    if validate_cmd:
        _validate_shell_command(cmd)

    LOGGER.debug('Running', cmd=cmd, timeout=timeout, cwd=cwd, validate_cmd=validate_cmd)

    start = time()
    subprocess.run(
        cmd,
        timeout=timeout or None,
        cwd=cwd,
        stdout=sys.stdout,
        stderr=sys.stderr,
        check=True,
        shell=True,
    )

    duration = time() - start
    LOGGER.debug('Shell command completed', cmd=cmd, returncode=0, duration_seconds=round(duration, 2), cwd=cwd)
