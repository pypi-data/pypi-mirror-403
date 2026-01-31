"""
Base Resource Classes

Abstract base classes for OneRoster resources.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, TypeVar

from timeback_common import (
    CreateResponse,
    validate_fields,
    validate_offset_list_params,
    validate_sourced_id,
    validate_with_schema,
)

from ..lib.pagination import PageResult, Paginator
from ..lib.params import build_list_params, build_list_params_no_search

if TYPE_CHECKING:
    from pydantic import BaseModel

    from ..lib.filter import WhereClause
    from ..lib.transport import Transport

T = TypeVar("T")


class ReadOnlyResource[T](ABC):
    """
    Base class for read-only OneRoster resources.

    Provides list, stream, and get operations.
    """

    def __init__(
        self,
        transport: Transport,
        service: str,
        path_suffix: str,
    ) -> None:
        """
        Initialize resource.

        Args:
            transport: Transport instance
            service: Service name ("rostering", "gradebook", "resources")
            path_suffix: Path suffix (e.g., "/users", "/schools")
        """
        self._transport = transport
        self._service = service
        self._path_suffix = path_suffix

    @property
    def _base_path(self) -> str:
        """Get full base path for this resource."""
        service_path = getattr(self._transport.paths, self._service)
        return f"{service_path}{self._path_suffix}"

    @property
    @abstractmethod
    def _unwrap_key(self) -> str:
        """Key to unwrap list responses (e.g., 'users', 'classes')."""
        ...

    @property
    @abstractmethod
    def _wrap_key(self) -> str:
        """Key to wrap single item responses (e.g., 'user', 'class')."""
        ...

    @property
    @abstractmethod
    def _model_class(self) -> type[T]:
        """Pydantic model class for this resource's entities."""
        ...

    def _transform(self, entity: dict | T) -> T:
        """
        Transform a response entity before returning it.

        Converts raw dicts to typed Pydantic models. Override in subclasses
        for additional transformations (e.g., normalizing grades).

        Args:
            entity: The raw entity from the API (dict or model)

        Returns:
            The transformed entity as a typed model
        """
        if isinstance(entity, dict):
            return self._model_class(**entity)
        return entity

    async def list(
        self,
        *,
        limit: int = 100,
        offset: int | None = None,
        sort: str | None = None,
        order_by: str | None = None,
        filter: str | None = None,
        where: WhereClause | None = None,
        fields: list[str] | None = None,
        search: str | None = None,
    ) -> PageResult[T]:
        """
        List the first page of items with pagination metadata.

        This returns a single page plus metadata (`has_more`, `total`, `next_offset`).
        Use `stream()` for lazy iteration or `list_all()` to fetch everything.

        Args:
            limit: Items per page (default: 100)
            offset: Starting offset (default: 0)
            sort: Field to sort by
            order_by: Sort direction ('asc' or 'desc')
            filter: OneRoster filter string (legacy, prefer `where`)
            where: Type-safe filter clause (recommended)
            fields: List of fields to include in response (sparse fieldsets)
            search: Full-text search query

        Returns:
            PageResult with data, has_more, total, and next_offset

        Example:
            ```python
            # Get first page with metadata
            page = await client.users.list(limit=50)
            print(f"Got {len(page.data)} users, has_more={page.has_more}")

            # Using where (recommended)
            page = await client.users.list(where={"status": "active"})

            # With sparse fieldsets
            page = await client.users.list(fields=["sourcedId", "givenName", "familyName"])

            # Pagination loop
            offset = 0
            while True:
                page = await client.users.list(offset=offset)
                process(page.data)
                if not page.has_more:
                    break
                offset = page.next_offset
            ```
        """
        validate_offset_list_params(limit=limit, offset=offset)
        validate_fields(fields)

        paginator = self.stream(
            limit=limit,
            offset=offset,
            sort=sort,
            order_by=order_by,
            filter=filter,
            where=where,
            fields=fields,
            search=search,
        )
        return await paginator.first_page()

    async def list_all(
        self,
        *,
        limit: int = 100,
        offset: int | None = None,
        sort: str | None = None,
        order_by: str | None = None,
        filter: str | None = None,
        where: WhereClause | None = None,
        fields: list[str] | None = None,
        search: str | None = None,
        max_items: int | None = None,
    ) -> list[T]:
        """
        List all items, fetching all pages automatically.

        Warning: Use with caution on large datasets as this loads all items
        into memory. Consider using `stream()` for better memory efficiency.

        Args:
            limit: Items per page (default: 100)
            offset: Starting offset
            sort: Field to sort by
            order_by: Sort direction ('asc' or 'desc')
            filter: OneRoster filter string (legacy, prefer `where`)
            where: Type-safe filter clause (recommended)
            fields: List of fields to include in response (sparse fieldsets)
            search: Full-text search query
            max_items: Maximum total items to fetch (safety limit)

        Returns:
            List of all items

        Example:
            ```python
            # Fetch all active users
            users = await client.users.list_all(where={"status": "active"})

            # With operators
            users = await client.users.list_all(
                where={"role": {"in_": ["teacher", "aide"]}}
            )

            # Legacy filter string (still supported)
            users = await client.users.list_all(filter="status='active'")
            ```
        """
        validate_offset_list_params(limit=limit, offset=offset, max_items=max_items)
        validate_fields(fields)

        return await self.stream(
            limit=limit,
            offset=offset,
            sort=sort,
            order_by=order_by,
            filter=filter,
            where=where,
            fields=fields,
            search=search,
            max_items=max_items,
        ).to_list()

    async def first(
        self,
        *,
        filter: str | None = None,
        where: WhereClause | None = None,
        fields: list[str] | None = None,
        search: str | None = None,
    ) -> T | None:
        """
        Get the first matching item, or None if none match.

        Args:
            filter: OneRoster filter string (legacy, prefer `where`)
            where: Type-safe filter clause (recommended)
            fields: List of fields to include in response (sparse fieldsets)
            search: Full-text search query

        Returns:
            The first matching item, or None

        Example:
            ```python
            user = await client.users.first(where={"email": "jane@example.com"})
            if not user:
                raise ValueError("User not found")
            ```
        """
        result = await self.list(limit=1, filter=filter, where=where, fields=fields, search=search)
        return result.data[0] if result.data else None

    def stream(
        self,
        *,
        limit: int = 100,
        offset: int | None = None,
        sort: str | None = None,
        order_by: str | None = None,
        filter: str | None = None,
        where: WhereClause | None = None,
        fields: list[str] | None = None,
        search: str | None = None,
        max_items: int | None = None,
    ) -> Paginator[T]:
        """
        Stream items with lazy pagination.

        Args:
            limit: Items per page
            offset: Starting offset
            sort: Field to sort by
            order_by: Sort direction
            filter: OneRoster filter string (legacy, prefer `where`)
            where: Type-safe filter clause (recommended)
            fields: List of fields to include in response (sparse fieldsets)
            search: Full-text search query
            max_items: Maximum total items to fetch

        Returns:
            Paginator for lazy iteration

        Example:
            ```python
            # Stream with filtering
            async for user in client.users.stream(where={"status": "active"}):
                print(user.given_name)

            # With operators
            paginator = client.users.stream(
                where={"role": {"in_": ["teacher", "aide"]}},
                max_items=100,
            )
            ```
        """
        validate_offset_list_params(limit=limit, offset=offset, max_items=max_items)
        validate_fields(fields)

        params = build_list_params(
            offset=offset,
            sort=sort,
            order_by=order_by,
            filter=filter,
            where=where,
            fields=fields,
            search=search,
        )

        return Paginator(
            self._transport,
            self._base_path,
            unwrap_key=self._unwrap_key,
            params=params,
            limit=limit,
            max_items=max_items,
            transform=self._transform,
        )

    async def get(self, sourced_id: str) -> T:
        """
        Get a single item by sourcedId.


        Args:
            sourced_id: The sourcedId of the item

        Returns:
            The item

        Raises:
            InputValidationError: If sourcedId is empty
        """
        validate_sourced_id(sourced_id, f"get {self._unwrap_key}")
        response = await self._transport.get(f"{self._base_path}/{sourced_id}")
        entity = response[self._wrap_key]
        return self._transform(entity)


