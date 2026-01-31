"""
Utility Functions

Internal utilities for the OneRoster client.
"""

from __future__ import annotations

from timeback_common import normalize_boolean, normalize_date_only


def parse_grades(grades: list[str] | None) -> list[int] | None:
    """
    Convert grade strings from API responses to numeric grade values.

    The API returns grades as strings (e.g., "5", "-1") because the database
    stores them as text. This function normalizes them to numbers for
    a better developer experience.

    Args:
        grades: Array of string grades from API, or None

    Returns:
        Array of numeric grades, or None if input was None

    Example:
        ```python
        parse_grades(["1", "2", "3"])  # [1, 2, 3]
        parse_grades(None)  # None
        parse_grades(["-1", "0", "13"])  # [-1, 0, 13]
        ```
    """
    if grades is None:
        return None
    return [int(g) for g in grades]


__all__ = [
    "normalize_boolean",
    "normalize_date_only",
    "parse_grades",
]
