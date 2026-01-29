"""Tests for user agent relationship methods."""

from __future__ import annotations

from typing import Any

import pytest

from timeback_common import InputValidationError
from timeback_oneroster.resources.rostering.users import ScopedUserResource


class MockPaths:
    rostering = "/ims/oneroster/rostering/v1p2"


class MockTransport:
    def __init__(self) -> None:
        self.paths = MockPaths()
        self.last_path: str | None = None
        self.last_body: dict[str, Any] | None = None

    async def post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        self.last_path = path
        self.last_body = body
        return {}


@pytest.mark.asyncio
async def test_add_agent_raises_input_validation_error_on_invalid_payload() -> None:
    transport = MockTransport()
    scoped = ScopedUserResource(transport, "user-1")

    with pytest.raises(InputValidationError):
        await scoped.add_agent({"agentSourcedId": ""})
