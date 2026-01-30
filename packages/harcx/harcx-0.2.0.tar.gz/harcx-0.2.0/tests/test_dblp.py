"""Tests for DBLP citation checker."""

import pytest

from reference_checker.dblp import DBLPClient


class TestDBLPClientIntegration:
    """Integration tests for DBLP client (require network)."""

    @pytest.fixture
    def client(self):
        return DBLPClient(delay=0.5)

    @pytest.mark.network
    def test_search_paper_by_title(self, client):
        """Test searching for a well-known paper."""
        result = client.search_paper("Attention Is All You Need")
        assert result is not None
        assert "attention" in result["title"].lower()
        assert len(result["authors"]) > 0

    @pytest.mark.network
    def test_search_nonexistent_paper(self, client):
        """Test searching for a paper that doesn't exist."""
        result = client.search_paper("This Paper Title Does Not Exist Anywhere 12345")
        assert result is None
