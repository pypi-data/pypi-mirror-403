"""Word extraction pipeline for pycewl."""

from __future__ import annotations

import html
import re
from collections import Counter

from bs4 import BeautifulSoup

from pycewl.config import WordConfig

# Umlaut conversion mapping (German)
UMLAUT_MAP: dict[str, str] = {
    "ä": "ae",
    "ö": "oe",
    "ü": "ue",
    "Ä": "Ae",
    "Ö": "Oe",
    "Ü": "Ue",
    "ß": "ss",
}


class WordExtractor:
    """Extract words from HTML content matching CeWL's pipeline."""

    # Pattern for words - letters and optionally numbers
    WORD_PATTERN_ALPHA = re.compile(r"\b[a-zA-ZÀ-ÿ]+\b")
    WORD_PATTERN_ALPHANUM = re.compile(r"\b[a-zA-ZÀ-ÿ][a-zA-ZÀ-ÿ0-9]*\b")

    def __init__(self, config: WordConfig) -> None:
        """Initialize the word extractor.

        Args:
            config: Word extraction configuration.
        """
        self._config = config
        self._word_counts: Counter[str] = Counter()
        self._word_pattern = (
            self.WORD_PATTERN_ALPHANUM if config.with_numbers else self.WORD_PATTERN_ALPHA
        )

    @property
    def word_counts(self) -> Counter[str]:
        """Get word counts."""
        return self._word_counts.copy()

    def _convert_umlauts(self, text: str) -> str:
        """Convert German umlauts to ASCII equivalents.

        Args:
            text: Text to convert.

        Returns:
            Text with umlauts converted.
        """
        for umlaut, replacement in UMLAUT_MAP.items():
            text = text.replace(umlaut, replacement)
        return text

    def _extract_text_from_html(self, html_content: str) -> str:
        """Extract text content from HTML.

        Args:
            html_content: Raw HTML content.

        Returns:
            Extracted text content.
        """
        soup = BeautifulSoup(html_content, "lxml")

        # Remove script and style elements
        for element in soup(["script", "style", "noscript"]):
            element.decompose()

        texts: list[str] = []

        # Get body text
        body = soup.find("body")
        if body:
            texts.append(body.get_text(separator=" "))

        # Get meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and hasattr(meta_desc, "get"):
            content = meta_desc.get("content")
            if isinstance(content, str):
                texts.append(content)

        # Get meta keywords
        meta_keywords = soup.find("meta", attrs={"name": "keywords"})
        if meta_keywords and hasattr(meta_keywords, "get"):
            content = meta_keywords.get("content")
            if isinstance(content, str):
                texts.append(content)

        # Get alt attributes from images
        for img in soup.find_all("img", alt=True):
            alt = img.get("alt")
            if alt and isinstance(alt, str):
                texts.append(alt)

        # Get title attributes
        for tag in soup.find_all(title=True):
            title = tag.get("title")
            if title and isinstance(title, str):
                texts.append(title)

        # Combine all text
        combined = " ".join(texts)

        # Decode HTML entities
        combined = html.unescape(combined)

        return combined

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into words.

        Args:
            text: Text to tokenize.

        Returns:
            List of words.
        """
        # Convert umlauts if configured
        if self._config.convert_umlauts:
            text = self._convert_umlauts(text)

        # Lowercase if configured
        if self._config.lowercase:
            text = text.lower()

        # Find all words
        words = self._word_pattern.findall(text)

        # Filter by length
        filtered: list[str] = []
        for word in words:
            if len(word) < self._config.min_length:
                continue
            if self._config.max_length and len(word) > self._config.max_length:
                continue
            filtered.append(word)

        return filtered

    def extract_from_html(self, html_content: str) -> list[str]:
        """Extract words from HTML content.

        Args:
            html_content: Raw HTML content.

        Returns:
            List of extracted words.
        """
        text = self._extract_text_from_html(html_content)
        return self._tokenize(text)

    def extract_from_text(self, text: str) -> list[str]:
        """Extract words from plain text.

        Args:
            text: Plain text content.

        Returns:
            List of extracted words.
        """
        # Decode HTML entities just in case
        text = html.unescape(text)
        return self._tokenize(text)

    def add_words(self, words: list[str]) -> None:
        """Add words to the counter.

        Args:
            words: List of words to add.
        """
        self._word_counts.update(words)

    def process_html(self, html_content: str) -> None:
        """Process HTML and add words to counter.

        Args:
            html_content: Raw HTML content.
        """
        words = self.extract_from_html(html_content)
        self.add_words(words)

    def get_sorted_words(self) -> list[tuple[str, int]]:
        """Get words sorted by count descending.

        Returns:
            List of (word, count) tuples sorted by count descending.
        """
        return self._word_counts.most_common()

    def get_grouped_words(self, group_size: int) -> list[list[tuple[str, int]]]:
        """Get words grouped by count ranges.

        Args:
            group_size: Size of each group.

        Returns:
            List of groups, each containing (word, count) tuples.
        """
        sorted_words = self.get_sorted_words()
        if not sorted_words:
            return []

        # Group by count ranges
        groups: list[list[tuple[str, int]]] = []
        current_group: list[tuple[str, int]] = []

        for word, count in sorted_words:
            if not current_group:
                current_group.append((word, count))
            else:
                # Check if this word should be in a new group
                first_count = current_group[0][1]
                if first_count - count >= group_size:
                    groups.append(current_group)
                    current_group = [(word, count)]
                else:
                    current_group.append((word, count))

        if current_group:
            groups.append(current_group)

        return groups

    def reset(self) -> None:
        """Reset the word counter."""
        self._word_counts.clear()
