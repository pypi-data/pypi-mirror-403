"""Semantic Scholar API wrapper."""

import re
import time
from typing import Any

import httpx

BASE_URL = "https://api.semanticscholar.org/graph/v1"

# Fields to request from Semantic Scholar API
PAPER_FIELDS = "title,authors,year,paperId,citationCount"


def extract_arxiv_id(entry: dict) -> str | None:
    """Extract arXiv ID from a bib entry.

    Looks for:
    - eprint field (e.g., "2410.11287")
    - arXiv ID in URL (e.g., "https://arxiv.org/abs/2410.11287")

    Args:
        entry: Raw bib entry dict

    Returns:
        arXiv ID string or None
    """
    # Check eprint field first
    eprint = entry.get("eprint", "")
    if eprint and entry.get("archiveprefix", "").lower() == "arxiv":
        return eprint

    # Try to extract from URL
    url = entry.get("url", "")
    if "arxiv.org" in url:
        # Match patterns like arxiv.org/abs/2410.11287 or arxiv.org/pdf/2410.11287
        match = re.search(r"arxiv\.org/(?:abs|pdf)/(\d+\.\d+)", url)
        if match:
            return match.group(1)

    return None


def extract_doi(entry: dict) -> str | None:
    """Extract DOI from a bib entry.

    Args:
        entry: Raw bib entry dict

    Returns:
        DOI string or None
    """
    return entry.get("doi")


class ScholarClient:
    """Client for Semantic Scholar API with rate limiting."""

    def __init__(self, api_key: str | None = None, delay: float = 3.0, timeout: float = 10.0):
        """Initialize the Semantic Scholar client.

        Args:
            api_key: Optional API key for higher rate limits
            delay: Delay between API calls in seconds
            timeout: Request timeout in seconds
        """
        headers = {}
        if api_key:
            headers["x-api-key"] = api_key
        self.client = httpx.Client(headers=headers, timeout=timeout)
        self.delay = delay
        self._last_call = 0.0

    def _rate_limit(self) -> None:
        """Ensure minimum delay between API calls."""
        elapsed = time.time() - self._last_call
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self._last_call = time.time()

    def _parse_paper_response(self, paper: dict) -> dict[str, Any]:
        """Parse a paper response into a standardized format."""
        return {
            "paperId": paper.get("paperId"),
            "title": paper.get("title"),
            "authors": [a.get("name", "") for a in paper.get("authors", []) if a.get("name")],
            "year": paper.get("year"),
            "citationCount": paper.get("citationCount"),
        }

    def get_paper_by_arxiv_id(self, arxiv_id: str, max_retries: int = 3) -> dict[str, Any] | None:
        """Get paper by arXiv ID.

        Args:
            arxiv_id: arXiv ID (e.g., "2410.11287")
            max_retries: Maximum number of retries

        Returns:
            Paper dict or None if not found
        """
        for attempt in range(max_retries):
            self._rate_limit()

            try:
                response = self.client.get(
                    f"{BASE_URL}/paper/ARXIV:{arxiv_id}",
                    params={"fields": PAPER_FIELDS},
                )

                if response.status_code == 404:
                    return None

                if response.status_code == 429:
                    wait_time = (2 ** attempt) * 5
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                return self._parse_paper_response(response.json())

            except httpx.HTTPStatusError:
                if attempt < max_retries - 1:
                    time.sleep((2 ** attempt) * 2)
                    continue
                return None
            except Exception:
                return None

        return None

    def get_paper_by_doi(self, doi: str, max_retries: int = 3) -> dict[str, Any] | None:
        """Get paper by DOI.

        Args:
            doi: DOI string (e.g., "10.1038/nature12373")
            max_retries: Maximum number of retries

        Returns:
            Paper dict or None if not found
        """
        for attempt in range(max_retries):
            self._rate_limit()

            try:
                response = self.client.get(
                    f"{BASE_URL}/paper/DOI:{doi}",
                    params={"fields": PAPER_FIELDS},
                )

                if response.status_code == 404:
                    return None

                if response.status_code == 429:
                    wait_time = (2 ** attempt) * 5
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                return self._parse_paper_response(response.json())

            except httpx.HTTPStatusError:
                if attempt < max_retries - 1:
                    time.sleep((2 ** attempt) * 2)
                    continue
                return None
            except Exception:
                return None

        return None

    def search_paper(self, title: str, year: str | None = None, max_retries: int = 3) -> dict[str, Any] | None:
        """Search Semantic Scholar for paper by title.

        Args:
            title: Paper title to search for
            year: Optional year to help with matching
            max_retries: Maximum number of retries on rate limit

        Returns:
            Paper dict with title, authors, year, paperId or None if not found
        """
        query = title
        if year:
            query = f"{title} {year}"

        for attempt in range(max_retries):
            self._rate_limit()

            try:
                response = self.client.get(
                    f"{BASE_URL}/paper/search",
                    params={
                        "query": query,
                        "limit": 1,
                        "fields": PAPER_FIELDS,
                    },
                )

                # Handle rate limiting with exponential backoff
                if response.status_code == 429:
                    wait_time = (2 ** attempt) * 5  # 5, 10, 20 seconds
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                data = response.json()

                papers = data.get("data", [])
                if not papers:
                    return None

                return self._parse_paper_response(papers[0])

            except httpx.HTTPStatusError:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) * 2
                    time.sleep(wait_time)
                    continue
                return None
            except Exception:
                return None

        return None

    def __del__(self):
        """Close the HTTP client."""
        if hasattr(self, "client"):
            self.client.close()