class ReadOnlyResourceNoSearch[T](ABC):
    """
    Base class for read-only OneRoster resources that do NOT support search.

    Use this for resources where Timeback ignores the search parameter:
    classes, schools, teachers, terms, enrollments, orgs, demographics,
    line_items, results, categories, score_scales, resources.

    Provides list, stream, and get operations without the search parameter.
    """

    def __init__(
        self,
        transport: Transport,
        service: str,
        path_suffix: str,
    ) -> None:
        """
        Initialize resource.

        Args:
            transport: Transport instance
            service: Service name ("rostering", "gradebook", "resources")
            path_suffix: Path suffix (e.g., "/classes", "/schools")
        """
        self._transport = transport
        self._service = service
        self._path_suffix = path_suffix

    @property
    def _base_path(self) -> str:
        """Get full base path for this resource."""
        service_path = getattr(self._transport.paths, self._service)
        return f"{service_path}{self._path_suffix}"

    @property
    @abstractmethod
    def _unwrap_key(self) -> str:
        """Key to unwrap list responses (e.g., 'classes')."""
        ...

    @property
    @abstractmethod
    def _wrap_key(self) -> str:
        """Key to wrap single item responses (e.g., 'class')."""
        ...

    @property
    @abstractmethod
    def _model_class(self) -> type[T]:
        """Pydantic model class for this resource's entities."""
        ...

    def _transform(self, entity: dict | T) -> T:
        """Transform a response entity before returning it."""
        if isinstance(entity, dict):
            return self._model_class(**entity)
        return entity

    async def list(
        self,
        *,
        limit: int = 100,
        offset: int | None = None,
        sort: str | None = None,
        order_by: str | None = None,
        filter: str | None = None,
        where: WhereClause | None = None,
        fields: list[str] | None = None,
    ) -> PageResult[T]:
        """
        List the first page of items with pagination metadata.

        Note: This resource does not support the `search` parameter.

        Args:
            limit: Items per page (default: 100)
            offset: Starting offset (default: 0)
            sort: Field to sort by
            order_by: Sort direction ('asc' or 'desc')
            filter: OneRoster filter string (legacy, prefer `where`)
            where: Type-safe filter clause (recommended)
            fields: List of fields to include in response (sparse fieldsets)

        Returns:
            PageResult with data, has_more, total, and next_offset
        """
        validate_offset_list_params(limit=limit, offset=offset)
        validate_fields(fields)

        paginator = self.stream(
            limit=limit,
            offset=offset,
            sort=sort,
            order_by=order_by,
            filter=filter,
            where=where,
            fields=fields,
        )
        return await paginator.first_page()

    async def list_all(
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
    ) -> list[T]:
        """
        List all items, fetching all pages automatically.

        Note: This resource does not support the `search` parameter.

        Args:
            limit: Items per page (default: 100)
            offset: Starting offset
            sort: Field to sort by
            order_by: Sort direction ('asc' or 'desc')
            filter: OneRoster filter string (legacy, prefer `where`)
            where: Type-safe filter clause (recommended)
            fields: List of fields to include in response (sparse fieldsets)
            max_items: Maximum total items to fetch (safety limit)

        Returns:
            List of all items
        """
        validate_offset_list_params(limit=limit, offset=offset, max_items=max_items)
        validate_fields(fields)

        return await self.stream(
            limit=limit,
            offset=offset,
            sort=sort,
            order_by=order_by,
            filter=filter,
            where=where,
            fields=fields,
            max_items=max_items,
        ).to_list()

    async def first(
        self,
        *,
        filter: str | None = None,
        where: WhereClause | None = None,
        fields: list[str] | None = None,
    ) -> T | None:
        """
        Get the first matching item, or None if none match.

        Note: This resource does not support the `search` parameter.

        Args:
            filter: OneRoster filter string (legacy, prefer `where`)
            where: Type-safe filter clause (recommended)
            fields: List of fields to include in response (sparse fieldsets)

        Returns:
            The first matching item, or None
        """
        result = await self.list(limit=1, filter=filter, where=where, fields=fields)
        return result.data[0] if result.data else None

    def stream(
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
    ) -> Paginator[T]:
        """
        Stream items with lazy pagination.

        Note: This resource does not support the `search` parameter.

        Args:
            limit: Items per page
            offset: Starting offset
            sort: Field to sort by
            order_by: Sort direction
            filter: OneRoster filter string (legacy, prefer `where`)
            where: Type-safe filter clause (recommended)
            fields: List of fields to include in response (sparse fieldsets)
            max_items: Maximum total items to fetch

        Returns:
            Paginator for lazy iteration
        """
        validate_offset_list_params(limit=limit, offset=offset, max_items=max_items)
        validate_fields(fields)

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
            self._base_path,
            unwrap_key=self._unwrap_key,
            params=params,
            limit=limit,
            max_items=max_items,
            transform=self._transform,
        )

    async def get(self, sourced_id: str) -> T:
        """
        Get a single item by sourcedId.

        Args:
            sourced_id: The sourcedId of the item

        Returns:
            The item

        Raises:
            InputValidationError: If sourcedId is empty
        """
        validate_sourced_id(sourced_id, f"get {self._unwrap_key}")
        response = await self._transport.get(f"{self._base_path}/{sourced_id}")
        entity = response[self._wrap_key]
        return self._transform(entity)


