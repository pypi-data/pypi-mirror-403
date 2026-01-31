"""
OneRoster Pagination Support

Uses header-based pagination (Link + X-Total-Count) per IMS Global spec.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, TypeVar

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable

    from .transport import PaginatedResponse

T = TypeVar("T")


@dataclass
class PageResult[T]:
    """
    Result of fetching a single page of resources.

    Provides pagination metadata for building custom pagination UIs.
    """

    data: list[T]
    """Array of items in this page."""

    has_more: bool
    """Whether more pages are available."""

    total: int | None = None
    """Total count of items (if provided by server)."""

    next_offset: int | None = None
    """Offset to use for fetching the next page."""


class PaginatedTransportProtocol(Protocol):
    """Protocol for transports that support header-based pagination."""

    async def request_paginated(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        unwrap_key: str | None = None,
    ) -> PaginatedResponse: ...


class Paginator[T]:
    """
    Async paginator for OneRoster list endpoints.

    Uses header-based pagination (Link header for `rel=next`, X-Total-Count for total).

    Example:
        ```python
        async for user in paginator:
            print(user["givenName"])

        # Or collect all at once
        all_users = await paginator.to_list()

        # Get just the first item
        first = await paginator.first()
        ```
    """

    def __init__(
        self,
        transport: PaginatedTransportProtocol,
        path: str,
        *,
        unwrap_key: str,
        params: dict[str, Any] | None = None,
        limit: int = 100,
        max_items: int | None = None,
        transform: Callable[[T], T] | None = None,
    ) -> None:
        """
        Initialize paginator.

        Args:
            transport: Transport instance with request_paginated() method
            path: API endpoint path
            unwrap_key: Key to unwrap from response (e.g., "users", "classes")
            params: Additional query parameters
            limit: Items per page
            max_items: Maximum total items to fetch (None for all)
            transform: Optional function to transform each item before returning

        """
        self._transport = transport
        self._path = path
        self._unwrap_key = unwrap_key
        self._params = params or {}
        self._limit = limit
        self._max_items = max_items
        self._transform = transform
        self._offset = 0
        self._total_fetched = 0
        self._has_more = True
        self._total: int | None = None
        self._buffer: list[T] = []
        self._buffer_index = 0

    @property
    def total(self) -> int | None:
        """Total number of items (from X-Total-Count header)."""
        return self._total

    def _has_more_pages(
        self,
        has_more_from_link: bool,
        total: int | None,
        item_count: int,
        offset: int,
    ) -> bool:
        """
        Determine if more pages are available using fallback strategy.

        Uses a three-tier fallback:
        1. Link header (most reliable)
        2. X-Total-Count header comparison
        3. Full page heuristic (assumes more if page is full and no total provided)

        Always returns False for empty pages to prevent infinite loops from
        buggy servers that return has_more=True with no data.

        Args:
            has_more_from_link: Whether Link header indicates more pages
            total: Total count from X-Total-Count header (if available)
            item_count: Number of items in current page
            offset: Current offset (after fetching this page)

        Returns:
            True if more pages are available
        """
        # Empty page always means no more (prevents infinite loops)
        if item_count == 0:
            return False

        # Tier 1: Link header says there's more
        if has_more_from_link:
            return True

        # Tier 2: Total count says there's more
        if total is not None and offset < total:
            return True

        # Tier 3: Full page heuristic (only if no total provided)
        # If we got a full page and don't know the total, assume there might be more
        return bool(total is None and item_count == self._limit)

    def _apply_transform(self, items: list[T]) -> list[T]:
        """Apply transform to a list of items if transform is defined."""
        if self._transform is None:
            return items
        return [self._transform(item) for item in items]

    async def _fetch_page(self) -> list[T]:
        """Fetch the next page of results."""
        params = {
            **self._params,
            "limit": self._limit,
            "offset": self._offset,
        }

        response = await self._transport.request_paginated(
            self._path,
            params=params,
            unwrap_key=self._unwrap_key,
        )

        items = response.data

        # Update total if provided
        if response.total is not None:
            self._total = response.total

        # Update offset
        self._offset += len(items)

        # Determine has_more using fallback logic
        self._has_more = self._has_more_pages(
            has_more_from_link=response.has_more,
            total=response.total,
            item_count=len(items),
            offset=self._offset,
        )

        # Apply transform to items
        return self._apply_transform(items)

    def __aiter__(self) -> AsyncIterator[T]:
        """Return async iterator."""
        return self

    async def __anext__(self) -> T:
        """Get next item, fetching pages as needed."""
        # Check max items limit
        if self._max_items is not None and self._total_fetched >= self._max_items:
            raise StopAsyncIteration

        # If buffer is exhausted, fetch more
        while self._buffer_index >= len(self._buffer):
            if not self._has_more and self._offset > 0:
                raise StopAsyncIteration

            self._buffer = await self._fetch_page()
            self._buffer_index = 0

            if not self._buffer:
                raise StopAsyncIteration

        # Return next item from buffer
        item = self._buffer[self._buffer_index]
        self._buffer_index += 1
        self._total_fetched += 1
        return item

    async def to_list(self) -> list[T]:
        """
        Fetch all pages and return as a single list.

        Alias for `to_array()` without safety guard.

        Returns:
            List of all items across all pages
        """
        all_items: list[T] = []

        async for item in self:
            all_items.append(item)

        return all_items

    async def to_array(self, *, max_items: int | None = 10_000) -> list[T]:
        """
        Collect all items into an array with safety guard.

        **Warning**: Use with caution on large datasets as this loads
        all items into memory. Consider iterating with `async for` for
        better memory efficiency.

        Args:
            max_items: Maximum items to collect (default: 10,000).
                Raises error if limit is exceeded. Set to None to disable.

        Returns:
            List of all items across all pages

        Raises:
            RuntimeError: If max_items limit is exceeded
        """
        all_items: list[T] = []

        async for item in self:
            if max_items is not None and len(all_items) >= max_items:
                raise RuntimeError(
                    f"to_array() exceeded max_items limit of {max_items}. "
                    "Use 'async for' to stream large datasets, or increase max_items."
                )
            all_items.append(item)

        return all_items

    async def first(self) -> T | None:
        """
        Fetch just the first item.

        Returns:
            First item or None if empty
        """
        response = await self._transport.request_paginated(
            self._path,
            params={**self._params, "limit": 1, "offset": 0},
            unwrap_key=self._unwrap_key,
        )
        items = self._apply_transform(response.data)
        return items[0] if items else None

    async def first_page(self) -> PageResult[T]:
        """
        Fetch only the first page of results with pagination metadata.

        Useful when you need pagination metadata (total count, has_more)
        or want to implement custom pagination UI.

        Returns:
            PageResult with data, has_more, total, and next_offset
        """
        offset = self._params.get("offset", 0) or 0
        params = {
            **self._params,
            "limit": self._limit,
            "offset": offset,
        }

        response = await self._transport.request_paginated(
            self._path,
            params=params,
            unwrap_key=self._unwrap_key,
        )

        items = self._apply_transform(response.data)
        total = response.total
        next_offset = offset + len(items)

        # Use fallback logic for has_more
        has_more = self._has_more_pages(
            has_more_from_link=response.has_more,
            total=total,
            item_count=len(items),
            offset=next_offset,
        )

        return PageResult(
            data=items,
            has_more=has_more,
            total=total,
            next_offset=next_offset if has_more else None,
        )

    def reset(self) -> None:
        """Reset the paginator to start from the beginning."""
        self._offset = 0
        self._total_fetched = 0
        self._has_more = True
        self._buffer = []
        self._buffer_index = 0


__all__ = ["PageResult", "PaginatedTransportProtocol", "Paginator"]
