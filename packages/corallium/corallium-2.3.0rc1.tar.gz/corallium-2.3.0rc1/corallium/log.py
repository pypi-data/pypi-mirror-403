"""Log."""

from __future__ import annotations

import logging
from functools import partial
from typing import Any

from beartype.typing import Protocol, runtime_checkable
from rich.console import Console

from .loggers.rich_printer import rich_printer
from .loggers.styles import STYLES, Styles

DEF_LEVEL = logging.ERROR


@runtime_checkable
class LogCallable(Protocol):
    """Defined the kwargs accepted for a delegated task."""

    def __call__(
        self,
        message: str,
        *,
        is_header: bool,
        _this_level: int,
        _is_text: bool,
    ) -> Any:
        """Type-checked arguments."""


class _LogSingleton:
    """Store pointer to log function."""

    _logger: LogCallable | None = None
    _log_level: int = DEF_LEVEL

    def set_logger(
        self,
        *,
        log_level: int,
        logger: LogCallable | None = None,
        _console: Console | None = None,
        _styles: Styles | None = None,
        **kwargs: Any,
    ) -> LogCallable:
        """Return after updating the internal logger instance."""
        if not (logger_ := logger or self._logger):
            logger_ = partial(rich_printer, _console=_console or Console(), _styles=_styles or STYLES)
        self._logger = partial(logger_, **kwargs)
        self._log_level = log_level
        return self._logger

    def log(self, *args: Any, _this_level: int, is_header: bool = False, _is_text: bool = False, **kwargs: Any) -> None:
        """Delegate the arguments to the logger if this level above the threshold."""
        if _this_level < self._log_level:
            return
        # Ensure logger is configured
        logger = self._logger or self.set_logger(log_level=self._log_level)
        logger(*args, _this_level=_this_level, is_header=is_header, _is_text=_is_text, **kwargs)


_LOG_SINGLETON = _LogSingleton()


class _Logger:
    def text(self, message: str, *, is_header: bool = False, **kwargs: Any) -> None:
        """Print the content without a leading timestamp.

        If writing to a file or not natively supported by the logger, will appear in the logs as level info.

        """
        self.info(message, **{'_is_text': True, 'is_header': is_header, **kwargs})

    def text_debug(self, message: str, *, is_header: bool = False, **kwargs: Any) -> None:
        """Variation on text that will appear as a debug log if not supported."""
        self.debug(message, **{'_is_text': True, 'is_header': is_header, **kwargs})

    def debug(self, message: str, **kwargs: Any) -> None:  # noqa: PLR6301
        _LOG_SINGLETON.log(message, _this_level=logging.DEBUG, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:  # noqa: PLR6301
        _LOG_SINGLETON.log(message, _this_level=logging.INFO, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:  # noqa: PLR6301
        _LOG_SINGLETON.log(message, _this_level=logging.WARNING, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:  # noqa: PLR6301
        _LOG_SINGLETON.log(message, _this_level=logging.ERROR, **kwargs)

    def exception(self, message: str, **kwargs: Any) -> None:  # noqa: PLR6301
        _LOG_SINGLETON.log(message, _this_level=logging.CRITICAL, **kwargs)


def configure_logger(*, log_level: int = DEF_LEVEL, logger: LogCallable | None = None, **kwargs: Any) -> None:
    """Configure the global log level or replace the logger."""
    _LOG_SINGLETON.set_logger(logger=logger, log_level=log_level, **kwargs)


def get_logger() -> _Logger:
    """Return global logger."""
    return _Logger()


LOGGER = get_logger()
