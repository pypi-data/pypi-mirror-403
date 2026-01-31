# ruff: noqa: RUF067
"""corallium."""

from ._runtime_type_check_setup import configure_runtime_type_checking_mode

__version__ = '2.3.0rc1'
__pkg_name__ = 'corallium'

configure_runtime_type_checking_mode()


# == Above code must always be first ==

from corallium.markup_table import format_table  # noqa: E402

__all__ = ['format_table']
