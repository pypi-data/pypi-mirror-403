"""URL filtering for the spider."""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

from pycewl.config import SpiderConfig


class URLFilter:
    """Filter URLs based on spider configuration."""

    # File extensions to skip
    SKIP_EXTENSIONS = frozenset({
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".ico", ".svg", ".webp",
        ".mp3", ".mp4", ".avi", ".mov", ".wmv", ".flv", ".webm",
        ".zip", ".tar", ".gz", ".rar", ".7z",
        ".exe", ".dll", ".so", ".bin",
        ".css", ".js", ".woff", ".woff2", ".ttf", ".eot",
    })

    def __init__(self, config: SpiderConfig, base_url: str) -> None:
        """Initialize the URL filter.

        Args:
            config: Spider configuration.
            base_url: Base URL for relative URL resolution.
        """
        self._config = config
        self._base_url = base_url
        self._base_parsed = urlparse(base_url)
        self._allowed_pattern: re.Pattern[str] | None = None

        if config.allowed_pattern:
            self._allowed_pattern = re.compile(config.allowed_pattern)

    def normalize(self, url: str, referrer: str | None = None) -> str | None:
        """Normalize a URL.

        Args:
            url: URL to normalize.
            referrer: Referrer URL for relative resolution.

        Returns:
            Normalized absolute URL, or None if invalid.
        """
        # Skip empty or javascript URLs
        if not url or url.startswith(("javascript:", "#", "data:")):
            return None

        # Handle mailto links specially
        if url.startswith("mailto:"):
            return url

        # Resolve relative URLs
        base = referrer or self._base_url
        try:
            absolute = urljoin(base, url)
        except ValueError:
            return None

        # Parse and validate
        try:
            parsed = urlparse(absolute)
        except ValueError:
            return None

        # Must have scheme and netloc
        if not parsed.scheme or not parsed.netloc:
            return None

        # Only HTTP(S)
        if parsed.scheme not in ("http", "https"):
            return None

        return absolute

    def should_crawl(self, url: str) -> bool:
        """Check if a URL should be crawled.

        Args:
            url: URL to check.

        Returns:
            True if URL should be crawled.
        """
        # Handle mailto links
        if url.startswith("mailto:"):
            return False

        parsed = urlparse(url)

        # Check if offsite
        if not self._config.offsite and parsed.netloc != self._base_parsed.netloc:
            return False

        # Check excluded paths
        for excluded in self._config.exclude_paths:
            if parsed.path.startswith(excluded):
                return False

        # Check allowed pattern
        if self._allowed_pattern and not self._allowed_pattern.search(url):
            return False

        # Check file extension
        path_lower = parsed.path.lower()
        return all(not path_lower.endswith(ext) for ext in self.SKIP_EXTENSIONS)

    def is_document(self, url: str) -> bool:
        """Check if URL points to a document (PDF, DOC, etc.).

        Args:
            url: URL to check.

        Returns:
            True if URL is a document.
        """
        parsed = urlparse(url)
        path_lower = parsed.path.lower()

        doc_extensions = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".pptx", ".odt", ".ods"}
        return any(path_lower.endswith(ext) for ext in doc_extensions)


def extract_links(html: str, _base_url: str) -> list[str]:
    """Extract links from HTML content.

    Args:
        html: HTML content.
        _base_url: Base URL for relative resolution (unused, kept for API compatibility).

    Returns:
        List of extracted URLs.
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "lxml")
    links: list[str] = []

    # Extract from <a> tags
    for tag in soup.find_all("a", href=True):
        href = tag.get("href")
        if href and isinstance(href, str):
            links.append(href)

    # Extract from <area> tags (image maps)
    for tag in soup.find_all("area", href=True):
        href = tag.get("href")
        if href and isinstance(href, str):
            links.append(href)

    return links
