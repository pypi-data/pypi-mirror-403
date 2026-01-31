"""Tests for Demographics resource."""

from __future__ import annotations

from typing import Any

import pytest

from timeback_common import InputValidationError
from timeback_oneroster.resources.rostering.demographics import DemographicsResource


class MockPaths:
    """Mock paths for testing."""

    rostering = "/ims/oneroster/rostering/v1p2"
    gradebook = "/ims/oneroster/gradebook/v1p2"
    resources = "/ims/oneroster/resources/v1p2"


class MockTransport:
    """Mock transport for testing demographics."""

    def __init__(self) -> None:
        self.paths = MockPaths()
        self.last_path: str | None = None
        self.last_body: dict[str, Any] | None = None

    async def put(self, path: str, body: dict[str, Any]) -> None:
        """Record PUT call."""
        self.last_path = path
        self.last_body = body


class TestDemographicsUpdate:
    """Tests for demographics update behavior."""

    @pytest.mark.asyncio
    async def test_update_injects_sourced_id_when_missing(self):
        """update() should inject sourcedId from path when missing from data."""
        transport = MockTransport()
        resource = DemographicsResource(transport)

        await resource.update("user-123", {"birthDate": "2000-01-01"})

        assert transport.last_body is not None
        demographics_data = transport.last_body["demographics"]
        assert demographics_data["sourcedId"] == "user-123"
        assert demographics_data["birthDate"] == "2000-01-01"

    @pytest.mark.asyncio
    async def test_update_rejects_mismatched_sourced_id(self):
        """update() should reject when data contains a different sourcedId than path."""
        transport = MockTransport()
        resource = DemographicsResource(transport)

        # Path says "user-123" but data says "user-456" - this should fail
        with pytest.raises(InputValidationError) as exc_info:
            await resource.update(
                "user-123",
                {"sourcedId": "user-456", "birthDate": "2000-01-01"},
            )

        assert "sourcedId" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_allows_matching_sourced_id(self):
        """update() should allow when data sourcedId matches path."""
        transport = MockTransport()
        resource = DemographicsResource(transport)

        # Path and data both say "user-123" - this should work
        await resource.update(
            "user-123",
            {"sourcedId": "user-123", "birthDate": "2000-01-01"},
        )

        assert transport.last_body is not None
        demographics_data = transport.last_body["demographics"]
        assert demographics_data["sourcedId"] == "user-123"
