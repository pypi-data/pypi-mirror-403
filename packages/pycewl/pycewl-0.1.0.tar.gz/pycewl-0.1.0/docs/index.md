# pycewl

**Python async re-implementation of CeWL (Custom Word List Generator)**

pycewl is a modern, high-performance Python tool for generating custom wordlists by spidering websites. It's a complete re-implementation of the original [CeWL](https://github.com/digininja/CeWL) Ruby tool with additional features.

## Features

- **Async Spider**: High-performance crawling with configurable concurrency
- **Word Extraction**: Extract words from HTML content with flexible filtering
- **Email Extraction**: Find email addresses in mailto links and page content
- **Metadata Extraction**: Extract author names from PDF and Office documents
- **Google Search Integration**: Use Google to discover seed URLs
- **Smart Relevance Scoring**: Group words by relevance using Google NLP

## Quick Example

```bash
# Basic usage
pycewl https://example.com -w words.txt

# With word counts and email extraction
pycewl https://example.com -c -e --email-file emails.txt -w words.txt

# Google search with relevance scoring
pycewl --google-keyword "star trek" --relevance-scoring \
    --related-file related.txt --unrelated-file general.txt
```

## Why pycewl?

| Feature | CeWL (Ruby) | pycewl |
|---------|-------------|--------|
| Async requests | No | Yes |
| Concurrent connections | Limited | Configurable (default 10) |
| Google Search | No | Yes |
| Relevance scoring | No | Yes (via Google NLP) |
| Type hints | N/A | Full coverage |
| Modern packaging | Gem | PyPI/pip |

## Getting Started

Check out the [Installation](installation.md) guide to get started, then head to [Usage](usage.md) for examples.
