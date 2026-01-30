"""Extractors module for pycewl."""

from pycewl.extractors.emails import extract_emails
from pycewl.extractors.metadata import extract_metadata
from pycewl.extractors.words import WordExtractor

__all__ = ["WordExtractor", "extract_emails", "extract_metadata"]
