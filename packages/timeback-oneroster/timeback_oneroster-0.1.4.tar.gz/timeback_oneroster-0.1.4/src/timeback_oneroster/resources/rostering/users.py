"""
Users Resource

Access all users regardless of role.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from timeback_common import validate_sourced_id, validate_with_schema

from ...lib.pagination import Paginator
from ...lib.params import build_list_params_no_search
from ...types import Class, User, UserCreateInput
from ...types.input import AgentInput
from ...types.resources import (
    CredentialCreateResponse,
    DecryptedCredential,
    Resource,
)
from ..base import CRUDResource, ReadOnlyResource, ReadOnlyResourceNoSearch

if TYPE_CHECKING:
    from pydantic import BaseModel

    from ...lib.filter import WhereClause
    from ...lib.transport import Transport


# ═══════════════════════════════════════════════════════════════════════════════
# SCOPED USER RESOURCE
# ═══════════════════════════════════════════════════════════════════════════════


class ScopedUserResource:
    """
    Scoped resource for operations on a specific user.

    Access via `client.users(user_id)`.

    Example:
        ```python
        user = await client.users(user_id).get()
        classes = await client.users(user_id).classes()
        agents = await client.users(user_id).agents()
        ```
    """

    def __init__(self, transport: Transport, user_id: str) -> None:
        validate_sourced_id(user_id, "user")
        self._transport = transport
        self._user_id = user_id
        self._base_path = f"{transport.paths.rostering}/users/{user_id}"

    async def get(self) -> User:
        """Get the user details."""
        response = await self._transport.get(self._base_path)
        return User(**response["user"])

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
        """
        List classes for this user.

        Note: This endpoint does not support the `search` parameter.

        Args:
            limit: Items per page
            offset: Starting offset
            sort: Field to sort by
            order_by: Sort direction ('asc' or 'desc')
            filter: OneRoster filter string (legacy, prefer `where`)
            where: Type-safe filter clause
            fields: Sparse fieldset - list of fields to return

        Returns:
            List of classes the user is enrolled in
        """
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

    # ── Demographics ───────────────────────────────────────────────────────────

    async def demographics(self) -> User:
        """
        Get the user with their demographic information.

        Returns:
            User with demographics field populated
        """
        response = await self._transport.get(f"{self._base_path}/demographics")
        return User(**response["user"])

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
        """List resources for this user."""
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
            f"{self._transport.paths.resources}/resources/users/{self._user_id}/resources",
            unwrap_key="resources",
            params=params,
            limit=limit,
            max_items=max_items,
        )

    # ── Agent Methods ──────────────────────────────────────────────────────────

    async def agent_for(self) -> list[User]:
        """
        Get users that this user is an agent (guardian/parent) for.

        For example, if this user is a parent, returns their children.

        Returns:
            Array of users this user represents
        """
        response = await self._transport.get(f"{self._base_path}/agentFor")
        return [User(**u) for u in response.get("users", [])]

    async def agents(self) -> list[User]:
        """
        Get agents (guardians/parents) for this user.

        For example, if this user is a student, returns their parents/guardians.

        Returns:
            Array of agent users
        """
        response = await self._transport.get(f"{self._base_path}/agents")
        return [User(**u) for u in response.get("agents", [])]

    async def add_agent(self, data: AgentInput | dict[str, Any]) -> None:
        """
        Add an agent (guardian/parent) relationship for this user.

        Args:
            data: Agent input with the agent user reference
        """
        validate_with_schema(AgentInput, data, "agent")
        agent = AgentInput.model_validate(data)
        await self._transport.post(
            f"{self._base_path}/agents",
            agent.model_dump(by_alias=True),
        )

    async def remove_agent(self, agent_sourced_id: str) -> None:
        """
        Remove an agent (guardian/parent) relationship from this user.

        Args:
            agent_sourced_id: The sourcedId of the agent to remove

        Raises:
            InputValidationError: If agent_sourced_id is empty
        """
        validate_sourced_id(agent_sourced_id, "remove agent")
        await self._transport.delete(f"{self._base_path}/agents/{agent_sourced_id}")

    # ── Credential Methods ─────────────────────────────────────────────────────

    async def create_credential(self, credential: dict[str, Any]) -> CredentialCreateResponse:
        """
        Create credentials for this user.

        Args:
            credential: Credential data to create

        Returns:
            Response with userProfileId, credentialId, and message
        """
        response = await self._transport.post(
            f"{self._base_path}/credentials",
            {"credential": credential},
        )
        return CredentialCreateResponse(**response)

    async def decrypt_credential(self, credential_id: str) -> DecryptedCredential:
        """
        Decrypt a user's credential to retrieve the password.

        Args:
            credential_id: The credential ID to decrypt

        Returns:
            Decrypted credential with password

        Raises:
            InputValidationError: If credential_id is empty
        """
        validate_sourced_id(credential_id, "decrypt credential")
        response = await self._transport.post(
            f"{self._base_path}/credentials/{credential_id}/decrypt",
            {},
        )
        return DecryptedCredential(**response)


# ═══════════════════════════════════════════════════════════════════════════════
# USERS RESOURCE
# ═══════════════════════════════════════════════════════════════════════════════


class UsersResource(CRUDResource[User]):
    """
    Resource for all users (students, teachers, parents, administrators).

    Example:
        ```python
        # List all users
        users = await client.users.list()

        # Get specific user
        user = await client.users.get("user-id")

        # Scoped operations
        classes = await client.users("user-id").classes()
        agents = await client.users("user-id").agents()
        ```
    """

    def __init__(self, transport: Transport) -> None:
        super().__init__(transport, "rostering", "/users")

    @property
    def _unwrap_key(self) -> str:
        return "users"

    @property
    def _wrap_key(self) -> str:
        return "user"

    @property
    def _model_class(self) -> type[User]:
        return User

    @property
    def _create_schema(self) -> type[BaseModel]:
        """Pydantic model for validating user create input."""
        return UserCreateInput

    def __call__(self, user_id: str) -> ScopedUserResource:
        """Get scoped resource for a specific user."""
        return ScopedUserResource(self._transport, user_id)


# ═══════════════════════════════════════════════════════════════════════════════
# STUDENTS RESOURCE (Read-only filtered view)
# ═══════════════════════════════════════════════════════════════════════════════


class ScopedStudentResource:
    """Scoped resource for a specific student."""

    def __init__(self, transport: Transport, student_id: str) -> None:
        validate_sourced_id(student_id, "student")
        self._transport = transport
        self._student_id = student_id
        self._base_path = f"{transport.paths.rostering}/students/{student_id}"

    async def get(self) -> User:
        """Get the student details."""
        response = await self._transport.get(self._base_path)
        return User(**response["user"])

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
        """List classes this student is enrolled in."""
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


class StudentsResource(ReadOnlyResource[User]):
    """
    Read-only resource for students (filtered users with role=student).

    Example:
        ```python
        students = await client.students.list()
        student = await client.students.get("student-id")
        classes = await client.students("student-id").classes()
        ```
    """

    def __init__(self, transport: Transport) -> None:
        super().__init__(transport, "rostering", "/students")

    @property
    def _unwrap_key(self) -> str:
        return "users"

    @property
    def _wrap_key(self) -> str:
        return "user"

    @property
    def _model_class(self) -> type[User]:
        return User

    def __call__(self, student_id: str) -> ScopedStudentResource:
        """Get scoped resource for a specific student."""
        return ScopedStudentResource(self._transport, student_id)


# ═══════════════════════════════════════════════════════════════════════════════
# TEACHERS RESOURCE (Read-only filtered view)
# ═══════════════════════════════════════════════════════════════════════════════


class ScopedTeacherResource:
    """Scoped resource for a specific teacher."""

    def __init__(self, transport: Transport, teacher_id: str) -> None:
        validate_sourced_id(teacher_id, "teacher")
        self._transport = transport
        self._teacher_id = teacher_id
        self._base_path = f"{transport.paths.rostering}/teachers/{teacher_id}"

    async def get(self) -> User:
        """Get the teacher details."""
        response = await self._transport.get(self._base_path)
        return User(**response["user"])

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
        """List classes this teacher is assigned to."""
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


class TeachersResource(ReadOnlyResourceNoSearch[User]):
    """
    Read-only resource for teachers (filtered users with role=teacher).

    Example:
        ```python
        teachers = await client.teachers.list()
        teacher = await client.teachers.get("teacher-id")
        classes = await client.teachers("teacher-id").classes()
        ```
    """

    def __init__(self, transport: Transport) -> None:
        super().__init__(transport, "rostering", "/teachers")

    @property
    def _unwrap_key(self) -> str:
        return "users"

    @property
    def _wrap_key(self) -> str:
        return "user"

    @property
    def _model_class(self) -> type[User]:
        return User

    def __call__(self, teacher_id: str) -> ScopedTeacherResource:
        """Get scoped resource for a specific teacher."""
        return ScopedTeacherResource(self._transport, teacher_id)
