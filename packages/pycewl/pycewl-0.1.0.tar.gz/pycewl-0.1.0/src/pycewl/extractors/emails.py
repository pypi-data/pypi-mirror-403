"""Email extraction for pycewl."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

# Email regex pattern matching CeWL's pattern
EMAIL_PATTERN = re.compile(
    r"\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})\b",
    re.IGNORECASE,
)


def extract_emails_from_text(text: str) -> set[str]:
    """Extract email addresses from text.

    Args:
        text: Text content to search.

    Returns:
        Set of unique email addresses.
    """
    return set(EMAIL_PATTERN.findall(text))


def extract_emails_from_mailto(html_content: str) -> set[str]:
    """Extract email addresses from mailto links.

    Args:
        html_content: HTML content to parse.

    Returns:
        Set of unique email addresses from mailto links.
    """
    soup = BeautifulSoup(html_content, "lxml")
    emails: set[str] = set()

    for link in soup.find_all("a", href=True):
        href = link.get("href")
        if href and isinstance(href, str) and href.startswith("mailto:"):
            # Extract email, removing any query parameters
            email = href.replace("mailto:", "").split("?")[0].strip()
            if email and "@" in email:
                emails.add(email.lower())

    return emails


def extract_emails(html_content: str, include_text: bool = True) -> set[str]:
    """Extract all email addresses from HTML.

    Args:
        html_content: HTML content to parse.
        include_text: Whether to also search body text for emails.

    Returns:
        Set of unique email addresses.
    """
    emails: set[str] = set()

    # Extract from mailto links
    emails.update(extract_emails_from_mailto(html_content))

    # Extract from body text if requested
    if include_text:
        soup = BeautifulSoup(html_content, "lxml")
        body = soup.find("body")
        if body:
            text = body.get_text()
            emails.update(extract_emails_from_text(text))

    return emails