class CRUDResource[T](ReadOnlyResource[T]):
    """
    Base class for resources with full CRUD operations.

    Extends ReadOnlyResource with create, update, and delete.
    """

    @property
    def _create_schema(self) -> type[BaseModel] | None:
        """
        Pydantic model for validating create input.

        Override in subclasses to enable client-side validation before create requests.
        Returns:
            Pydantic model for validation, or None to skip validation
        """
        return None

    @property
    def _update_schema(self) -> type[BaseModel] | None:
        """
        Pydantic model for validating update input.

        Override in subclasses to enable client-side validation before update requests.
        Returns:
            Pydantic model for validation, or None to skip validation
        """
        return None

    @property
    def _patch_schema(self) -> type[BaseModel] | None:
        """
        Pydantic model for validating patch input.

        Override in subclasses to enable client-side validation before patch requests.
        Returns:
            Pydantic model for validation, or None to skip validation
        """
        return None

    @property
    def _resource_name(self) -> str:
        """
        Human-readable resource name for error messages.

        Derived from _wrap_key by default (e.g., "user", "class").

        Returns:
            Resource name for error messages
        """
        return self._wrap_key

    async def create(self, data: dict[str, Any]) -> CreateResponse:
        """
        Create a new item.

        Args:
            data: Item data

        Returns:
            Create response with sourcedIdPairs

        Raises:
            InputValidationError: If data fails client-side validation
        """
        schema = self._create_schema
        if schema is not None:
            validate_with_schema(schema, data, self._resource_name)

        body = {self._wrap_key: data}
        response = await self._transport.post(self._base_path, body)
        return CreateResponse.model_validate(response)

    async def update(self, sourced_id: str, data: dict[str, Any]) -> None:
        """
        Update an existing item (full replacement).

        Args:
            sourced_id: The sourcedId of the item
            data: Updated item data

        Raises:
            InputValidationError: If sourcedId is empty or data fails validation
        """
        validate_sourced_id(sourced_id, f"update {self._unwrap_key}")

        schema = self._update_schema
        if schema is not None:
            validate_with_schema(schema, data, f"update {self._resource_name}")

        body = {self._wrap_key: data}
        await self._transport.put(f"{self._base_path}/{sourced_id}", body)

    async def delete(self, sourced_id: str) -> None:
        """
        Delete an item.

        Args:
            sourced_id: The sourcedId of the item

        Raises:
            InputValidationError: If sourcedId is empty
        """
        validate_sourced_id(sourced_id, f"delete {self._unwrap_key}")
        await self._transport.delete(f"{self._base_path}/{sourced_id}")

    async def patch(self, sourced_id: str, data: dict[str, Any]) -> None:
        """
        Partially update an item.

        Args:
            sourced_id: The sourcedId of the item
            data: Partial item data

        Raises:
            InputValidationError: If sourcedId is empty or data fails validation
        """
        validate_sourced_id(sourced_id, f"patch {self._unwrap_key}")

        schema = self._patch_schema
        if schema is not None:
            validate_with_schema(schema, data, f"patch {self._resource_name}")

        body = {self._wrap_key: data}
        await self._transport.patch(f"{self._base_path}/{sourced_id}", body)


