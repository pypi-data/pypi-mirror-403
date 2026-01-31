"""Export tomllib compatibility layer for Python 3.9+."""

# TODO: Remove when dropping 3.10!

try:
    import tomllib  # type: ignore[import-not-found] # pyright: ignore[reportAttributeAccessIssue]
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[import-not-found,attr-defined,unused-ignore] # pyright: ignore[reportAttributeAccessIssue]

TOMLDecodeError = tomllib.TOMLDecodeError

__all__ = ('TOMLDecodeError', 'tomllib')
