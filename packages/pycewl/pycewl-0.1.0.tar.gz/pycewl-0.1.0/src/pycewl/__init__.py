"""pycewl - Python async re-implementation of CeWL (Custom Word List Generator)."""

from pycewl.config import (
    AuthConfig,
    AuthType,
    CeWLConfig,
    CrawlResult,
    GoogleConfig,
    HeaderConfig,
    OutputConfig,
    ProxyConfig,
    RelevanceResult,
    SpiderConfig,
    WordConfig,
    WordResult,
)
from pycewl.extractors import WordExtractor, extract_emails, extract_metadata
from pycewl.google import GoogleSearch, RelevanceScorer
from pycewl.spider import Crawler, URLFilter, URLManager, URLNode

__version__ = "0.1.0"

__all__ = [
    "AuthConfig",
    "AuthType",
    "CeWLConfig",
    "CrawlResult",
    "Crawler",
    "GoogleConfig",
    "GoogleSearch",
    "HeaderConfig",
    "OutputConfig",
    "ProxyConfig",
    "RelevanceResult",
    "RelevanceScorer",
    "SpiderConfig",
    "URLFilter",
    "URLManager",
    "URLNode",
    "WordConfig",
    "WordExtractor",
    "WordResult",
    "__version__",
    "extract_emails",
    "extract_metadata",
]
