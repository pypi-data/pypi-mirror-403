"""Reference Checker - Verify .bib file entries against academic databases.

Supports:
- Papers: Semantic Scholar, DBLP (with DOI and arXiv ID lookup)
- Books: Open Library (with ISBN lookup)
- URLs: Reachability and title matching
"""

from .books import OpenLibraryClient, extract_isbn
from .dblp import DBLPClient
from .matcher import calculate_author_match
from .models import BibEntry, CheckResult, WebCheckResult
from .parser import parse_bib_file
from .scholar import ScholarClient, extract_arxiv_id, extract_doi
from .web_checker import WebChecker

__all__ = [
    "check_citations",
    "check_web_citations",
    "BibEntry",
    "CheckResult",
    "WebCheckResult",
]

# Entry types that are considered books
BOOK_TYPES = {"book", "inbook", "incollection", "booklet", "manual"}


def check_citations(
    bib_file: str,
    author_threshold: float = 0.6,
    year_tolerance: int = 1,
    api_key: str | None = None,
    verbose: bool = False,
) -> list[CheckResult]:
    """Check all citations in a .bib file against academic databases.

    Papers are checked against Semantic Scholar and DBLP.
    Books are checked against Open Library.

    Args:
        bib_file: Path to .bib file
        author_threshold: Minimum author match score (0.0-1.0) to consider found
        year_tolerance: Allow this many years difference when matching
        api_key: Optional Semantic Scholar API key for higher rate limits
        verbose: If True, print progress information

    Returns:
        List of CheckResult objects for entries that were NOT found/verified.
    """
    entries = parse_bib_file(bib_file)

    if verbose:
        print(f"Parsed {len(entries)} entries from {bib_file}", flush=True)

    # Initialize clients
    scholar_client = ScholarClient(api_key=api_key)
    dblp_client = DBLPClient()
    book_client = OpenLibraryClient()

    not_found = []

    for i, entry in enumerate(entries):
        if verbose:
            entry_type = entry.raw_entry.get("ENTRYTYPE", "unknown")
            print(f"[{i + 1}/{len(entries)}] Checking ({entry_type}): {entry.key}", flush=True)

        # Route to appropriate checker based on entry type
        entry_type = entry.raw_entry.get("ENTRYTYPE", "").lower()

        if entry_type in BOOK_TYPES:
            result = _check_book_entry(
                entry, book_client, author_threshold, year_tolerance, verbose
            )
        else:
            result = _check_paper_entry(
                entry, scholar_client, dblp_client, author_threshold, year_tolerance, verbose
            )

        if not result.found:
            not_found.append(result)
            if verbose:
                print(f"  ISSUE: {result.message}", flush=True)
        elif verbose:
            print(f"  Found (author match: {result.author_match_score:.2f})", flush=True)

    return not_found


def _check_paper_entry(
    entry: BibEntry,
    scholar_client: ScholarClient,
    dblp_client: DBLPClient,
    author_threshold: float,
    year_tolerance: int,
    verbose: bool = False,
) -> CheckResult:
    """Check a paper entry against Semantic Scholar and DBLP.

    Lookup priority: DOI > arXiv ID > Semantic Scholar title > DBLP title
    """
    paper = None
    lookup_method = None
    source = None

    # Try DOI first (most reliable)
    doi = extract_doi(entry.raw_entry)
    if doi:
        if verbose:
            print(f"    Trying DOI: {doi}", flush=True)
        paper = scholar_client.get_paper_by_doi(doi)
        if paper:
            lookup_method = "DOI"
            source = "Semantic Scholar"

    # Try arXiv ID next
    if paper is None:
        arxiv_id = extract_arxiv_id(entry.raw_entry)
        if arxiv_id:
            if verbose:
                print(f"    Trying arXiv ID: {arxiv_id}", flush=True)
            paper = scholar_client.get_paper_by_arxiv_id(arxiv_id)
            if paper:
                lookup_method = "arXiv"
                source = "Semantic Scholar"

    # Try Semantic Scholar title search
    if paper is None:
        if verbose:
            print("    Trying Semantic Scholar title search", flush=True)
        paper = scholar_client.search_paper(entry.title, entry.year)
        if paper:
            lookup_method = "title search"
            source = "Semantic Scholar"

    # Fall back to DBLP
    if paper is None:
        if verbose:
            print("    Trying DBLP title search", flush=True)
        paper = dblp_client.search_paper(entry.title)
        if paper:
            lookup_method = "title search"
            source = "DBLP"

    if paper is None:
        arxiv_id = extract_arxiv_id(entry.raw_entry)
        if arxiv_id:
            return CheckResult(
                entry=entry,
                found=False,
                matched_paper=None,
                author_match_score=0.0,
                message=f"Not found in databases. Has arXiv ID {arxiv_id} - verify at https://arxiv.org/abs/{arxiv_id}",
            )
        return CheckResult(
            entry=entry,
            found=False,
            matched_paper=None,
            author_match_score=0.0,
            message="Not found in Semantic Scholar or DBLP",
        )

    return _validate_result(entry, paper, source, lookup_method, author_threshold, year_tolerance)


