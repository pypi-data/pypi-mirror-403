"""Tests for grading period request wrapping."""

from __future__ import annotations

import pytest

from timeback_oneroster.resources.rostering.academic_sessions import (
    GradingPeriodsResource,
    ScopedTermResource,
)


class MockPaths:
    rostering = "/ims/oneroster/rostering/v1p2"


class MockTransport:
    def __init__(self, post_response: dict | None = None) -> None:
        self.paths = MockPaths()
        self.last_path: str | None = None
        self.last_body: dict | None = None
        self._post_response = post_response or {"sourcedIdPairs": []}

    async def post(self, path: str, body: dict) -> dict:
        self.last_path = path
        self.last_body = body
        return self._post_response

    async def put(self, path: str, body: dict) -> None:
        self.last_path = path
        self.last_body = body

    async def patch(self, path: str, body: dict) -> None:
        self.last_path = path
        self.last_body = body


def _session_payload() -> dict:
    return {
        "sourcedId": "gp-1",
        "status": "active",
        "title": "Q1",
        "startDate": "2024-08-15",
        "endDate": "2024-10-15",
        "type": "gradingPeriod",
        "schoolYear": "2024",
        "org": {"sourcedId": "org-1"},
    }


@pytest.mark.asyncio
async def test_grading_period_create_wraps_academic_session() -> None:
    transport = MockTransport({"sourcedIdPairs": []})
    resource = GradingPeriodsResource(transport)
    data = _session_payload()

    await resource.create(data)

    assert transport.last_body == {"academicSession": data}


@pytest.mark.asyncio
async def test_grading_period_update_wraps_academic_session() -> None:
    transport = MockTransport()
    resource = GradingPeriodsResource(transport)
    data = _session_payload()

    await resource.update("gp-1", data)

    assert transport.last_body == {"academicSession": data}


@pytest.mark.asyncio
async def test_scoped_term_create_grading_period_wraps_academic_session() -> None:
    payload = _session_payload()
    transport = MockTransport({"academicSession": payload})
    scoped = ScopedTermResource(transport, "term-1")

    await scoped.create_grading_period(payload)

    assert transport.last_body == {"academicSession": payload}
