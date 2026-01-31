"""Tests for class enrollment convenience method."""

from __future__ import annotations

from typing import Any

import pytest

from timeback_common import InputValidationError
from timeback_oneroster.resources.rostering.classes import ScopedClassResource


class MockPaths:
    rostering = "/ims/oneroster/rostering/v1p2"
    gradebook = "/ims/oneroster/gradebook/v1p2"


class MockTransport:
    def __init__(self) -> None:
        self.paths = MockPaths()
        self.last_path: str | None = None
        self.last_body: dict[str, Any] | None = None

    async def post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        self.last_path = path
        self.last_body = body
        return {"enrollment": body.get("enrollment", {})}


@pytest.mark.asyncio
async def test_enroll_copies_metadata_to_enrollment_payload() -> None:
    transport = MockTransport()
    scoped = ScopedClassResource(transport, "class-1")

    await scoped.enroll(
        {
            "sourcedId": "user-123",
            "role": "student",
            "metadata": {"source": "unit-test", "attempt": 3},
        }
    )

    assert transport.last_path == "/ims/oneroster/rostering/v1p2/classes/class-1/students"
    assert transport.last_body == {
        "enrollment": {
            "user": {"sourcedId": "user-123"},
            "metadata": {"source": "unit-test", "attempt": 3},
        }
    }


@pytest.mark.asyncio
async def test_enroll_raises_input_validation_error_on_invalid_payload() -> None:
    transport = MockTransport()
    scoped = ScopedClassResource(transport, "class-1")

    with pytest.raises(InputValidationError):
        await scoped.enroll({"sourcedId": "user-123", "role": "not-a-role"})
