# Installation

## Requirements

- Python 3.11 or higher
- pip (Python package installer)

## Basic Installation

Install pycewl from PyPI:

```bash
pip install pycewl
```

## Optional Dependencies

### PDF Metadata Support

To extract metadata from PDF files:

```bash
pip install pycewl[pdf]
```

### Development Tools

For running tests and linting:

```bash
pip install pycewl[dev]
```

### Documentation

For building documentation locally:

```bash
pip install pycewl[docs]
```

### All Optional Dependencies

```bash
pip install pycewl[all]
```

## Development Installation

Clone the repository and install in development mode:

```bash
git clone https://github.com/digininja/CeWL.git
cd CeWL/pycewl
pip install -e ".[dev]"
```

## Verify Installation

```bash
pycewl --version
```

You should see output like:

```
pycewl version 0.1.0
```

## Google Cloud Setup (Optional)

For Google Search integration and relevance scoring, you need to configure Google Cloud.

### Google Custom Search API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the **Custom Search API**
4. Go to **Credentials** and create an **API Key**
5. Set up a [Programmable Search Engine](https://programmablesearchengine.google.com/)
6. Note your Search Engine ID (cx parameter)

Set environment variables:

```bash
export GOOGLE_API_KEY="your-api-key-here"
export GOOGLE_SEARCH_ENGINE_ID="your-search-engine-id"
```

### Google Natural Language API (for relevance scoring)

1. In Google Cloud Console, enable the **Natural Language API**
2. Go to **IAM & Admin** > **Service Accounts**
3. Create a service account with **Cloud Natural Language API User** role
4. Create and download a JSON key for the service account

Set the credentials path:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

## Troubleshooting

### ImportError for lxml

If you get an lxml import error, install the system dependencies:

**Ubuntu/Debian:**
```bash
sudo apt-get install libxml2-dev libxslt-dev python3-dev
pip install lxml
```

**macOS:**
```bash
brew install libxml2 libxslt
pip install lxml
```

### SSL Certificate Errors

pycewl disables SSL verification by default (matching CeWL behavior). If you need strict SSL verification, it's not currently configurable via CLI but can be set in the Python API.
