"""Tests for OneRoster utility functions."""

from timeback_oneroster.utils import normalize_boolean, normalize_date_only, parse_grades


class TestParseGrades:
    """Tests for parse_grades function."""

    def test_parses_string_grades_to_ints(self):
        """Converts string grades to integers."""
        assert parse_grades(["1", "2", "3"]) == [1, 2, 3]

    def test_handles_negative_grades(self):
        """Handles negative grade values (e.g., PreK = -1)."""
        assert parse_grades(["-1", "0", "1"]) == [-1, 0, 1]

    def test_handles_double_digit_grades(self):
        """Handles double-digit grades (high school)."""
        assert parse_grades(["9", "10", "11", "12"]) == [9, 10, 11, 12]

    def test_returns_none_for_none_input(self):
        """Returns None when input is None."""
        assert parse_grades(None) is None

    def test_returns_empty_list_for_empty_input(self):
        """Returns empty list for empty input."""
        assert parse_grades([]) == []


class TestNormalizeDateOnly:
    """Tests for normalize_date_only function."""

    def test_extracts_date_from_iso_timestamp(self):
        """Extracts YYYY-MM-DD from ISO timestamp."""
        assert normalize_date_only("2024-01-15T00:00:00.000Z") == "2024-01-15"

    def test_handles_date_only_input(self):
        """Passes through date-only strings unchanged."""
        assert normalize_date_only("2024-01-15") == "2024-01-15"

    def test_handles_timestamp_with_time(self):
        """Extracts date from timestamp with time component."""
        assert normalize_date_only("2024-12-25T14:30:00Z") == "2024-12-25"


class TestNormalizeBoolean:
    """Tests for normalize_boolean function."""

    def test_passes_through_true(self):
        """Passes through boolean True."""
        assert normalize_boolean(True) is True

    def test_passes_through_false(self):
        """Passes through boolean False."""
        assert normalize_boolean(False) is False

    def test_converts_string_true(self):
        """Converts string 'true' to True."""
        assert normalize_boolean("true") is True

    def test_converts_string_false(self):
        """Converts string 'false' to False."""
        assert normalize_boolean("false") is False

    def test_empty_string_is_false(self):
        """Empty string converts to False."""
        assert normalize_boolean("") is False

    def test_other_strings_are_false(self):
        """Any string other than 'true' converts to False."""
        assert normalize_boolean("True") is False  # Case-sensitive
        assert normalize_boolean("yes") is False
        assert normalize_boolean("1") is False
