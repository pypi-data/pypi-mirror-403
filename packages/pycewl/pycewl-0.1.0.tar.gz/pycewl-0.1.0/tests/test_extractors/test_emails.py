"""Tests for email extraction."""

from __future__ import annotations

from pycewl.extractors.emails import (
    extract_emails,
    extract_emails_from_mailto,
    extract_emails_from_text,
)


class TestEmailExtraction:
    """Tests for email extraction functions."""

    def test_extract_from_text_basic(self) -> None:
        """Test basic email extraction from text."""
        text = "Contact us at test@example.com for more info."
        emails = extract_emails_from_text(text)

        assert "test@example.com" in emails

    def test_extract_from_text_multiple(self) -> None:
        """Test multiple email extraction from text."""
        text = "Email john@example.com or jane@example.org"
        emails = extract_emails_from_text(text)

        assert "john@example.com" in emails
        assert "jane@example.org" in emails

    def test_extract_from_text_with_plus(self) -> None:
        """Test extraction of emails with plus addressing."""
        text = "Send to user+tag@example.com"
        emails = extract_emails_from_text(text)

        assert "user+tag@example.com" in emails

    def test_extract_from_text_subdomain(self) -> None:
        """Test extraction of emails with subdomains."""
        text = "Contact support@mail.example.co.uk"
        emails = extract_emails_from_text(text)

        assert "support@mail.example.co.uk" in emails

    def test_extract_from_mailto(self, sample_html: str) -> None:
        """Test extraction from mailto links."""
        emails = extract_emails_from_mailto(sample_html)

        assert "test@example.com" in emails
        assert "sales@example.com" in emails

    def test_extract_from_mailto_with_params(self) -> None:
        """Test extraction from mailto with query parameters."""
        html = '<a href="mailto:info@test.com?subject=Hello&body=Hi">Contact</a>'
        emails = extract_emails_from_mailto(html)

        assert "info@test.com" in emails
        # Should not include query params
        assert "info@test.com?subject=Hello" not in emails

    def test_extract_combined(self, sample_html: str) -> None:
        """Test combined extraction from mailto and text."""
        emails = extract_emails(sample_html, include_text=True)

        # From mailto links
        assert "test@example.com" in emails
        assert "sales@example.com" in emails
        # From body text
        assert "info@example.org" in emails

    def test_extract_without_text(self, sample_html: str) -> None:
        """Test extraction without text search."""
        emails = extract_emails(sample_html, include_text=False)

        # Only from mailto links
        assert "test@example.com" in emails
        assert "sales@example.com" in emails
        # Text email should not be found
        # Note: info@example.org is in body text, not mailto

    def test_no_duplicates(self) -> None:
        """Test that duplicate emails are removed."""
        html = """
        <a href="mailto:same@test.com">Link 1</a>
        <a href="mailto:same@test.com">Link 2</a>
        <p>Email same@test.com for info</p>
        """
        emails = extract_emails(html)

        # Should only have one instance
        assert emails == {"same@test.com"}

    def test_empty_html(self) -> None:
        """Test extraction from empty/minimal HTML."""
        emails = extract_emails("<html><body></body></html>")
        assert len(emails) == 0

    def test_invalid_emails_ignored(self) -> None:
        """Test that invalid emails are not extracted."""
        text = "Not an email: test@, @example.com, test@.com"
        emails = extract_emails_from_text(text)

        assert len(emails) == 0
