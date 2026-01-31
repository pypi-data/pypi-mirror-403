"""
Classes Resource

Access class sections.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from timeback_common import validate_sourced_id, validate_with_schema

from ...lib.pagination import Paginator
from ...lib.params import build_list_params_no_search
from ...types import (
    Class,
    ClassCreateInput,
    ClassUpdateInput,
    EnrollInput,
    Enrollment,
    LineItemCreateInput,
    ResultCreateInput,
    User,
)
from ...utils import parse_grades
from ..base import CRUDResourceNoSearch

if TYPE_CHECKING:
    from pydantic import BaseModel

    from ...lib.filter import WhereClause
    from ...lib.transport import Transport
    from ...types.gradebook import Category, LineItem, Result, ScoreScale
    from ...types.resources import Resource


# ═══════════════════════════════════════════════════════════════════════════════
# SCOPED CLASS ACADEMIC SESSION RESOURCE
# ═══════════════════════════════════════════════════════════════════════════════


class ScopedClassAcademicSessionResource:
    """
    Scoped resource for a specific academic session within a class.

    Access via `client.classes(class_id).academic_session(session_id)`.

    Example:
        ```python
        # Create a result for a student in this class/session
        await client.classes(class_id).academic_session(session_id).create_result({
            "student": {"sourcedId": "student1"},
            "lineItem": {"sourcedId": "li1"},
            "scoreStatus": "fully graded",
            "scoreDate": "2024-12-24",
            "score": 85,
        })
        ```
    """

    def __init__(self, transport: Transport, class_id: str, session_id: str) -> None:
        validate_sourced_id(class_id, "class")
        validate_sourced_id(session_id, "academic session")
        self._transport = transport
        self._class_id = class_id
        self._session_id = session_id
        self._gradebook_path = (
            f"{transport.paths.gradebook}/classes/{class_id}/academicSessions/{session_id}"
        )

    async def create_result(self, result: dict[str, Any]) -> dict[str, Any]:
        """
        Create a result for this class and academic session.

        Args:
            result: Result data including student, lineItem, score, and scoreDate

        Returns:
            Create response with sourcedIdPairs

        Raises:
            InputValidationError: If result data fails client-side validation
        """
        validate_with_schema(ResultCreateInput, result, "result")
        return await self._transport.post(
            f"{self._gradebook_path}/results",
            {"results": result},
        )


# ═══════════════════════════════════════════════════════════════════════════════
# SCOPED CLASS STUDENT RESOURCE
# ═══════════════════════════════════════════════════════════════════════════════


class ScopedClassStudentResource:
    """
    Scoped resource for a specific student within a class.

    Access via `client.classes(class_id).student(student_id)`.

    Example:
        ```python
        results = await client.classes(class_id).student(student_id).results()
        ```
    """

    def __init__(self, transport: Transport, class_id: str, student_id: str) -> None:
        validate_sourced_id(class_id, "class")
        validate_sourced_id(student_id, "student")
        self._transport = transport
        self._class_id = class_id
        self._student_id = student_id
        self._gradebook_path = (
            f"{transport.paths.gradebook}/classes/{class_id}/students/{student_id}"
        )

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
        """List results for this student in this class."""
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
            f"{self._gradebook_path}/results",
            unwrap_key="results",
            params=params,
            limit=limit,
            max_items=max_items,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# SCOPED CLASS LINE ITEM RESOURCE
# ═══════════════════════════════════════════════════════════════════════════════


class ScopedClassLineItemResource:
    """
    Scoped resource for a specific line item within a class.

    Access via `client.classes(class_id).line_item(line_item_id)`.

    Example:
        ```python
        results = await client.classes(class_id).line_item(line_item_id).results()
        ```
    """

    def __init__(self, transport: Transport, class_id: str, line_item_id: str) -> None:
        validate_sourced_id(class_id, "class")
        validate_sourced_id(line_item_id, "line item")
        self._transport = transport
        self._class_id = class_id
        self._line_item_id = line_item_id
        self._gradebook_path = (
            f"{transport.paths.gradebook}/classes/{class_id}/lineItems/{line_item_id}"
        )

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
        """List results for this line item in this class."""
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
            f"{self._gradebook_path}/results",
            unwrap_key="results",
            params=params,
            limit=limit,
            max_items=max_items,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# SCOPED CLASS RESOURCE
# ═══════════════════════════════════════════════════════════════════════════════


class ScopedClassResource:
    """
    Scoped resource for operations on a specific class.

    Access via `client.classes(class_id)`.

    Example:
        ```python
        cls = await client.classes(class_id).get()
        students = await client.classes(class_id).students()
        teachers = await client.classes(class_id).teachers()
        line_items = await client.classes(class_id).line_items()
        student_results = await client.classes(class_id).student(student_id).results()
        ```
    """

    def __init__(self, transport: Transport, class_id: str) -> None:
        validate_sourced_id(class_id, "class")
        self._transport = transport
        self._class_id = class_id
        self._rostering_path = f"{transport.paths.rostering}/classes/{class_id}"
        self._gradebook_path = f"{transport.paths.gradebook}/classes/{class_id}"

    async def get(self) -> Class:
        """Get the class details."""
        response = await self._transport.get(self._rostering_path)
        cls_data = response["class"]
        # Apply grades normalization
        if cls_data.get("grades"):
            cls_data["grades"] = parse_grades(cls_data["grades"])
        return Class(**cls_data)

    # ── Nested Scopes ──────────────────────────────────────────────────────────

    def student(self, student_id: str) -> ScopedClassStudentResource:
        """
        Get a scoped resource for a specific student in this class.

        Args:
            student_id: Student ID

        Returns:
            Scoped resource for the student

        Example:
            ```python
            results = await client.classes(class_id).student(student_id).results()
            ```
        """
        return ScopedClassStudentResource(self._transport, self._class_id, student_id)

    def line_item(self, line_item_id: str) -> ScopedClassLineItemResource:
        """
        Get a scoped resource for a specific line item in this class.

        Args:
            line_item_id: Line item ID

        Returns:
            Scoped resource for the line item

        Example:
            ```python
            results = await client.classes(class_id).line_item(line_item_id).results()
            ```
        """
        return ScopedClassLineItemResource(self._transport, self._class_id, line_item_id)

    def academic_session(self, session_id: str) -> ScopedClassAcademicSessionResource:
        """
        Get a scoped resource for a specific academic session in this class.

        Args:
            session_id: Academic session ID (term, grading period, etc.)

        Returns:
            Scoped resource for session-scoped operations

        Example:
            ```python
            # Create a result for a grading period
            await client.classes(class_id).academic_session(session_id).create_result({
                "student": {"sourcedId": "student1"},
                "lineItem": {"sourcedId": "lineItem1"},
                "scoreStatus": "fully graded",
                "scoreDate": "2024-12-24",
                "score": 85,
            })
            ```
        """
        return ScopedClassAcademicSessionResource(self._transport, self._class_id, session_id)

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
        """List students enrolled in this class."""
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
            f"{self._rostering_path}/students",
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
        """List teachers assigned to this class."""
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
            f"{self._rostering_path}/teachers",
            unwrap_key="users",
            params=params,
            limit=limit,
            max_items=max_items,
            transform=lambda item: User.model_validate(item),
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
        """List enrollments for this class."""
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
            f"{self._rostering_path}/enrollments",
            unwrap_key="enrollments",
            params=params,
            limit=limit,
            max_items=max_items,
        )

    # ── Enroll ─────────────────────────────────────────────────────────────────

    async def enroll(
        self,
        data: EnrollInput | dict[str, Any],
    ) -> dict[str, Any]:
        """
        Enroll a user in this class.

        Args:
            data: Enrollment input payload (dict or `EnrollInput`)

        Returns:
            Create response

        Raises:
            InputValidationError: If inputs fail client-side validation
        """
        validate_with_schema(EnrollInput, data, "enrollment")
        model = EnrollInput.model_validate(data)
        payload = model.model_dump(by_alias=True, exclude_none=True)

        user_sourced_id = payload["sourcedId"]
        role = payload["role"]
        endpoint = "students" if role == "student" else "teachers"

        enrollment: dict[str, Any] = {"user": {"sourcedId": user_sourced_id}}

        # `primary` is modeled as string booleans; API expects boolean.
        if "primary" in payload:
            enrollment["primary"] = payload["primary"] == "true"
        if "beginDate" in payload:
            enrollment["beginDate"] = payload["beginDate"]
        if "endDate" in payload:
            enrollment["endDate"] = payload["endDate"]
        if "metadata" in payload:
            enrollment["metadata"] = payload["metadata"]

        return await self._transport.post(
            f"{self._rostering_path}/{endpoint}",
            {"enrollment": enrollment},
        )

    async def enroll_user(
        self,
        user_id: str,
        *,
        role: str = "student",
        primary: bool | None = None,
        begin_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        """
        Convenience helper for enrolling a user.

        Prefer `enroll({...})` for a consistent payload-based write API.
        """
        payload: dict[str, Any] = {"sourcedId": user_id, "role": role}
        if primary is not None:
            payload["primary"] = "true" if primary else "false"
        if begin_date is not None:
            payload["beginDate"] = begin_date
        if end_date is not None:
            payload["endDate"] = end_date
        return await self.enroll(payload)

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
        """List line items (assignments) in this class."""
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
        Create a line item (assignment) in this class.

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

    # ── Results (Gradebook) ────────────────────────────────────────────────────

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
        """List results in this class."""
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
            f"{self._gradebook_path}/results",
            unwrap_key="results",
            params=params,
            limit=limit,
            max_items=max_items,
        )

    # ── Resources ──────────────────────────────────────────────────────────────

    async def resources(
        self,
        *,
        limit: int = 100,
        offset: int | None = None,
        sort: str | None = None,
        order_by: str | None = None,
        filter: str | None = None,
        where: WhereClause | None = None,
        fields: list[str] | None = None,
    ) -> list[Resource]:
        """List resources for this class."""
        return await self.stream_resources(
            limit=limit,
            offset=offset,
            sort=sort,
            order_by=order_by,
            filter=filter,
            where=where,
            fields=fields,
        ).to_list()

    def stream_resources(
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
    ) -> Paginator[Resource]:
        """Stream resources with lazy pagination."""
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
            f"{self._transport.paths.resources}/resources/classes/{self._class_id}/resources",
            unwrap_key="resources",
            params=params,
            limit=limit,
            max_items=max_items,
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
        """List score scales for this class."""
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

    # ── Categories (Gradebook) ─────────────────────────────────────────────────

    async def categories(
        self,
        *,
        limit: int = 100,
        offset: int | None = None,
        sort: str | None = None,
        order_by: str | None = None,
        filter: str | None = None,
        where: WhereClause | None = None,
        fields: list[str] | None = None,
    ) -> list[Category]:
        """List categories for this class."""
        return await self.stream_categories(
            limit=limit,
            offset=offset,
            sort=sort,
            order_by=order_by,
            filter=filter,
            where=where,
            fields=fields,
        ).to_list()

    def stream_categories(
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
    ) -> Paginator[Category]:
        """Stream categories with lazy pagination."""
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
            f"{self._gradebook_path}/categories",
            unwrap_key="categories",
            params=params,
            limit=limit,
            max_items=max_items,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# CLASSES RESOURCE
# ═══════════════════════════════════════════════════════════════════════════════


class ClassesResource(CRUDResourceNoSearch[Class]):
    """
    Resource for class sections.

    Example:
        ```python
        # List all classes
        classes = await client.classes.list()

        # Get specific class
        cls = await client.classes.get("class-id")

        # Nested resources
        students = await client.classes("class-id").students()
        teachers = await client.classes("class-id").teachers()
        line_items = await client.classes("class-id").line_items()
        ```
    """

    def __init__(self, transport: Transport) -> None:
        super().__init__(transport, "rostering", "/classes")

    @property
    def _unwrap_key(self) -> str:
        return "classes"

    @property
    def _wrap_key(self) -> str:
        return "class"

    @property
    def _model_class(self) -> type[Class]:
        return Class

    @property
    def _create_schema(self) -> type[BaseModel]:
        """Pydantic model for validating class create input."""
        return ClassCreateInput

    @property
    def _update_schema(self) -> type[BaseModel]:
        """Pydantic model for validating class update input."""
        return ClassUpdateInput

    def _transform(self, entity: dict | Class) -> Class:
        """
        Transform class response by converting to model and normalizing grades.
        """
        # First convert dict to model
        model = super()._transform(entity)

        # Then normalize grades if present
        if model.grades is not None:
            grades = parse_grades(model.grades)  # type: ignore[arg-type]
            return model.model_copy(update={"grades": grades})
        return model

    def __call__(self, class_id: str) -> ScopedClassResource:
        """Get scoped resource for a specific class."""
        return ScopedClassResource(self._transport, class_id)
