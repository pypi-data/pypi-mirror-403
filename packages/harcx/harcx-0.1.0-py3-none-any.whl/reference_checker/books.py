"""Open Library API wrapper for book verification."""

import re
import time
from typing import Any

import httpx

OPENLIBRARY_API_URL = "https://openlibrary.org"


def extract_isbn(entry: dict) -> str | None:
    """Extract ISBN from a bib entry.

    Args:
        entry: Raw bib entry dict

    Returns:
        ISBN string (10 or 13 digit) or None
    """
    # Check isbn field directly
    isbn = entry.get("isbn", "")
    if isbn:
        # Clean up ISBN (remove dashes, spaces)
        isbn = re.sub(r"[-\s]", "", isbn)
        # Validate it looks like an ISBN
        if re.match(r"^\d{10}$|^\d{13}$|^\d{9}X$", isbn, re.IGNORECASE):
            return isbn

    return None


class OpenLibraryClient:
    """Client for Open Library API with rate limiting."""

    def __init__(self, delay: float = 1.0, timeout: float = 10.0):
        """Initialize the Open Library client.

        Args:
            delay: Delay between API calls in seconds
            timeout: Request timeout in seconds
        """
        self.client = httpx.Client(timeout=timeout)
        self.delay = delay
        self._last_call = 0.0

    def _rate_limit(self) -> None:
        """Ensure minimum delay between API calls."""
        elapsed = time.time() - self._last_call
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self._last_call = time.time()

    def get_book_by_isbn(self, isbn: str, max_retries: int = 3) -> dict[str, Any] | None:
        """Get book by ISBN.

        Args:
            isbn: ISBN-10 or ISBN-13
            max_retries: Maximum number of retries

        Returns:
            Book dict with title, authors, year or None if not found
        """
        for attempt in range(max_retries):
            self._rate_limit()

            try:
                response = self.client.get(
                    f"{OPENLIBRARY_API_URL}/isbn/{isbn}.json",
                )

                if response.status_code == 404:
                    return None

                if response.status_code == 429:
                    wait_time = (2 ** attempt) * 2
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                data = response.json()

                # Get authors (need separate request for author names)
                authors = []
                author_keys = data.get("authors", [])
                for author_ref in author_keys[:5]:  # Limit to 5 authors
                    author_key = author_ref.get("key", "")
                    if author_key:
                        author_name = self._get_author_name(author_key)
                        if author_name:
                            authors.append(author_name)

                # Extract year from publish_date
                year = None
                publish_date = data.get("publish_date", "")
                year_match = re.search(r"\b(19|20)\d{2}\b", publish_date)
                if year_match:
                    year = year_match.group(0)

                return {
                    "title": data.get("title", ""),
                    "authors": authors,
                    "year": year,
                    "publisher": ", ".join(data.get("publishers", [])),
                    "isbn": isbn,
                }

            except httpx.HTTPStatusError:
                if attempt < max_retries - 1:
                    time.sleep((2 ** attempt) * 2)
                    continue
                return None
            except Exception:
                return None

        return None

    def _get_author_name(self, author_key: str) -> str | None:
        """Get author name from Open Library author key.

        Args:
            author_key: Open Library author key (e.g., "/authors/OL123A")

        Returns:
            Author name or None
        """
        try:
            self._rate_limit()
            response = self.client.get(f"{OPENLIBRARY_API_URL}{author_key}.json")
            if response.status_code == 200:
                data = response.json()
                return data.get("name")
        except Exception:
            pass
        return None

    def search_book(self, title: str, author: str | None = None, max_retries: int = 3) -> dict[str, Any] | None:
        """Search Open Library for book by title.

        Args:
            title: Book title to search for
            author: Optional author name to improve matching
            max_retries: Maximum number of retries

        Returns:
            Book dict or None if not found
        """
        for attempt in range(max_retries):
            self._rate_limit()

            try:
                params = {"title": title, "limit": 1}
                if author:
                    params["author"] = author

                response = self.client.get(
                    f"{OPENLIBRARY_API_URL}/search.json",
                    params=params,
                )

                if response.status_code == 429:
                    wait_time = (2 ** attempt) * 2
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                data = response.json()

                docs = data.get("docs", [])
                if not docs:
                    return None

                doc = docs[0]
                return {
                    "title": doc.get("title", ""),
                    "authors": doc.get("author_name", []),
                    "year": str(doc.get("first_publish_year", "")) or None,
                    "publisher": ", ".join(doc.get("publisher", [])[:3]),
                }

            except httpx.HTTPStatusError:
                if attempt < max_retries - 1:
                    time.sleep((2 ** attempt) * 2)
                    continue
                return None
            except Exception:
                return None

        return None

    def __del__(self):
        """Close the HTTP client."""
        if hasattr(self, "client"):
            self.client.close()
