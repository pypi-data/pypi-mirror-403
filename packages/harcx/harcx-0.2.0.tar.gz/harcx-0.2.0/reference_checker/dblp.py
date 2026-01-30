"""DBLP API wrapper."""

import time
from typing import Any

import httpx

DBLP_API_URL = "https://dblp.org/search/publ/api"


class DBLPClient:
    """Client for DBLP API with rate limiting."""

    def __init__(self, delay: float = 1.0, timeout: float = 10.0):
        """Initialize the DBLP client.

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

    def search_paper(self, title: str, max_retries: int = 3) -> dict[str, Any] | None:
        """Search DBLP for paper by title.

        Args:
            title: Paper title to search for
            max_retries: Maximum number of retries

        Returns:
            Paper dict with title, authors, year or None if not found
        """
        for attempt in range(max_retries):
            self._rate_limit()

            try:
                response = self.client.get(
                    DBLP_API_URL,
                    params={
                        "q": title,
                        "format": "json",
                        "h": 1,  # Return only 1 result
                    },
                )

                if response.status_code == 429:
                    wait_time = (2 ** attempt) * 2
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                data = response.json()

                hits = data.get("result", {}).get("hits", {}).get("hit", [])
                if not hits:
                    return None

                hit = hits[0].get("info", {})

                # Parse authors - can be a string or list
                authors_data = hit.get("authors", {}).get("author", [])
                if isinstance(authors_data, str):
                    authors = [authors_data]
                elif isinstance(authors_data, dict):
                    authors = [authors_data.get("text", authors_data.get("@text", ""))]
                elif isinstance(authors_data, list):
                    authors = []
                    for a in authors_data:
                        if isinstance(a, str):
                            authors.append(a)
                        elif isinstance(a, dict):
                            authors.append(a.get("text", a.get("@text", "")))
                else:
                    authors = []

                return {
                    "title": hit.get("title", ""),
                    "authors": [a for a in authors if a],
                    "year": hit.get("year"),
                    "venue": hit.get("venue"),
                    "doi": hit.get("doi"),
                    "url": hit.get("url"),
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
