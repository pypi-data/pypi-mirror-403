"""Pytest fixtures for pycewl tests."""

from __future__ import annotations

import pytest


@pytest.fixture
def sample_html() -> str:
    """Sample HTML content for testing."""
    return """<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
    <meta name="description" content="This is a test description with keywords">
    <meta name="keywords" content="test, sample, example">
    <style>
        .hidden { display: none; }
    </style>
    <script>
        var hidden = "should not appear";
    </script>
</head>
<body>
    <h1>Welcome to the Test Page</h1>
    <p>This is a paragraph with some <strong>important</strong> words.</p>
    <p>Contact us at <a href="mailto:test@example.com">test@example.com</a></p>
    <p>Another email: info@example.org</p>
    <img src="image.png" alt="Alternative text here" title="Image title">
    <a href="/about">About Us</a>
    <a href="https://external.com/page">External Link</a>
    <a href="mailto:sales@example.com?subject=Hello">Sales Contact</a>
</body>
</html>"""


@pytest.fixture
def sample_html_german() -> str:
    """Sample HTML with German umlauts."""
    return """<!DOCTYPE html>
<html>
<body>
    <h1>Willkommen auf der Webseite</h1>
    <p>Die Größe der Öffnung ist größer als erwartet.</p>
    <p>München, Düsseldorf und Nürnberg sind schöne Städte.</p>
</body>
</html>"""


@pytest.fixture
def sample_html_with_numbers() -> str:
    """Sample HTML with words containing numbers."""
    return """<!DOCTYPE html>
<html>
<body>
    <p>Version 2.0 was released in 2024.</p>
    <p>The API returns json2xml format.</p>
    <p>Use Python3 for best results.</p>
</body>
</html>"""


@pytest.fixture
def sample_pdf_metadata() -> bytes:
    """Sample PDF-like content with metadata patterns."""
    return b"""%PDF-1.4
/Author (John Smith)
/Creator (Microsoft Word)
/Producer (Adobe PDF Library)
/Title (Sample Document)
/Subject (Test Subject)
/Keywords (test, pdf, sample)
endobj"""
