"""
Score Scales Resource

Access and manage score scales for grading.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...types import ScoreScaleCreateInput
from ...types.gradebook import ScoreScale
from ..base import CRUDResourceNoSearch

if TYPE_CHECKING:
    from pydantic import BaseModel

    from ...lib.transport import Transport


# ═══════════════════════════════════════════════════════════════════════════════
# SCOPED SCORE SCALE RESOURCE
# ═══════════════════════════════════════════════════════════════════════════════


class ScopedScoreScaleResource:
    """
    Scoped resource for operations on a specific score scale.

    Access via `client.score_scales(scale_id)`.

    Example:
        ```python
        scale = await client.score_scales(scale_id).get()
        ```
    """

    def __init__(self, transport: Transport, scale_id: str) -> None:
        self._transport = transport
        self._scale_id = scale_id
        self._base_path = f"{transport.paths.gradebook}/scoreScales/{scale_id}"

    async def get(self) -> ScoreScale:
        """Get the score scale details."""
        response = await self._transport.get(self._base_path)
        return ScoreScale(**response["scoreScale"])

    async def delete(self) -> None:
        """Delete this score scale."""
        await self._transport.delete(self._base_path)


# ═══════════════════════════════════════════════════════════════════════════════
# SCORE SCALES RESOURCE
# ═══════════════════════════════════════════════════════════════════════════════


class ScoreScalesResource(CRUDResourceNoSearch[ScoreScale]):
    """
    Resource for score scales.

    Score scales define grading systems (e.g., letter grades, pass/fail).

    Example:
        ```python
        # List all score scales
        scales = await client.score_scales.list()

        # Get specific score scale
        scale = await client.score_scales.get("scale-id")

        # Create a score scale
        await client.score_scales.create({
            "title": "Letter Grades",
            "scoreScaleValues": [
                {"value": "A", "description": "90-100%"},
                {"value": "B", "description": "80-89%"},
                {"value": "C", "description": "70-79%"},
                {"value": "D", "description": "60-69%"},
                {"value": "F", "description": "Below 60%"},
            ]
        })
        ```
    """

    def __init__(self, transport: Transport) -> None:
        super().__init__(transport, "gradebook", "/scoreScales")

    @property
    def _unwrap_key(self) -> str:
        return "scoreScales"

    @property
    def _wrap_key(self) -> str:
        return "scoreScale"

    @property
    def _model_class(self) -> type[ScoreScale]:
        return ScoreScale

    @property
    def _create_schema(self) -> type[BaseModel]:
        """Pydantic model for validating score scale create input."""
        return ScoreScaleCreateInput

    @property
    def _update_schema(self) -> type[BaseModel]:
        """Pydantic model for validating score scale update input."""
        return ScoreScaleCreateInput

    def __call__(self, scale_id: str) -> ScopedScoreScaleResource:
        """Get scoped resource for a specific score scale."""
        return ScopedScoreScaleResource(self._transport, scale_id)
