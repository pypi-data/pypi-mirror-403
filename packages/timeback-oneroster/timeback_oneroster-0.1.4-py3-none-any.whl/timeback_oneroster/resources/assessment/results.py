"""
Assessment Results Resource

Access and manage standardized assessment results.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ...types import AssessmentResultCreateInput
from ...types.assessment import AssessmentResult
from ..base import CRUDResourceNoSearch

if TYPE_CHECKING:
    from pydantic import BaseModel

    from ...lib.transport import Transport


# ═══════════════════════════════════════════════════════════════════════════════
# ASSESSMENT RESULTS RESOURCE
# ═══════════════════════════════════════════════════════════════════════════════


class AssessmentResultsResource(CRUDResourceNoSearch[AssessmentResult]):
    """
    Resource for assessment results.

    Assessment results record scores for formal assessments.

    Example:
        ```python
        # List all assessment results
        results = await client.assessment_results.list()

        # Get specific assessment result
        result = await client.assessment_results.get("result-id")

        # Create an assessment result
        await client.assessment_results.create({
            "assessmentLineItem": {"sourcedId": "line-item-id"},
            "student": {"sourcedId": "student-id"},
            "score": 85.5,
            "scoreStatus": "fully graded",
            "scoreDate": "2024-01-22",
        })

        # Filter by student
        student_results = await client.assessment_results.list(
            filter="student.sourcedId='student-id'"
        )

        # Patch a result
        await client.assessment_results.patch("result-id", {
            "score": 90.0,
        })
        ```
    """

    def __init__(self, transport: Transport) -> None:
        super().__init__(transport, "gradebook", "/assessmentResults")

    @property
    def _unwrap_key(self) -> str:
        return "assessmentResults"

    @property
    def _wrap_key(self) -> str:
        return "assessmentResult"

    @property
    def _model_class(self) -> type[AssessmentResult]:
        return AssessmentResult

    @property
    def _create_schema(self) -> type[BaseModel]:
        """Pydantic model for validating assessment result create input."""
        return AssessmentResultCreateInput

    @property
    def _update_schema(self) -> type[BaseModel]:
        """Pydantic model for validating assessment result update input."""
        return AssessmentResultCreateInput

    async def patch(self, sourced_id: str, data: dict[str, Any]) -> None:
        """
        Partially update an assessment result.

        Only the fields provided will be updated. Other fields remain unchanged.

        Args:
            sourced_id: The assessment result sourcedId
            data: The fields to update
        """
        body = {self._wrap_key: data}
        await self._transport.patch(f"{self._base_path}/{sourced_id}", body)
