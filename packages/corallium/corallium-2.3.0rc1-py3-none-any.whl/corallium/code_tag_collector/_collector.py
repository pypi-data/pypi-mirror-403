"""Collect code tags and output for review in a single location."""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from subprocess import CalledProcessError  # nosec

import arrow
from beartype.typing import Dict, List, Pattern, Sequence

from corallium.file_helpers import read_lines
from corallium.log import LOGGER
from corallium.markup_table import format_table
from corallium.vcs import RepoMetadata, forge_blame_url, get_repo_metadata
from corallium.vcs._git_commands import git_blame_porcelain
from corallium.vcs._jj_commands import jj_file_annotate
from corallium.vcs._types import VcsKind

SKIP_PHRASE = 'corallium_skip_tags'
"""String that indicates the file should be excluded from the tag search.

When writing, uses 'corallium_skip_tags'. When reading, also checks for legacy 'calcipy_skip_tags'.
"""

_LEGACY_SKIP_PHRASES = ['calcipy_skip_tags']
"""Legacy skip phrases supported for backward compatibility when reading files."""

COMMON_CODE_TAGS = ['FIXME', 'TODO', 'PLANNED', 'HACK', 'REVIEW', 'TBD', 'DEBUG']
"""Most common code tags.

FYI and NOTE are excluded to not be tracked in the Code Summary.

"""

CODE_TAG_RE = r'((^|\s|\(|"|\')(?P<tag>{tag})(:| -)([^\r\n]))(?P<text>.+)'
"""Default code tag regex with `tag` and `text` matching groups.

Requires formatting with list of tags: `CODE_TAG_RE.format(tag='|'.join(tag_list))`

Commonly, the `tag_list` could be `COMMON_CODE_TAGS`

"""


@dataclass(frozen=True)
class _CodeTag:
    """Code Tag (FIXME,TODO,etc) with contextual information."""

    lineno: int
    tag: str
    text: str


@dataclass(frozen=True)
class _Tags:
    """Collection of code tags with additional contextual information."""

    path_source: Path
    code_tags: List[_CodeTag]


def _search_lines(
    lines: List[str],
    regex_compiled: Pattern[str],
    skip_phrase: str = SKIP_PHRASE,
) -> List[_CodeTag]:
    """Search lines of text for matches to the compiled regular expression.

    Args:
        lines: lines of text as list
        regex_compiled: compiled regular expression. Expected to have matching groups `(tag, text)`
        skip_phrase: skip file if string is found in final two lines. Default is `SKIP_PHRASE`

    Returns:
        list of all code tags found in lines

    """
    final_lines = '\n'.join(lines[-2:])
    skip_phrases = [skip_phrase, *_LEGACY_SKIP_PHRASES]
    if any(phrase in final_lines for phrase in skip_phrases):
        return []

    max_len = 400
    comments = []
    for lineno, line in enumerate(lines):
        if match := regex_compiled.search(line):
            if len(line) <= max_len:  # FYI: Suppress long lines
                group = match.groupdict()
                comments.append(_CodeTag(lineno=lineno + 1, tag=group['tag'], text=group['text']))
            else:
                LOGGER.text_debug('Skipping long line', lineno=lineno, line=line[:200])
    return comments


def _search_files(paths_source: Sequence[Path], regex_compiled: Pattern[str]) -> List[_Tags]:
    """Collect matches from multiple files.

    Args:
        paths_source: list of source files to parse
        regex_compiled: compiled regular expression. Expected to have matching groups `(tag, text)`

    Returns:
        list of all code tags found in files

    """
    matches = []
    for path_source in paths_source:
        lines = []
        try:
            lines = read_lines(path_source)
        except UnicodeDecodeError as err:
            LOGGER.text_debug('Could not parse', path_source=path_source, err=err)

        if comments := _search_lines(lines, regex_compiled):
            matches.append(_Tags(path_source=path_source, code_tags=comments))

    return matches


@dataclass(frozen=True)
class _CollectorRow:
    """Each row of the Code Tag table."""

    tag_name: str
    comment: str
    last_edit: str
    source_file: str

    @classmethod
    def from_code_tag(cls, code_tag: _CodeTag, last_edit: str, source_file: str) -> _CollectorRow:
        return cls(
            tag_name=f'{code_tag.tag:>7}',
            comment=code_tag.text,
            last_edit=last_edit,
            source_file=source_file,
        )


def _format_from_blame(
    *,
    collector_row: _CollectorRow,
    blame: str,
    metadata: RepoMetadata | None,
    rel_path: Path,
) -> _CollectorRow:
    """Parse the git blame for useful timestamps and author when available.

    Returns:
        new _CollectorRow with updated timestamps and source file link.

    """
    revision, old_line_number = blame.split('\n', maxsplit=1)[0].split(' ')[:2]
    if all(c_ == '0' for c_ in revision) and metadata:
        revision = metadata.branch
    blame_dict = {line.split(' ')[0]: ' '.join(line.split(' ')[1:]) for line in blame.split('\n')}

    user = 'committer' if 'committer-tz' in blame_dict else 'author'
    dt = arrow.get(int(blame_dict[f'{user}-time']))
    tz = blame_dict[f'{user}-tz'][:3] + ':' + blame_dict[f'{user}-tz'][-2:]
    last_edit = arrow.get(dt.isoformat()[:-6] + tz).format('YYYY-MM-DD')

    source_file = collector_row.source_file
    if metadata and metadata.owner and metadata.repo_name:
        remote_file_path = blame_dict.get('filename', rel_path.as_posix())
        git_url = forge_blame_url(
            forge=metadata.forge,
            owner=metadata.owner,
            repo=metadata.repo_name,
            rev=revision,
            path=remote_file_path,
            line=int(old_line_number),
        )
        if git_url:
            source_file = f'[{source_file}]({git_url})'

    return _CollectorRow(
        tag_name=collector_row.tag_name,
        comment=collector_row.comment,
        last_edit=last_edit,
        source_file=source_file,
    )