def _check_book_entry(
    entry: BibEntry,
    book_client: OpenLibraryClient,
    author_threshold: float,
    year_tolerance: int,
    verbose: bool = False,
) -> CheckResult:
    """Check a book entry against Open Library.

    Lookup priority: ISBN > title search
    """
    book = None
    lookup_method = None
    source = "Open Library"

    # Try ISBN first (most reliable)
    isbn = extract_isbn(entry.raw_entry)
    if isbn:
        if verbose:
            print(f"    Trying ISBN: {isbn}", flush=True)
        book = book_client.get_book_by_isbn(isbn)
        if book:
            lookup_method = "ISBN"

    # Fall back to title search
    if book is None:
        if verbose:
            print("    Trying Open Library title search", flush=True)
        # Use first author if available to improve search
        first_author = entry.authors[0] if entry.authors else None
        book = book_client.search_book(entry.title, first_author)
        if book:
            lookup_method = "title search"

    if book is None:
        isbn = extract_isbn(entry.raw_entry)
        if isbn:
            return CheckResult(
                entry=entry,
                found=False,
                matched_paper=None,
                author_match_score=0.0,
                message=f"Not found in Open Library. Has ISBN {isbn} - verify manually",
            )
        return CheckResult(
            entry=entry,
            found=False,
            matched_paper=None,
            author_match_score=0.0,
            message="Not found in Open Library",
        )

    return _validate_result(entry, book, source, lookup_method, author_threshold, year_tolerance)


def _validate_result(
    entry: BibEntry,
    found_item: dict,
    source: str,
    lookup_method: str,
    author_threshold: float,
    year_tolerance: int,
) -> CheckResult:
    """Validate a found result against the bib entry."""
    item_authors = found_item.get("authors", [])
    author_score = calculate_author_match(entry.authors, item_authors)

    # Check year if available
    year_match = True
    if entry.year and found_item.get("year"):
        try:
            bib_year = int(entry.year)
            found_year = int(found_item["year"])
            year_match = abs(bib_year - found_year) <= year_tolerance
        except (ValueError, TypeError):
            year_match = True  # Can't compare, assume match

    if author_score < author_threshold:
        found_authors = ", ".join(item_authors[:3])
        if len(item_authors) > 3:
            found_authors += f" (+{len(item_authors) - 3} more)"
        return CheckResult(
            entry=entry,
            found=False,
            matched_paper=found_item,
            author_match_score=author_score,
            message=f"Title exists on {source} but authors don't match. Found: [{found_authors}]. Please verify.",
        )

    if not year_match:
        return CheckResult(
            entry=entry,
            found=False,
            matched_paper=found_item,
            author_match_score=author_score,
            message=f"Title exists on {source} but year mismatch (bib: {entry.year}, found: {found_item.get('year')}). Please verify.",
        )

    return CheckResult(
        entry=entry,
        found=True,
        matched_paper=found_item,
        author_match_score=author_score,
        message=f"Found via {lookup_method} on {source}",
    )


def check_web_citations(
    bib_file: str,
    title_threshold: float = 0.6,
    verbose: bool = False,
) -> list[WebCheckResult]:
    """Check URL citations in a .bib file for reachability and title match.

    Args:
        bib_file: Path to .bib file
        title_threshold: Minimum title match score (0.0-1.0) to consider valid
        verbose: If True, print progress information

    Returns:
        List of WebCheckResult objects for entries with URL issues.
    """
    entries = parse_bib_file(bib_file)

    entries_with_urls = [
        entry for entry in entries if entry.raw_entry.get("url")
    ]

    if verbose:
        print(
            f"Found {len(entries_with_urls)} entries with URLs out of {len(entries)} total",
            flush=True,
        )

    if not entries_with_urls:
        return []

    checker = WebChecker()
    issues = []

    for i, entry in enumerate(entries_with_urls):
        url = entry.raw_entry.get("url", "")

        if verbose:
            print(f"[{i + 1}/{len(entries_with_urls)}] Checking URL: {entry.key}", flush=True)

        result = checker.check_url(entry, url, entry.title)

        if not result.reachable:
            issues.append(result)
            if verbose:
                print(f"  UNREACHABLE: {result.message}", flush=True)
        elif result.title_match_score < title_threshold:
            issues.append(result)
            if verbose:
                print(f"  TITLE MISMATCH: score {result.title_match_score:.2f}", flush=True)
        elif verbose:
            print(f"  OK (title match: {result.title_match_score:.2f})", flush=True)

    return issues
