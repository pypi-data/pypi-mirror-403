"""Code tag collector for tracking TODOs, FIXMEs, and other code tags.

Migrated from calcipy.code_tag_collector.

"""

try:  # noqa: RUF067
    from ._collector import CODE_TAG_RE, COMMON_CODE_TAGS, SKIP_PHRASE, write_code_tag_file
except ImportError as exc:
    msg = "The 'arrow' package is required for code_tag_collector. Install with: pip install arrow"
    raise ImportError(msg) from exc

__all__ = ('CODE_TAG_RE', 'COMMON_CODE_TAGS', 'SKIP_PHRASE', 'write_code_tag_file')
