"""
Academic Sessions Resource

Access terms, semesters, grading periods, and school years.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from timeback_common import CreateResponse, validate_sourced_id, validate_with_schema

from ...lib.pagination import Paginator
from ...types import AcademicSession, AcademicSessionCreateInput, Class
from ..base import CRUDResourceNoSearch

if TYPE_CHECKING:
    from pydantic import BaseModel

    from ...lib.transport import Transport


# ═══════════════════════════════════════════════════════════════════════════════
# SCOPED ACADEMIC SESSION RESOURCE
# ═══════════════════════════════════════════════════════════════════════════════


class ScopedAcademicSessionResource:
    """
    Scoped resource for operations on a specific academic session.

    Access via `client.academic_sessions(session_id)`.

    Example:
        ```python
        session = await client.academic_sessions(session_id).get()
        ```
    """

    def __init__(self, transport: Transport, session_id: str) -> None:
        validate_sourced_id(session_id, "academic session")
        self._transport = transport
        self._session_id = session_id
        self._base_path = f"{transport.paths.rostering}/academicSessions/{session_id}"

    async def get(self) -> AcademicSession:
        """Get the academic session details."""
        response = await self._transport.get(self._base_path)
        return AcademicSession(**response["academicSession"])


# ═══════════════════════════════════════════════════════════════════════════════
# ACADEMIC SESSIONS RESOURCE
# ═══════════════════════════════════════════════════════════════════════════════


class AcademicSessionsResource(CRUDResourceNoSearch[AcademicSession]):
    """
    Resource for academic sessions.

    Academic sessions include terms, semesters, grading periods, and school years.

    Example:
        ```python
        # List all academic sessions
        sessions = await client.academic_sessions.list()

        # Get specific session
        session = await client.academic_sessions.get("session-id")

        # Filter by type
        terms = await client.academic_sessions.list(filter="type='term'")
        semesters = await client.academic_sessions.list(filter="type='semester'")
        ```
    """

    def __init__(self, transport: Transport) -> None:
        super().__init__(transport, "rostering", "/academicSessions")

    @property
    def _unwrap_key(self) -> str:
        return "academicSessions"

    @property
    def _wrap_key(self) -> str:
        return "academicSession"

    @property
    def _model_class(self) -> type[AcademicSession]:
        return AcademicSession

    @property
    def _create_schema(self) -> type[BaseModel]:
        """Pydantic model for validating academic session create input."""
        return AcademicSessionCreateInput

    @property
    def _update_schema(self) -> type[BaseModel]:
        """Pydantic model for validating academic session update input."""
        return AcademicSessionCreateInput

    def __call__(self, session_id: str) -> ScopedAcademicSessionResource:
        """Get scoped resource for a specific academic session."""
        return ScopedAcademicSessionResource(self._transport, session_id)


# ═══════════════════════════════════════════════════════════════════════════════
# SCOPED TERM RESOURCE
# ═══════════════════════════════════════════════════════════════════════════════


class ScopedTermResource:
    """
    Scoped resource for operations on a specific term.

    Access via `client.terms(term_id)`.

    Example:
        ```python
        term = await client.terms(term_id).get()
        classes = await client.terms(term_id).classes()
        grading_periods = await client.terms(term_id).grading_periods()
        ```
    """

    def __init__(self, transport: Transport, term_id: str) -> None:
        validate_sourced_id(term_id, "term")
        self._transport = transport
        self._term_id = term_id
        self._base_path = f"{transport.paths.rostering}/terms/{term_id}"

    async def get(self) -> AcademicSession:
        """Get the term details."""
        response = await self._transport.get(self._base_path)
        return AcademicSession(**response["term"])

    # ── Classes ────────────────────────────────────────────────────────────────

    async def classes(
        self,
        *,
        limit: int = 100,
        offset: int | None = None,
        filter: str | None = None,
    ) -> list[Class]:
        """List classes in this term."""
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

    # ── Grading Periods ────────────────────────────────────────────────────────

    async def grading_periods(
        self,
        *,
        limit: int = 100,
        offset: int | None = None,
        filter: str | None = None,
    ) -> list[AcademicSession]:
        """List grading periods in this term."""
        return await self.stream_grading_periods(
            limit=limit, offset=offset, filter=filter
        ).to_list()

    def stream_grading_periods(
        self,
        *,
        limit: int = 100,
        offset: int | None = None,
        filter: str | None = None,
        max_items: int | None = None,
    ) -> Paginator[AcademicSession]:
        """Stream grading periods with lazy pagination."""
        params: dict[str, Any] = {}
        if offset is not None:
            params["offset"] = offset
        if filter is not None:
            params["filter"] = filter

        return Paginator(
            self._transport,
            f"{self._base_path}/gradingPeriods",
            unwrap_key="gradingPeriods",
            params=params,
            limit=limit,
            max_items=max_items,
            transform=lambda item: AcademicSession.model_validate(item),
        )

    async def create_grading_period(self, data: dict[str, Any]) -> AcademicSession:
        """
        Create a grading period in this term.

        Args:
            data: Grading period data

        Returns:
            The created grading period (as academicSession)

        Raises:
            InputValidationError: If data fails client-side validation
        """
        validate_with_schema(AcademicSessionCreateInput, data, "grading period")
        response = await self._transport.post(
            f"{self._base_path}/gradingPeriods",
            {"academicSession": data},
        )
        return AcademicSession(**response["academicSession"])


# ═══════════════════════════════════════════════════════════════════════════════
# TERMS RESOURCE
# ═══════════════════════════════════════════════════════════════════════════════


class TermsResource(CRUDResourceNoSearch[AcademicSession]):
    """
    Resource for terms (filtered academic sessions).

    Example:
        ```python
        terms = await client.terms.list()
        term = await client.terms.get("term-id")
        classes = await client.terms("term-id").classes()
        grading_periods = await client.terms("term-id").grading_periods()
        ```
    """

    def __init__(self, transport: Transport) -> None:
        super().__init__(transport, "rostering", "/terms")

    @property
    def _unwrap_key(self) -> str:
        return "terms"

    @property
    def _wrap_key(self) -> str:
        return "term"

    @property
    def _model_class(self) -> type[AcademicSession]:
        return AcademicSession

    @property
    def _create_schema(self) -> type[BaseModel]:
        """Pydantic model for validating term create input."""
        return AcademicSessionCreateInput

    @property
    def _update_schema(self) -> type[BaseModel]:
        """Pydantic model for validating term update input."""
        return AcademicSessionCreateInput

    def __call__(self, term_id: str) -> ScopedTermResource:
        """Get scoped resource for a specific term."""
        return ScopedTermResource(self._transport, term_id)


# ═══════════════════════════════════════════════════════════════════════════════
# SCOPED GRADING PERIOD RESOURCE
# ═══════════════════════════════════════════════════════════════════════════════


class ScopedGradingPeriodResource:
    """Scoped resource for a specific grading period."""

    def __init__(self, transport: Transport, period_id: str) -> None:
        validate_sourced_id(period_id, "grading period")
        self._transport = transport
        self._period_id = period_id
        self._base_path = f"{transport.paths.rostering}/gradingPeriods/{period_id}"

    async def get(self) -> AcademicSession:
        """Get the grading period details."""
        response = await self._transport.get(self._base_path)
        return AcademicSession(**response["academicSession"])


# ═══════════════════════════════════════════════════════════════════════════════
# GRADING PERIODS RESOURCE
# ═══════════════════════════════════════════════════════════════════════════════


class GradingPeriodsResource(CRUDResourceNoSearch[AcademicSession]):
    """
    Resource for grading periods (filtered academic sessions).

    Example:
        ```python
        periods = await client.grading_periods.list()
        period = await client.grading_periods.get("period-id")
        ```
    """

    def __init__(self, transport: Transport) -> None:
        super().__init__(transport, "rostering", "/gradingPeriods")

    @property
    def _unwrap_key(self) -> str:
        return "gradingPeriods"

    @property
    def _wrap_key(self) -> str:
        return "gradingPeriod"

    @property
    def _model_class(self) -> type[AcademicSession]:
        return AcademicSession

    @property
    def _create_schema(self) -> type[BaseModel]:
        """Pydantic model for validating grading period create input."""
        return AcademicSessionCreateInput

    @property
    def _update_schema(self) -> type[BaseModel]:
        """Pydantic model for validating grading period update input."""
        return AcademicSessionCreateInput

    async def create(self, data: dict[str, Any]) -> CreateResponse:
        """
        Create a grading period.

        The Beyond-AI API expects grading period creates to be wrapped as
        {"academicSession": ...}, even though GET responses use "gradingPeriod".
        """
        validate_with_schema(self._create_schema, data, self._wrap_key)
        response = await self._transport.post(self._base_path, {"academicSession": data})
        return CreateResponse.model_validate(response)

    async def update(self, sourced_id: str, data: dict[str, Any]) -> None:
        """
        Update an existing grading period.

        The Beyond-AI API expects grading period updates to be wrapped as
        {"academicSession": ...}, even though GET responses use "gradingPeriod".
        """
        validate_sourced_id(sourced_id, f"update {self._unwrap_key}")
        if self._update_schema is not None:
            validate_with_schema(self._update_schema, data, f"update {self._wrap_key}")
        await self._transport.put(f"{self._base_path}/{sourced_id}", {"academicSession": data})

    async def patch(self, sourced_id: str, data: dict[str, Any]) -> None:
        """
        Partially update an existing grading period.

        The Beyond-AI API expects grading period updates to be wrapped as
        {"academicSession": ...}, even though GET responses use "gradingPeriod".
        """
        validate_sourced_id(sourced_id, f"patch {self._unwrap_key}")
        if self._patch_schema is not None:
            validate_with_schema(self._patch_schema, data, f"patch {self._wrap_key}")
        await self._transport.patch(f"{self._base_path}/{sourced_id}", {"academicSession": data})

    def __call__(self, period_id: str) -> ScopedGradingPeriodResource:
        """Get scoped resource for a specific grading period."""
        return ScopedGradingPeriodResource(self._transport, period_id)
