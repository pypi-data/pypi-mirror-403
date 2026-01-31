"""
Tests for OneRoster header-based pagination.

Covers Link header parsing, X-Total-Count parsing, and Paginator behavior.
"""

from __future__ import annotations

from timeback_oneroster.lib.transport import PaginatedResponse, Transport


class TestLinkHeaderParsing:
    """Tests for Link header next detection."""

    def test_detects_double_quoted_rel_next(self):
        """Detects rel="next" with double quotes."""
        transport = Transport.__new__(Transport)
        link = '<https://api.example.com/users?page=2>; rel="next"'
        assert transport._parse_has_more(link) is True

    def test_detects_single_quoted_rel_next(self):
        """Detects rel='next' with single quotes."""
        transport = Transport.__new__(Transport)
        link = "<https://api.example.com/users?page=2>; rel='next'"
        assert transport._parse_has_more(link) is True

    def test_detects_unquoted_rel_next(self):
        """Detects rel=next without quotes."""
        transport = Transport.__new__(Transport)
        link = "<https://api.example.com/users?page=2>; rel=next"
        assert transport._parse_has_more(link) is True

    def test_returns_false_for_rel_prev(self):
        """Returns False when only rel=prev is present."""
        transport = Transport.__new__(Transport)
        link = '<https://api.example.com/users?page=1>; rel="prev"'
        assert transport._parse_has_more(link) is False

    def test_returns_false_for_no_link_header(self):
        """Returns False when Link header is None."""
        transport = Transport.__new__(Transport)
        assert transport._parse_has_more(None) is False

    def test_returns_false_for_empty_link_header(self):
        """Returns False when Link header is empty."""
        transport = Transport.__new__(Transport)
        assert transport._parse_has_more("") is False

    def test_detects_next_in_multi_link_header(self):
        """Detects rel=next in a multi-link header."""
        transport = Transport.__new__(Transport)
        link = '<https://api.example.com?page=1>; rel="prev", <https://api.example.com?page=3>; rel="next"'
        assert transport._parse_has_more(link) is True


class TestTotalCountParsing:
    """Tests for X-Total-Count header parsing."""

    def test_parses_valid_total_count(self):
        """Parses valid X-Total-Count header."""
        transport = Transport.__new__(Transport)
        assert transport._parse_total_count("100") == 100

    def test_returns_none_for_invalid_total_count(self):
        """Returns None for invalid X-Total-Count header."""
        transport = Transport.__new__(Transport)
        assert transport._parse_total_count("invalid") is None

    def test_returns_none_for_no_total_count(self):
        """Returns None when X-Total-Count header is missing."""
        transport = Transport.__new__(Transport)
        assert transport._parse_total_count(None) is None


class TestPaginatedResponse:
    """Tests for PaginatedResponse dataclass."""

    def test_creates_response_with_all_fields(self):
        """PaginatedResponse can be created with all fields."""
        response = PaginatedResponse(
            data=[{"id": 1}, {"id": 2}],
            has_more=True,
            total=100,
        )

        assert len(response.data) == 2
        assert response.has_more is True
        assert response.total == 100

    def test_total_defaults_to_none(self):
        """PaginatedResponse.total defaults to None."""
        response = PaginatedResponse(
            data=[],
            has_more=False,
        )

        assert response.total is None
