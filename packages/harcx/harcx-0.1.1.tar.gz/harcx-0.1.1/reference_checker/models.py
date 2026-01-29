"""Data classes for reference checker."""

from dataclasses import dataclass


@dataclass
class BibEntry:
    """Represents a parsed BibTeX entry."""

    key: str  # BibTeX key (e.g., "smith2023")
    title: str
    authors: list[str]  # Parsed author names
    year: str | None
    raw_entry: dict  # Original bibtexparser dict


@dataclass
class CheckResult:
    """Result of checking a single BibTeX entry against Semantic Scholar."""

    entry: BibEntry
    found: bool
    matched_paper: dict | None  # Semantic Scholar paper data if found
    author_match_score: float  # 0.0-1.0 confidence
    message: str  # Human-readable status


@dataclass
class WebCheckResult:
    """Result of checking a URL citation for reachability and title match."""

    entry: BibEntry
    url: str
    reachable: bool
    status_code: int | None  # HTTP status code
    page_title: str | None  # Extracted title from page
    title_match_score: float  # 0.0-1.0 fuzzy match score
    message: str  # Human-readable status
