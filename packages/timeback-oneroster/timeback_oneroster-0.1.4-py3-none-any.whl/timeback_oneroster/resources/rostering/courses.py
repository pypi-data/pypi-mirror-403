"""
Courses Resource

Access courses offered by schools.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ...lib.pagination import Paginator
from ...types import Class, Course, CourseCreateInput
from ...types.resources import ComponentResource, CourseComponent, Resource
from ..base import CRUDResource

if TYPE_CHECKING:
    from pydantic import BaseModel

    from ...lib.transport import Transport


# ═══════════════════════════════════════════════════════════════════════════════
# SCOPED COURSE RESOURCE
# ═══════════════════════════════════════════════════════════════════════════════


class ScopedCourseResource:
    """
    Scoped resource for operations on a specific course.

    Access via `client.courses(course_id)`.

    Example:
        ```python
        course = await client.courses(course_id).get()
        classes = await client.courses(course_id).classes()
        components = await client.courses(course_id).components()
        resources = await client.courses(course_id).resources()
        ```
    """

    def __init__(self, transport: Transport, course_id: str) -> None:
        self._transport = transport
        self._course_id = course_id
        self._base_path = f"{transport.paths.rostering}/courses/{course_id}"

    async def get(self) -> Course:
        """Get the course details."""
        response = await self._transport.get(self._base_path)
        return Course(**response["course"])

    # ── Classes ────────────────────────────────────────────────────────────────

    async def classes(
        self,
        *,
        limit: int = 100,
        offset: int | None = None,
        filter: str | None = None,
    ) -> list[Class]:
        """List classes (sections) for this course."""
        return await self.stream_classes(limit=limit, offset=offset, filter=filter).to_list()

    def stream_classes(
        self,
        *,
        limit: int = 100,
        offset: int | None = None,
        filter: str | None = None,
        max_items: int | None = None,
    ) -> Paginator[Class]:
        """Stream classes with lazy pagination."""
        params: dict[str, Any] = {}
        if offset is not None:
            params["offset"] = offset
        if filter is not None:
            params["filter"] = filter

        return Paginator(
            self._transport,
            f"{self._base_path}/classes",
            unwrap_key="classes",
            params=params,
            limit=limit,
            max_items=max_items,
            transform=lambda item: Class.model_validate(item),
        )

    # ── Components ─────────────────────────────────────────────────────────────

    async def components(
        self,
        *,
        limit: int = 100,
        offset: int | None = None,
        filter: str | None = None,
    ) -> list[CourseComponent]:
        """List components for this course."""
        return await self.stream_components(limit=limit, offset=offset, filter=filter).to_list()

    def stream_components(
        self,
        *,
        limit: int = 100,
        offset: int | None = None,
        filter: str | None = None,
        max_items: int | None = None,
    ) -> Paginator[CourseComponent]:
        """Stream components with lazy pagination."""
        params: dict[str, Any] = {"filter": f"course.sourcedId='{self._course_id}'"}
        if offset is not None:
            params["offset"] = offset
        if filter is not None:
            # Combine filters
            params["filter"] = f"{params['filter']} AND {filter}"

        return Paginator(
            self._transport,
            f"{self._transport.paths.rostering}/courses/components",
            unwrap_key="courseComponents",
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
        filter: str | None = None,
    ) -> list[Resource]:
        """List resources for this course."""
        return await self.stream_resources(limit=limit, offset=offset, filter=filter).to_list()

    def stream_resources(
        self,
        *,
        limit: int = 100,
        offset: int | None = None,
        filter: str | None = None,
        max_items: int | None = None,
    ) -> Paginator[Resource]:
        """Stream resources with lazy pagination."""
        params: dict[str, Any] = {}
        if offset is not None:
            params["offset"] = offset
        if filter is not None:
            params["filter"] = filter

        return Paginator(
            self._transport,
            f"{self._transport.paths.resources}/resources/courses/{self._course_id}/resources",
            unwrap_key="resources",
            params=params,
            limit=limit,
            max_items=max_items,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# COURSES RESOURCE
# ═══════════════════════════════════════════════════════════════════════════════


class CoursesResource(CRUDResource[Course]):
    """
    Resource for courses.

    Example:
        ```python
        # List all courses
        courses = await client.courses.list()

        # Get specific course
        course = await client.courses.get("course-id")

        # Get classes for a course
        classes = await client.courses("course-id").classes()

        # Component management
        components = await client.courses.components()
        await client.courses.create_component({...})
        ```
    """

    def __init__(self, transport: Transport) -> None:
        super().__init__(transport, "rostering", "/courses")

    @property
    def _unwrap_key(self) -> str:
        return "courses"

    @property
    def _wrap_key(self) -> str:
        return "course"

    @property
    def _model_class(self) -> type[Course]:
        return Course

    @property
    def _create_schema(self) -> type[BaseModel]:
        """Pydantic model for validating course create input."""
        return CourseCreateInput

    @property
    def _update_schema(self) -> type[BaseModel]:
        """Pydantic model for validating course update input."""
        return CourseCreateInput

    def __call__(self, course_id: str) -> ScopedCourseResource:
        """Get scoped resource for a specific course."""
        return ScopedCourseResource(self._transport, course_id)

    # ── Course Components ──────────────────────────────────────────────────────

    async def components(
        self,
        *,
        limit: int = 100,
        offset: int | None = None,
        filter: str | None = None,
    ) -> list[CourseComponent]:
        """List all course components."""
        return await self.stream_components(limit=limit, offset=offset, filter=filter).to_list()

    def stream_components(
        self,
        *,
        limit: int = 100,
        offset: int | None = None,
        filter: str | None = None,
        max_items: int | None = None,
    ) -> Paginator[CourseComponent]:
        """Stream course components with lazy pagination."""
        params: dict[str, Any] = {}
        if offset is not None:
            params["offset"] = offset
        if filter is not None:
            params["filter"] = filter

        return Paginator(
            self._transport,
            f"{self._base_path}/components",
            unwrap_key="courseComponents",
            params=params,
            limit=limit,
            max_items=max_items,
        )

    async def get_component(self, sourced_id: str) -> CourseComponent:
        """Get a specific course component."""
        response = await self._transport.get(f"{self._base_path}/components/{sourced_id}")
        return CourseComponent(**response["courseComponent"])

    async def create_component(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new course component."""
        return await self._transport.post(
            f"{self._base_path}/components",
            {"courseComponent": data},
        )

    async def update_component(self, sourced_id: str, data: dict[str, Any]) -> None:
        """Update an existing course component."""
        await self._transport.put(
            f"{self._base_path}/components/{sourced_id}",
            {"courseComponent": data},
        )

    async def delete_component(self, sourced_id: str) -> None:
        """Delete a course component."""
        await self._transport.delete(f"{self._base_path}/components/{sourced_id}")

    # ── Component Resources ────────────────────────────────────────────────────

    async def component_resources(
        self,
        *,
        limit: int = 100,
        offset: int | None = None,
        filter: str | None = None,
    ) -> list[ComponentResource]:
        """List all component resources."""
        return await self.stream_component_resources(
            limit=limit, offset=offset, filter=filter
        ).to_list()

    def stream_component_resources(
        self,
        *,
        limit: int = 100,
        offset: int | None = None,
        filter: str | None = None,
        max_items: int | None = None,
    ) -> Paginator[ComponentResource]:
        """Stream component resources with lazy pagination."""
        params: dict[str, Any] = {}
        if offset is not None:
            params["offset"] = offset
        if filter is not None:
            params["filter"] = filter

        return Paginator(
            self._transport,
            f"{self._base_path}/component-resources",
            unwrap_key="componentResources",
            params=params,
            limit=limit,
            max_items=max_items,
        )

    async def get_component_resource(self, sourced_id: str) -> ComponentResource:
        """Get a specific component resource."""
        response = await self._transport.get(f"{self._base_path}/component-resources/{sourced_id}")
        return ComponentResource(**response["componentResource"])

    async def create_component_resource(self, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new component resource."""
        return await self._transport.post(
            f"{self._base_path}/component-resources",
            {"componentResource": data},
        )

    async def update_component_resource(self, sourced_id: str, data: dict[str, Any]) -> None:
        """Update an existing component resource."""
        await self._transport.put(
            f"{self._base_path}/component-resources/{sourced_id}",
            {"componentResource": data},
        )

    async def delete_component_resource(self, sourced_id: str) -> None:
        """Delete a component resource."""
        await self._transport.delete(f"{self._base_path}/component-resources/{sourced_id}")

    # ── Course Structure ───────────────────────────────────────────────────────

    async def create_structure(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Create a course structure from QTI tests.

        This endpoint creates a course along with its structure derived from QTI test data.

        Args:
            data: Object containing both course and courseStructure

        Returns:
            Create response with sourcedIdPairs
        """
        return await self._transport.post(f"{self._base_path}/structure", data)
