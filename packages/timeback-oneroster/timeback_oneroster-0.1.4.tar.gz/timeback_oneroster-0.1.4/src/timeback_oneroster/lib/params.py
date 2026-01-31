"""
List Parameter Builders

Shared helpers for building query parameters for list operations.
Two variants are provided based on whether the endpoint supports search.
"""

from __future__ import annotations

from typing import Any

from timeback_common import validate_fields

from .filter import WhereClause, where_to_filter


def build_list_params(
    *,
    offset: int | None = None,
    sort: str | None = None,
    order_by: str | None = None,
    filter: str | None = None,
    where: WhereClause | None = None,
    fields: list[str] | None = None,
    search: str | None = None,
) -> dict[str, Any]:
    """
    Build query params dict for endpoints that support search.

    Use this for: users, students, courses

    Args:
        offset: Starting offset for pagination
        sort: Field to sort by
        order_by: Sort direction ('asc' or 'desc')
        filter: OneRoster filter string (legacy, prefer `where`)
        where: Type-safe filter clause
        fields: Sparse fieldset - list of fields to return
        search: Full-text search query

    Returns:
        Query parameters dict ready for transport
    """
    validate_fields(fields)

    params: dict[str, Any] = {}
    if offset is not None:
        params["offset"] = offset
    if sort is not None:
        params["sort"] = sort
    if order_by is not None:
        params["orderBy"] = order_by
    if fields is not None:
        params["fields"] = ",".join(fields)
    if search is not None:
        params["search"] = search

    if where is not None:
        filter_str = where_to_filter(where)
        if filter_str:
            params["filter"] = filter_str
    elif filter is not None:
        params["filter"] = filter

    return params


def build_list_params_no_search(
    *,
    offset: int | None = None,
    sort: str | None = None,
    order_by: str | None = None,
    filter: str | None = None,
    where: WhereClause | None = None,
    fields: list[str] | None = None,
) -> dict[str, Any]:
    """
    Build query params dict for endpoints that do NOT support search.

    Use this for: classes, schools, teachers, terms, enrollments, orgs,
    demographics, line_items, results, categories, score_scales, resources,
    and all scoped methods.

    Args:
        offset: Starting offset for pagination
        sort: Field to sort by
        order_by: Sort direction ('asc' or 'desc')
        filter: OneRoster filter string (legacy, prefer `where`)
        where: Type-safe filter clause
        fields: Sparse fieldset - list of fields to return

    Returns:
        Query parameters dict ready for transport
    """
    validate_fields(fields)

    params: dict[str, Any] = {}
    if offset is not None:
        params["offset"] = offset
    if sort is not None:
        params["sort"] = sort
    if order_by is not None:
        params["orderBy"] = order_by
    if fields is not None:
        params["fields"] = ",".join(fields)

    if where is not None:
        filter_str = where_to_filter(where)
        if filter_str:
            params["filter"] = filter_str
    elif filter is not None:
        params["filter"] = filter

    return params
