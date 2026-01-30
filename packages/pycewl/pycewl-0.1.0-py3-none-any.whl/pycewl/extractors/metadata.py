"""Document metadata extraction for pycewl."""

from __future__ import annotations

import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DocumentMetadata:
    """Metadata extracted from a document."""

    filename: str
    authors: list[str] = field(default_factory=list)
    creators: list[str] = field(default_factory=list)
    producers: list[str] = field(default_factory=list)
    last_modified_by: list[str] = field(default_factory=list)
    title: str | None = None
    subject: str | None = None
    keywords: list[str] = field(default_factory=list)

    @property
    def all_names(self) -> set[str]:
        """Get all person names found in metadata."""
        names: set[str] = set()
        names.update(self.authors)
        names.update(self.creators)
        names.update(self.last_modified_by)
        return {n for n in names if n and n.strip()}


def extract_pdf_metadata(content: bytes) -> DocumentMetadata:
    """Extract metadata from PDF content.

    Uses regex patterns matching CeWL's PDF extraction.

    Args:
        content: PDF file content.

    Returns:
        DocumentMetadata with extracted information.
    """
    metadata = DocumentMetadata(filename="")

    # Convert bytes to string for regex searching
    # PDF metadata is often in ASCII/Latin-1
    try:
        text = content.decode("latin-1", errors="ignore")
    except Exception:
        return metadata

    # Look for /Author field
    author_match = re.search(r"/Author\s*\(([^)]+)\)", text)
    if author_match:
        metadata.authors.append(author_match.group(1).strip())

    # Look for /Creator field
    creator_match = re.search(r"/Creator\s*\(([^)]+)\)", text)
    if creator_match:
        metadata.creators.append(creator_match.group(1).strip())

    # Look for /Producer field
    producer_match = re.search(r"/Producer\s*\(([^)]+)\)", text)
    if producer_match:
        metadata.producers.append(producer_match.group(1).strip())

    # Look for /Title field
    title_match = re.search(r"/Title\s*\(([^)]+)\)", text)
    if title_match:
        metadata.title = title_match.group(1).strip()

    # Look for /Subject field
    subject_match = re.search(r"/Subject\s*\(([^)]+)\)", text)
    if subject_match:
        metadata.subject = subject_match.group(1).strip()

    # Look for /Keywords field
    keywords_match = re.search(r"/Keywords\s*\(([^)]+)\)", text)
    if keywords_match:
        keywords = keywords_match.group(1).strip()
        metadata.keywords = [k.strip() for k in keywords.split(",") if k.strip()]

    return metadata


def extract_office_xml_metadata(content: bytes) -> DocumentMetadata:
    """Extract metadata from Office 2007+ documents (DOCX, XLSX, PPTX).

    These are ZIP files with XML metadata in docProps/core.xml.

    Args:
        content: Office document content.

    Returns:
        DocumentMetadata with extracted information.
    """
    metadata = DocumentMetadata(filename="")

    try:
        # Write to temp file for zipfile
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)

        try:
            with zipfile.ZipFile(tmp_path, "r") as zf:
                # Try to read core.xml
                if "docProps/core.xml" in zf.namelist():
                    core_xml = zf.read("docProps/core.xml")
                    metadata = _parse_core_xml(core_xml, metadata)

                # Try to read app.xml for additional info
                if "docProps/app.xml" in zf.namelist():
                    app_xml = zf.read("docProps/app.xml")
                    metadata = _parse_app_xml(app_xml, metadata)

        finally:
            tmp_path.unlink(missing_ok=True)

    except (zipfile.BadZipFile, OSError):
        pass

    return metadata


def _parse_core_xml(xml_content: bytes, metadata: DocumentMetadata) -> DocumentMetadata:
    """Parse docProps/core.xml for metadata.

    Args:
        xml_content: XML content.
        metadata: Existing metadata to update.

    Returns:
        Updated DocumentMetadata.
    """
    # Define namespaces
    namespaces = {
        "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
        "dc": "http://purl.org/dc/elements/1.1/",
        "dcterms": "http://purl.org/dc/terms/",
    }

    try:
        root = ET.fromstring(xml_content)

        # dc:creator (author)
        creator = root.find("dc:creator", namespaces)
        if creator is not None and creator.text:
            metadata.authors.append(creator.text.strip())

        # cp:lastModifiedBy
        last_mod = root.find("cp:lastModifiedBy", namespaces)
        if last_mod is not None and last_mod.text:
            metadata.last_modified_by.append(last_mod.text.strip())

        # dc:title
        title = root.find("dc:title", namespaces)
        if title is not None and title.text:
            metadata.title = title.text.strip()

        # dc:subject
        subject = root.find("dc:subject", namespaces)
        if subject is not None and subject.text:
            metadata.subject = subject.text.strip()

        # cp:keywords
        keywords = root.find("cp:keywords", namespaces)
        if keywords is not None and keywords.text:
            metadata.keywords = [k.strip() for k in keywords.text.split(",") if k.strip()]

    except ET.ParseError:
        pass

    return metadata


def _parse_app_xml(xml_content: bytes, metadata: DocumentMetadata) -> DocumentMetadata:
    """Parse docProps/app.xml for additional metadata.

    Args:
        xml_content: XML content.
        metadata: Existing metadata to update.

    Returns:
        Updated DocumentMetadata.
    """
    namespace = "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"

    try:
        root = ET.fromstring(xml_content)

        # Application
        app = root.find(f"{{{namespace}}}Application")
        if app is not None and app.text:
            metadata.producers.append(app.text.strip())

    except ET.ParseError:
        pass

    return metadata


def extract_office_legacy_metadata(_content: bytes, filepath: Path) -> DocumentMetadata:
    """Extract metadata from Office 2003 documents using exiftool.

    Falls back to exiftool subprocess for legacy Office formats.

    Args:
        _content: Document content (unused, kept for API compatibility).
        filepath: Path to the document file.

    Returns:
        DocumentMetadata with extracted information.
    """
    metadata = DocumentMetadata(filename=filepath.name)

    try:
        # Try to use exiftool
        result = subprocess.run(
            ["exiftool", "-Author", "-Creator", "-LastModifiedBy", "-j", str(filepath)],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            import json

            data = json.loads(result.stdout)
            if data and isinstance(data, list) and len(data) > 0:
                doc = data[0]

                if "Author" in doc:
                    metadata.authors.append(str(doc["Author"]))
                if "Creator" in doc:
                    metadata.creators.append(str(doc["Creator"]))
                if "LastModifiedBy" in doc:
                    metadata.last_modified_by.append(str(doc["LastModifiedBy"]))

    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    return metadata


def extract_metadata(content: bytes, filename: str) -> DocumentMetadata:
    """Extract metadata from a document based on its type.

    Args:
        content: Document content.
        filename: Filename for type detection.

    Returns:
        DocumentMetadata with extracted information.
    """
    lower_name = filename.lower()

    if lower_name.endswith(".pdf"):
        metadata = extract_pdf_metadata(content)
    elif lower_name.endswith((".docx", ".xlsx", ".pptx", ".odt", ".ods", ".odp")):
        metadata = extract_office_xml_metadata(content)
    elif lower_name.endswith((".doc", ".xls", ".ppt")):
        # Legacy Office - need to save to temp file for exiftool
        with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix, delete=False) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)

        try:
            metadata = extract_office_legacy_metadata(content, tmp_path)
        finally:
            tmp_path.unlink(missing_ok=True)
    else:
        metadata = DocumentMetadata(filename=filename)

    metadata.filename = filename
    return metadata
