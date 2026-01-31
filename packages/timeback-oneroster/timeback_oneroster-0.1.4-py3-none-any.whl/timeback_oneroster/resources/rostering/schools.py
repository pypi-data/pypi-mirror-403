"""
Schools Resource

Access schools (organizations with type=school).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from timeback_common import validate_sourced_id, validate_with_schema

from ...lib.pagination import Paginator
from ...lib.params import build_list_params_no_search
from ...types import (
    AcademicSession,
    Class,
    Course,
    Enrollment,
    LineItemCreateInput,
    Organization,
    SchoolCreateInput,
    User,
)
from ..base import CRUDResourceNoSearch

if TYPE_CHECKING:
    from pydantic import BaseModel

    from ...lib.filter import WhereClause
    from ...lib.transport import Transport
    from ...types.gradebook import LineItem, ScoreScale


# ═══════════════════════════════════════════════════════════════════════════════
# SCOPED SCHOOL CLASS RESOURCE
# ═══════════════════════════════════════════════════════════════════════════════


class ScopedSchoolClassResource:
    """
    Scoped resource for a specific class within a school.

    Access via `client.schools(school_id).class_(class_id)`.

    Example:
        ```python
        enrollments = await client.schools(school_id).class_(class_id).enrollments()
        students = await client.schools(school_id).class_(class_id).students()
        ```
    """

    def __init__(self, transport: Transport, school_id: str, class_id: str) -> None:
        validate_sourced_id(school_id, "school")
        validate_sourced_id(class_id, "class")
        self._transport = transport
        self._school_id = school_id
        self._class_id = class_id
        self._base_path = f"{transport.paths.rostering}/schools/{school_id}/classes/{class_id}"

    # ── Enrollments ────────────────────────────────────────────────────────────

    async def enrollments(
        self,
        *,
        limit: int = 100,
        offset: int | None = None,
        sort: str | None = None,
        order_by: str | None = None,
        filter: str | None = None,
        where: WhereClause | None = None,
        fields: list[str] | None = None,
    ) -> list[Enrollment]:
        """List enrollments for this class within this school."""
        return await self.stream_enrollments(
            limit=limit,
            offset=offset,
            sort=sort,
            order_by=order_by,
            filter=filter,
            where=where,
            fields=fields,
        ).to_list()

    def stream_enrollments(
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
    ) -> Paginator[Enrollment]:
        """Stream enrollments with lazy pagination."""
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
            f"{self._base_path}/enrollments",
            unwrap_key="enrollments",
            params=params,
            limit=limit,
            max_items=max_items,
            transform=lambda item: Enrollment.model_validate(item),
        )

    # ── Students ───────────────────────────────────────────────────────────────

    async def students(
        self,
        *,
        limit: int = 100,
        offset: int | None = None,
        sort: str | None = None,
        order_by: str | None = None,
        filter: str | None = None,
        where: WhereClause | None = None,
        fields: list[str] | None = None,
    ) -> list[User]:
        """List students in this class at this school."""
        return await self.stream_students(
            limit=limit,
            offset=offset,
            sort=sort,
            order_by=order_by,
            filter=filter,
            where=where,
            fields=fields,
        ).to_list()

    def stream_students(
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
    ) -> Paginator[User]:
        """Stream students with lazy pagination."""
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
            f"{self._base_path}/students",
            unwrap_key="users",
            params=params,
            limit=limit,
            max_items=max_items,
            transform=lambda item: User.model_validate(item),
        )

    # ── Teachers ───────────────────────────────────────────────────────────────

    async def teachers(
        self,
        *,
        limit: int = 100,
        offset: int | None = None,
        sort: str | None = None,
        order_by: str | None = None,
        filter: str | None = None,
        where: WhereClause | None = None,
        fields: list[str] | None = None,
    ) -> list[User]:
        """List teachers for this class at this school."""
        return await self.stream_teachers(
            limit=limit,
            offset=offset,
            sort=sort,
            order_by=order_by,
            filter=filter,
            where=where,
            fields=fields,
        ).to_list()

    def stream_teachers(
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
    ) -> Paginator[User]:
        """Stream teachers with lazy pagination."""
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
            f"{self._base_path}/teachers",
            unwrap_key="users",
            params=params,
            limit=limit,
            max_items=max_items,
            transform=lambda item: User.model_validate(item),
        )


# ═══════════════════════════════════════════════════════════════════════════════
# SCOPED SCHOOL RESOURCE
# ═══════════════════════════════════════════════════════════════════════════════


class ScopedSchoolResource:
    """
    Scoped resource for operations on a specific school.

    Access via `client.schools(school_id)`.

    Example:
        ```python
        school = await client.schools(school_id).get()
        classes = await client.schools(school_id).classes()
        students = await client.schools(school_id).students()
        line_items = await client.schools(school_id).line_items()
        ```
    """

    def __init__(self, transport: Transport, school_id: str) -> None:
        validate_sourced_id(school_id, "school")
        self._transport = transport
        self._school_id = school_id
        self._base_path = f"{transport.paths.rostering}/schools/{school_id}"
        self._gradebook_path = f"{transport.paths.gradebook}/schools/{school_id}"

    async def get(self) -> Organization:
        """Get the school details."""
        response = await self._transport.get(self._base_path)
        return Organization(**response["org"])

    def class_(self, class_id: str) -> ScopedSchoolClassResource:
        """
        Scope to a specific class within this school.

        Args:
            class_id: The class sourcedId

        Returns:
            Scoped class resource for school-class operations
        """
        return ScopedSchoolClassResource(self._transport, self._school_id, class_id)

    # ── Classes ────────────────────────────────────────────────────────────────

    async def classes(
        self,
        *,
        limit: int = 100,
        offset: int | None = None,
        sort: str | None = None,
        order_by: str | None = None,
        filter: str | None = None,
        where: WhereClause | None = None,
        fields: list[str] | None = None,
    ) -> list[Class]:
        """List classes at this school."""
        return await self.stream_classes(
            limit=limit,
            offset=offset,
            sort=sort,
            order_by=order_by,
            filter=filter,
            where=where,
            fields=fields,
        ).to_list()

    def stream_classes(
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
    ) -> Paginator[Class]:
        """Stream classes with lazy pagination."""
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
            f"{self._base_path}/classes",
            unwrap_key="classes",
            params=params,
            limit=limit,
            max_items=max_items,
            transform=lambda item: Class.model_validate(item),
        )

    # ── Students ───────────────────────────────────────────────────────────────

    async def students(
        self,
        *,
        limit: int = 100,
        offset: int | None = None,
        sort: str | None = None,
        order_by: str | None = None,
        filter: str | None = None,
        where: WhereClause | None = None,
        fields: list[str] | None = None,
    ) -> list[User]:
        """List students at this school."""
        return await self.stream_students(
            limit=limit,
            offset=offset,
            sort=sort,
            order_by=order_by,
            filter=filter,
            where=where,
            fields=fields,
        ).to_list()

    def stream_students(
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
    ) -> Paginator[User]:
        """Stream students with lazy pagination."""
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
            f"{self._base_path}/students",
            unwrap_key="users",
            params=params,
            limit=limit,
            max_items=max_items,
            transform=lambda item: User.model_validate(item),
        )

    # ── Teachers ───────────────────────────────────────────────────────────────

    async def teachers(
        self,
        *,
        limit: int = 100,
        offset: int | None = None,
        sort: str | None = None,
        order_by: str | None = None,
        filter: str | None = None,
        where: WhereClause | None = None,
        fields: list[str] | None = None,
    ) -> list[User]:
        """List teachers at this school."""
        return await self.stream_teachers(
            limit=limit,
            offset=offset,
            sort=sort,
            order_by=order_by,
            filter=filter,
            where=where,
            fields=fields,
        ).to_list()

    def stream_teachers(
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
    ) -> Paginator[User]:
        """Stream teachers with lazy pagination."""
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
            f"{self._base_path}/teachers",
            unwrap_key="users",
            params=params,
            limit=limit,
            max_items=max_items,
            transform=lambda item: User.model_validate(item),
        )

    # ── Courses ────────────────────────────────────────────────────────────────

    async def courses(
        self,
        *,
        limit: int = 100,
        offset: int | None = None,
        sort: str | None = None,
        order_by: str | None = None,
        filter: str | None = None,
        where: WhereClause | None = None,
        fields: list[str] | None = None,
    ) -> list[Course]:
        """List courses at this school."""
        return await self.stream_courses(
            limit=limit,
            offset=offset,
            sort=sort,
            order_by=order_by,
            filter=filter,
            where=where,
            fields=fields,
        ).to_list()

    def stream_courses(
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
    ) -> Paginator[Course]:
        """Stream courses with lazy pagination."""
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
            f"{self._base_path}/courses",
            unwrap_key="courses",
            params=params,
            limit=limit,
            max_items=max_items,
            transform=lambda item: Course.model_validate(item),
        )

    # ── Enrollments ────────────────────────────────────────────────────────────

    async def enrollments(
        self,
        *,
        limit: int = 100,
        offset: int | None = None,
        sort: str | None = None,
        order_by: str | None = None,
        filter: str | None = None,
        where: WhereClause | None = None,
        fields: list[str] | None = None,
    ) -> list[Enrollment]:
        """List enrollments at this school."""
        return await self.stream_enrollments(
            limit=limit,
            offset=offset,
            sort=sort,
            order_by=order_by,
            filter=filter,
            where=where,
            fields=fields,
        ).to_list()

    def stream_enrollments(
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
    ) -> Paginator[Enrollment]:
        """Stream enrollments with lazy pagination."""
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
            f"{self._base_path}/enrollments",
            unwrap_key="enrollments",
            params=params,
            limit=limit,
            max_items=max_items,
            transform=lambda item: Enrollment.model_validate(item),
        )

    # ── Terms ──────────────────────────────────────────────────────────────────

    async def terms(
        self,
        *,
        limit: int = 100,
        offset: int | None = None,
        sort: str | None = None,
        order_by: str | None = None,
        filter: str | None = None,
        where: WhereClause | None = None,
        fields: list[str] | None = None,
    ) -> list[AcademicSession]:
        """List terms/academic sessions for this school."""
        return await self.stream_terms(
            limit=limit,
            offset=offset,
            sort=sort,
            order_by=order_by,
            filter=filter,
            where=where,
            fields=fields,
        ).to_list()

    def stream_terms(
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
    ) -> Paginator[AcademicSession]:
        """Stream terms with lazy pagination."""
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
            f"{self._base_path}/terms",
            unwrap_key="terms",
            params=params,
            limit=limit,
            max_items=max_items,
            transform=lambda item: AcademicSession.model_validate(item),
        )

    # ── Line Items (Gradebook) ─────────────────────────────────────────────────

    async def line_items(
        self,
        *,
        limit: int = 100,
        offset: int | None = None,
        sort: str | None = None,
        order_by: str | None = None,
        filter: str | None = None,
        where: WhereClause | None = None,
        fields: list[str] | None = None,
    ) -> list[LineItem]:
        """List line items (assignments) in this school."""
        return await self.stream_line_items(
            limit=limit,
            offset=offset,
            sort=sort,
            order_by=order_by,
            filter=filter,
            where=where,
            fields=fields,
        ).to_list()

    def stream_line_items(
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
    ) -> Paginator[LineItem]:
        """Stream line items with lazy pagination."""
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
            f"{self._gradebook_path}/lineItems",
            unwrap_key="lineItems",
            params=params,
            limit=limit,
            max_items=max_items,
        )

    async def create_line_item(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Create a line item (assignment) in this school.

        Args:
            data: Line item data

        Returns:
            Create response with sourcedIdPairs

        Raises:
            InputValidationError: If data fails client-side validation
        """
        validate_with_schema(LineItemCreateInput, data, "line item")
        return await self._transport.post(
            f"{self._gradebook_path}/lineItems",
            {"lineItems": data},
        )

    # ── Score Scales (Gradebook) ───────────────────────────────────────────────

    async def score_scales(
        self,
        *,
        limit: int = 100,
        offset: int | None = None,
        sort: str | None = None,
        order_by: str | None = None,
        filter: str | None = None,
        where: WhereClause | None = None,
        fields: list[str] | None = None,
    ) -> list[ScoreScale]:
        """List score scales for this school."""
        return await self.stream_score_scales(
            limit=limit,
            offset=offset,
            sort=sort,
            order_by=order_by,
            filter=filter,
            where=where,
            fields=fields,
        ).to_list()

    def stream_score_scales(
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
    ) -> Paginator[ScoreScale]:
        """Stream score scales with lazy pagination."""
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
            f"{self._gradebook_path}/scoreScales",
            unwrap_key="scoreScales",
            params=params,
            limit=limit,
            max_items=max_items,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# SCHOOLS RESOURCE
# ═══════════════════════════════════════════════════════════════════════════════


class SchoolsResource(CRUDResourceNoSearch[Organization]):
    """
    Resource for schools (organizations with type=school).

    Example:
        ```python
        # List all schools
        schools = await client.schools.list()

        # Get specific school
        school = await client.schools.get("school-id")

        # Nested resources
        classes = await client.schools("school-id").classes()
        students = await client.schools("school-id").students()
        line_items = await client.schools("school-id").line_items()
        ```
    """

    def __init__(self, transport: Transport) -> None:
        super().__init__(transport, "rostering", "/schools")

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
        """Pydantic model for validating school create input."""
        return SchoolCreateInput

    @property
    def _update_schema(self) -> type[BaseModel]:
        """Pydantic model for validating school update input."""
        return SchoolCreateInput

    def __call__(self, school_id: str) -> ScopedSchoolResource:
        """Get scoped resource for a specific school."""
        return ScopedSchoolResource(self._transport, school_id)
