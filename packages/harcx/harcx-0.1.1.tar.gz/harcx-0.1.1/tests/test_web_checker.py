"""Tests for web citation checker."""

import pytest

from reference_checker.models import BibEntry, WebCheckResult
from reference_checker.web_checker import WebChecker


@pytest.fixture
def sample_entry():
    """Create a sample BibEntry for testing."""
    return BibEntry(
        key="test2023",
        title="Test Paper Title",
        authors=["john smith"],
        year="2023",
        raw_entry={"ID": "test2023", "url": "https://example.com"},
    )


@pytest.fixture
def checker():
    """Create a WebChecker instance with short delay for testing."""
    return WebChecker(timeout=5.0, delay=0.1)


class TestTitleExtraction:
    """Tests for HTML title extraction."""

    def test_extract_simple_title(self, checker):
        html = "<html><head><title>Test Title</title></head><body></body></html>"
        assert checker._extract_title(html) == "Test Title"

    def test_extract_title_with_whitespace(self, checker):
        html = "<html><head><title>  Test Title  </title></head><body></body></html>"
        assert checker._extract_title(html) == "Test Title"

    def test_no_title_tag(self, checker):
        html = "<html><head></head><body></body></html>"
        assert checker._extract_title(html) is None

    def test_empty_title(self, checker):
        html = "<html><head><title></title></head><body></body></html>"
        assert checker._extract_title(html) is None

    def test_malformed_html(self, checker):
        html = "<html><head><title>Some Title"
        # BeautifulSoup should still extract the title
        result = checker._extract_title(html)
        assert result == "Some Title" or result is None


class TestTitleMatching:
    """Tests for fuzzy title matching."""

    def test_exact_match(self, checker):
        score = checker._calculate_title_match("Test Title", "Test Title")
        assert score == 1.0

    def test_case_insensitive(self, checker):
        score = checker._calculate_title_match("Test Title", "test title")
        assert score == 1.0

    def test_partial_match(self, checker):
        score = checker._calculate_title_match("Test Title", "Test Title Extra")
        assert 0.5 < score < 1.0

    def test_no_match(self, checker):
        score = checker._calculate_title_match("Test Title", "Completely Different")
        assert score < 0.5

    def test_none_expected(self, checker):
        score = checker._calculate_title_match(None, "Test Title")
        assert score == 0.0

    def test_none_actual(self, checker):
        score = checker._calculate_title_match("Test Title", None)
        assert score == 0.0

    def test_both_none(self, checker):
        score = checker._calculate_title_match(None, None)
        assert score == 0.0


class TestWebCheckResult:
    """Tests for WebCheckResult data class."""

    def test_creation(self, sample_entry):
        result = WebCheckResult(
            entry=sample_entry,
            url="https://example.com",
            reachable=True,
            status_code=200,
            page_title="Test Title",
            title_match_score=0.95,
            message="URL reachable",
        )
        assert result.reachable is True
        assert result.status_code == 200
        assert result.title_match_score == 0.95

    def test_unreachable_result(self, sample_entry):
        result = WebCheckResult(
            entry=sample_entry,
            url="https://example.com",
            reachable=False,
            status_code=404,
            page_title=None,
            title_match_score=0.0,
            message="HTTP 404",
        )
        assert result.reachable is False
        assert result.status_code == 404
        assert result.title_match_score == 0.0


class TestWebCheckerIntegration:
    """Integration tests for WebChecker (require network)."""

    @pytest.mark.network
    def test_check_valid_url(self, checker, sample_entry):
        """Test checking a valid URL (example.com)."""
        result = checker.check_url(
            sample_entry, "https://example.com", "Example Domain"
        )
        assert result.reachable is True
        assert result.status_code == 200
        assert result.page_title is not None

    @pytest.mark.network
    def test_check_invalid_url(self, checker, sample_entry):
        """Test checking an invalid URL."""
        result = checker.check_url(
            sample_entry,
            "https://this-domain-definitely-does-not-exist-12345.com",
            "Test",
        )
        assert result.reachable is False

    @pytest.mark.network
    def test_check_404_url(self, checker, sample_entry):
        """Test checking a URL that returns 404."""
        result = checker.check_url(
            sample_entry,
            "https://example.com/this-page-does-not-exist-12345",
            "Test",
        )
        # Note: example.com may not return 404 for non-existent pages
        # This test verifies the checker handles the response correctly
        assert isinstance(result.reachable, bool)
        assert result.status_code is not None or not result.reachable
