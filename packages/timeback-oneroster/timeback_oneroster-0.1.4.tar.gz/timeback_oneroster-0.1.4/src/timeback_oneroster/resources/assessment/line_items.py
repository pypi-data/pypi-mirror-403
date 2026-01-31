"""
Assessment Line Items Resource

Access and manage standardized assessment line items.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ...types import AssessmentLineItemCreateInput
from ...types.assessment import AssessmentLineItem
from ..base import CRUDResourceNoSearch

if TYPE_CHECKING:
    from pydantic import BaseModel

    from ...lib.transport import Transport


# ═══════════════════════════════════════════════════════════════════════════════
# SCOPED ASSESSMENT LINE ITEM RESOURCE
# ═══════════════════════════════════════════════════════════════════════════════


class ScopedAssessmentLineItemResource:
    """
    Scoped resource for operations on a specific assessment line item.

    Access via `client.assessment_line_items(line_item_id)`.

    Example:
        ```python
        line_item = await client.assessment_line_items(line_item_id).get()

        # To get results for an assessment line item, use assessment_results with a filter:
        results = await client.assessment_results.list(
            filter="assessmentLineItem.sourcedId='line-item-id'"
        )
        ```
    """

    def __init__(self, transport: Transport, line_item_id: str) -> None:
        self._transport = transport
        self._line_item_id = line_item_id
        self._base_path = f"{transport.paths.gradebook}/assessmentLineItems/{line_item_id}"

    async def get(self) -> AssessmentLineItem:
        """Get the assessment line item details."""
        response = await self._transport.get(self._base_path)
        return AssessmentLineItem(**response["assessmentLineItem"])


# ═══════════════════════════════════════════════════════════════════════════════
# ASSESSMENT LINE ITEMS RESOURCE
# ═══════════════════════════════════════════════════════════════════════════════


class AssessmentLineItemsResource(CRUDResourceNoSearch[AssessmentLineItem]):
    """
    Resource for assessment line items.

    Assessment line items are similar to line items but designed for
    formal assessments with more detailed tracking capabilities.

    Example:
        ```python
        # List all assessment line items
        items = await client.assessment_line_items.list()

        # Get specific assessment line item
        item = await client.assessment_line_items.get("line-item-id")

        # Create an assessment line item
        await client.assessment_line_items.create({
            "title": "Final Exam",
            "class": {"sourcedId": "class-id"},
            "resultValueMin": 0,
            "resultValueMax": 100,
        })

        # Patch an assessment line item
        await client.assessment_line_items.patch("line-item-id", {
            "title": "Updated Title",
        })
        ```
    """

    def __init__(self, transport: Transport) -> None:
        super().__init__(transport, "gradebook", "/assessmentLineItems")

    @property
    def _unwrap_key(self) -> str:
        return "assessmentLineItems"

    @property
    def _wrap_key(self) -> str:
        return "assessmentLineItem"

    @property
    def _model_class(self) -> type[AssessmentLineItem]:
        return AssessmentLineItem

    @property
    def _create_schema(self) -> type[BaseModel]:
        """Pydantic model for validating assessment line item create input."""
        return AssessmentLineItemCreateInput

    @property
    def _update_schema(self) -> type[BaseModel]:
        """Pydantic model for validating assessment line item update input."""
        return AssessmentLineItemCreateInput

    def __call__(self, line_item_id: str) -> ScopedAssessmentLineItemResource:
        """Get scoped resource for a specific assessment line item."""
        return ScopedAssessmentLineItemResource(self._transport, line_item_id)

    async def patch(self, sourced_id: str, data: dict[str, Any]) -> None:
        """
        Partially update an assessment line item.

        Only the fields provided will be updated. Other fields remain unchanged.

        Args:
            sourced_id: The assessment line item sourcedId
            data: The fields to update
        """
        body = {self._wrap_key: data}
        await self._transport.patch(f"{self._base_path}/{sourced_id}", body)
