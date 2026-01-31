"""
Organizations Resource

Access all organizations (schools, districts, departments, etc.).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...types import Organization, OrgCreateInput
from ..base import CRUDResourceNoSearch

if TYPE_CHECKING:
    from pydantic import BaseModel

    from ...lib.transport import Transport


# ═══════════════════════════════════════════════════════════════════════════════
# SCOPED ORG RESOURCE
# ═══════════════════════════════════════════════════════════════════════════════


class ScopedOrgResource:
    """
    Scoped resource for operations on a specific organization.

    Access via `client.orgs(org_id)`.

    Example:
        ```python
        org = await client.orgs(org_id).get()
        ```
    """

    def __init__(self, transport: Transport, org_id: str) -> None:
        self._transport = transport
        self._org_id = org_id
        self._base_path = f"{transport.paths.rostering}/orgs/{org_id}"

    async def get(self) -> Organization:
        """Get the organization details."""
        response = await self._transport.get(self._base_path)
        return Organization(**response["org"])


# ═══════════════════════════════════════════════════════════════════════════════
# ORGS RESOURCE
# ═══════════════════════════════════════════════════════════════════════════════


class OrgsResource(CRUDResourceNoSearch[Organization]):
    """
    Resource for all organizations.

    Includes schools, districts, departments, and other organization types.

    Example:
        ```python
        # List all organizations
        orgs = await client.orgs.list()

        # Get specific organization
        org = await client.orgs.get("org-id")

        # Filter by type
        districts = await client.orgs.list(filter="type='district'")
        schools = await client.orgs.list(filter="type='school'")
        ```
    """

    def __init__(self, transport: Transport) -> None:
        super().__init__(transport, "rostering", "/orgs")

    @property
    def _unwrap_key(self) -> str:
        return "orgs"

    @property
    def _wrap_key(self) -> str:
        return "org"

    @property
    def _model_class(self) -> type[Organization]:
        return Organization

    @property
    def _create_schema(self) -> type[BaseModel]:
        """Pydantic model for validating organization create input."""
        return OrgCreateInput

    @property
    def _update_schema(self) -> type[BaseModel]:
        """Pydantic model for validating organization update input."""
        return OrgCreateInput

    def __call__(self, org_id: str) -> ScopedOrgResource:
        """Get scoped resource for a specific organization."""
        return ScopedOrgResource(self._transport, org_id)
