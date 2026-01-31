"""
Demographics Resource

Access demographic information for users.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from timeback_common import InputValidationError, ValidationIssue

from ...types import Demographics, DemographicsCreateInput
from ..base import CRUDResourceNoSearch

if TYPE_CHECKING:
    from pydantic import BaseModel

    from ...lib.transport import Transport


# ═══════════════════════════════════════════════════════════════════════════════
# SCOPED DEMOGRAPHICS RESOURCE
# ═══════════════════════════════════════════════════════════════════════════════


class ScopedDemographicsResource:
    """
    Scoped resource for operations on a specific demographics record.

    Access via `client.demographics(user_id)`.

    Example:
        ```python
        demographics = await client.demographics(user_id).get()
        ```
    """

    def __init__(self, transport: Transport, user_id: str) -> None:
        self._transport = transport
        self._user_id = user_id
        self._base_path = f"{transport.paths.rostering}/demographics/{user_id}"

    async def get(self) -> Demographics:
        """Get the demographics record."""
        response = await self._transport.get(self._base_path)
        return Demographics(**response["demographics"])


# ═══════════════════════════════════════════════════════════════════════════════
# DEMOGRAPHICS RESOURCE
# ═══════════════════════════════════════════════════════════════════════════════


class DemographicsResource(CRUDResourceNoSearch[Demographics]):
    """
    Resource for user demographics.

    Demographics records are keyed by user sourcedId.

    Example:
        ```python
        # List all demographics
        all_demographics = await client.demographics.list()

        # Get demographics for a specific user
        user_demographics = await client.demographics.get("user-id")

        # Or via scoped resource
        user_demographics = await client.demographics("user-id").get()
        ```
    """

    def __init__(self, transport: Transport) -> None:
        super().__init__(transport, "rostering", "/demographics")

    @property
    def _unwrap_key(self) -> str:
        return "demographics"

    @property
    def _wrap_key(self) -> str:
        return "demographics"

    @property
    def _model_class(self) -> type[Demographics]:
        return Demographics

    @property
    def _create_schema(self) -> type[BaseModel]:
        """Pydantic model for validating demographics create input."""
        return DemographicsCreateInput

    @property
    def _update_schema(self) -> type[BaseModel]:
        """
        Pydantic model for validating demographics update input.

        Beyond AI requires `demographics.sourcedId` in the request body, even though the
        record is keyed by the sourcedId in the path. We validate that requirement client-side.
        """
        return DemographicsCreateInput

    def __call__(self, user_id: str) -> ScopedDemographicsResource:
        """Get scoped resource for a specific user's demographics."""
        return ScopedDemographicsResource(self._transport, user_id)

    async def update(self, sourced_id: str, data: dict[str, Any]) -> None:
        """
        Update demographics.

        The Beyond AI API requires `sourcedId` in the request body; if omitted, inject it from
        the path parameter so callers can pass partial demographics payloads.

        Raises:
            InputValidationError: If data contains a sourcedId that doesn't match the path.
        """
        if "sourcedId" in data:
            if data["sourcedId"] != sourced_id:
                raise InputValidationError(
                    message=(
                        f"sourcedId in data ('{data['sourcedId']}') does not match "
                        f"path parameter ('{sourced_id}')"
                    ),
                    issues=[
                        ValidationIssue(
                            path="sourcedId",
                            message=f"Must match path parameter '{sourced_id}'",
                        )
                    ],
                )
        else:
            data = {"sourcedId": sourced_id, **data}
        await super().update(sourced_id, data)
