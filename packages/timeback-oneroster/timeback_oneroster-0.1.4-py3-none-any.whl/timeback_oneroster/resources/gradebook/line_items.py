"""
Line Items Resource

Access and manage gradebook line items (assignments, tests, etc.).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from timeback_common import BulkCreateResponse, validate_sourced_id

from ...lib.pagination import Paginator
from ...lib.params import build_list_params_no_search
from ...types import LineItemCreateInput
from ...types.gradebook import LineItem, Result
from ..base import CRUDResourceNoSearch

if TYPE_CHECKING:
    from pydantic import BaseModel

    from ...lib.filter import WhereClause
    from ...lib.transport import Transport


# ═══════════════════════════════════════════════════════════════════════════════
# SCOPED LINE ITEM RESOURCE
# ═══════════════════════════════════════════════════════════════════════════════


class ScopedLineItemResource:
    """
    Scoped resource for operations on a specific line item.

    Access via `client.line_items(line_item_id)`.

    Example:
        ```python
        line_item = await client.line_items(line_item_id).get()
        results = await client.line_items(line_item_id).results()
        ```
    """

    def __init__(self, transport: Transport, line_item_id: str) -> None:
        validate_sourced_id(line_item_id, "line item")
        self._transport = transport
        self._line_item_id = line_item_id
        self._base_path = f"{transport.paths.gradebook}/lineItems/{line_item_id}"

    async def get(self) -> LineItem:
        """Get the line item details."""
        response = await self._transport.get(self._base_path)
        return LineItem(**response["lineItem"])

    async def delete(self) -> None:
        """Delete this line item."""
        await self._transport.delete(self._base_path)

    async def create_results(self, results: list[dict[str, Any]]) -> BulkCreateResponse:
        """
        Bulk create results for this line item.

        Use this to submit multiple student grades at once.

        Args:
            results: Array of results to create

        Returns:
            Bulk create response with list of sourcedIdPairs (one per result)

        Example:
            ```python
            response = await client.line_items(line_item_id).create_results([
                {"student": {"sourcedId": "student1"}, "score": 85},
                {"student": {"sourcedId": "student2"}, "score": 92},
            ])
            # Access individual pairs
            for pair in response.sourced_id_pairs:
                print(pair.allocated_sourced_id)
            ```
        """
        response = await self._transport.post(
            f"{self._base_path}/results",
            {"results": results},
        )
        return BulkCreateResponse.model_validate(response)

    # ── Results ────────────────────────────────────────────────────────────────

    async def results(
        self,
        *,
        limit: int = 100,
        offset: int | None = None,
        sort: str | None = None,
        order_by: str | None = None,
        filter: str | None = None,
        where: WhereClause | None = None,
        fields: list[str] | None = None,
    ) -> list[Result]:
        """List results for this line item."""
        return await self.stream_results(
            limit=limit,
            offset=offset,
            sort=sort,
            order_by=order_by,
            filter=filter,
            where=where,
            fields=fields,
        ).to_list()

    def stream_results(
        self,
        *,
        limit: int = 100,
        offset: int | None = None,
        sort: str | None = None,
        order_by: str | None = None,
        filter: str | None = None,
        where: WhereClause | None = None,
        fields: list[str] | None = None,
        max_items: int | None = None,
    ) -> Paginator[Result]:
        """Stream results with lazy pagination."""
        params = build_list_params_no_search(
            offset=offset,
            sort=sort,
            order_by=order_by,
            filter=filter,
            where=where,
            fields=fields,
        )

        return Paginator(
            self._transport,
            f"{self._base_path}/results",
            unwrap_key="results",
            params=params,
            limit=limit,
            max_items=max_items,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# LINE ITEMS RESOURCE
# ═══════════════════════════════════════════════════════════════════════════════


class LineItemsResource(CRUDResourceNoSearch[LineItem]):
    """
    Resource for gradebook line items.

    Line items represent gradable activities (assignments, tests, quizzes).

    Example:
        ```python
        # List all line items
        line_items = await client.line_items.list()

        # Get specific line item
        line_item = await client.line_items.get("line-item-id")

        # Get results for a line item
        results = await client.line_items("line-item-id").results()

        # Create a line item
        await client.line_items.create({
            "title": "Chapter 1 Quiz",
            "class": {"sourcedId": "class-id"},
            "assignDate": "2024-01-15",
            "dueDate": "2024-01-22",
            "resultValueMin": 0,
            "resultValueMax": 100,
        })

        # Filter by class
        class_items = await client.line_items.list(
            filter="class.sourcedId='class-id'"
        )
        ```
    """

    def __init__(self, transport: Transport) -> None:
        super().__init__(transport, "gradebook", "/lineItems")

    @property
    def _unwrap_key(self) -> str:
        return "lineItems"

    @property
    def _wrap_key(self) -> str:
        return "lineItem"

    @property
    def _model_class(self) -> type[LineItem]:
        return LineItem

    @property
    def _create_schema(self) -> type[BaseModel]:
        """Pydantic model for validating line item create input."""
        return LineItemCreateInput

    @property
    def _update_schema(self) -> type[BaseModel]:
        """Pydantic model for validating line item update input."""
        return LineItemCreateInput

    def __call__(self, line_item_id: str) -> ScopedLineItemResource:
        """Get scoped resource for a specific line item."""
        return ScopedLineItemResource(self._transport, line_item_id)
