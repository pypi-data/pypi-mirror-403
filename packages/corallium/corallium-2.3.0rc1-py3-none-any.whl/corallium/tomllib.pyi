from collections.abc import Callable
from typing import Any, BinaryIO

class TOMLDecodeError(ValueError): ...

def load(fp: BinaryIO, /) -> dict[str, Any]: ...
def loads(s: str, /) -> dict[str, Any]: ...

# Re-export tomllib module (the actual module from stdlib or tomli)
class _TomllibModule:
    TOMLDecodeError: type[TOMLDecodeError]
    load: Callable[[BinaryIO], dict[str, Any]]
    loads: Callable[[str], dict[str, Any]]

tomllib: _TomllibModule

__all__ = ('TOMLDecodeError', 'tomllib')
