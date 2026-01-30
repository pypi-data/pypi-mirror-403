"""Output writers for pycewl."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, TextIO

from pycewl.extractors.metadata import DocumentMetadata
from pycewl.google.nlp import ScoredWord

if TYPE_CHECKING:
    from collections.abc import Sequence


def write_words(
    words: Sequence[tuple[str, int]],
    output_path: Path | None = None,
    show_count: bool = False,
    stream: TextIO | None = None,
) -> None:
    """Write word list to file or stdout.

    Args:
        words: List of (word, count) tuples.
        output_path: Path to output file. If None, writes to stream/stdout.
        show_count: Whether to include word counts.
        stream: Output stream if output_path is None.
    """
    out = stream or sys.stdout

    if output_path:
        with output_path.open("w", encoding="utf-8") as f:
            _write_words_to_stream(words, f, show_count)
    else:
        _write_words_to_stream(words, out, show_count)


def _write_words_to_stream(
    words: Sequence[tuple[str, int]],
    stream: TextIO,
    show_count: bool,
) -> None:
    """Write words to a stream.

    Args:
        words: List of (word, count) tuples.
        stream: Output stream.
        show_count: Whether to include counts.
    """
    for word, count in words:
        if show_count:
            stream.write(f"{word}, {count}\n")
        else:
            stream.write(f"{word}\n")


def write_grouped_words(
    groups: Sequence[Sequence[tuple[str, int]]],
    output_path: Path | None = None,
    show_count: bool = False,
    stream: TextIO | None = None,
) -> None:
    """Write grouped word list to file or stdout.

    Args:
        groups: List of word groups, each containing (word, count) tuples.
        output_path: Path to output file. If None, writes to stream/stdout.
        show_count: Whether to include word counts.
        stream: Output stream if output_path is None.
    """
    out = stream or sys.stdout

    if output_path:
        with output_path.open("w", encoding="utf-8") as f:
            _write_grouped_to_stream(groups, f, show_count)
    else:
        _write_grouped_to_stream(groups, out, show_count)


def _write_grouped_to_stream(
    groups: Sequence[Sequence[tuple[str, int]]],
    stream: TextIO,
    show_count: bool,
) -> None:
    """Write grouped words to a stream.

    Args:
        groups: List of word groups.
        stream: Output stream.
        show_count: Whether to include counts.
    """
    for i, group in enumerate(groups):
        if i > 0:
            stream.write("\n")

        for word, count in group:
            if show_count:
                stream.write(f"{word}, {count}\n")
            else:
                stream.write(f"{word}\n")


def write_emails(
    emails: set[str],
    output_path: Path | None = None,
    stream: TextIO | None = None,
) -> None:
    """Write email list to file or stdout.

    Args:
        emails: Set of email addresses.
        output_path: Path to output file. If None, writes to stream/stdout.
        stream: Output stream if output_path is None.
    """
    out = stream or sys.stdout
    sorted_emails = sorted(emails)

    if output_path:
        with output_path.open("w", encoding="utf-8") as f:
            for email in sorted_emails:
                f.write(f"{email}\n")
    else:
        for email in sorted_emails:
            out.write(f"{email}\n")


def write_metadata(
    metadata_list: Sequence[DocumentMetadata],
    output_path: Path | None = None,
    stream: TextIO | None = None,
) -> None:
    """Write document metadata to file or stdout.

    Args:
        metadata_list: List of DocumentMetadata objects.
        output_path: Path to output file. If None, writes to stream/stdout.
        stream: Output stream if output_path is None.
    """
    out = stream or sys.stdout

    if output_path:
        with output_path.open("w", encoding="utf-8") as f:
            _write_metadata_to_stream(metadata_list, f)
    else:
        _write_metadata_to_stream(metadata_list, out)


def _write_metadata_to_stream(
    metadata_list: Sequence[DocumentMetadata],
    stream: TextIO,
) -> None:
    """Write metadata to a stream.

    Args:
        metadata_list: List of DocumentMetadata objects.
        stream: Output stream.
    """
    # Collect all unique names
    all_names: set[str] = set()
    for meta in metadata_list:
        all_names.update(meta.all_names)

    for name in sorted(all_names):
        stream.write(f"{name}\n")


def write_relevance_grouped(
    query: str,
    related: Sequence[ScoredWord],
    unrelated: Sequence[ScoredWord],
    related_path: Path | None = None,
    unrelated_path: Path | None = None,
    show_count: bool = False,
    stream: TextIO | None = None,
) -> None:
    """Write relevance-grouped words to files or stdout.

    Args:
        query: The search query.
        related: Words related to the query.
        unrelated: Words not related to the query.
        related_path: Path for related words file.
        unrelated_path: Path for unrelated words file.
        show_count: Whether to include word counts.
        stream: Output stream for stdout output.
    """
    out = stream or sys.stdout

    # Write related words
    if related_path:
        with related_path.open("w", encoding="utf-8") as f:
            for word in related:
                if show_count:
                    f.write(f"{word.word}, {word.count}\n")
                else:
                    f.write(f"{word.word}\n")
    else:
        out.write(f'=== Words Related to "{query}" ===\n')
        for word in related:
            if show_count:
                out.write(f"{word.word}, {word.count}\n")
            else:
                out.write(f"{word.word}\n")
        out.write("\n")

    # Write unrelated words
    if unrelated_path:
        with unrelated_path.open("w", encoding="utf-8") as f:
            for word in unrelated:
                if show_count:
                    f.write(f"{word.word}, {word.count}\n")
                else:
                    f.write(f"{word.word}\n")
    else:
        out.write("=== General Words (Not Query-Specific) ===\n")
        for word in unrelated:
            if show_count:
                out.write(f"{word.word}, {word.count}\n")
            else:
                out.write(f"{word.word}\n")
