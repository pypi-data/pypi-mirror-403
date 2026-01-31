"""
Enrollments Resource

Access and manage user enrollments in classes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...types import Enrollment, EnrollmentCreateInput
from ..base import CRUDResourceNoSearch

if TYPE_CHECKING:
    from pydantic import BaseModel

    from ...lib.transport import Transport


# ═══════════════════════════════════════════════════════════════════════════════
# SCOPED ENROLLMENT RESOURCE
# ═══════════════════════════════════════════════════════════════════════════════


class ScopedEnrollmentResource:
    """
    Scoped resource for operations on a specific enrollment.

    Access via `client.enrollments(enrollment_id)`.

    Example:
        ```python
        enrollment = await client.enrollments(enrollment_id).get()
        await client.enrollments(enrollment_id).delete()
        ```
    """

    def __init__(self, transport: Transport, enrollment_id: str) -> None:
        self._transport = transport
        self._enrollment_id = enrollment_id
        self._base_path = f"{transport.paths.rostering}/enrollments/{enrollment_id}"

    async def get(self) -> Enrollment:
        """Get the enrollment details."""
        response = await self._transport.get(self._base_path)
        return Enrollment(**response["enrollment"])

    async def delete(self) -> None:
        """Delete this enrollment."""
        await self._transport.delete(self._base_path)


# ═══════════════════════════════════════════════════════════════════════════════
# ENROLLMENTS RESOURCE
# ═══════════════════════════════════════════════════════════════════════════════


class EnrollmentsResource(CRUDResourceNoSearch[Enrollment]):
    """
    Resource for enrollments.

    Enrollments link users to classes with a specific role.

    Example:
        ```python
        # List all enrollments
        enrollments = await client.enrollments.list()

        # Get specific enrollment
        enrollment = await client.enrollments.get("enrollment-id")

        # Create enrollment
        await client.enrollments.create({
            "user": {"sourcedId": "user-id"},
            "class": {"sourcedId": "class-id"},
            "role": "student",
        })

        # Filter enrollments by class
        class_enrollments = await client.enrollments.list(
            filter="class.sourcedId='class-id'"
        )
        ```
    """

    def __init__(self, transport: Transport) -> None:
        super().__init__(transport, "rostering", "/enrollments")

    @property
    def _unwrap_key(self) -> str:
        return "enrollments"

    @property
    def _wrap_key(self) -> str:
        return "enrollment"

    @property
    def _model_class(self) -> type[Enrollment]:
        return Enrollment

    @property
    def _create_schema(self) -> type[BaseModel]:
        """Pydantic model for validating enrollment create input."""
        return EnrollmentCreateInput

    @property
    def _update_schema(self) -> type[BaseModel]:
        """Pydantic model for validating enrollment update input."""
        return EnrollmentCreateInput

    def __call__(self, enrollment_id: str) -> ScopedEnrollmentResource:
        """Get scoped resource for a specific enrollment."""
        return ScopedEnrollmentResource(self._transport, enrollment_id)
