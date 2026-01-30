"""Google Scholar search wrapper using scholarly library."""

import time
from typing import Any

try:
    from scholarly import scholarly
    SCHOLARLY_AVAILABLE = True
except ImportError:
    SCHOLARLY_AVAILABLE = False


class GoogleScholarClient:
    """Client for Google Scholar with rate limiting.

    Note: Google Scholar doesn't have an official API and may block
    excessive requests. Use sparingly as a last resort fallback.
    """

    def __init__(self, delay: float = 2.0):
        """Initialize the Google Scholar client.

        Args:
            delay: Delay between API calls in seconds (higher recommended to avoid blocks)
        """
        self.delay = delay
        self._last_call = 0.0
        self._available = SCHOLARLY_AVAILABLE

    def _rate_limit(self) -> None:
        """Ensure minimum delay between API calls."""
        elapsed = time.time() - self._last_call
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self._last_call = time.time()

    def is_available(self) -> bool:
        """Check if scholarly library is available."""
        return self._available

    def search_paper(self, title: str, max_retries: int = 2) -> dict[str, Any] | None:
        """Search Google Scholar for paper by title.

        Args:
            title: Paper title to search for
            max_retries: Maximum number of retries

        Returns:
            Paper dict with title, authors, year or None if not found
        """
        if not self._available:
            return None

        for attempt in range(max_retries):
            self._rate_limit()

            try:
                # Search for the paper
                search_query = scholarly.search_pubs(title)

                # Get the first result
                result = next(search_query, None)

                if result is None:
                    return None

                # Extract bib information
                bib = result.get("bib", {})

                # Parse authors - scholarly returns a list of author names
                authors = bib.get("author", [])
                if isinstance(authors, str):
                    # Sometimes it's a string with "and" separating authors
                    authors = [a.strip() for a in authors.replace(" and ", ",").split(",")]

                # Get year
                year = bib.get("pub_year") or bib.get("year")

                return {
                    "title": bib.get("title", ""),
                    "authors": [a for a in authors if a],
                    "year": year,
                    "venue": bib.get("venue", ""),
                    "url": result.get("pub_url") or result.get("eprint_url"),
                }

            except StopIteration:
                return None
            except Exception:
                if attempt < max_retries - 1:
                    # Exponential backoff on failures (might be rate limited)
                    time.sleep((2 ** attempt) * 3)
                    continue
                return None

        return None
