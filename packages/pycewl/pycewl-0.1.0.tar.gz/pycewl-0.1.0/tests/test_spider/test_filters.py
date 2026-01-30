"""Tests for URL filtering."""

from __future__ import annotations

from pycewl.config import SpiderConfig
from pycewl.spider.filters import URLFilter, extract_links


class TestURLFilter:
    """Tests for URLFilter class."""

    def test_normalize_absolute_url(self) -> None:
        """Test normalization of absolute URL."""
        config = SpiderConfig()
        filter_ = URLFilter(config, "https://example.com")

        result = filter_.normalize("https://example.com/page")

        assert result == "https://example.com/page"

    def test_normalize_relative_url(self) -> None:
        """Test normalization of relative URL."""
        config = SpiderConfig()
        filter_ = URLFilter(config, "https://example.com")

        result = filter_.normalize("/about", "https://example.com/page")

        assert result == "https://example.com/about"

    def test_normalize_javascript_url(self) -> None:
        """Test that javascript URLs are rejected."""
        config = SpiderConfig()
        filter_ = URLFilter(config, "https://example.com")

        result = filter_.normalize("javascript:void(0)")

        assert result is None

    def test_normalize_data_url(self) -> None:
        """Test that data URLs are rejected."""
        config = SpiderConfig()
        filter_ = URLFilter(config, "https://example.com")

        result = filter_.normalize("data:text/html,<h1>Test</h1>")

        assert result is None

    def test_normalize_mailto(self) -> None:
        """Test that mailto URLs are preserved."""
        config = SpiderConfig()
        filter_ = URLFilter(config, "https://example.com")

        result = filter_.normalize("mailto:test@example.com")

        assert result == "mailto:test@example.com"

    def test_should_crawl_same_domain(self) -> None:
        """Test crawling allowed for same domain."""
        config = SpiderConfig(offsite=False)
        filter_ = URLFilter(config, "https://example.com")

        assert filter_.should_crawl("https://example.com/page") is True

    def test_should_crawl_different_domain_blocked(self) -> None:
        """Test crawling blocked for different domain."""
        config = SpiderConfig(offsite=False)
        filter_ = URLFilter(config, "https://example.com")

        assert filter_.should_crawl("https://other.com/page") is False

    def test_should_crawl_offsite_allowed(self) -> None:
        """Test crawling allowed for different domain when offsite enabled."""
        config = SpiderConfig(offsite=True)
        filter_ = URLFilter(config, "https://example.com")

        assert filter_.should_crawl("https://other.com/page") is True

    def test_should_crawl_excluded_path(self) -> None:
        """Test crawling blocked for excluded paths."""
        config = SpiderConfig(exclude_paths=("/admin", "/private"))
        filter_ = URLFilter(config, "https://example.com")

        assert filter_.should_crawl("https://example.com/admin/users") is False
        assert filter_.should_crawl("https://example.com/private/data") is False
        assert filter_.should_crawl("https://example.com/public") is True

    def test_should_crawl_image_extension(self) -> None:
        """Test that image URLs are skipped."""
        config = SpiderConfig()
        filter_ = URLFilter(config, "https://example.com")

        assert filter_.should_crawl("https://example.com/image.jpg") is False
        assert filter_.should_crawl("https://example.com/image.PNG") is False
        assert filter_.should_crawl("https://example.com/image.gif") is False

    def test_should_crawl_css_js_extensions(self) -> None:
        """Test that CSS/JS files are skipped."""
        config = SpiderConfig()
        filter_ = URLFilter(config, "https://example.com")

        assert filter_.should_crawl("https://example.com/style.css") is False
        assert filter_.should_crawl("https://example.com/script.js") is False

    def test_should_crawl_allowed_pattern(self) -> None:
        """Test URL allowed pattern matching."""
        config = SpiderConfig(allowed_pattern=r"/blog/")
        filter_ = URLFilter(config, "https://example.com")

        assert filter_.should_crawl("https://example.com/blog/post") is True
        assert filter_.should_crawl("https://example.com/about") is False

    def test_is_document_pdf(self) -> None:
        """Test document detection for PDF."""
        config = SpiderConfig()
        filter_ = URLFilter(config, "https://example.com")

        assert filter_.is_document("https://example.com/file.pdf") is True
        assert filter_.is_document("https://example.com/file.PDF") is True

    def test_is_document_office(self) -> None:
        """Test document detection for Office files."""
        config = SpiderConfig()
        filter_ = URLFilter(config, "https://example.com")

        assert filter_.is_document("https://example.com/file.docx") is True
        assert filter_.is_document("https://example.com/file.xlsx") is True
        assert filter_.is_document("https://example.com/file.pptx") is True

    def test_is_document_html(self) -> None:
        """Test that HTML is not detected as document."""
        config = SpiderConfig()
        filter_ = URLFilter(config, "https://example.com")

        assert filter_.is_document("https://example.com/page.html") is False


class TestExtractLinks:
    """Tests for link extraction function."""

    def test_extract_links_basic(self, sample_html: str) -> None:
        """Test basic link extraction."""
        links = extract_links(sample_html, "https://example.com")

        assert "/about" in links
        assert "https://external.com/page" in links

    def test_extract_mailto_links(self, sample_html: str) -> None:
        """Test mailto link extraction."""
        links = extract_links(sample_html, "https://example.com")

        assert "mailto:test@example.com" in links
        assert "mailto:sales@example.com?subject=Hello" in links

    def test_extract_empty_html(self) -> None:
        """Test extraction from empty HTML."""
        links = extract_links("<html><body></body></html>", "https://example.com")

        assert links == []

    def test_extract_no_href(self) -> None:
        """Test extraction from anchor without href."""
        html = '<a name="anchor">Anchor</a>'
        links = extract_links(html, "https://example.com")

        assert links == []
