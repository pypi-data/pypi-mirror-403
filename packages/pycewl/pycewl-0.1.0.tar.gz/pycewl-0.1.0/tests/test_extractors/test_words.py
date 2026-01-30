"""Tests for word extraction."""

from __future__ import annotations

from pycewl.config import WordConfig
from pycewl.extractors.words import WordExtractor


class TestWordExtractor:
    """Tests for WordExtractor class."""

    def test_basic_extraction(self, sample_html: str) -> None:
        """Test basic word extraction from HTML."""
        config = WordConfig(min_length=3)
        extractor = WordExtractor(config)

        words = extractor.extract_from_html(sample_html)

        assert "Welcome" in words
        assert "Test" in words
        assert "Page" in words
        assert "paragraph" in words

    def test_script_and_style_removed(self, sample_html: str) -> None:
        """Test that script and style content is removed."""
        config = WordConfig(min_length=3)
        extractor = WordExtractor(config)

        words = extractor.extract_from_html(sample_html)

        # Script variable content should not appear
        assert "hidden" not in words or words.count("hidden") == 0

    def test_min_length_filter(self, sample_html: str) -> None:
        """Test minimum word length filtering."""
        config = WordConfig(min_length=5)
        extractor = WordExtractor(config)

        words = extractor.extract_from_html(sample_html)

        # All words should be at least 5 characters
        for word in words:
            assert len(word) >= 5

    def test_max_length_filter(self, sample_html: str) -> None:
        """Test maximum word length filtering."""
        config = WordConfig(min_length=3, max_length=6)
        extractor = WordExtractor(config)

        words = extractor.extract_from_html(sample_html)

        # All words should be at most 6 characters
        for word in words:
            assert len(word) <= 6

    def test_lowercase_conversion(self, sample_html: str) -> None:
        """Test lowercase conversion."""
        config = WordConfig(min_length=3, lowercase=True)
        extractor = WordExtractor(config)

        words = extractor.extract_from_html(sample_html)

        # All words should be lowercase
        for word in words:
            assert word == word.lower()

    def test_umlaut_conversion(self, sample_html_german: str) -> None:
        """Test German umlaut conversion."""
        config = WordConfig(min_length=3, convert_umlauts=True)
        extractor = WordExtractor(config)

        words = extractor.extract_from_html(sample_html_german)

        # Check that umlauts are converted
        assert "Groesse" in words or "groesse" in words
        assert "Muenchen" in words or "muenchen" in words
        assert "schoene" in words or "Schoene" in words

    def test_with_numbers(self, sample_html_with_numbers: str) -> None:
        """Test extraction of words with numbers."""
        config = WordConfig(min_length=3, with_numbers=True)
        extractor = WordExtractor(config)

        words = extractor.extract_from_html(sample_html_with_numbers)

        # Should include words with numbers
        assert "json2xml" in words
        assert "Python3" in words

    def test_without_numbers(self, sample_html_with_numbers: str) -> None:
        """Test extraction excludes words with numbers by default."""
        config = WordConfig(min_length=3, with_numbers=False)
        extractor = WordExtractor(config)

        words = extractor.extract_from_html(sample_html_with_numbers)

        # Should not include words with numbers
        assert "json2xml" not in words
        assert "Python3" not in words
        # But should include pure alpha words
        assert "Version" in words or "version" in words

    def test_word_counting(self, sample_html: str) -> None:
        """Test word frequency counting."""
        config = WordConfig(min_length=3)
        extractor = WordExtractor(config)

        extractor.process_html(sample_html)
        sorted_words = extractor.get_sorted_words()

        # Should be list of (word, count) tuples
        assert len(sorted_words) > 0
        for word, count in sorted_words:
            assert isinstance(word, str)
            assert isinstance(count, int)
            assert count >= 1

    def test_sorted_by_count(self, sample_html: str) -> None:
        """Test that results are sorted by count descending."""
        config = WordConfig(min_length=3)
        extractor = WordExtractor(config)

        # Process same HTML multiple times
        extractor.process_html(sample_html)
        extractor.process_html(sample_html)

        sorted_words = extractor.get_sorted_words()

        # Verify sorted by count descending
        counts = [count for _, count in sorted_words]
        assert counts == sorted(counts, reverse=True)

    def test_meta_description_extracted(self, sample_html: str) -> None:
        """Test that meta description content is extracted."""
        config = WordConfig(min_length=3)
        extractor = WordExtractor(config)

        words = extractor.extract_from_html(sample_html)

        # Words from meta description should be present
        assert "description" in words or "keywords" in words

    def test_alt_and_title_extracted(self, sample_html: str) -> None:
        """Test that alt and title attributes are extracted."""
        config = WordConfig(min_length=3)
        extractor = WordExtractor(config)

        words = extractor.extract_from_html(sample_html)

        # Words from alt attribute
        assert "Alternative" in words
        # Words from title attribute
        assert "Image" in words or "title" in words

    def test_reset(self) -> None:
        """Test counter reset."""
        config = WordConfig(min_length=3)
        extractor = WordExtractor(config)

        extractor.add_words(["test", "word", "test"])
        assert len(extractor.word_counts) > 0

        extractor.reset()
        assert len(extractor.word_counts) == 0

    def test_grouping(self) -> None:
        """Test word grouping by count ranges."""
        config = WordConfig(min_length=3)
        extractor = WordExtractor(config)

        # Add words with varying counts
        extractor.add_words(["high"] * 100)
        extractor.add_words(["medium"] * 50)
        extractor.add_words(["low"] * 10)

        groups = extractor.get_grouped_words(group_size=30)

        assert len(groups) > 0
        # First group should have highest count words
        assert groups[0][0][0] == "high"
