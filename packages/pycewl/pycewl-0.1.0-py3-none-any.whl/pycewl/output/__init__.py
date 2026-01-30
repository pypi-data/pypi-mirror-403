"""Output module for pycewl."""

from pycewl.output.writers import (
    write_emails,
    write_metadata,
    write_relevance_grouped,
    write_words,
)

__all__ = ["write_emails", "write_metadata", "write_relevance_grouped", "write_words"]
