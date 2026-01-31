"""
Resources Resource

Access and manage digital learning resources.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ...types import ResourceCreateInput
from ...types.resources import Resource
from ..base import CRUDResourceNoSearch

if TYPE_CHECKING:
    from pydantic import BaseModel

    from ...lib.transport import Transport


# ═══════════════════════════════════════════════════════════════════════════════
# SCOPED RESOURCE RESOURCE
# ═══════════════════════════════════════════════════════════════════════════════


class ScopedResourceResource:
    """
    Scoped resource for operations on a specific resource.

    Access via `client.resources(resource_id)`.

    Example:
        ```python
        resource = await client.resources(resource_id).get()
        await client.resources(resource_id).export()
        ```
    """

    def __init__(self, transport: Transport, resource_id: str) -> None:
        self._transport = transport
        self._resource_id = resource_id
        self._base_path = f"{transport.paths.resources}/resources/{resource_id}"

    async def get(self) -> Resource:
        """Get the resource details."""
        response = await self._transport.get(self._base_path)
        return Resource(**response["resource"])

    async def export(self) -> dict[str, Any]:
        """
        Export this resource.

        Returns:
            Export response
        """
        return await self._transport.post(
            f"{self._transport.paths.resources}/resources/export/{self._resource_id}",
            {},
        )


# ═══════════════════════════════════════════════════════════════════════════════
# RESOURCES RESOURCE
# ═══════════════════════════════════════════════════════════════════════════════


class ResourcesResource(CRUDResourceNoSearch[Resource]):
    """
    Resource for digital learning resources.

    Resources represent external content that can be assigned to
    students through courses and classes.

    Example:
        ```python
        # List all resources
        resources = await client.resources.list()

        # Get specific resource
        resource = await client.resources.get("resource-id")

        # Create a resource
        await client.resources.create({
            "title": "Algebra Lesson 1",
            "vendorResourceId": "ext-123",
            "importance": "primary",
        })

        # Export a resource
        await client.resources.export("resource-id")
        # Or via scoped resource:
        await client.resources("resource-id").export()
        ```
    """

    def __init__(self, transport: Transport) -> None:
        # Use the resources service path
        super().__init__(transport, "resources", "/resources")

    @property
    def _unwrap_key(self) -> str:
        return "resources"

    @property
    def _wrap_key(self) -> str:
        return "resource"

    @property
    def _model_class(self) -> type[Resource]:
        return Resource

    @property
    def _create_schema(self) -> type[BaseModel]:
        """Pydantic model for validating resource create input."""
        return ResourceCreateInput

    @property
    def _update_schema(self) -> type[BaseModel]:
        """Pydantic model for validating resource update input."""
        return ResourceCreateInput

    def __call__(self, resource_id: str) -> ScopedResourceResource:
        """Get scoped resource for a specific resource."""
        return ScopedResourceResource(self._transport, resource_id)

    async def export(self, resource_id: str) -> dict[str, Any]:
        """
        Export a resource by ID.

        Args:
            resource_id: Resource sourcedId

        Returns:
            Export response
        """
        return await self._transport.post(
            f"{self._base_path}/export/{resource_id}",
            {},
        )
