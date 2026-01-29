"""
Utility Functions

Internal utilities for the OneRoster client.
"""

from __future__ import annotations


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


def normalize_date_only(date: str) -> str:
    """
    Normalize a date string to `YYYY-MM-DD`.

    The Beyond-AI API sometimes returns ISO timestamps (e.g., `2024-01-01T00:00:00.000Z`)
    for fields that are conceptually dates. This function normalizes these to date-only
    strings for a stable, predictable API.

    Args:
        date: Date string from the API

    Returns:
        Normalized date string in `YYYY-MM-DD` format

    Example:
        ```python
        normalize_date_only("2024-01-15T00:00:00.000Z")  # "2024-01-15"
        normalize_date_only("2024-01-15")  # "2024-01-15"
        ```
    """
    return date[:10]


def normalize_boolean(value: bool | str) -> bool:
    """
    Normalize a boolean-like value to a boolean.

    The Beyond-AI API sometimes returns boolean fields as strings (`"true"`/`"false"`).
    This function normalizes these for a stable, predictable API.

    Args:
        value: Boolean-like value from the API

    Returns:
        Normalized boolean

    Example:
        ```python
        normalize_boolean(True)  # True
        normalize_boolean("true")  # True
        normalize_boolean("false")  # False
        normalize_boolean(False)  # False
        ```
    """
    if isinstance(value, bool):
        return value
    return value == "true"


__all__ = [
    "normalize_boolean",
    "normalize_date_only",
    "parse_grades",
]