def _format_record(base_dir: Path, file_path: Path, comment: _CodeTag) -> _CollectorRow:
    """Format each table row for the code tag summary file. Include git permalink.

    Args:
        base_dir: base path of the project if git directory is not known
        file_path: path to the file of interest
        comment: _CodeTag information for the matched tag

    Returns:
        formatted _CollectorRow with file info

    """
    cwd = file_path.parent
    metadata = get_repo_metadata(cwd=cwd)

    rel_path = file_path.relative_to(base_dir)
    collector_row = _CollectorRow.from_code_tag(
        code_tag=comment,
        last_edit='N/A',
        source_file=f'{rel_path.as_posix()}:{comment.lineno}',
    )

    vcs = metadata.vcs if metadata else None
    match vcs:
        case VcsKind.JUJUTSU:
            if annotate := jj_file_annotate(file_path=file_path, line=comment.lineno, cwd=cwd):
                lines = annotate.splitlines()
                if comment.lineno <= len(lines):
                    LOGGER.text_debug('jj annotate line', line=lines[comment.lineno - 1])
        case _:
            try:
                blame = git_blame_porcelain(file_path=file_path, line=comment.lineno, cwd=cwd)
                if blame:
                    collector_row = _format_from_blame(
                        collector_row=collector_row,
                        blame=blame,
                        metadata=metadata,
                        rel_path=rel_path,
                    )
            except CalledProcessError as exc:
                handled_errors = (128,)
                if exc.returncode not in handled_errors:
                    raise
                LOGGER.text_debug('Skipping blame', file_path=file_path, exc=exc)

    return collector_row


def _format_report(
    base_dir: Path,
    code_tags: List[_Tags],
    tag_order: List[str],
) -> str:
    """Pretty-format the code tags by file and line number.

    Args:
        base_dir: base directory relative to the searched files
        code_tags: list of all code tags found in files
        tag_order: subset of all tags to include in the report and specified order

    Returns:
        str: pretty-formatted text

    """
    output = ''
    records = []
    counter: Dict[str, int] = defaultdict(int)
    for comments in sorted(code_tags, key=lambda tc: tc.path_source, reverse=False):
        for comment in comments.code_tags:
            if comment.tag in tag_order:
                collector_row = _format_record(base_dir, comments.path_source, comment)
                records.append(
                    {
                        'Type': collector_row.tag_name,
                        'Comment': collector_row.comment,
                        'Last Edit': collector_row.last_edit,
                        'Source File': collector_row.source_file,
                    },
                )
                counter[comment.tag] += 1
    if records:
        output += '\n' + format_table(headers=[*records[0]], records=records)
    LOGGER.text_debug('counter', counter=counter)

    sorted_counter = {tag: counter[tag] for tag in tag_order if tag in counter}
    LOGGER.text_debug('sorted_counter', sorted_counter=sorted_counter)
    if formatted_summary := ', '.join(f'{tag} ({count})' for tag, count in sorted_counter.items()):
        output += f'\n\nFound code tags for {formatted_summary}\n'
    return output


def write_code_tag_file(
    *,
    path_tag_summary: Path,
    paths_source: List[Path],
    base_dir: Path,
    regex: str = '',
    tags: str = '',
    header: str = '# Task Summary\n\nAuto-Generated by `corallium`',
) -> None:
    """Create the code tag summary file.

    Args:
        path_tag_summary: Path to the output file
        paths_source: list of source files to parse
        base_dir: base directory relative to the searched files
        regex: compiled regular expression. Expected to have matching groups `(tag, text)`.
            Default is CODE_TAG_RE with tags from tag_order
        tags: subset of all tags to include in the report and specified order. Default is COMMON_CODE_TAGS
        header: header text

    """
    tag_order = [t_.strip() for t_ in tags.split(',') if t_] or COMMON_CODE_TAGS
    matcher = (regex or CODE_TAG_RE).format(tag='|'.join(tag_order))

    matches = _search_files(paths_source, re.compile(matcher))
    if report := _format_report(
        base_dir,
        matches,
        tag_order=tag_order,
    ).strip():
        path_tag_summary.parent.mkdir(exist_ok=True, parents=True)
        path_tag_summary.write_text(f'{header}\n\n{report}\n\n<!-- {SKIP_PHRASE} -->\n', encoding='utf-8')
        LOGGER.text('Created Code Tag Summary', path_tag_summary=path_tag_summary)
    elif path_tag_summary.is_file():
        path_tag_summary.unlink()
