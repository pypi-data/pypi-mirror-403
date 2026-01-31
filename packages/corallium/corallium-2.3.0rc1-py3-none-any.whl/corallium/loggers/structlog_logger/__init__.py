"""Only importable when `structlog` is installed."""

try:  # noqa: RUF067
    from ._structlog_logger import structlog_logger
except ModuleNotFoundError as exc:  # pragma: no cover
    msg = 'Install "structlog" in order to use the "structlog_logger"'
    raise RuntimeError(msg) from exc

__all__ = ('structlog_logger',)
