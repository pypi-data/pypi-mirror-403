"""Tests for metadata extraction."""

from __future__ import annotations

from pycewl.extractors.metadata import (
    DocumentMetadata,
    extract_pdf_metadata,
)


class TestPDFMetadataExtraction:
    """Tests for PDF metadata extraction."""

    def test_extract_author(self, sample_pdf_metadata: bytes) -> None:
        """Test extraction of author from PDF."""
        metadata = extract_pdf_metadata(sample_pdf_metadata)

        assert "John Smith" in metadata.authors

    def test_extract_creator(self, sample_pdf_metadata: bytes) -> None:
        """Test extraction of creator from PDF."""
        metadata = extract_pdf_metadata(sample_pdf_metadata)

        assert "Microsoft Word" in metadata.creators

    def test_extract_producer(self, sample_pdf_metadata: bytes) -> None:
        """Test extraction of producer from PDF."""
        metadata = extract_pdf_metadata(sample_pdf_metadata)

        assert "Adobe PDF Library" in metadata.producers

    def test_extract_title(self, sample_pdf_metadata: bytes) -> None:
        """Test extraction of title from PDF."""
        metadata = extract_pdf_metadata(sample_pdf_metadata)

        assert metadata.title == "Sample Document"

    def test_extract_subject(self, sample_pdf_metadata: bytes) -> None:
        """Test extraction of subject from PDF."""
        metadata = extract_pdf_metadata(sample_pdf_metadata)

        assert metadata.subject == "Test Subject"

    def test_all_names_property(self, sample_pdf_metadata: bytes) -> None:
        """Test all_names property aggregation."""
        metadata = extract_pdf_metadata(sample_pdf_metadata)

        names = metadata.all_names
        assert "John Smith" in names

    def test_empty_pdf(self) -> None:
        """Test extraction from PDF without metadata."""
        metadata = extract_pdf_metadata(b"%PDF-1.4\nendobj")

        assert len(metadata.authors) == 0
        assert len(metadata.creators) == 0
        assert metadata.title is None


class TestDocumentMetadata:
    """Tests for DocumentMetadata dataclass."""

    def test_all_names_combines_sources(self) -> None:
        """Test that all_names combines all name sources."""
        metadata = DocumentMetadata(
            filename="test.pdf",
            authors=["Author One"],
            creators=["Creator Two"],
            last_modified_by=["Modifier Three"],
        )

        names = metadata.all_names
        assert "Author One" in names
        assert "Creator Two" in names
        assert "Modifier Three" in names

    def test_all_names_removes_empty(self) -> None:
        """Test that all_names filters empty strings."""
        metadata = DocumentMetadata(
            filename="test.pdf",
            authors=["Valid Name", "", "  "],
        )

        names = metadata.all_names
        assert "Valid Name" in names
        assert "" not in names

    def test_all_names_deduplicates(self) -> None:
        """Test that all_names removes duplicates."""
        metadata = DocumentMetadata(
            filename="test.pdf",
            authors=["Same Name"],
            creators=["Same Name"],
        )

        names = metadata.all_names
        assert len([n for n in names if n == "Same Name"]) == 1