class CRUDResourceNoSearch[T](ReadOnlyResourceNoSearch[T]):
    """
    Base class for resources with full CRUD operations that do NOT support search.

    Extends ReadOnlyResourceNoSearch with create, update, and delete.
    Use this for: classes, schools, enrollments, orgs, line_items, results, etc.
    """

    @property
    def _create_schema(self) -> type[BaseModel] | None:
        """Pydantic model for validating create input."""
        return None

    @property
    def _update_schema(self) -> type[BaseModel] | None:
        """Pydantic model for validating update input."""
        return None

    @property
    def _patch_schema(self) -> type[BaseModel] | None:
        """Pydantic model for validating patch input."""
        return None

    @property
    def _resource_name(self) -> str:
        """Human-readable resource name for error messages."""
        return self._wrap_key

    async def create(self, data: dict[str, Any]) -> CreateResponse:
        """Create a new item."""
        schema = self._create_schema
        if schema is not None:
            validate_with_schema(schema, data, self._resource_name)

        body = {self._wrap_key: data}
        response = await self._transport.post(self._base_path, body)
        return CreateResponse.model_validate(response)

    async def update(self, sourced_id: str, data: dict[str, Any]) -> None:
        """Update an existing item (full replacement)."""
        validate_sourced_id(sourced_id, f"update {self._unwrap_key}")

        schema = self._update_schema
        if schema is not None:
            validate_with_schema(schema, data, f"update {self._resource_name}")

        body = {self._wrap_key: data}
        await self._transport.put(f"{self._base_path}/{sourced_id}", body)

    async def delete(self, sourced_id: str) -> None:
        """Delete an item."""
        validate_sourced_id(sourced_id, f"delete {self._unwrap_key}")
        await self._transport.delete(f"{self._base_path}/{sourced_id}")

    async def patch(self, sourced_id: str, data: dict[str, Any]) -> None:
        """Partially update an item."""
        validate_sourced_id(sourced_id, f"patch {self._unwrap_key}")

        schema = self._patch_schema
        if schema is not None:
            validate_with_schema(schema, data, f"patch {self._resource_name}")

        body = {self._wrap_key: data}
        await self._transport.patch(f"{self._base_path}/{sourced_id}", body)
