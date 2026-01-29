"""
Tests for OneRoster base resources.

Covers list, list_all, first, stream, validation, and CRUD operations.
"""

from __future__ import annotations

from typing import Any

import pytest

from timeback_common import InputValidationError
from timeback_oneroster.lib.pagination import PageResult
from timeback_oneroster.resources.base import CRUDResource, ReadOnlyResource


class PaginatedResponse:
    """Mock paginated response."""

    def __init__(self, data: list[Any], has_more: bool = False, total: int | None = None):
        self.data = data
        self.has_more = has_more
        self.total = total


class MockTransport:
    """Mock transport for testing resources."""

    def __init__(self, responses: list[dict[str, Any]] | None = None):
        """Initialize with canned responses."""
        self._responses = responses or []
        self._call_index = 0
        self._last_path: str | None = None
        self._last_params: dict[str, Any] | None = None
        self._last_body: dict[str, Any] | None = None

        # Mock paths attribute
        self.paths = MockPaths()

    async def get(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Return next canned response."""
        self._last_path = path
        self._last_params = params
        if self._call_index < len(self._responses):
            response = self._responses[self._call_index]
            self._call_index += 1
            return response
        return {"items": []}

    async def request_paginated(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        unwrap_key: str | None = None,
    ) -> PaginatedResponse:
        """Return paginated response for OneRoster Paginator."""
        self._last_path = path
        self._last_params = params
        if self._call_index < len(self._responses):
            response = self._responses[self._call_index]
            self._call_index += 1
            items = response.get(unwrap_key, []) if unwrap_key else []
            # Determine has_more based on limit in params
            limit = params.get("limit", 100) if params else 100
            has_more = len(items) >= limit
            return PaginatedResponse(data=items, has_more=has_more, total=len(items))
        return PaginatedResponse(data=[], has_more=False, total=0)

    async def post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        """Record POST call."""
        self._last_path = path
        self._last_body = body
        return {"sourcedIdPairs": []}

    async def put(self, path: str, body: dict[str, Any]) -> None:
        """Record PUT call."""
        self._last_path = path
        self._last_body = body

    async def delete(self, path: str) -> None:
        """Record DELETE call."""
        self._last_path = path

    async def patch(self, path: str, body: dict[str, Any]) -> None:
        """Record PATCH call."""
        self._last_path = path
        self._last_body = body


class MockPaths:
    """Mock paths for testing."""

    rostering = "/ims/oneroster/rostering/v1p2"
    gradebook = "/ims/oneroster/gradebook/v1p2"
    resources = "/ims/oneroster/resources/v1p2"


class ConcreteReadOnlyResource(ReadOnlyResource[dict[str, Any]]):
    """Concrete implementation for testing."""

    @property
    def _unwrap_key(self) -> str:
        return "items"

    @property
    def _wrap_key(self) -> str:
        return "item"

    @property
    def _model_class(self) -> type[dict[str, Any]]:
        return dict  # type: ignore[return-value]

    def _transform(self, entity: dict | dict[str, Any]) -> dict[str, Any]:
        """For testing, just return the dict as-is."""
        return entity  # type: ignore[return-value]


class ConcreteCRUDResource(CRUDResource[dict[str, Any]]):
    """Concrete CRUD implementation for testing."""

    @property
    def _unwrap_key(self) -> str:
        return "items"

    @property
    def _wrap_key(self) -> str:
        return "item"

    @property
    def _model_class(self) -> type[dict[str, Any]]:
        return dict  # type: ignore[return-value]

    def _transform(self, entity: dict | dict[str, Any]) -> dict[str, Any]:
        """For testing, just return the dict as-is."""
        return entity  # type: ignore[return-value]


# ═══════════════════════════════════════════════════════════════════════════════
# LIST TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestList:
    """Tests for list() method (returns single page PageResult)."""

    @pytest.mark.asyncio
    async def test_returns_page_result(self):
        """list() returns PageResult with data and metadata."""
        transport = MockTransport([{"items": [{"id": 1}, {"id": 2}]}])
        resource = ConcreteReadOnlyResource(transport, "rostering", "/items")

        result = await resource.list()

        assert isinstance(result, PageResult)
        assert len(result.data) == 2
        assert result.data[0]["id"] == 1

    @pytest.mark.asyncio
    async def test_returns_has_more_false_when_not_full(self):
        """list() returns has_more=False when page is not full."""
        transport = MockTransport([{"items": [{"id": 1}]}])  # Less than limit
        resource = ConcreteReadOnlyResource(transport, "rostering", "/items")

        result = await resource.list(limit=100)

        assert result.has_more is False

    @pytest.mark.asyncio
    async def test_returns_has_more_true_when_full(self):
        """list() returns has_more=True when page is full."""
        transport = MockTransport([{"items": [{"id": i} for i in range(10)]}])
        resource = ConcreteReadOnlyResource(transport, "rostering", "/items")

        result = await resource.list(limit=10)

        assert result.has_more is True
        assert result.next_offset == 10

    @pytest.mark.asyncio
    async def test_validates_limit(self):
        """list() validates limit parameter."""
        transport = MockTransport([])
        resource = ConcreteReadOnlyResource(transport, "rostering", "/items")

        with pytest.raises(InputValidationError) as exc_info:
            await resource.list(limit=-1)

        assert any(i.path == "limit" for i in exc_info.value.issues)

    @pytest.mark.asyncio
    async def test_validates_offset(self):
        """list() validates offset parameter."""
        transport = MockTransport([])
        resource = ConcreteReadOnlyResource(transport, "rostering", "/items")

        with pytest.raises(InputValidationError) as exc_info:
            await resource.list(offset=-1)

        assert any(i.path == "offset" for i in exc_info.value.issues)


# ═══════════════════════════════════════════════════════════════════════════════
# LIST VALIDATION TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestListValidation:
    """Tests for list() validation."""

    @pytest.mark.asyncio
    async def test_validates_limit(self):
        """list() validates limit parameter."""
        transport = MockTransport([])
        resource = ConcreteReadOnlyResource(transport, "rostering", "/items")

        with pytest.raises(InputValidationError):
            await resource.list(limit=0)

    @pytest.mark.asyncio
    async def test_validates_offset(self):
        """list() validates offset parameter."""
        transport = MockTransport([])
        resource = ConcreteReadOnlyResource(transport, "rostering", "/items")

        with pytest.raises(InputValidationError):
            await resource.list(offset=-5)


# ═══════════════════════════════════════════════════════════════════════════════
# STREAM VALIDATION TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestStreamValidation:
    """Tests for stream() validation."""

    def test_validates_limit(self):
        """stream() validates limit parameter."""
        transport = MockTransport([])
        resource = ConcreteReadOnlyResource(transport, "rostering", "/items")

        with pytest.raises(InputValidationError):
            resource.stream(limit=-1)

    def test_validates_max_items(self):
        """stream() validates max_items parameter."""
        transport = MockTransport([])
        resource = ConcreteReadOnlyResource(transport, "rostering", "/items")

        with pytest.raises(InputValidationError):
            resource.stream(max_items=-100)


# ═══════════════════════════════════════════════════════════════════════════════
# GET VALIDATION TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestGetValidation:
    """Tests for get() validation."""

    @pytest.mark.asyncio
    async def test_validates_sourced_id(self):
        """get() validates sourcedId parameter."""
        transport = MockTransport([])
        resource = ConcreteReadOnlyResource(transport, "rostering", "/items")

        with pytest.raises(InputValidationError) as exc_info:
            await resource.get("")

        assert any(i.path == "sourcedId" for i in exc_info.value.issues)

    @pytest.mark.asyncio
    async def test_validates_whitespace_sourced_id(self):
        """get() rejects whitespace-only sourcedId."""
        transport = MockTransport([])
        resource = ConcreteReadOnlyResource(transport, "rostering", "/items")

        with pytest.raises(InputValidationError):
            await resource.get("   ")

    @pytest.mark.asyncio
    async def test_allows_valid_sourced_id(self):
        """get() allows valid sourcedId."""
        transport = MockTransport([{"item": {"id": "abc-123"}}])
        resource = ConcreteReadOnlyResource(transport, "rostering", "/items")

        result = await resource.get("abc-123")

        assert result["id"] == "abc-123"


# ═══════════════════════════════════════════════════════════════════════════════
# CRUD VALIDATION TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestCRUDValidation:
    """Tests for CRUD operation validation."""

    @pytest.mark.asyncio
    async def test_update_validates_sourced_id(self):
        """update() validates sourcedId parameter."""
        transport = MockTransport([])
        resource = ConcreteCRUDResource(transport, "rostering", "/items")

        with pytest.raises(InputValidationError):
            await resource.update("", {"name": "test"})

    @pytest.mark.asyncio
    async def test_delete_validates_sourced_id(self):
        """delete() validates sourcedId parameter."""
        transport = MockTransport([])
        resource = ConcreteCRUDResource(transport, "rostering", "/items")

        with pytest.raises(InputValidationError):
            await resource.delete("")

    @pytest.mark.asyncio
    async def test_patch_validates_sourced_id(self):
        """patch() validates sourcedId parameter."""
        transport = MockTransport([])
        resource = ConcreteCRUDResource(transport, "rostering", "/items")

        with pytest.raises(InputValidationError):
            await resource.patch("", {"name": "test"})

    @pytest.mark.asyncio
    async def test_crud_operations_work_with_valid_id(self):
        """CRUD operations work with valid sourcedId."""
        transport = MockTransport([])
        resource = ConcreteCRUDResource(transport, "rostering", "/items")

        # These should not raise
        await resource.update("abc-123", {"name": "test"})
        await resource.delete("def-456")
        await resource.patch("ghi-789", {"name": "test"})
