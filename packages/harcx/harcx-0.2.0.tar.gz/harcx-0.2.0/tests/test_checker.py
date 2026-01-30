"""Tests for reference checker."""

import tempfile
from pathlib import Path

import pytest

from reference_checker.matcher import (
    calculate_author_match,
    names_match,
    normalize_author_name,
)
from reference_checker.models import BibEntry
from reference_checker.parser import parse_authors, parse_bib_file


class TestNormalizeAuthorName:
    """Tests for author name normalization."""

    def test_last_first_format(self):
        assert normalize_author_name("Smith, John") == "john smith"

    def test_first_last_format(self):
        assert normalize_author_name("John Smith") == "john smith"

    def test_initials(self):
        assert normalize_author_name("J. Smith") == "j. smith"

    def test_braces(self):
        assert normalize_author_name("{van der Berg}, Jan") == "jan van der berg"

    def test_extra_whitespace(self):
        assert normalize_author_name("  John   Smith  ") == "john smith"


class TestParseAuthors:
    """Tests for BibTeX author string parsing."""

    def test_single_author(self):
        assert parse_authors("John Smith") == ["john smith"]

    def test_multiple_authors(self):
        result = parse_authors("John Smith and Jane Doe")
        assert result == ["john smith", "jane doe"]

    def test_multiple_authors_last_first(self):
        result = parse_authors("Smith, John and Doe, Jane")
        assert result == ["john smith", "jane doe"]

    def test_empty_string(self):
        assert parse_authors("") == []

    def test_three_authors(self):
        result = parse_authors("Alice Brown and Bob White and Carol Green")
        assert result == ["alice brown", "bob white", "carol green"]


class TestNamesMatch:
    """Tests for fuzzy name matching."""

    def test_exact_match(self):
        assert names_match("john smith", "john smith")

    def test_initial_vs_full(self):
        assert names_match("j smith", "john smith")

    def test_different_names(self):
        assert not names_match("john smith", "jane doe")

    def test_same_last_different_first(self):
        assert not names_match("john smith", "jane smith")


class TestCalculateAuthorMatch:
    """Tests for author list matching."""

    def test_perfect_match(self):
        bib = ["john smith", "jane doe"]
        paper = ["John Smith", "Jane Doe"]
        assert calculate_author_match(bib, paper) == 1.0

    def test_partial_match(self):
        bib = ["john smith", "jane doe"]
        paper = ["John Smith", "Bob Brown"]
        assert calculate_author_match(bib, paper) == 0.5

    def test_no_match(self):
        bib = ["john smith"]
        paper = ["Jane Doe"]
        assert calculate_author_match(bib, paper) == 0.0

    def test_empty_lists(self):
        assert calculate_author_match([], ["John Smith"]) == 0.0
        assert calculate_author_match(["john smith"], []) == 0.0

    def test_initials_match(self):
        bib = ["j smith"]
        paper = ["John Smith"]
        score = calculate_author_match(bib, paper)
        assert score > 0.5


class TestParseBibFile:
    """Tests for BibTeX file parsing."""

    def test_parse_simple_entry(self):
        bib_content = """
@article{smith2023,
    author = {Smith, John and Doe, Jane},
    title = {A Sample Paper Title},
    year = {2023},
    journal = {Sample Journal}
}
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".bib", delete=False
        ) as f:
            f.write(bib_content)
            f.flush()

            entries = parse_bib_file(f.name)

            assert len(entries) == 1
            entry = entries[0]
            assert entry.key == "smith2023"
            assert entry.title == "A Sample Paper Title"
            assert entry.authors == ["john smith", "jane doe"]
            assert entry.year == "2023"

            Path(f.name).unlink()

    def test_parse_multiple_entries(self):
        bib_content = """
@article{paper1,
    author = {Author One},
    title = {First Paper},
    year = {2021}
}

@inproceedings{paper2,
    author = {Author Two},
    title = {Second Paper},
    year = {2022}
}
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".bib", delete=False
        ) as f:
            f.write(bib_content)
            f.flush()

            entries = parse_bib_file(f.name)

            assert len(entries) == 2
            assert entries[0].key == "paper1"
            assert entries[1].key == "paper2"

            Path(f.name).unlink()


class TestBibEntry:
    """Tests for BibEntry data class."""

    def test_creation(self):
        entry = BibEntry(
            key="test2023",
            title="Test Title",
            authors=["john smith"],
            year="2023",
            raw_entry={"ID": "test2023"},
        )
        assert entry.key == "test2023"
        assert entry.title == "Test Title"
        assert entry.authors == ["john smith"]
        assert entry.year == "2023"
