"""
OneRoster Transport Layer
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from timeback_common import BaseTransport, OneRosterPaths, TokenManager
from timeback_common.pagination_strategies import parse_header_has_more, parse_header_total

if TYPE_CHECKING:
    import httpx


@dataclass
class PaginatedResponse:
    """Response from a paginated OneRoster request."""

    data: list[Any]
    has_more: bool
    total: int | None = None


class Transport(BaseTransport):
    """HTTP transport layer for OneRoster API communication."""

    paths: OneRosterPaths

    def __init__(
        self,
        *,
        base_url: str,
        token_manager: TokenManager | None = None,
        paths: OneRosterPaths,
        timeout: float = 30.0,
        http_client: httpx.AsyncClient | None = None,
        no_auth: bool = False,
    ) -> None:
        super().__init__(
            base_url=base_url,
            timeout=timeout,
            token_manager=token_manager,
            http_client=http_client,
            no_auth=no_auth,
        )
        self.paths = paths

    async def request_paginated(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        unwrap_key: str | None = None,
    ) -> PaginatedResponse:
        """
        Make a paginated request using header-based pagination (OneRoster style).
        """
        response = await self.request_raw("GET", path, params=params)

        data = response.json()
        if unwrap_key and isinstance(data, dict):
            data = data.get(unwrap_key, [])
        if not isinstance(data, list):
            data = []

        return PaginatedResponse(
            data=data,
            has_more=parse_header_has_more(response.headers),
            total=parse_header_total(response.headers),
        )

    # Backwards-compatible helpers used by older tests (and mirroring TS helper logic)
    def _parse_has_more(self, link_header: str | None) -> bool:
        if not link_header:
            return False
        from httpx import Headers

        return parse_header_has_more(Headers({"link": link_header}))

    def _parse_total_count(self, total_header: str | None) -> int | None:
        if not total_header:
            return None
        from httpx import Headers

        return parse_header_total(Headers({"x-total-count": total_header}))


__all__ = ["PaginatedResponse", "Transport"]
