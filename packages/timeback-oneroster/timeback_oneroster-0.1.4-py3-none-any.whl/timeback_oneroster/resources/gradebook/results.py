"""
Results Resource

Access and manage student grades/results.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...types import ResultCreateInput
from ...types.gradebook import Result
from ..base import CRUDResourceNoSearch

if TYPE_CHECKING:
    from pydantic import BaseModel

    from ...lib.transport import Transport


# ═══════════════════════════════════════════════════════════════════════════════
# SCOPED RESULT RESOURCE
# ═══════════════════════════════════════════════════════════════════════════════


class ScopedResultResource:
    """
    Scoped resource for operations on a specific result.

    Access via `client.results(result_id)`.

    Example:
        ```python
        result = await client.results(result_id).get()
        await client.results(result_id).delete()
        ```
    """

    def __init__(self, transport: Transport, result_id: str) -> None:
        self._transport = transport
        self._result_id = result_id
        self._base_path = f"{transport.paths.gradebook}/results/{result_id}"

    async def get(self) -> Result:
        """Get the result details."""
        response = await self._transport.get(self._base_path)
        return Result(**response["result"])

    async def delete(self) -> None:
        """Delete this result."""
        await self._transport.delete(self._base_path)


# ═══════════════════════════════════════════════════════════════════════════════
# RESULTS RESOURCE
# ═══════════════════════════════════════════════════════════════════════════════


class ResultsResource(CRUDResourceNoSearch[Result]):
    """
    Resource for student results (grades).

    Results link students to line items with their scores.

    Example:
        ```python
        # List all results
        results = await client.results.list()

        # Get specific result
        result = await client.results.get("result-id")

        # Create a result
        await client.results.create({
            "lineItem": {"sourcedId": "line-item-id"},
            "student": {"sourcedId": "student-id"},
            "score": 85.5,
            "scoreStatus": "fully graded",
            "scoreDate": "2024-01-22",
        })

        # Filter by student
        student_results = await client.results.list(
            filter="student.sourcedId='student-id'"
        )

        # Filter by line item
        item_results = await client.results.list(
            filter="lineItem.sourcedId='line-item-id'"
        )
        ```
    """

    def __init__(self, transport: Transport) -> None:
        super().__init__(transport, "gradebook", "/results")

    @property
    def _unwrap_key(self) -> str:
        return "results"

    @property
    def _wrap_key(self) -> str:
        return "result"

    @property
    def _model_class(self) -> type[Result]:
        return Result

    @property
    def _create_schema(self) -> type[BaseModel]:
        """Pydantic model for validating result create input."""
        return ResultCreateInput

    @property
    def _update_schema(self) -> type[BaseModel]:
        """Pydantic model for validating result update input."""
        return ResultCreateInput

    def __call__(self, result_id: str) -> ScopedResultResource:
        """Get scoped resource for a specific result."""
        return ScopedResultResource(self._transport, result_id)
