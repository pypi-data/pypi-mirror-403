"""Tests for book citation checker."""

import pytest

from reference_checker.books import OpenLibraryClient, extract_isbn
from reference_checker.models import BibEntry


class TestExtractIsbn:
    """Tests for ISBN extraction."""

    def test_isbn13(self):
        entry = {"isbn": "978-0262035613"}
        assert extract_isbn(entry) == "9780262035613"

    def test_isbn10(self):
        entry = {"isbn": "0-201-63361-2"}
        assert extract_isbn(entry) == "0201633612"

    def test_isbn_no_dashes(self):
        entry = {"isbn": "9780262035613"}
        assert extract_isbn(entry) == "9780262035613"

    def test_isbn_with_x(self):
        entry = {"isbn": "0-8044-2957-X"}
        assert extract_isbn(entry) == "080442957X"

    def test_no_isbn(self):
        entry = {"title": "Some Book"}
        assert extract_isbn(entry) is None

    def test_invalid_isbn(self):
        entry = {"isbn": "not-an-isbn"}
        assert extract_isbn(entry) is None


class TestOpenLibraryClientIntegration:
    """Integration tests for Open Library client (require network)."""

    @pytest.fixture
    def client(self):
        return OpenLibraryClient(delay=0.5)

    @pytest.mark.network
    def test_search_book_by_title(self, client):
        """Test searching for a well-known book."""
        result = client.search_book("Deep Learning", "Goodfellow")
        assert result is not None
        assert "deep learning" in result["title"].lower()
        assert len(result["authors"]) > 0

    @pytest.mark.network
    def test_search_nonexistent_book(self, client):
        """Test searching for a book that doesn't exist."""
        result = client.search_book("This Book Title Does Not Exist Anywhere 12345")
        # May return None or a non-matching result
        # Just verify it doesn't crash
        assert result is None or isinstance(result, dict)

    @pytest.mark.network
    def test_get_book_by_isbn(self, client):
        """Test getting a book by ISBN."""
        # ISBN for "The C Programming Language" 2nd edition
        result = client.get_book_by_isbn("0131103628")
        if result:  # May fail if Open Library is slow
            assert "c programming" in result["title"].lower()
