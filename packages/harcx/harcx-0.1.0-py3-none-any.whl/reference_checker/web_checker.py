"""Web URL checker for citations."""

import time

import httpx
from bs4 import BeautifulSoup
from rapidfuzz import fuzz

from .models import BibEntry, WebCheckResult

# Browser-like User-Agent to avoid being blocked
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


class WebChecker:
    """Client for checking URL citations with rate limiting."""

    def __init__(self, timeout: float = 10.0, delay: float = 1.0):
        """Initialize the web checker.

        Args:
            timeout: Request timeout in seconds
            delay: Delay between requests in seconds
        """
        self.client = httpx.Client(
            timeout=timeout,
            follow_redirects=True,
            headers={"User-Agent": USER_AGENT},
        )
        self.delay = delay
        self._last_call = 0.0

    def _rate_limit(self) -> None:
        """Ensure minimum delay between requests."""
        elapsed = time.time() - self._last_call
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self._last_call = time.time()

    def _extract_title(self, html: str) -> str | None:
        """Extract title from HTML content.

        Args:
            html: HTML content as string

        Returns:
            Title text or None if not found
        """
        try:
            soup = BeautifulSoup(html, "html.parser")
            if soup.title and soup.title.string:
                return soup.title.string.strip()
            return None
        except Exception:
            return None

    def _calculate_title_match(
        self, expected_title: str | None, actual_title: str | None
    ) -> float:
        """Calculate fuzzy match score between expected and actual titles.

        Args:
            expected_title: Expected title from citation
            actual_title: Actual title from webpage

        Returns:
            Match score between 0.0 and 1.0
        """
        if not expected_title or not actual_title:
            return 0.0

        return fuzz.ratio(expected_title.lower(), actual_title.lower()) / 100.0

    def check_url(
        self, entry: BibEntry, url: str, expected_title: str | None, max_retries: int = 2
    ) -> WebCheckResult:
        """Check if a URL is reachable and if the page title matches.

        Args:
            entry: The BibEntry this URL belongs to
            url: URL to check
            expected_title: Expected title from citation (for matching)
            max_retries: Maximum number of retries on transient failures

        Returns:
            WebCheckResult with reachability and title match info
        """
        for attempt in range(max_retries):
            self._rate_limit()

            try:
                response = self.client.get(url)

                # Successful response
                if response.status_code == 200:
                    page_title = self._extract_title(response.text)
                    title_score = self._calculate_title_match(expected_title, page_title)

                    return WebCheckResult(
                        entry=entry,
                        url=url,
                        reachable=True,
                        status_code=response.status_code,
                        page_title=page_title,
                        title_match_score=title_score,
                        message="URL reachable",
                    )

                # Server error - retry
                if response.status_code >= 500 and attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue

                # Client or server error - return as unreachable
                return WebCheckResult(
                    entry=entry,
                    url=url,
                    reachable=False,
                    status_code=response.status_code,
                    page_title=None,
                    title_match_score=0.0,
                    message=f"HTTP {response.status_code}",
                )

            except httpx.TimeoutException:
                if attempt < max_retries - 1:
                    continue
                return WebCheckResult(
                    entry=entry,
                    url=url,
                    reachable=False,
                    status_code=None,
                    page_title=None,
                    title_match_score=0.0,
                    message="Request timed out",
                )

            except httpx.ConnectError:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return WebCheckResult(
                    entry=entry,
                    url=url,
                    reachable=False,
                    status_code=None,
                    page_title=None,
                    title_match_score=0.0,
                    message="Connection failed",
                )

            except Exception as e:
                return WebCheckResult(
                    entry=entry,
                    url=url,
                    reachable=False,
                    status_code=None,
                    page_title=None,
                    title_match_score=0.0,
                    message=f"Error: {type(e).__name__}",
                )

        # Should not reach here, but return unreachable just in case
        return WebCheckResult(
            entry=entry,
            url=url,
            reachable=False,
            status_code=None,
            page_title=None,
            title_match_score=0.0,
            message="Max retries exceeded",
        )

    def __del__(self):
        """Close the HTTP client."""
        if hasattr(self, "client"):
            self.client.close()
